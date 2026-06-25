#!/usr/bin/env python3
"""PDF에서 주요 figure/table 이미지를 뽑아 저장한다 (PyMuPDF). — 리뷰 HTML(심화)용.

추출 목록(manifest)을 출력하니, 그중 핵심 그림을 골라 리뷰 카드에 넣으면 된다.
출력 폴더는 보통 `review/<주제>/images/` 로 지정한다.

설치: pip install pymupdf  (또는 uv add pymupdf — requirements/pyproject에 이미 있음)

모드 (--mode):
  caption  (기본·권장) "Figure N"/"Table N" 캡션을 찾아 그 위 그림 영역을 통째로 렌더.
                       벡터·래스터 그림 모두 한 장으로 온전히 나온다.
  embedded             논문에 박힌 raster 이미지를 그대로 추출 (사진 많은 논문).
  pages                각 페이지 통째 렌더 (최후 수단).

사용 예:
  python scripts/extract_figures.py papers/paolillo2014-...pdf --prefix paolillo2014 --out review/humanoid-driving/images
  python scripts/extract_figures.py papers/xxx.pdf --prefix xxx --mode embedded --out review/topic/images
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _wiki import ROOT

CAP_RE = re.compile(r"^\s*(figure|fig|table)\s*\.?\s*(\d+)", re.I)

try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except Exception:
    HAVE_FITZ = False


def _need_fitz():
    if not HAVE_FITZ:
        print("[!] PyMuPDF 미설치. 설치 후 다시 실행:\n    pip install pymupdf   (또는 uv add pymupdf)", file=sys.stderr)
        sys.exit(3)


def _save_pix(pix, out):
    if pix.n - pix.alpha >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(str(out))
    return out.stat().st_size // 1024


# ---- 모드 1: 캡션 기준 영역 렌더링 (기본, 권장) ----
def by_caption(doc, prefix, out_dir, dpi, band_frac, pad):
    """캡션("Fig. N …") 위의 그림 영역만 잘라 렌더한다.

    합쳐짐·본문 캡쳐를 막기 위한 규칙:
      - ceiling: 같은 열에서 **바로 위 캡션**의 아래까지만 거슬러 올라간다(이전 그림 침범 금지).
      - 그림(임베디드 이미지·벡터 드로잉)이 캡션 위에 **없으면 건너뛴다** — 본문 텍스트 밴드로 fallback 하지 않는다.
      - 간격이 큰(다른 그림으로 추정되는) 블록은 union 하지 않는다.
      - 캡션 블록이 다음 단락과 붙어 있어도, 캡션부는 최대 몇 줄만 포함한다.
    """
    saved, used = [], {}
    for pno in range(len(doc)):
        page = doc[pno]
        H, W = page.rect.height, page.rect.width
        blocks = page.get_text("dict").get("blocks", [])
        caps = []
        for b in blocks:
            if b.get("type") != 0:
                continue
            txt = "".join(s.get("text", "") for l in b.get("lines", []) for s in l.get("spans", []))
            m = CAP_RE.match(txt)
            if m:
                lines = [(fitz.Rect(l["bbox"]), "".join(s.get("text", "") for s in l.get("spans", [])))
                         for l in b.get("lines", [])]
                caps.append((m.group(1).lower(), m.group(2), fitz.Rect(b["bbox"]), lines))
        if not caps:
            continue
        # 그림 후보 = 임베디드 이미지(type 1) + 벡터 드로잉 (텍스트는 제외)
        content = [fitz.Rect(b["bbox"]) for b in blocks if b.get("type") == 1]
        try:
            content += [fitz.Rect(d["rect"]) for d in page.get_drawings()]
        except Exception:
            pass
        cap_rects = [c[2] for c in caps]
        gap_limit = 0.10 * H
        for kind, num, cb, cap_lines in caps:
            x0, x1 = max(0, cb.x0 - pad), min(W, cb.x1 + pad)
            # ceiling: 같은 열에서 바로 위 캡션의 아래 경계 (없으면 band_frac 만큼만)
            ceiling = max(0.0, cb.y0 - band_frac * H)
            for rc in cap_rects:
                if rc is cb:
                    continue
                if rc.y1 <= cb.y0 - 2 and rc.x1 > x0 and rc.x0 < x1:
                    ceiling = max(ceiling, rc.y1 + 1)
            # 캡션 위·ceiling 아래·같은 열에 있는 그림 블록만
            cand = [r for r in content
                    if r.y1 <= cb.y0 + 2 and r.y0 >= ceiling and r.x1 > x0 and r.x0 < x1
                    and r.height > 6 and r.width > 16]
            if not cand:
                continue  # 그림이 없으면 건너뜀 (본문 텍스트로 fallback 하지 않음)
            # 캡션에 가장 가까운 블록부터, 간격이 크면(다른 그림) 멈추고 union
            cand.sort(key=lambda r: r.y1, reverse=True)
            union = cand[0]
            for r in cand[1:]:
                if union.y0 - r.y1 > gap_limit:
                    break
                union = union | r
            # crop: 그림 영역 + 캡션부. 캡션 블록에 다음 단락이 붙어 있으면
            # (빈 줄 또는 큰 줄간격에서) 끊어 본문이 딸려오지 않게 한다.
            cap_bottom = cb.y1
            cl = sorted(cap_lines, key=lambda lr: lr[0].y0)
            got = False
            prev_y1 = None
            lh = 10.0
            for r, t in cl:
                blank = (t.strip() == "")
                big_gap = (prev_y1 is not None and r.y0 - prev_y1 > 0.7 * lh)
                if got and (blank or big_gap):
                    break
                if not blank:
                    cap_bottom = r.y1
                    got = True
                    lh = max(r.height, 6)
                prev_y1 = r.y1
            cap_bottom = min(cap_bottom, cb.y0 + 0.13 * H)
            cx0 = min(union.x0, cb.x0) - pad
            cx1 = max(union.x1, cb.x1) + pad
            clip = fitz.Rect(cx0, union.y0 - pad, cx1, cap_bottom) & page.rect
            # 크기 sanity: 진짜 그림인지 (밑줄·조각 배제)
            if clip.width < 80 or clip.height < 60 or clip.width * clip.height < 0.03 * W * H:
                continue
            label = f"{'table' if kind == 'table' else 'fig'}{num}"
            used[label] = used.get(label, 0) + 1
            name = f"{prefix}_{label}" + (f"_{used[label]}" if used[label] > 1 else "") + ".png"
            out = out_dir / name
            kb = _save_pix(page.get_pixmap(dpi=dpi, clip=clip), out)
            saved.append((out, int(clip.width), int(clip.height), kb))
    return saved


# ---- 모드 2: 임베디드 raster 추출 ----
def embedded(doc, prefix, out_dir, min_w, min_h, min_area, max_ar):
    saved, seen = [], set()
    for pno in range(len(doc)):
        for idx, img in enumerate(doc[pno].get_images(full=True)):
            xref = img[0]
            if xref in seen:
                continue
            seen.add(xref)
            try:
                pix = fitz.Pixmap(doc, xref)
                w, h = pix.width, pix.height
                ar = max(w, h) / max(1, min(w, h))
                if w < min_w or h < min_h or w * h < min_area or ar > max_ar:
                    continue
                out = out_dir / f"{prefix}_p{pno + 1}_{idx + 1}.png"
                kb = _save_pix(pix, out)
                saved.append((out, w, h, kb))
            except Exception as e:
                print(f"  (p{pno + 1} img{idx + 1} 실패: {e})", file=sys.stderr)
    return saved


# ---- 모드 3: 페이지 통째 렌더링 ----
def pages(doc, prefix, out_dir, dpi):
    saved = []
    for pno in range(len(doc)):
        out = out_dir / f"{prefix}_page{pno + 1}.png"
        kb = _save_pix(doc[pno].get_pixmap(dpi=dpi), out)
        saved.append((out, None, None, kb))
    return saved


def main():
    ap = argparse.ArgumentParser(description="PDF figure 추출 (PyMuPDF) — 리뷰 HTML용")
    ap.add_argument("pdf")
    ap.add_argument("--prefix", help="파일명 접두어 (기본: PDF stem)")
    ap.add_argument("--out", help="출력 폴더 (기본: review/images). 보통 review/<주제>/images 로 지정")
    ap.add_argument("--mode", choices=["caption", "embedded", "pages"], default="caption")
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--band-frac", type=float, default=0.5)
    ap.add_argument("--pad", type=float, default=6.0)
    ap.add_argument("--min-width", type=int, default=250)
    ap.add_argument("--min-height", type=int, default=150)
    ap.add_argument("--min-area", type=int, default=60000)
    ap.add_argument("--max-aspect", type=float, default=8.0)
    args = ap.parse_args()

    _need_fitz()
    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"[!] PDF 없음: {pdf}", file=sys.stderr)
        sys.exit(2)
    prefix = args.prefix or pdf.stem.replace(".", "_")
    out_dir = Path(args.out) if args.out else (ROOT / "review" / "images")
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf))
    if args.mode == "caption":
        saved = by_caption(doc, prefix, out_dir, args.dpi, args.band_frac, args.pad)
    elif args.mode == "embedded":
        saved = embedded(doc, prefix, out_dir, args.min_width, args.min_height, args.min_area, args.max_aspect)
    else:
        saved = pages(doc, prefix, out_dir, args.dpi)
    doc.close()

    print(f"[extract_figures · {args.mode}] {pdf.name} → {out_dir}")
    saved.sort(key=lambda t: t[3], reverse=True)
    for out, w, h, kb in saved:
        dim = f"{w}x{h}" if w else "page"
        print(f"  {out.name}  {dim}  {kb}KB")
    print(f"총 {len(saved)}개 저장. 열어 확인하고 핵심 그림을 골라 리뷰 카드에 넣으세요.")
    if not saved and args.mode == "caption":
        print("캡션을 못 찾음 → --mode embedded 또는 --mode pages 로 재시도.")


if __name__ == "__main__":
    main()
