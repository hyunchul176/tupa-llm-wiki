#!/usr/bin/env python3
"""search.py — 주제/키워드로 논문 후보를 찾는다 (arXiv + OpenAlex + Semantic Scholar + Scopus). 표준 라이브러리만.

받는 게 아니라 '찾아 보여주는' 단계다. 결과에서 받을 것을 골라 fetch_paper.py 로 넘긴다.
출처는 커버리지가 서로 달라 보완적이다 — arXiv=프리프린트, OpenAlex=넓은 메타데이터,
Semantic Scholar=TL;DR 요약·다른 랭킹, Scopus=큐레이션·인용(키 필요).

사용:
  python scripts/search.py "vision language action humanoid driving"
  python scripts/search.py "micromobility overtaking safety" --limit 10 --source openalex

옵션:
  --limit N      각 출처에서 N개 (기본 8)
  --source X     arxiv | openalex | semanticscholar(s2) | scopus | both | all (기본 all)
                 Scopus는 키가 있어야 동작(secrets: scopus_api_key, 기관망 밖이면 scopus_inst_token).
                 all 에서는 Scopus 키가 있을 때만 자동 포함.

출력의 각 항목 끝에 '받기' 명령을 같이 보여준다. 무료본(OA) 여부도 표시.
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

import _wiki
from _wiki import http_bytes, http_json, norm_doi

ATOM = "{http://www.w3.org/2005/Atom}"


def _authors_str(names, n=3):
    names = [x for x in names if x]
    if not names:
        return "(저자 미상)"
    return ", ".join(names[:n]) + (f" 외 {len(names) - n}명" if len(names) > n else "")


def search_arxiv(query: str, limit: int):
    url = (f"http://export.arxiv.org/api/query?search_query=all:"
           f"{urllib.parse.quote(query)}&start=0&max_results={limit}")
    root = ET.fromstring(http_bytes(url, timeout=30).decode("utf-8", "replace"))
    out = []
    for e in root.findall(f"{ATOM}entry"):
        sid = (e.findtext(f"{ATOM}id", "") or "").rsplit("/abs/", 1)[-1]
        out.append({
            "title": " ".join((e.findtext(f"{ATOM}title", "") or "").split()),
            "authors": [a.findtext(f"{ATOM}name", "") for a in e.findall(f"{ATOM}author")],
            "year": (e.findtext(f"{ATOM}published", "") or "")[:4],
            "abstract": " ".join((e.findtext(f"{ATOM}summary", "") or "").split()),
            "id": sid, "id_kind": "arXiv", "oa": True,
        })
    return out


def _oa_abstract(w):
    """OpenAlex abstract_inverted_index → 평문 초록. 없으면 ''."""
    inv = w.get("abstract_inverted_index")
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[k] for k in sorted(pos))


def search_openalex(query: str, limit: int):
    url = (f"https://api.openalex.org/works?search={urllib.parse.quote(query)}"
           f"&per_page={limit}&mailto={urllib.parse.quote(_wiki.CONTACT)}")
    works = http_json(url, timeout=30).get("results", [])
    out = []
    for w in works:
        names = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])]
        doi = norm_doi(w.get("doi") or "")
        out.append({
            "title": w.get("display_name", "(제목 없음)"),
            "authors": names,
            "year": str(w.get("publication_year") or "?"),
            "abstract": _oa_abstract(w),
            "id": doi, "id_kind": "DOI",
            "oa": bool((w.get("open_access") or {}).get("is_oa")),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "cited": w.get("cited_by_count", 0),
        })
    return out


def search_semanticscholar(query: str, limit: int):
    """Semantic Scholar Graph API. 무료(키 없으면 rate limit). TL;DR 자동요약 제공."""
    fields = "title,authors,year,abstract,externalIds,openAccessPdf,venue,citationCount,tldr"
    url = (f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}"
           f"&limit={limit}&fields={fields}")
    # 선택적 API 키(secrets/api-keys.json의 "semantic_scholar")가 있으면 rate limit이 크게 완화된다.
    key = (_wiki.KEYS.get("semantic_scholar") or "").strip()
    headers = {"x-api-key": key} if key else None
    data = []
    for attempt in range(3):
        try:
            data = http_json(url, headers=headers, timeout=30).get("data", []) or []
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:  # 무료 공용 풀은 자주 429 → 잠깐 쉬고 재시도
                time.sleep(2 * (attempt + 1))
                continue
            raise
    out = []
    for w in data:
        ext = w.get("externalIds") or {}
        doi = norm_doi(ext.get("DOI") or "")
        arx = ext.get("ArXiv") or ""
        if doi:
            ident, kind = doi, "DOI"
        elif arx:
            ident, kind = arx, "arXiv"
        else:
            ident, kind = "", "DOI"
        tldr = (w.get("tldr") or {}).get("text") or ""
        out.append({
            "title": w.get("title") or "(제목 없음)",
            "authors": [a.get("name", "") for a in (w.get("authors") or [])],
            "year": str(w.get("year") or "?"),
            "abstract": (f"TL;DR: {tldr}" if tldr else (w.get("abstract") or "")),
            "id": ident, "id_kind": kind,
            "oa": bool(w.get("openAccessPdf")),
            "venue": w.get("venue") or "",
            "cited": w.get("citationCount", 0),
        })
    return out


def search_scopus(query: str, limit: int):
    """Scopus Search API. 키 필요(secrets: scopus_api_key, 기관망 밖이면 scopus_inst_token)."""
    key = (_wiki.KEYS.get("scopus_api_key") or "").strip()
    if not key:
        raise RuntimeError("scopus_api_key 없음 — Scopus는 키 필요 (secrets/api-keys.json)")
    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    inst = (_wiki.KEYS.get("scopus_inst_token") or "").strip()
    if inst:
        headers["X-ELS-Insttoken"] = inst
    q = f"TITLE-ABS-KEY({query})"
    url = (f"https://api.elsevier.com/content/search/scopus?query={urllib.parse.quote(q)}"
           f"&count={limit}")
    res = http_json(url, headers=headers, timeout=30).get("search-results", {})
    out = []
    for e in res.get("entry", []) or []:
        if e.get("error"):
            continue
        doi = norm_doi(e.get("prism:doi") or "")
        out.append({
            "title": e.get("dc:title") or "(제목 없음)",
            "authors": [e.get("dc:creator")] if e.get("dc:creator") else [],
            "year": (e.get("prism:coverDate") or "")[:4] or "?",
            "abstract": e.get("dc:description") or "",
            "id": doi, "id_kind": "DOI",
            "oa": str(e.get("openaccess")) == "1",
            "venue": e.get("prism:publicationName") or "",
            "cited": int(e.get("citedby-count") or 0),
        })
    return out


def _print(section, items):
    print(f"\n===== {section} — {len(items)}편 =====")
    for i, it in enumerate(items, 1):
        oa = "무료본 있음" if it.get("oa") else "기관키/브라우저 필요"
        print(f"[{i}] {it['title']}")
        print(f"    {_authors_str(it['authors'])} · {it['year']}"
              + (f" · {it.get('venue')}" if it.get("venue") else "")
              + (f" · 인용 {it.get('cited')}" if it.get("cited") is not None and it.get("venue") else ""))
        ab = (it.get("abstract") or "").strip()
        if ab:
            ab = ab[:240].rsplit(" ", 1)[0] + "…" if len(ab) > 240 else ab
            print(f"    초록: {ab}")
        if it["id"]:
            print(f"    {it['id_kind']}: {it['id']}   ({oa})")
            print(f"    받기 →  python scripts/fetch_paper.py {it['id']}")
        else:
            print(f"    ({it['id_kind']} 없음 — 받기 어려움)")
        print()


def main():
    ap = argparse.ArgumentParser(description="주제/키워드 논문 검색 (arXiv + OpenAlex + Semantic Scholar)")
    ap.add_argument("query", help="검색어 (따옴표로 묶기)")
    ap.add_argument("--limit", type=int, default=8, help="각 출처에서 N개 (기본 8)")
    ap.add_argument("--source", choices=["arxiv", "openalex", "semanticscholar", "s2", "scopus", "both", "all"],
                    default="all", help="기본 all(arXiv+OpenAlex+Semantic Scholar+Scopus(키 있을 때)). both=arXiv+OpenAlex")
    args = ap.parse_args()
    src = args.source

    def run(name, fn):
        # 출처별로 독립 실행 — 한 곳이 실패(예: rate limit)해도 나머지는 계속.
        try:
            _print(name, fn(args.query, args.limit))
        except Exception as e:
            print(f"[{name} 검색 건너뜀] {e}", file=sys.stderr)

    have_scopus = bool((_wiki.KEYS.get("scopus_api_key") or "").strip())
    if src in ("arxiv", "both", "all"):
        run("arXiv", search_arxiv)
    if src in ("openalex", "both", "all"):
        run("OpenAlex", search_openalex)
    if src in ("semanticscholar", "s2", "all"):
        run("Semantic Scholar", search_semanticscholar)
    if src == "scopus" or (src == "all" and have_scopus):  # all에선 키 있을 때만(없으면 조용히 건너뜀)
        run("Scopus", search_scopus)

    print("받을 논문을 골라 식별자를 fetch_paper.py 에 넘기세요 (여러 개 가능):")
    print("  python scripts/fetch_paper.py <DOI 또는 arXiv id> [...]")


if __name__ == "__main__":
    main()
