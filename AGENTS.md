# AGENTS.md — TUPA LLM-Wiki (개인 위키) 운영 매뉴얼

> 이 폴더에서 일하는 **모든 AI 에이전트(Claude Code, Codex CLI 등)의 단일 운영 매뉴얼**.
> 여기는 **너 한 사람의 개인 LLM-Wiki**다. 새 세션마다 가장 먼저 이 파일을 읽는다.
> 패턴 출처: Karpathy LLM-Wiki / joonan30 llm-wiki-labs.
> **버전**: v1.0 (개인 스타터 — 굴리며 계속 수정)

---

## 0. 부트스트랩 체크리스트 (매 세션 강제)

작업 시작 전 반드시:
1. **이 `AGENTS.md`를 처음부터 다시 읽는다.**
2. **이전 세션 메모리를 신뢰하지 않는다.** 실제 파일 상태(폴더·기존 stem)를 확인한다.
3. 반복되는 교정은 **즉시 이 파일에 한 줄로 박는다.** 같은 룰을 두 번 설명하게 만들지 않는다.

---

## 1. 이 위키는 무엇인가

- 내가 읽은 논문을 `PDF → 요약 → 구조화 노트 → 종합`으로 쌓는 **개인 지식베이스**.
- 목표: 흩어진 논문 지식을 **검색·연결 가능한 한 덩어리**로 만들어, 질문에 답할 때 **웹이 아니라 이 위키를 근거로** 한다.
- 운영 방침: **최소 1개월 각자 구축·체득** → 추후 **그룹별 통합**. (`README.md` 참고)

---

## 2. 폴더 구조 (Karpathy LLM-Wiki 패턴)

```
my-wiki/                           ← 위키 루트
├── AGENTS.md / CLAUDE.md / README.md
│
│   ── Core 3 (같은 정보의 세 검색 표면 · 주제 분류) ──
├── papers/                        ← 원본 PDF (flat). 파일명 = stem 규칙 (§3)
├── sources/                       ← LLM 요약 마크다운 (flat). 논문 1편 = .md 1개
├── wiki/                          ← 구조화 노트 (frontmatter·백링크)
│   ├── <category>/                ← 주제 카테고리 — 내용 보고 자동 부여, 쌓이면 세분화
│   ├── concepts/                  ← 분야 횡단 개념 노트
│   ├── methods/                   ← 분야 횡단 방법론 노트
│   └── overviews/                 ← 카테고리 종합 허브 (백링크 모음)
│
├── scripts/                       ← 수집 자동화 (search · fetch_paper · fetch_ieee · _wiki)
└── secrets/                       ← API 키 (gitignore. example만 커밋)
```

### 지식 체인 (각 단계는 아래 단계 없이 존재 불가)
`PDF` → `요약(sources/)` → `위키(wiki/)` → `종합(overviews/)` → `내 연구(분석·발표·코드)`

> **Obsidian 호환**: `wiki/`·`sources/`는 그대로 Obsidian 볼트로 열린다(사람이 그래프·백링크로 탐색). `[[stem]]` 위키링크(확장자 없이 파일명)와 YAML frontmatter 형식을 유지해 Obsidian이 자동 해석하게 한다.

---

## 3. 논문 수집 → 인제스트 워크플로

논문은 **(A) 수집(PDF 확보) → (B) 인제스트(요약·구조화)** 두 단계로 들어온다.

### A. 수집 (collection) — 주제로 lit review

> **연구 아이디어는 사용자가 들고 온다.** 에이전트는 아이디어를 만들지 않는다. 사용자가 *"X에 대해 lit review 해줘"* 라고 주제를 주면, 그 주제의 문헌을 **① 찾고(discovery) → ② 받는다(fetch).** 둘은 다른 일이다. 받은 PDF는 모두 `papers/`에 stem 이름으로 저장된다. 어느 출처·스크립트를 쓸지 판단, 실패 처리, 중복 확인은 에이전트가 한다.

**① 찾기 (discovery) — 어떤 논문이 있나**
- **arXiv · OpenAlex · Semantic Scholar · Scopus** — `python scripts/search.py "<영어 키워드>"` (기본 `--source all`). 무료·자동(Scopus는 키 있을 때만 자동 포함). 출처마다 커버리지가 달라 보완적이다 — arXiv=프리프린트, OpenAlex=넓은 메타데이터+인용, Semantic Scholar=TL;DR 요약·다른 랭킹, Scopus=큐레이션·인용. search.py는 각 후보의 **초록/TL;DR**도 함께 출력한다. (Semantic Scholar는 키 없으면 rate limit으로 가끔 건너뛴다; **Scopus는 `elsevier_api_key`를 그대로 쓴다** — 같은 Elsevier 개발자포털 키라 별도 키가 필요 없다(기관망 필요). 다른 키를 쓰려면 `scopus_api_key`, 기관망 밖이면 `scopus_inst_token`.)
  - 후보를 사용자에게 보여줄 때는 그 **초록을 한국어로 요약**(1~2줄, 필요하면 2~3문장)해, 제목·저자·연도·식별자(DOI/arXiv id)·무료본 여부와 함께 **표로** 제시한다. 영어 초록은 한국어로 옮겨 주고, 추측으로 채우지 말고 초록에 있는 내용만 쓴다.
- **LeapSpace (선택, 사람 손 필요)** — OpenAlex/arXiv로 부족할 때만. Elsevier의 LLM으로, 웹 대신 ScienceDirect 등 주요 DB(초록·일부 full-text)만 근거로 답하고 문장마다 citation을 단다. 에이전트가 **영어 질문**을 만들어 주면(★ **반드시 500자 이하**: 글자 수를 세어 초과하면 줄여서 다시 준다), 사용자가 https://researcher.elsevier.com/ 에서 돌려 답(인용·DOI 포함)을 붙여넣는다 → 그 답에 나온 논문을 **후보에 더해 '받을 논문 고르기'(curation)로 보낸다**(바로 받기로 가지 않음 — 형식이 다르므로 선별 단계를 거친다). (LeapSpace도 LLM이므로 답은 '검증할 단서'로 다룬다.)

**★ 받을 논문 고르기 — 받기 전, 사용자가 고른다**
- 후보가 여럿이면 곧장 받지 말고, 각 논문에 **한국어 한 줄 요약(`summary`) · 한국어 초록 요약(`abstract`, 2~3문장) · 관련성 판단(`note`)**을 단 JSON을 만들어 `python scripts/make_shortlist.py --input <json>` 로 클릭형 체크리스트(`shortlist.html`)를 만든다 (관련 낮은 건 `exclude:true`).
  - 만든 `shortlist.html`을 **브라우저로 열도록 안내**한다 (Claude Code면 직접 열어줘도 된다). 사용자가 체크해 **'선택 복사'한 id만** ②로 받는다.
  - (후보가 소수로 명확하면 굳이 만들지 말고 대화에서 번호로 골라도 된다.)

**② 받기 (fetch) — 그 PDF를 다운로드**
- `python scripts/fetch_paper.py <DOI 또는 arXiv id> [...]`
  - DOI: **무료 공개본(OA) 우선** → 없으면 출판사 API(Elsevier·Wiley·Springer, `secrets/api-keys.json` 키, 보통 KAIST 망 필요). *LeapSpace가 찾아준 Elsevier DOI도 여기서 받는다.*
  - arXiv id: 키 없이 바로.
- **IEEE 등 키 없는 곳** — `python scripts/fetch_ieee.py fetch <DOI>` (브라우저. Playwright는 셋업 `requirements.txt`에서 설치됨. 캠퍼스망/KAIST VPN이면 로그인 없이도 받힘.)

> 헷갈리지 말 것: **LeapSpace=찾기, 출판사 API=받기.** Elsevier 키가 있어도 LeapSpace가 불필요해지는 게 아니라(서로 다른 단계), 다만 '찾기'는 OpenAlex가 무료·자동으로 하므로 LeapSpace는 선택이다.

**수집 규칙:**
- PDF를 즉흥 `curl`로 받지 말고 **반드시 위 스크립트**를 쓴다 (재현성 + 키 보안).
- 키가 없거나 못 받으면 추측하지 말고 사용자에게 *"이 PDF를 직접 `papers/`에 넣어주세요"* 라고 요청한다(§5 룰4). 사람이 해줘야 풀리는 막힘은 먼저 알려준다.
- 받은 PDF는 곧장 아래 **B. 인제스트**로 이어진다.

### B. 인제스트 (ingest)
**"이 PDF ingest해줘"** 한 마디에:
1. PDF를 `papers/`로 옮기고 **stem 규칙**으로 이름 변경: `<firstauthor><year>-<핵심키워드>.pdf` (예: `park2026-micromobility-overtaking.pdf`). 중복 stem 금지.
2. `sources/<stem>.md`에 요약 마크다운 1편 생성.
3. **주제 카테고리 판정**(내용 기반, §4) → `wiki/<category>/<stem>.md` 구조화 노트 생성.
4. 등장한 핵심 개념·방법은 `wiki/concepts/`·`wiki/methods/` 노트로 만들고 백링크.
5. `wiki/overviews/<category>.md` 종합 페이지에 백링크 추가(없으면 생성).

**규칙:**
- 생성 순서 엄수: `PDF → sources → wiki`.
- **stem은 papers/sources/wiki 3곳에서 동일**하게 (추적·중복방지).
- 모르는 값은 prose로 얼버무리지 말고 `unknown`으로 표시.

---

## 4. 주제(topic) 분류 원칙

> 분류는 **논문 내용 기준**이다. 소속 연구 그룹이나 프로젝트로 나누지 않는다.

- 카테고리는 미리 정해두지 않는다. **내용 보고 부여**하고, 맞는 게 없으면 새로 만든다.
- 한 카테고리가 너무 커지면 **세분화**한다 (예: `safety` → `pedestrian-safety` / `crash-severity` / …).
- 관련 분야·키워드는 frontmatter `tags`로만 표시.

### frontmatter 표준
```markdown
---
title: <논문 제목>
authors: <First-Author et al.>
year: <연도>
venue: <저널/학회>
category: <주제 카테고리>      # 내용 보고 부여. 예: micromobility-safety
tags: [overtaking, eye-tracking, ...]
ingested: 2026-06-11
---

## Summary
- (핵심 3~6줄)
## Key methods
- (방법론)
## Why it matters / 내 연구와의 관계
- (내 연구·관심 주제와 어떻게 연결되는지)
## 다음 작업 / Open questions
- (이 논문에서 끌어낼 후속 분석·질문)
## Related
- [[overviews/<category>]]
- [[concepts/<concept>]]
- [[methods/<method>]]
```

---

## 5. ★ 4대 룰 (위키의 가치를 만드는 핵심)

1. **웹검색 금지 (기본).** 검색은 사용자가 명시적으로 요청할 때만. 잡지식으로 빈칸을 채우지 않는다.
2. **위키 우선.** 질문에 답할 땐 먼저 `sources/`·`wiki/`를 근거로 한다.
3. **모르면 PDF 재독.** 위키에 답이 흐릿하면 `papers/`의 원문 PDF를 다시 읽는다.
4. **위키에 없으면 요청.** 근거 자료가 위키에 없으면 추측하지 말고 *"이 PDF를 추가해 주세요"*라고 요청한다.

---

## 6. 언어 정책
- 기본 **한국어**. 위키·요약·노트 모두 한국어 우선.
- 영어 원문 인용(논문 제목·핵심 문장)은 보존.
- 영-한 중복 작성 금지.
- **HTML 생성 시**(guide·리뷰카드 등) 한글이 단어 중간에서 끊기지 않게 `body{word-break:keep-all; overflow-wrap:break-word;}`를 넣는다 (PPT '한글 잘림 허용' 끄기와 같은 효과).

---

## 7. 이전 가능한 운영 원칙
1. 단일 운영 매뉴얼 (이 파일) · 2. 반복 교정은 즉시 룰로 박기 · 3. 덤프→분류→정리 순서 ·
4. 출력 경로 사전 지정 · 5. 노트 끝에 "다음 작업" 박기 · 6. 웹검색 차단(unknown은 필드에) ·
7. 매일 조금씩 ingest 하는 누적의 가치

---

## 8. HTML 기반 리뷰카드 만들기 (심화·선택)

> **역할 — 〈리뷰카드 제작 담당〉.** 사용자가 *"이 논문들로 리뷰카드 만들어줘"* 라고 하면, 너는 이 역할을 맡아 아래 규칙대로 만든다. **사용자는 논문(제목·DOI)만** 주면 된다 — 출력 위치(`review/<주제>/index.html`)·템플릿·깊이·figure·하이라이트는 **프롬프트에 없어도 네가 규칙대로 알아서** 정한다. 경로·템플릿을 사용자가 매번 적게 하지 말 것.

> 위키(ingest)와 **역할이 다른 산출물**이다. 위키는 여러 주제를 누적·질의응답하는 지식베이스이고, 리뷰카드는 **한 주제를 깊게** 정리하고 figure까지 담아 **읽고 비교**하는 리뷰 문서다. 그래서 **주제 1개당 1편** — 서로 다른 주제 논문을 한 리뷰에 섞지 않는다.

**기본 포함 (사용자가 따로 요청하지 않아도 항상)**: 깊은 카드(연구배경~한계) · 핵심 figure · 그림 클릭 확대(lightbox) · 핵심 구절 형광펜 · 한글 `word-break:keep-all` · 출력은 `review/<주제>/index.html`. 프롬프트가 *"리뷰카드 만들어줘"*처럼 짧아도 아래를 전부 적용한다.

진행 (대상은 **사용자가 지정한 논문**. 시연은 보통 **2편** — wiki 전체를 다 만들면 오래 걸린다):

1. **대상 논문 확정 (주제 격리)** — 사용자가 지정한 논문(시연은 2편)만 쓴다. **지정이 없으면** `wiki/<category>/` 목록을 보여주고 *어느 논문으로 할지 먼저 묻는다* — wiki 전체를 임의로 자동 생성하지 않는다. 주제가 어긋나는 논문은 한 리뷰에 섞지 않는다.
2. **figure 추출 + 반드시 눈으로 검증** — 논문마다 `python scripts/extract_figures.py papers/<stem>.pdf --prefix <stem> --out review/<주제>/images` (caption 모드). ⚠ 자동 추출은 완벽하지 않다 — **고른 그림을 직접 열어 확인**하고 ① 본문 텍스트가 잡힌 것 ② 두 그림이 합쳐진 것 ③ 캡션 아래 본문이 딸려온 것은 **쓰지 않는다**. 핵심 그림 1~3장(아키텍처·결과 위주)만 고르고, 잘 안 나오면 `--mode embedded`(사진)·`--mode pages`(페이지 통째)로 재시도하거나 다른 figure 번호를 쓴다.
3. **리뷰 생성** — `review/<주제>/index.html` **한 파일**로, `<head>`에 `<link rel="stylesheet" href="../assets/shared.css">`만 건다(폰트 Pretendard는 shared.css가 `@import`로 불러온다). head에 작은 `<style>`만 얹는다: 한글이 단어 중간에서 끊기지 않게 `body{word-break:keep-all; overflow-wrap:break-word;}` + 방법론 불릿 여백(`.paper-section ul.method`). 기존 lit-review 템플릿 클래스를 그대로 쓴다:
   - `<header class="landing-hero">`: `<h1>` 제목 · `.subtitle` · `.meta`(작성자·논문 수·버전·날짜)
   - `<div class="page-grid">` 안에 `<aside class="toc-sidebar">`(`.toc-title` + 섹션/논문 링크, 라인별 `<details class="toc-line">`) + `<main>`
   - `<main>`: `.lede`(주제·왜 보는지 2~4줄) → 섹션마다 `<h2 id="sN">§N. 제목 <span class="section-status">…</span></h2>` → 그 아래 `.paper` 카드들
   - **`.paper` 카드 1장(깊게)** = `<article class="paper line-a anchor-offset" id="paper-...">` 안에:
     `.tag-row`(`.tag.tag-line-a` + `.tag.tag-conf`/`.tag-journal` + `.tag.tag-year`) · `<h4>`제목 · `.citation`(저자·venue·연도·DOI) · `.paper-body`[ `.paper-figs`>`.paper-figure`(`.fig-label` + img + `.paper-figure-caption`, 캡션 끝에 `<em>(클릭 시 확대)</em>`) + `<div>`( `.tldr`(`.tldr-label`+요약) · `.attrs`>`.attr`(로봇·차량·센서·학습여부) · `.paper-section`(`.paper-section-label`) **연구 배경 · 무엇을 했는가 · 방법론 상세 · 결과/시연 · 한계** · `.paper-section.relevance`(본 연구와의 관계) ) ]
   - **방법론 상세**는 `<ul class="method">`로 핵심 포인트 3~6개, 각 `<li>`는 `<b>소제목.</b> 설명` 형태. 가장 중요한 1~2개는 `<span class="key">★ …</span>`로.
   - 라인(클러스터) 색: line-a/line-b/… (toc 점 색과 tag-line-* 일치).
4. **그림 클릭 확대(lightbox)** — `</body>` 앞에 `<div id="lightbox" aria-hidden="true"><span class="lb-close">✕</span><img alt=""><div class="lb-hint">…</div></div>`와 작은 `<script>`(`.paper-figure img` 클릭 시 라이트박스 img.src 설정 + `.active` 토글, 클릭/Esc로 닫기)를 넣는다. CSS(`#lightbox`, `.paper-figure img{cursor:zoom-in}`)는 shared.css에 이미 있다.
5. **핵심 구절 형광펜** — 각 파트(lede·TL;DR·연구배경·무엇·방법론·결과·한계·관계)의 가장 중요한 구절 1개를 `<span class="mark">…</span>`로 감싼다(투명 형광펜). 파트당 1개 정도, 과하게 칠하지 말 것.
6. **깊이 — 기본은 위 깊은 카드**(연구배경~한계 + figure 클릭확대). **옵션**(요청 시만): 비교 매트릭스(`.matrix-wrap`>table) · 공백 분석(`.gap-card`).

규칙:
- 내용은 **`sources/`·`wiki/` 노트와 원문 PDF에 근거**. 추측·잡지식 금지(모르면 unknown). '본 연구와의 관계'는 사용자 주제 맥락에서 쓴다.
- figure는 `review/<주제>/images/`에 두고 카드에서 상대경로(`images/...`)로 참조, 캡션에 출처(Fig. N) 표기.
- 생성물 `review/<주제>/`는 gitignore된다. 공용 템플릿 `review/assets/shared.css`만 커밋.
