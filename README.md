# TUPA LLM-Wiki — 개인 위키 스타터

TUPA Lab 연구원이 **각자 자기 논문 지식베이스(LLM-Wiki)**를 만들기 위한 시작 키트.
읽은 논문을 `PDF → 요약 → 구조화 노트 → 종합`으로 쌓아, 나중에 **웹이 아니라 내 위키를 근거로** 묻고 답하는 개인 지식 시스템이다.
패턴 출처: [Karpathy LLM-Wiki](https://github.com/karpathy) 아이디어 / [joonan30/llm-wiki-labs](https://github.com/joonan30/llm-wiki-labs).

> 📄 **시각 안내**: 클론 후 `docs/guide.html` 를 브라우저로 열면 전체 그림(지식 사슬·수집 계층·셋업·4대 룰)을 한눈에 볼 수 있다. 한/영 토글 지원.
> 🧪 **실습**: 학생 워크숍용 단계별 프롬프트는 `docs/workshop.md` (가이드의 “실습 단계” 섹션에도 동일).

---

## 왜 "각자" 만드나 (운영 방침)

> **1단계 (최소 1개월) — 각자 구축·체득.**
> 모두가 자기 위키를 직접 쌓으며 ingest 흐름·분류·백링크에 익숙해진다. 위키는 직접 굴려봐야 가치를 안다.
>
> **2단계 — 그룹별 통합 운영.**
> 각자 충분히 체득한 뒤, 그룹 단위로 위키를 합쳐 공동 지식 지도로 키운다.

그래서 이 repo는 **개인용 빈 스타터**다. 처음엔 너만의 위키로 채우고, 나중에 그룹 통합 방식은 따로 안내한다.

---

## 빠른 시작

### 1. 받기 + 설치
```bash
git clone https://github.com/hyunchul176/tupa-llm-wiki.git my-wiki
cd my-wiki
pip install -r requirements.txt        # IEEE용 Playwright
python -m playwright install chromium   # IEEE용 브라우저
```
> 폴더 이름은 자유(`my-wiki` 등). 검색·arXiv/OA·Elsevier/Wiley/Springer 수집은 **설치 없이도** 되고, 위 두 줄은 **IEEE 본문**을 받기 위한 것이다(미리 깔아두면 데모 중 끊김이 없다).

### 2. AI 에이전트 준비
- **Claude Code** 또는 **Codex CLI** 중 하나를 이 폴더에서 연다.
- 에이전트는 세션 시작 시 `AGENTS.md`(룰)와 `CLAUDE.md`(진입점)를 읽는다.

### 3. (선택) 논문 자동 수집 키 설정
유료 출판사(Elsevier / Wiley / Springer) 본문을 DOI로 받고 싶으면:
```bash
cp secrets/api-keys.example.json secrets/api-keys.json
# 파일을 열어 본인 키 입력. 이 파일은 git에 안 올라간다.
```
> **키가 없어도** arXiv 논문과 무료 공개본(OA)은 받힌다. 그래도 안 되는 PDF는 직접 `papers/`에 넣으면 ingest는 똑같이 된다.

> **IEEE 본문**: Playwright는 1단계에서 이미 설치된다. 캠퍼스망/KAIST VPN이면 로그인 없이 바로 받히고, 그 외에는 `python scripts/fetch_ieee.py login` 으로 1회 로그인한다.

### 4. 첫 논문 넣기 — 먼저 PDF를 구한다
```bash
# 방법 A — 주제/키워드로 찾기 (arXiv + OpenAlex 후보 목록 → 받을 것 고르기)
python scripts/search.py "vision language action humanoid"

# 방법 B — 식별자로 바로 받기 (DOI는 무료 공개본 우선 → 없으면 출판사 API)
python scripts/fetch_paper.py 10.1016/j.trf.2025.103482   # DOI
python scripts/fetch_paper.py 2406.09246                  # arXiv id

# 방법 C — IEEE 등 키 없는 곳 (브라우저. Playwright 선택 설치, 캠퍼스망/VPN 권장)
python scripts/fetch_ieee.py fetch 10.1109/JSEN.2022.3156971

# 방법 D — PDF를 직접 papers/ 에 복사 (키 없어도 됨)
```
그다음 에이전트에게 한 마디:
> **"이 PDF ingest해줘"**

→ 에이전트가 stem 규칙으로 이름 정리 → `sources/` 요약 → `wiki/` 구조화 노트 → `overviews/` 종합까지 만든다.

> 수집 스크립트는 **표준 라이브러리만** 쓴다(설치 불필요). IEEE(`fetch_ieee.py`)만 예외로 `pip install playwright && python -m playwright install chromium` 가 필요하다.

---

## 폴더 구조

```
my-wiki/
├── AGENTS.md          ← AI 운영 매뉴얼 (룰의 단일 소스). 매 세션 먼저 읽음
├── CLAUDE.md          ← 진입점 포인터
├── README.md          ← 이 파일
│
├── papers/            ← 원본 PDF (flat). 파일명 = stem 규칙
├── sources/           ← 논문 1편 = 요약 .md 1개 (flat)
├── wiki/
│   ├── <category>/    ← 주제 카테고리 (내용 보고 자동 부여, 쌓이면 세분화)
│   ├── concepts/      ← 분야 횡단 개념 노트
│   ├── methods/       ← 분야 횡단 방법론 노트
│   └── overviews/     ← 카테고리 종합 허브 (백링크 모음)
│
├── scripts/             ← PDF 수집 (표준 라이브러리만, IEEE만 Playwright)
│   ├── search.py        ← 주제/키워드 → arXiv·OpenAlex 후보 검색
│   ├── fetch_paper.py   ← DOI·arXiv id → 전문 PDF (OA 우선 → 출판사 API)
│   ├── fetch_ieee.py    ← IEEE 등 키 없는 곳 (브라우저, 선택)
│   └── _wiki.py         ← 공용 헬퍼 (키 로드·Crossref·stem)
└── secrets/
    └── api-keys.example.json  ← 키 템플릿 (실제 키는 api-keys.json, gitignore)
```

지식 체인: `PDF → sources/ 요약 → wiki/ 구조화 → overviews/ 종합 → 내 연구`

---

## 핵심 규칙 (자세한 건 `AGENTS.md`)

- **주제(topic)로 분류** — 연구 그룹이 아니라 논문 내용으로. 미리 카테고리를 정하지 않고, 쌓이면 세분화.
- **stem 공유** — `papers/`·`sources/`·`wiki/` 세 곳에서 파일명(`{저자}{연도}-{키워드}`) 동일.
- **웹검색 금지 (기본)** — 답변은 내 위키 근거로. 모르면 `unknown`, 없으면 "PDF 달라"고 요청.
- **노트 끝에 "다음 작업"** — 후속 분석·질문을 항상 박아둔다.

---

## 한 달 로드맵 (가이드)

- **1주차** — 셋업 + 핵심 논문 3~5편 ingest. ingest 흐름·stem·백링크 감 잡기.
- **2~3주차** — 주력 분야 논문 10~20편으로 카테고리 형성. concepts/methods 노트 시작.
- **4주차** — `overviews/`로 분야 종합 1~2개. "내 위키만으로 묻고 답하기" 시도.
- 이후 그룹 통합 운영으로 전환 (별도 안내).

---

*TUPA Lab · 시스템 안내: https://hyunchul176.github.io/tupa-system/*
