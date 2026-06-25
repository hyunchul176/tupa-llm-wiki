# TUPA LLM-Wiki — 실습 단계별 프롬프트 / Step-by-step Practice Prompts

각자 **연구 주제만 다르게** 하고, 나머지는 그대로 따라 합니다. 프롬프트에서 `〈내 연구 주제〉`만 바꿔 복사하세요.
Everyone uses the **same prompts — only the research topic differs**. Just replace `〈your topic〉` and copy.

> 시각 가이드(흐름도·로고·한영 토글)는 `docs/guide.html`의 **“실습 단계”** 섹션에도 같은 내용이 있습니다.
> The same steps live in the **“Practice”** section of `docs/guide.html` (visual, with a KO/EN toggle).

---

## 0. 준비 / Setup

**VS Code**(code.visualstudio.com)를 설치하고, 위키를 둘 폴더를 **원하는 이름·위치로 직접 만들어** VS Code로 연 뒤, 그 안에서 **Claude Code** 또는 **Codex CLI**를 실행한다. 깃헙 링크를 주면 **지금 연 폴더에** 클론·의존성(IEEE용 Playwright 포함)까지 알아서 설치한다(`tupa-llm-wiki`로 강제되지 않는다).
Install **VS Code** (code.visualstudio.com), create the folder for your wiki **with the name/location you want**, open it, then run **Claude Code** or **Codex CLI** inside. Give it the GitHub link and it clones **into the folder you opened** + installs deps (not forced to `tupa-llm-wiki`).

> 이 저장소를 지금 연 폴더에 그대로 복제하고 설치까지 진행해줘: https://github.com/hyunchul176/tupa-llm-wiki
> Clone this repo into the folder I have open and set it up: https://github.com/hyunchul176/tupa-llm-wiki

유료 출판사(Elsevier·Wiley·Springer) 본문이 필요하면 `secrets/api-keys.json`에 키를 입력한다. **키 없어도 arXiv·무료 공개본(OA)은 받힌다.**
For paywalled full text, add keys to `secrets/api-keys.json`. **Without keys, arXiv & open access still work.**

---

## 1. 문헌 찾기 (Find)

**하는 일 / Goal:** 주제에 맞는 후보 논문 목록 확보. / Get a candidate list for your topic.

**KO**
> 내 연구 주제는 "〈내 연구 주제〉"야. 이 주제로 literature review를 시작하자. 여러 학술 DB(arXiv·OpenAlex·Semantic Scholar·Scopus)에서 관련 논문을 찾아, 제목·저자·연도·DOI(또는 arXiv id)·무료본 여부를 표로 보여줘.

**EN**
> My research topic is "〈your topic〉". Let's start a literature review on it. Search several scholarly databases (arXiv, OpenAlex, Semantic Scholar, Scopus) for relevant papers and show a table with title, authors, year, DOI (or arXiv id), and open-access availability.

---

## 2. 받을 논문 고르기 (Pick)

**하는 일 / Goal:** 후보를 클릭형 체크리스트(`shortlist.html`)로 만들어 고른다. / Turn candidates into a clickable checklist (`shortlist.html`) and pick.

**KO**
> 위 후보로 shortlist.html을 만들어 열어줘. 각 논문에 한 줄 요약과 함께 **초록을 한국어로 2~3문장 요약**해 달고, 관련 낮은 건 '제외 추천'으로 빼줘.

**EN**
> Build a shortlist.html from those candidates and open it. For each, add a one-line summary plus a **2–3 sentence Korean summary of the abstract**, and mark the less relevant ones as "exclude".

→ 브라우저에서 받을 것만 체크 → **“선택 복사”** → 채팅에 붙여넣으면 그 논문만 받는다.
→ In the browser, check what you want → **“선택 복사”** → paste back in chat to fetch just those.

---

## 3. PDF 받기 (Fetch)

**하는 일 / Goal:** `papers/`에 전문 PDF 수집. / Collect full-text PDFs into `papers/`.

**KO**
> 고른 논문들의 전문 PDF를 받아줘. arXiv·무료 공개본(OA)을 먼저 시도하고, 안 되면 출판사 API, 그래도 안 되면 브라우저 자동화(Playwright, IEEE 등)로. 못 받은 건 목록으로 알려줘.

**EN**
> Download the full-text PDFs of the chosen papers. Try arXiv and open access (OA) first, then publisher APIs, and if still blocked, browser automation (Playwright, e.g. IEEE). List anything you couldn't get.

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

→ [researcher.elsevier.com](https://researcher.elsevier.com/) 에서 돌린 답(인용·DOI 포함)을 복사한다. / Run it on LeapSpace and copy the answer (with citations/DOIs).

**② 결과를 후보에 더하기 / Fold results into your candidates**

KO
> LeapSpace에서 이런 답을 받았어: 〈답변 붙여넣기〉. 여기 인용된 논문들을 내 후보 목록에 더해줘.

EN
> I got this from LeapSpace: 〈paste the answer〉. Add the papers it cites to my candidate list.

→ LeapSpace 답은 에이전트의 후보 리스트와 형식이 다르다. 받기로 바로 가지 말고 — 새 논문을 후보에 더하거나 에이전트와 더 논의한 뒤, **2단계(받을 논문 고르기)부터 다시 반복**한다.
→ A LeapSpace answer has a different shape than the agent's candidate list. Don't jump to fetching — add the new papers (or discuss with the agent), then **loop back to step 2 (pick papers)**.

---

## 심화 (선택) — HTML 기반 리뷰카드 만들기 / Advanced (optional) — build review cards (HTML)

**핵심 / Key:** 위키와 **역할이 다르다** — 위키는 여러 주제를 누적·질의응답하는 지식베이스, 리뷰카드는 **한 주제를 깊게**(주제당 1편, 다른 주제 섞지 않기) 정리하고 figure까지 담아 읽고 비교하는 문서.
A different role from the wiki — the wiki accumulates many topics for Q&A; review cards go **deep on one topic** (one per topic, no mixing), figures and all.

시연이라 **내가 고른 2편만** 지정한다(wiki 전체는 오래 걸림). 깊은 카드·핵심 figure·그림 클릭 확대는 규칙(AGENTS §8)대로 **자동 포함**되니 프롬프트에 적지 않아도 된다.
For the demo, pick **just 2 papers** (the whole wiki takes a while). Deep cards, key figures, and click-to-zoom are **automatic** per the rules (AGENTS §8) — no need to spell them out.

**KO**
> 이 2편으로 리뷰카드 만들어줘: 〈논문 1 — 제목 또는 DOI〉, 〈논문 2 — 제목 또는 DOI〉.

**EN**
> Make review cards from these 2 papers: 〈paper 1 — title or DOI〉, 〈paper 2 — title or DOI〉.

→ 출력 위치(`review/〈주제〉/`)·템플릿·깊은 카드·figure는 규칙(AGENTS §8)대로 자동이니 프롬프트엔 논문만 적는다. 생성된 결과를 브라우저로 열어 본다. 비교 매트릭스·공백 분석은 옵션.
→ Output location, template, deep cards, and figures are automatic per the rules (AGENTS §8) — just name the papers. Open the generated result in a browser. Matrix & gap analysis are optional.

---

*TUPA LLM-Wiki · 운영 규칙은 `AGENTS.md`, 셋업은 `README.md` 참고.*
