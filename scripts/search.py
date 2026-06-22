#!/usr/bin/env python3
"""search.py — 주제/키워드로 논문 후보를 찾는다 (arXiv + OpenAlex). 표준 라이브러리만.

받는 게 아니라 '찾아 보여주는' 단계다. 결과에서 받을 것을 골라 fetch_paper.py 로 넘긴다.

사용:
  python scripts/search.py "vision language action humanoid driving"
  python scripts/search.py "micromobility overtaking safety" --limit 10 --source openalex

옵션:
  --limit N      각 출처에서 N개 (기본 8)
  --source X     arxiv | openalex | both (기본 both)

출력의 각 항목 끝에 '받기' 명령을 같이 보여준다. 무료본(OA) 여부도 표시.
"""
from __future__ import annotations

import argparse
import sys
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
            "id": sid, "id_kind": "arXiv", "oa": True,
        })
    return out


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
            "id": doi, "id_kind": "DOI",
            "oa": bool((w.get("open_access") or {}).get("is_oa")),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "cited": w.get("cited_by_count", 0),
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
        if it["id"]:
            print(f"    {it['id_kind']}: {it['id']}   ({oa})")
            print(f"    받기 →  python scripts/fetch_paper.py {it['id']}")
        else:
            print(f"    ({it['id_kind']} 없음 — 받기 어려움)")
        print()


def main():
    ap = argparse.ArgumentParser(description="주제/키워드 논문 검색 (arXiv + OpenAlex)")
    ap.add_argument("query", help="검색어 (따옴표로 묶기)")
    ap.add_argument("--limit", type=int, default=8, help="각 출처에서 N개 (기본 8)")
    ap.add_argument("--source", choices=["arxiv", "openalex", "both"], default="both")
    args = ap.parse_args()

    try:
        if args.source in ("arxiv", "both"):
            _print("arXiv", search_arxiv(args.query, args.limit))
        if args.source in ("openalex", "both"):
            _print("OpenAlex", search_openalex(args.query, args.limit))
    except Exception as e:
        print(f"[검색 오류] {e}", file=sys.stderr)
        sys.exit(1)

    print("받을 논문을 골라 식별자를 fetch_paper.py 에 넘기세요 (여러 개 가능):")
    print("  python scripts/fetch_paper.py <DOI 또는 arXiv id> [...]")


if __name__ == "__main__":
    main()
