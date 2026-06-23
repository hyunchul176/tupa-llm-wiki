# TUPA LLM-Wiki — 실습 단계별 프롬프트 / Step-by-step Practice Prompts

각자 **연구 주제만 다르게** 하고, 나머지는 그대로 따라 합니다. 프롬프트에서 `〈내 연구 주제〉`만 바꿔 복사하세요.
Everyone uses the **same prompts — only the research topic differs**. Just replace `〈your topic〉` and copy.

> 시각 가이드(흐름도·로고·한영 토글)는 `docs/guide.html`의 **“실습 단계”** 섹션에도 같은 내용이 있습니다.
> The same steps live in the **“Practice”** section of `docs/guide.html` (visual, with a KO/EN toggle).

---

## 0. 준비 / Setup

빈 폴더에서 **Claude Code**를 열고(Codex도 동작), 깃헙 링크를 주며 설치를 맡긴다 — 클론·의존성(IEEE용 Playwright 포함)까지 알아서 한다.
Open **Claude Code** in an empty folder (Codex works too) and hand it the link — it clones and installs deps (incl. Playwright for IEEE).

> 이 깃헙 받아서 설치까지 해줘: https://github.com/hyunchul176/tupa-llm-wiki
> Clone and set this up for me: https://github.com/hyunchul176/tupa-llm-wiki

유료 출판사(Elsevier·Wiley·Springer) 본문이 필요하면 `secrets/api-keys.json`에 키를 입력한다. **키 없어도 arXiv·무료 공개본(OA)은 받힌다.**
For paywalled full text, add keys to `secrets/api-keys.json`. **Without keys, arXiv & open access still work.**

---

## 1. 문헌 찾기 (Find)

**하는 일 / Goal:** 주제에 맞는 후보 논문 목록 확보. / Get a candidate list for your topic.

**KO**
> 내 연구 주제는 "〈내 연구 주제〉"야. 이 주제로 literature review를 시작하자. arXiv와 OpenAlex에서 관련 논문을 찾아, 제목·저자·연도·DOI(또는 arXiv id)·무료본 여부를 표로 보여줘.

**EN**
> My research topic is "〈your topic〉". Let's start a literature review on it. Search arXiv and OpenAlex for relevant papers and show a table with title, authors, year, DOI (or arXiv id), and open-access availability.

---

## 2. 핵심 논문 추리기 (Shortlist)

**하는 일 / Goal:** 후보를 클릭형 체크리스트(아티팩트)로 만들어 고른다. / Turn candidates into a clickable checklist (artifact) and pick.

**KO**
> 위 후보로 선별 체크리스트를 만들어 아티팩트로 띄워줘. 각 논문에 초록 기반 한 줄 요약을 달고, 관련 낮은 건 '제외 추천'으로 빼줘.

**EN**
> Build a selection checklist from those candidates and open it as an artifact. Add a one-line abstract-based summary to each, and mark the less relevant ones as "exclude".

→ 아티팩트 링크에서 받을 것만 체크 → **“선택 복사”** → 채팅에 붙여넣으면 그 논문만 받는다. (Codex·오프라인은 로컬 `shortlist.html`로 열림.)
→ In the artifact, check what you want → **“선택 복사”** → paste back in chat. (Codex/offline opens a local `shortlist.html`.)

---

## 3. PDF 받기 (Fetch)

**하는 일 / Goal:** `papers/`에 전문 PDF 수집. / Collect full-text PDFs into `papers/`.

**KO**
> 고른 논문들의 전문 PDF를 받아줘. arXiv·무료 공개본(OA)을 먼저 시도하고, 안 되는 건 출판사 API나 IEEE로. 못 받은 건 목록으로 알려줘.

**EN**
> Download the full-text PDFs of the chosen papers. Try arXiv and open access (OA) first, then publisher APIs or IEEE. List anything you couldn't get.

---

## 4. 위키에 쌓기 (Ingest)

**하는 일 / Goal:** PDF가 지식 사슬을 타고 위키가 됨. / PDFs flow into the wiki.

**KO**
> 받은 PDF들을 ingest해줘. 각 논문을 sources/ 요약 → wiki/ 구조화 노트 → overviews/ 종합까지 만들어줘.

**EN**
> Ingest the downloaded PDFs. For each paper, create the sources/ summary → wiki/ structured note → overviews/ overview.

---

## 5. 내 위키에 질문하기 (Ask)

**하는 일 / Goal:** “웹이 아니라 내 위키가 답한다”를 직접 체험. / Experience answering from your wiki, not the web.

**KO**
> 지금까지 쌓은 위키만 근거로 답해줘(웹검색 금지): "〈궁금한 점〉?" 어느 노트·논문에서 나온 근거인지도 같이.

**EN**
> Answer using only the wiki built so far (no web search): "〈your question〉?" Cite which note/paper each point comes from.

---

## 6. 종합·연구 틈 찾기 (Synthesize)

**하는 일 / Goal:** 리뷰 종합 + 다음 연구 실마리. / Review synthesis + next research leads.

**KO**
> 이 주제 논문들을 종합해줘. 공통된 접근, 서로 다른 점, 아직 안 풀린 빈틈(gap)을 정리하고 근거 논문을 달아줘. 근거는 내 위키에서만.

**EN**
> Synthesize the papers on this topic. Lay out common approaches, differences, and open gaps, citing the supporting papers. Ground it only in my wiki.

---

## 심화 (선택) — LeapSpace로 더 찾기 / Advanced (optional)

**언제 / When:** 1단계(OpenAlex·arXiv) 찾기로 부족할 때만. ScienceDirect 본문 기반 의미 검색이라 사람 손이 한 번 들어간다.
Only when step 1 isn't enough. A full-text semantic search over ScienceDirect — it takes one manual step.

**① 질문 만들기 / Draft a query**

KO
> OpenAlex로 부족한 것 같아. 이 주제로 LeapSpace에 넣을 500자 이내 영어 질문을 만들어줘.

EN
> OpenAlex doesn't seem enough. Draft an English query (under 500 characters) for this topic to run on LeapSpace.

→ [sciencedirect.com/leapspace](https://www.sciencedirect.com/leapspace) 에서 돌린 결과(인용·DOI 포함)를 복사한다. / Run it on LeapSpace and copy the results (with DOIs).

**② 결과 붙여넣은 뒤 / After pasting the results**

KO
> 이 결과에서 DOI를 뽑아 PDF를 받아줘.

EN
> Extract the DOIs from these results and download the PDFs.

---

*TUPA LLM-Wiki · 운영 규칙은 `AGENTS.md`, 셋업은 `README.md` 참고.*
