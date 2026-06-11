#!/usr/bin/env python3
"""
fetch_paper.py — DOI로 전문(full-text) PDF를 받아 papers/에 저장.

사용:  python scripts/fetch_paper.py <DOI> [<DOI> ...]
예  :  python scripts/fetch_paper.py 10.1016/j.trf.2025.103482

- 키는 secrets/api-keys.json 에서 읽음 (커밋 안 됨. api-keys.example.json 참고).
- Crossref(무료)로 메타데이터 → 파일명 stem(<firstauthor><year>-<keyword>) 생성 + 출판사 판별.
- 출판사별 API로 PDF 다운로드: Elsevier(ScienceDirect), Wiley(TDM), Springer. (대학 망에서 실행 필요)
- 저장 후 내용 ingest는 AI 에이전트가 수행 (sources/wiki/...).
표준 라이브러리만 사용 (외부 설치 불필요).
"""
import json, sys, re, pathlib, urllib.request, urllib.parse, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEYS_PATH = ROOT / "secrets" / "api-keys.json"
KEYS = json.loads(KEYS_PATH.read_text(encoding="utf-8")) if KEYS_PATH.exists() else {}
PAPERS = ROOT / "papers"
UA = f"TUPA-LLM-Wiki/1.0 (mailto:{KEYS.get('contact_email', 'research@kaist.ac.kr')})"

try:  # Windows 콘솔(cp949)에서 이모지 출력 깨짐 방지
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def _get(url, headers, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)

def slugify(s, n=40):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:n]

def crossref(doi):
    """Crossref 메타데이터 → (firstauthor_family, year, title, publisher)."""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    with _get(url, {"User-Agent": UA}, 30) as r:
        m = json.loads(r.read())["message"]
    fam = ""
    if m.get("author"):
        a = m["author"][0]
        fam = a.get("family") or a.get("name") or ""
    year = ""
    for k in ("published-print", "published-online", "issued", "created"):
        dp = (m.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = str(dp[0][0]); break
    title = (m.get("title") or [""])[0]
    publisher = m.get("publisher", "")
    return fam, year, title, publisher

def make_stem(fam, year, title):
    kw = slugify(title.split(":")[0])
    return f"{slugify(fam)}{year}-{kw}".strip("-") if fam else (slugify(title) or f"doi-{year}")

def download_pdf(doi, publisher, dest):
    pub = (publisher or "").lower()
    if "elsevier" in pub:
        key = KEYS.get("elsevier_api_key", "")
        if not key: raise RuntimeError("elsevier_api_key 비어있음")
        url = f"https://api.elsevier.com/content/article/doi/{doi}"
        headers = {"X-ELS-APIKey": key, "Accept": "application/pdf", "User-Agent": UA}
    elif "wiley" in pub:
        tok = KEYS.get("wiley_tdm_token", "")
        if not tok: raise RuntimeError("wiley_tdm_token 비어있음")
        url = f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{urllib.parse.quote(doi, safe='')}"
        headers = {"Wiley-TDM-Client-Token": tok, "Accept": "application/pdf", "User-Agent": UA}
    elif "springer" in pub:
        key = KEYS.get("springer_api_key", "")
        if not key: raise RuntimeError("springer_api_key 비어있음 (Springer 미지원)")
        url = f"https://api.springernature.com/meta/v2/pdf/{doi}?api_key={key}"
        headers = {"Accept": "application/pdf", "User-Agent": UA}
    else:
        raise RuntimeError(f"미지원 출판사: {publisher!r} — PDF 수동 다운로드 필요")
    with _get(url, headers, 120) as r:
        data = r.read()
    if data[:4] != b"%PDF":
        raise RuntimeError(f"PDF 아님 (앞부분: {data[:60]!r}) — 권한/엔타이틀먼트 확인")
    dest.write_bytes(data)

def fetch(doi):
    fam, year, title, publisher = crossref(doi)
    stem = make_stem(fam, year, title)
    dest = PAPERS / f"{stem}.pdf"
    PAPERS.mkdir(exist_ok=True)
    print(f"  DOI       : {doi}")
    print(f"  title     : {title}")
    print(f"  publisher : {publisher}")
    print(f"  stem      : {stem}")
    download_pdf(doi, publisher, dest)
    print(f"  ✅ saved  : papers/{stem}.pdf ({dest.stat().st_size:,} bytes)\n")
    return stem

if __name__ == "__main__":
    dois = sys.argv[1:]
    if not dois:
        print("사용: python scripts/fetch_paper.py <DOI> [<DOI> ...]"); sys.exit(1)
    ok, fail = [], []
    for doi in dois:
        print(f"▶ {doi}")
        try:
            ok.append(fetch(doi))
        except urllib.error.HTTPError as e:
            body = e.read()[:200]
            print(f"  ❌ HTTP {e.code}: {body!r}\n"); fail.append(doi)
        except Exception as e:
            print(f"  ❌ {e}\n"); fail.append(doi)
    print(f"완료: 성공 {len(ok)} / 실패 {len(fail)}")
    if ok:   print("  ingest 대상:", ", ".join(ok))
    if fail: print("  실패:", ", ".join(fail))
