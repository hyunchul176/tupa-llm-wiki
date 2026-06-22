"""공용 헬퍼 — 표준 라이브러리만 사용 (외부 설치 불필요).

수집 스크립트(fetch_paper.py / search.py / fetch_ieee.py)가 공유한다.
파이썬이 스크립트 폴더를 sys.path에 자동 추가하므로 `import _wiki` 가능.

- 키는 secrets/api-keys.json 에서만 읽는다 (커밋 안 됨. api-keys.example.json 참고).
- 받은 PDF는 papers/ 에 stem 규칙(<firstauthor><year>-<keyword>.pdf)으로 저장한다.
- 코드/로그에 키 값을 출력하지 않는다.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# 윈도우 콘솔(cp949)에서 특수문자/이모지 출력 시 크래시 방지 — UTF-8 고정
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "papers"
BROWSER = ROOT / ".browser"          # IEEE 로그인 세션 (절대 커밋 금지)
KEYS_PATH = ROOT / "secrets" / "api-keys.json"


def load_keys() -> dict:
    if KEYS_PATH.exists():
        try:
            return json.loads(KEYS_PATH.read_text(encoding="utf-8"))
        except Exception:
            print("[!] secrets/api-keys.json 을 읽지 못했습니다 (형식 확인). 키 없이 진행합니다.", file=sys.stderr)
    return {}


KEYS = load_keys()
CONTACT = (KEYS.get("contact_email") or "research@kaist.ac.kr").strip()
UA = f"TUPA-LLM-Wiki/1.0 (mailto:{CONTACT})"


def norm_doi(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:", "", s, flags=re.I)
    return s


# arXiv id: 2406.09246 / 2406.09246v3 / math.GT/0309136 등
ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$|^[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$", re.I)


def looks_like_arxiv(s: str) -> bool:
    s = s.strip()
    s = re.sub(r"^arxiv:", "", s, flags=re.I)
    return bool(ARXIV_ID.match(s))


def looks_like_doi(s: str) -> bool:
    s = s.strip().lower()
    return s.startswith("10.") or "doi.org/" in s or s.startswith("doi:")


def slugify(s: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:n]


def make_stem(family: str, year: str, title: str) -> str:
    """<firstauthor><year>-<핵심키워드> (AGENTS.md §3 규칙)."""
    kw = slugify((title or "").split(":")[0])
    fam = slugify(family)
    if fam:
        return f"{fam}{year}-{kw}".strip("-")
    return (kw or f"paper-{year}").strip("-")


def family_of(name: str) -> str:
    """'Hyunchul Park' → 'Park', 'Park, Hyunchul' → 'Park'. 대략적."""
    name = (name or "").strip()
    if "," in name:
        return name.split(",")[0].strip()
    parts = name.split()
    return parts[-1] if parts else ""


def http_bytes(url: str, headers: dict | None = None, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_json(url: str, headers: dict | None = None, timeout: int = 30) -> dict:
    return json.loads(http_bytes(url, {"Accept": "application/json", **(headers or {})}, timeout))


def crossref(doi: str):
    """Crossref 메타데이터 → (family, year, title, publisher). 실패 시 ('', '', '', '')."""
    try:
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
        m = http_json(url, timeout=30)["message"]
    except Exception:
        return "", "", "", ""
    fam = ""
    if m.get("author"):
        a = m["author"][0]
        fam = a.get("family") or family_of(a.get("name", ""))
    year = ""
    for k in ("published-print", "published-online", "issued", "created"):
        dp = (m.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            year = str(dp[0][0])
            break
    title = (m.get("title") or [""])[0]
    publisher = m.get("publisher", "")
    return fam, year, title, publisher


def existing_stems() -> set[str]:
    if not PAPERS.exists():
        return set()
    return {p.stem for p in PAPERS.glob("*.pdf")}


def save_pdf(data: bytes, stem: str) -> Path:
    """%PDF 검증 후 papers/<stem>.pdf 로 저장. 잘못된 데이터면 RuntimeError."""
    if not data or data[:4] != b"%PDF":
        head = data[:80] if data else b""
        raise RuntimeError(f"PDF 아님 (앞부분: {head!r}) — 권한/엔타이틀먼트/네트워크 확인")
    PAPERS.mkdir(exist_ok=True)
    dest = PAPERS / f"{stem}.pdf"
    dest.write_bytes(data)
    return dest
