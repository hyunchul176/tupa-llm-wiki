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

---

## 3. 논문 수집 → 인제스트 워크플로

논문은 **(A) 수집(PDF 확보) → (B) 인제스트(요약·구조화)** 두 단계로 들어온다.

### A. 수집 (collection) — 주제로 lit review

> **연구 아이디어는 사용자가 들고 온다.** 에이전트는 아이디어를 만들지 않는다. 사용자가 *"X에 대해 lit review 해줘"* 라고 주제를 주면, 그 주제의 문헌을 **① 찾고(discovery) → ② 받는다(fetch).** 둘은 다른 일이다. 받은 PDF는 모두 `papers/`에 stem 이름으로 저장된다. 어느 출처·스크립트를 쓸지 판단, 실패 처리, 중복 확인은 에이전트가 한다.

**① 찾기 (discovery) — 어떤 논문이 있나**
- **arXiv · OpenAlex** — `python scripts/search.py "<영어 키워드>"` (기본). 무료·자동. OpenAlex는 거의 전 출판사 메타데이터 + 인용 그래프를 훑는다.
- **LeapSpace (선택, 사람 손 필요)** — OpenAlex/arXiv로 부족할 때만. ScienceDirect 본문 기반 의미검색. 에이전트가 **≤500자 영어 질문**을 만들어 주면, 사용자가 https://www.sciencedirect.com/leapspace 에서 돌려 답(인용·DOI 포함)을 붙여넣는다 → 거기서 **DOI를 추출**해 ②로 넘긴다. (LeapSpace도 LLM이므로 답은 '검증할 단서'로 다룬다.)

**② 받기 (fetch) — 그 PDF를 다운로드**
- `python scripts/fetch_paper.py <DOI 또는 arXiv id> [...]`
  - DOI: **무료 공개본(OA) 우선** → 없으면 출판사 API(Elsevier·Wiley·Springer, `secrets/api-keys.json` 키, 보통 KAIST 망 필요). *LeapSpace가 찾아준 Elsevier DOI도 여기서 받는다.*
  - arXiv id: 키 없이 바로.
- **IEEE 등 키 없는 곳** — `python scripts/fetch_ieee.py fetch <DOI>` (브라우저. Playwright 선택 설치. 캠퍼스망/KAIST VPN이면 로그인 없이도 받힘.)

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

---

## 7. 이전 가능한 운영 원칙
1. 단일 운영 매뉴얼 (이 파일) · 2. 반복 교정은 즉시 룰로 박기 · 3. 덤프→분류→정리 순서 ·
4. 출력 경로 사전 지정 · 5. 노트 끝에 "다음 작업" 박기 · 6. 웹검색 차단(unknown은 필드에) ·
7. 매일 조금씩 ingest 하는 누적의 가치
