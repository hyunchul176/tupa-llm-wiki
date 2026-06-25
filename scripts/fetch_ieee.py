#!/usr/bin/env python3
"""fetch_ieee.py — 브라우저 자동화(Playwright) 다운로드: API 없는 출판사용 (대표: IEEE, 선택 기능).

핵심 로직은 출판사 무관이다 — 페이지를 열어 `application/pdf` 응답을 가로채 저장하므로, PDF를
인라인으로 띄우는 사이트면 받힌다. IEEE는 PDF를 바로 안 띄워 전용 우회(stamp.jsp/getPDF.jsp)를
추가로 둔다. (이름이 fetch_ieee인 건 IEEE가 이 방식이 꼭 필요한 대표 사례이기 때문.)
이 스크립트만 외부 패키지(Playwright)가 필요하며, 다른 기능(fetch_paper.py / search.py)은 표준 라이브러리만으로 동작한다.

설치 (IEEE 받을 때만):
  pip install playwright && python -m playwright install chromium

접근 방식:
  - 캠퍼스망 또는 KAIST VPN: KAIST IP로 인증되어 로그인 없이 바로 풀텍스트가 열린다 (권장, 가장 간단).
  - 외부망: 한 번 'login' 으로 세션을 만들어 .browser/ 에 저장해 재사용한다.

로그인 세션 만들기 (외부망에서만 필요):
  python scripts/fetch_ieee.py login

받기 (DOI 또는 IEEE 문서 URL):
  python scripts/fetch_ieee.py fetch 10.1109/JSEN.2022.3156971
  python scripts/fetch_ieee.py fetch https://ieeexplore.ieee.org/document/9712345

주의:
  - 로그인 세션(.browser/)은 사람마다 다르며 공유되지 않는다 (.gitignore).
  - 기관 이용 약관을 지켜 짧은 시간에 과도하게 받지 않는다 (인가된 본인 접근용).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse

import _wiki
from _wiki import BROWSER, PAPERS, crossref, make_stem, norm_doi

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _need_pw():
    if not HAVE_PW:
        print("[!] Playwright 미설치 — IEEE 다운로드에만 필요합니다. 설치 후 다시 실행하세요:", file=sys.stderr)
        print("    pip install playwright && python -m playwright install chromium", file=sys.stderr)
        sys.exit(3)


def _ctx(p, headless):
    """IEEE 봇 차단(HTTP 418)을 피하려 실제 브라우저처럼 보이게 설정 (인가된 본인 접근용)."""
    ctx = p.chromium.launch_persistent_context(
        str(BROWSER), headless=headless, accept_downloads=True,
        args=["--disable-blink-features=AutomationControlled"],
        user_agent=UA, viewport={"width": 1366, "height": 900}, locale="en-US")
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return ctx


def do_login():
    _need_pw()
    BROWSER.mkdir(exist_ok=True)
    with sync_playwright() as p:
        ctx = _ctx(p, False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://ieeexplore.ieee.org/", wait_until="domcontentloaded")
        print("브라우저에서 KAIST/IEEE 로그인을 마친 뒤, 이 창에서 Enter 를 누르세요...")
        try:
            input()
        except EOFError:
            time.sleep(60)
        ctx.close()
    print(f"로그인 세션을 저장했습니다: {BROWSER}")


def _stem_for(target: str) -> str:
    """DOI면 Crossref로 stem, URL이면 임시 이름. ingest 때 에이전트가 재명명할 수 있음."""
    if target.strip().startswith("http"):
        return "ieee-paper"
    doi = norm_doi(target)
    fam, year, title, _ = crossref(doi)
    return make_stem(fam, year, title) or f"ieee-{doi.replace('/', '_')}"


def _article_url(target: str) -> str:
    t = target.strip()
    return t if t.startswith("http") else f"https://doi.org/{norm_doi(t)}"


def _find_pdf_url(page) -> str:
    """일반 출판사 PDF 주소 찾기 — 대부분 article HTML에 citation_pdf_url 메타가 있다(MDPI·Springer 등)."""
    el = page.query_selector('meta[name="citation_pdf_url"]')
    if el:
        u = (el.get_attribute("content") or "").strip()
        if u:
            return u if u.startswith("http") else urllib.parse.urljoin(page.url, u)
    for sel in ['a[href$=".pdf"]', 'a[href*="/pdf"]', 'a[data-track-action*="pdf" i]']:
        el = page.query_selector(sel)
        if el:
            href = (el.get_attribute("href") or "").strip()
            if href:
                return href if href.startswith("http") else urllib.parse.urljoin(page.url, href)
    return ""


def do_fetch(target, headless=False):
    _need_pw()
    BROWSER.mkdir(exist_ok=True)   # 캠퍼스/VPN이면 빈 세션이어도 KAIST IP로 인증됨
    PAPERS.mkdir(exist_ok=True)
    stem = _stem_for(target)
    out = PAPERS / f"{stem}.pdf"
    if stem in _wiki.existing_stems():
        print(f"  · 이미 있음: papers/{stem}.pdf — 건너뜀")
        return
    saved = {}

    with sync_playwright() as p:
        ctx = _ctx(p, headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # application/pdf 응답을 가로채 저장 (DOM 구조 변화에 강함)
        def on_response(resp):
            if saved:
                return
            try:
                if "application/pdf" in resp.headers.get("content-type", ""):
                    body = resp.body()
                    if body[:4] == b"%PDF":
                        out.write_bytes(body)
                        saved["size"] = len(body)
            except Exception:
                pass

        ctx.on("response", on_response)
        try:
            page.goto(_article_url(target), wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            m = re.search(r"/document/(\d+)", page.url)
            if m:
                arn = m.group(1)
                stamp = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arn}"
                page.goto(stamp, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)
                if not saved:
                    # stamp 뷰어가 embed 한 PDF(getPDF.jsp) 주소를 찾아 인증된 컨텍스트로 직접 받는다
                    pdf_url = ""
                    fr = page.query_selector("iframe, embed")
                    if fr:
                        src = fr.get_attribute("src") or ""
                        pdf_url = src if src.startswith("http") else (("https://ieeexplore.ieee.org" + src) if src else "")
                    if not pdf_url:
                        pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arn}&ref="
                    try:
                        r = ctx.request.get(pdf_url, headers={"Referer": stamp})
                        body = r.body()
                        if r.ok and body[:4] == b"%PDF":
                            out.write_bytes(body)
                            saved["size"] = len(body)
                    except Exception as ex:
                        print(f"  · 직접 다운로드 실패: {ex}", file=sys.stderr)
            if not saved and not m:
                # 일반 출판사(MDPI·Springer 등): citation_pdf_url/PDF 링크를 찾아 브라우저로 받는다 (urllib 403 우회)
                pdf_url = _find_pdf_url(page)
                if pdf_url:
                    print(f"  · PDF 주소: {pdf_url}")
                    try:
                        page.goto(pdf_url, wait_until="domcontentloaded", timeout=60000)
                        page.wait_for_timeout(3000)
                    except Exception:
                        pass
                    if not saved:
                        try:
                            r = ctx.request.get(pdf_url, headers={"Referer": _article_url(target)})
                            body = r.body()
                            if r.ok and body[:4] == b"%PDF":
                                out.write_bytes(body)
                                saved["size"] = len(body)
                        except Exception as ex:
                            print(f"  · 직접 다운로드 실패: {ex}", file=sys.stderr)
            page.wait_for_timeout(1500)
        except Exception as ex:
            print(f"  · 탐색 중 오류: {ex}", file=sys.stderr)
        finally:
            ctx.close()

    if saved:
        print(f"  ✅ 다운로드 성공: papers/{stem}.pdf  ({saved['size'] // 1024} KB)")
        print("  → 에이전트에게 '이 PDF ingest해줘'")
    else:
        print("  ❌ PDF를 못 받았습니다.")
        print("    캠퍼스망/KAIST VPN이면 보통 로그인 없이 받아집니다. 외부망이면 VPN을 켜거나 'login' 으로 세션을 만드세요.")
        print("    일부 사이트(예: MDPI)는 봇 차단(Access Denied)이 강해 자동 다운로드가 막힐 수 있습니다 — OA라면 브라우저에서 직접 'Download PDF' 후 papers/에 넣으세요.")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="IEEE 브라우저 기반 다운로드 (선택 기능)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login", help="로그인 세션 1회 생성 (외부망)")
    f = sub.add_parser("fetch", help="DOI/URL로 PDF 받기")
    f.add_argument("target", help="DOI 또는 IEEE 문서 URL")
    f.add_argument("--headless", action="store_true", help="창 없이 실행 (차단될 수 있음)")
    args = ap.parse_args()

    if args.cmd == "login":
        do_login()
    else:
        do_fetch(args.target, headless=args.headless)


if __name__ == "__main__":
    main()
