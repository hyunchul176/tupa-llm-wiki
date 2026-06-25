#!/usr/bin/env python3
"""fetch_paper.py — 식별자(DOI / arXiv id)로 전문 PDF를 받아 papers/에 저장.

사용:
  python scripts/fetch_paper.py 10.1016/j.trf.2025.103482
  python scripts/fetch_paper.py 2406.09246                 # arXiv id
  python scripts/fetch_paper.py 10.1016/... 2406.09246 ... # 여러 개 한꺼번에

수집 순서 (DOI):
  1) 무료 공개본(OA) 우선 — OpenAlex로 무료 PDF가 있으면 키 없이 받는다 (기관 쿼터 절약).
  2) 없으면 출판사 API — Elsevier / Wiley / Springer (secrets/api-keys.json 키, 대학 망 필요).
  3) IEEE 등 키 없는 곳 — 브라우저 로그인 필요 → fetch_ieee.py 안내 (blocker).

- 키는 secrets/api-keys.json 에서만 읽음 (api-keys.example.json 참고). 표준 라이브러리만 사용.
- 파일명은 stem 규칙(<firstauthor><year>-<keyword>.pdf). 저장 후 "ingest해줘"로 에이전트가 sources/wiki 생성.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

import _wiki
from _wiki import KEYS, crossref, http_bytes, http_json, make_stem, norm_doi, save_pdf

ATOM = "{http://www.w3.org/2005/Atom}"


# ---------- OpenAlex: 무료 OA PDF 위치 탐지 ----------
def openalex_oa_pdf(doi: str) -> str:
    """DOI에 무료 공개본이 있으면 그 PDF URL, 없으면 ''. (키 불필요)"""
    try:
        url = (f"https://api.openalex.org/works/doi:{urllib.parse.quote(norm_doi(doi))}"
               f"?mailto={urllib.parse.quote(_wiki.CONTACT)}")
        w = http_json(url, timeout=30)
    except Exception:
        return ""
    if not (w.get("open_access") or {}).get("is_oa"):
        return ""
    best = w.get("best_oa_location") or {}
    return best.get("pdf_url") or (w.get("open_access") or {}).get("oa_url") or ""


# ---------- PubMed Central (Europe PMC) — OA 우회 ----------
def pmc_pdf_url(doi: str) -> str:
    """DOI에 PMCID가 있으면 Europe PMC의 PDF render URL, 없으면 ''. (키 불필요)
    MDPI처럼 출판사가 봇을 막아도, 같은 OA 논문을 PMC가 서빙하므로 우회된다."""
    try:
        u = ("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=tupa-llm-wiki&email="
             + urllib.parse.quote(_wiki.CONTACT) + "&ids=" + urllib.parse.quote(norm_doi(doi))
             + "&format=json")
        rec = (http_json(u, timeout=30).get("records") or [{}])[0]
        pmcid = (rec.get("pmcid") or "").strip()
        return f"https://europepmc.org/articles/{pmcid}?pdf=render" if pmcid else ""
    except Exception:
        return ""


# ---------- arXiv ----------
def arxiv_meta(arxiv_id: str):
    """arXiv id → (family, year, title, pdf_url). 실패 시 None."""
    aid = arxiv_id.strip()
    aid = aid[6:] if aid.lower().startswith("arxiv:") else aid
    url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}"
    root = ET.fromstring(http_bytes(url, timeout=30).decode("utf-8", "replace"))
    e = root.find(f"{ATOM}entry")
    if e is None:
        return None
    title = " ".join((e.findtext(f"{ATOM}title", "") or "").split())
    year = (e.findtext(f"{ATOM}published", "") or "")[:4]
    authors = [a.findtext(f"{ATOM}name", "") for a in e.findall(f"{ATOM}author")]
    fam = _wiki.family_of(authors[0]) if authors else ""
    pdf_url = ""
    for link in e.findall(f"{ATOM}link"):
        if link.get("title") == "pdf":
            pdf_url = link.get("href")
            break
    sid = (e.findtext(f"{ATOM}id", "") or "").rsplit("/abs/", 1)[-1]
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{sid}"
    return fam, year, title, pdf_url


def fetch_arxiv(arxiv_id: str) -> str:
    meta = arxiv_meta(arxiv_id)
    if not meta:
        raise RuntimeError(f"arXiv에서 못 찾음: {arxiv_id}")
    fam, year, title, pdf_url = meta
    stem = make_stem(fam, year, title) or f"arxiv-{arxiv_id}"
    print(f"  title : {title}")
    print(f"  source: arXiv ({arxiv_id})")
    print(f"  stem  : {stem}")
    if stem in _wiki.existing_stems():
        print(f"  · 이미 있음: papers/{stem}.pdf — 건너뜀")
        return stem
    save_pdf(http_bytes(pdf_url, timeout=120), stem)
    return stem


# ---------- 출판사 API ----------
def publisher_url_headers(doi: str, publisher: str):
    pub = (publisher or "").lower()
    if "elsevier" in pub:
        key = (KEYS.get("elsevier_api_key") or "").strip()
        if not key:
            raise RuntimeError("elsevier_api_key 비어있음 (secrets/api-keys.json)")
        return (f"https://api.elsevier.com/content/article/doi/{doi}",
                {"X-ELS-APIKey": key, "Accept": "application/pdf"})
    if "wiley" in pub:
        tok = (KEYS.get("wiley_tdm_token") or "").strip()
        if not tok:
            raise RuntimeError("wiley_tdm_token 비어있음 (secrets/api-keys.json)")
        return (f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{urllib.parse.quote(doi, safe='')}",
                {"Wiley-TDM-Client-Token": tok, "Accept": "application/pdf"})
    if "springer" in pub:
        key = (KEYS.get("springer_api_key") or "").strip()
        if not key:
            raise RuntimeError("springer_api_key 비어있음 (secrets/api-keys.json)")
        return (f"https://api.springernature.com/meta/v2/pdf/{doi}?api_key={key}",
                {"Accept": "application/pdf"})
    return None, None


def fetch_doi(doi: str) -> str:
    doi = norm_doi(doi)
    fam, year, title, publisher = crossref(doi)
    stem = make_stem(fam, year, title) or f"doi-{doi.replace('/', '_')}"
    print(f"  title    : {title or '(제목 미상)'}")
    print(f"  publisher: {publisher or '(미상)'}")
    print(f"  stem     : {stem}")
    if stem in _wiki.existing_stems():
        print(f"  · 이미 있음: papers/{stem}.pdf — 건너뜀")
        return stem

    # 1) 무료 OA 우선
    oa = openalex_oa_pdf(doi)
    if oa:
        try:
            save_pdf(http_bytes(oa, timeout=120), stem)
            print("  · 경로  : 무료 공개본(OA)")
            return stem
        except Exception as e:
            print(f"  · OA 시도 실패({e}) → 다음 경로로 폴백")

    # 1.5) PubMed Central (Europe PMC) — OA지만 출판사가 봇을 막을 때(MDPI 등) 우회
    pmc = pmc_pdf_url(doi)
    if pmc:
        try:
            save_pdf(http_bytes(pmc, timeout=120), stem)
            print("  · 경로  : PubMed Central (Europe PMC)")
            return stem
        except Exception as e:
            print(f"  · PMC 시도 실패({e}) → 출판사 API로 폴백")

    # 2) 출판사 API
    url, headers = publisher_url_headers(doi, publisher)
    if url:
        save_pdf(http_bytes(url, headers, timeout=120), stem)
        print(f"  · 경로  : 출판사 API ({(publisher or '').split()[0] if publisher else ''})")
        return stem

    # 3) IEEE / 미지원 → 안내(blocker)
    if "ieee" in (publisher or "").lower():
        raise RuntimeError(
            "IEEE는 키가 없어 브라우저 로그인이 필요합니다 → "
            f"python scripts/fetch_ieee.py fetch {doi}  (캠퍼스망/VPN이면 로그인 없이도 받힘)")
    raise RuntimeError(f"미지원 출판사: {publisher!r} — 무료본·키 없음. 브라우저 자동화로 시도: "
                       f"python scripts/fetch_ieee.py fetch {doi}  (캠퍼스망/VPN). 그래도 안 되면 PDF를 직접 papers/에 넣어주세요.")


# ---------- 라우팅 ----------
def fetch_one(token: str) -> str:
    if _wiki.looks_like_arxiv(token):
        return fetch_arxiv(token)
    return fetch_doi(token)   # DOI 또는 doi.org URL


def main():
    args = sys.argv[1:]
    if not args:
        print("사용: python scripts/fetch_paper.py <DOI 또는 arXiv id> [...]")
        print("예  : python scripts/fetch_paper.py 10.1016/j.trf.2025.103482  2406.09246")
        sys.exit(1)

    ok, blocked = [], []
    for token in args:
        print(f"▶ {token}")
        try:
            stem = fetch_one(token)
            ok.append(stem)
            print(f"  ✅ saved: papers/{stem}.pdf\n")
        except urllib.error.HTTPError as e:
            try:
                body = e.read()[:200]
            except Exception:
                body = b""
            print(f"  ❌ HTTP {e.code}: {body!r}\n")
            blocked.append(token)
        except Exception as e:
            print(f"  ❌ {e}\n")
            blocked.append(token)

    print(f"완료: 성공 {len(ok)} / 막힘 {len(blocked)}")
    if ok:
        print("  ingest 대상 (에이전트에게 '이 PDF ingest해줘'):", ", ".join(ok))
    if blocked:
        print("  막힘 (blocker로 기록 권장):", ", ".join(blocked))
        sys.exit(1)


if __name__ == "__main__":
    main()
