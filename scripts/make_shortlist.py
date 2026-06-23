#!/usr/bin/env python3
"""make_shortlist.py — 후보 논문 선별(curation) 체크리스트 생성.

검색(search.py) 후보를 JSON으로 받아, 사람이 취사선택하는 클릭형 체크리스트를 만든다.
출력은 **아티팩트로 바로 발행 가능한 형식**(body-only HTML, 외부 폰트/요청 없음 — 시스템 폰트).

  찾기 → (이 단계: 선별) → 받기

쓰는 법:
  - Claude Code: 이 스크립트로 shortlist.html 을 만든 뒤, 그 파일을 **아티팩트로 발행**해
    학생에게 링크를 준다. 학생이 체크 → "선택 복사" → 채팅에 붙여넣으면 그 id만 받는다.
  - Codex / 오프라인: shortlist.html 을 브라우저로 직접 열어 고른다 (동일 동작).

표준 라이브러리만 사용. 아티팩트는 외부 CSS/폰트를 막으므로 시스템 폰트만 쓴다.

JSON 스키마 (에이전트가 search.py 결과 + 초록 요약으로 만든다):
{
  "topic": "내 연구 주제(선택)",
  "categories": [
    {"name": "후보",
     "papers": [
       {"title":"...", "authors":"Kim et al.", "year":2024, "venue":"arXiv",
        "id":"2406.09246", "url":"https://...",
        "summary":"초록 기반 한두 줄 요약", "note":"왜 관련 있는지(선택)",
        "oa":true, "exclude":false}
     ]}
  ]
}
- id: DOI 또는 arXiv id (선택 복사 시 이 값이 줄바꿈으로 모임)
- exclude: true 면 기본 체크 해제 + "제외 추천" 표시

사용 예:
  python scripts/make_shortlist.py --input shortlist.json
  cat shortlist.json | python scripts/make_shortlist.py --out shortlist.html
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

from _wiki import ROOT


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def main():
    ap = argparse.ArgumentParser(description="후보 논문 선별 체크리스트 생성 (아티팩트 호환)")
    ap.add_argument("--input", help="JSON 경로 (없으면 stdin)")
    ap.add_argument("--out", help="출력 HTML (기본: shortlist.html)")
    args = ap.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    d = json.loads(raw)
    cats = d.get("categories", [])
    total = sum(len(c.get("papers", [])) for c in cats)
    rec = sum(1 for c in cats for p in c.get("papers", []) if not p.get("exclude"))

    rows = []
    for c in cats:
        items = []
        for p in c.get("papers", []):
            ex = bool(p.get("exclude"))
            pid = esc(p.get("id") or "")
            title = esc(p.get("title") or "(제목 없음)")
            if p.get("url"):
                title = f'<a href="{esc(p["url"])}" target="_blank" rel="noopener">{title}</a>'
            meta = " · ".join(esc(x) for x in [p.get("authors"), p.get("year"), p.get("venue"), p.get("id")] if x)
            tags = ""
            if ex:
                tags += '<span class="extag">제외 추천</span>'
            tags += '<span class="oatag free">무료본</span>' if p.get("oa") else '<span class="oatag key">키/브라우저</span>'
            summary = f'<span class="rsum"><b>내용</b> {esc(p.get("summary"))}</span>' if p.get("summary") else ""
            note = f'<span class="rnote"><b>판단</b> {esc(p.get("note"))}</span>' if p.get("note") else ""
            items.append(
                f'<label class="row{" ex" if ex else ""}">'
                f'<input type="checkbox" class="cb" data-id="{pid}"{"" if ex else " checked"}>'
                f'<span class="rmain"><span class="rtitle">{title}{tags}</span>'
                f'<span class="rmeta">{meta}</span>{summary}{note}</span></label>'
            )
        rows.append(f'<section class="cat"><h2>{esc(c.get("name") or "후보")} <span class="n">{len(c.get("papers", []))}</span></h2>{"".join(items)}</section>')

    # body-only (아티팩트 발행용). 외부 폰트/요청 없음.
    page = f"""<style>
  .sl{{--navy-900:#0c1f3d;--navy-800:#13294b;--navy-700:#1d3a5f;--navy-600:#2f5a8a;--navy-100:#e7eef8;--navy-050:#f4f7fc;
    --ink:#17202d;--muted:#5d6878;--line:#e3e9f2;--red:#d12f3c;--red-dark:#a81b27;--red-050:#fdeef0;
    --sans:"Apple SD Gothic Neo","Malgun Gothic",-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
    background:var(--navy-050);color:var(--ink);font-family:var(--sans);line-height:1.6;font-size:16px;
    max-width:880px;margin:0 auto;padding:1.4rem 1.2rem 3rem;}}
  .sl *{{box-sizing:border-box;}}
  .sl header{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--red);border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:1.1rem;}}
  .sl .kick{{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--red-dark);font-weight:700;}}
  .sl h1{{font-size:1.4rem;margin:.25rem 0 .5rem;color:var(--navy-800);}}
  .sl .q{{font-size:.92rem;color:var(--muted);}}
  .sl .hint{{font-size:.86rem;color:var(--muted);margin-top:.5rem;}}
  .sl .bar{{position:sticky;top:0;z-index:5;background:var(--navy-050);padding:.7rem 0;display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:.6rem;}}
  .sl .btn{{font:600 .9rem var(--sans);padding:.5rem .9rem;border-radius:8px;border:1px solid var(--navy-800);background:var(--navy-800);color:#fff;cursor:pointer;}}
  .sl .btn.ghost{{background:#fff;color:var(--muted);border-color:var(--line);}}
  .sl .cat{{margin:1.2rem 0;}}
  .sl .cat h2{{font-size:1.05rem;color:var(--navy-800);border-bottom:2px solid var(--line);padding-bottom:.35rem;}}
  .sl .cat h2 .n{{font-size:.78rem;color:var(--muted);font-weight:600;}}
  .sl .row{{display:flex;gap:.7rem;align-items:flex-start;padding:.7rem .8rem;border:1px solid var(--line);border-radius:10px;margin:.45rem 0;background:#fff;cursor:pointer;}}
  .sl .row.ex{{opacity:.6;background:var(--navy-050);}}
  .sl .cb{{margin-top:.25rem;width:18px;height:18px;flex:none;accent-color:var(--red);}}
  .sl .rtitle{{font-weight:700;font-size:.98rem;color:var(--navy-800);}}
  .sl .rtitle a{{color:var(--navy-800);text-decoration:none;}}
  .sl .rtitle a:hover{{color:var(--red);}}
  .sl .extag{{font-size:.68rem;font-weight:800;color:var(--red-dark);background:var(--red-050);border:1px solid #eec4c9;border-radius:5px;padding:.05rem .4rem;margin-left:.45rem;vertical-align:middle;}}
  .sl .oatag{{font-size:.68rem;font-weight:700;border-radius:5px;padding:.05rem .4rem;margin-left:.45rem;vertical-align:middle;}}
  .sl .oatag.free{{color:var(--navy-800);background:var(--navy-100);}}
  .sl .oatag.key{{color:#fff;background:var(--navy-600);}}
  .sl .rmeta{{display:block;font-size:.8rem;color:var(--muted);margin-top:.15rem;}}
  .sl .rsum{{display:block;font-size:.88rem;color:var(--ink);margin-top:.35rem;line-height:1.55;}}
  .sl .rnote{{display:block;font-size:.86rem;color:var(--muted);margin-top:.3rem;font-style:italic;}}
  .sl .rsum b,.sl .rnote b{{display:inline-block;font-style:normal;font-size:.66rem;font-weight:800;letter-spacing:.04em;color:#fff;background:var(--navy-700);border-radius:4px;padding:.05rem .35rem;margin-right:.4rem;vertical-align:middle;}}
  .sl .rnote b{{background:var(--muted);}}
  .sl textarea#slout{{width:100%;height:90px;margin-top:.7rem;border:1px solid var(--line);border-radius:8px;padding:.6rem;font:13px/1.5 ui-monospace,Consolas,monospace;display:none;}}
  .sl .toast{{font-size:.85rem;color:var(--red-dark);font-weight:700;}}
</style>
<div class="sl">
  <header>
    <div class="kick">후보 선별 · Curation</div>
    <h1>이 논문들 중 받을 것을 골라주세요</h1>
    <div class="q"><b>주제:</b> {esc(d.get("topic") or "(미지정)")}</div>
    <div class="hint">관련 없는 건 체크를 해제하세요. <b>제외 추천</b>은 기본 해제돼 있습니다. 다 고른 뒤 <b>선택 복사</b>를 눌러 에이전트에 붙여넣으면, 그 논문만 받습니다.</div>
  </header>
  <div class="bar">
    <button class="btn" onclick="slCopy()">✓ 선택한 <span id="slcnt">{rec}</span>편 복사</button>
    <button class="btn ghost" onclick="slAll(true)">모두 선택</button>
    <button class="btn ghost" onclick="slAll(false)">모두 해제</button>
    <span class="toast" id="sltoast"></span>
  </div>
  <textarea id="slout" readonly></textarea>
  {"".join(rows)}
</div>
<script>
  var slcbs=function(){{return Array.prototype.slice.call(document.querySelectorAll('.sl .cb'));}};
  function slUpd(){{document.getElementById('slcnt').textContent=slcbs().filter(function(c){{return c.checked;}}).length;}}
  function slAll(v){{slcbs().forEach(function(c){{c.checked=v;}});slUpd();}}
  function slCopy(){{
    var ids=slcbs().filter(function(c){{return c.checked;}}).map(function(c){{return c.dataset.id;}}).filter(Boolean);
    var text=ids.join('\\n');
    var ta=document.getElementById('slout');ta.style.display='block';ta.value=text;ta.focus();ta.select();
    try{{ta.setSelectionRange(0,text.length);}}catch(e){{}}
    var toast=document.getElementById('sltoast');
    var ok=function(){{toast.textContent=ids.length+'편 복사됨 — 에이전트에 붙여넣으세요';}};
    var manual=function(){{toast.textContent=ids.length+'편 선택됨 — 아래 칸을 Ctrl+C로 복사하세요';}};
    var did=false; try{{did=document.execCommand('copy');}}catch(e){{}}
    if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(text).then(ok,function(){{if(did){{ok();}}else{{manual();}}}});}}
    else{{if(did){{ok();}}else{{manual();}}}}
  }}
  document.addEventListener('change',function(e){{if(e.target.classList&&e.target.classList.contains('cb'))slUpd();}});
  slUpd();
</script>
"""
    out = Path(args.out) if args.out else ROOT / "shortlist.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"후보 선별 체크리스트 생성: {out}")
    print(f"  총 {total}편 · 추천(기본 선택) {rec}편 · 제외 추천 {total - rec}편")
    print("  → Claude Code: 이 파일을 아티팩트로 발행해 링크 제공 / Codex·오프라인: 브라우저로 직접 열기")


if __name__ == "__main__":
    main()
