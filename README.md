# TUPA LLM-Wiki — personal wiki starter

A starter kit for TUPA Lab members to build **their own paper knowledge base (an LLM-Wiki)**.
You accumulate the papers you read as `PDF → summary → structured note → synthesis`, so later you can ask questions and get answers grounded in **your own wiki, not the web**.
Pattern sources: [Karpathy's LLM-Wiki](https://github.com/karpathy) idea / [joonan30/llm-wiki-labs](https://github.com/joonan30/llm-wiki-labs).

> 📄 **Visual guide (online)**: **https://hyunchul176.github.io/tupa-llm-wiki/** — an explainer you can read without cloning (knowledge chain · collection · practice steps · the 4 core rules, with a KO/EN toggle). Locally it's `docs/guide.html`.
> 🧪 **Workshop**: step-by-step prompts for the student workshop live in `docs/workshop.md` (also in the guide's "Practice" section).
> 🗂️ **Advanced (optional)**: you can build **HTML review cards** that go deep on one topic — a deep card per paper plus key figures (click to enlarge). Rules in `AGENTS.md §8`, example in the guide.

---

## Why "each person" builds their own (operating policy)

> **Phase 1 (≥ 1 month) — build and internalize on your own.**
> Everyone grows their own wiki and gets fluent with the ingest flow, classification, and backlinks. You only understand a wiki's value by running one yourself.
>
> **Phase 2 — merge per group.**
> Once everyone is fluent, groups merge their wikis into a shared knowledge map.

So this repo is an **empty personal starter**. Fill it with your own wiki first; group integration is covered separately later.

---

## Quick start

### 1. Clone + install
```bash
git clone https://github.com/hyunchul176/tupa-llm-wiki.git my-wiki
cd my-wiki

# (recommended) uv — no anaconda needed
uv sync                               # installs Playwright (for IEEE)
uv run playwright install chromium    # browser for IEEE

# or pip
pip install -r requirements.txt && python -m playwright install chromium
```
> The folder name is up to you. Search, arXiv/OA, and Elsevier/Wiley/Springer collection use **only the standard library**, so they work without the install above; the install is for **IEEE full text** (pre-installing avoids hiccups during a demo). Run the IEEE script with `uv run python scripts/fetch_ieee.py …`; everything else runs with plain `python scripts/…`.

### 2. Set up an AI agent (works with both Claude Code and Codex)
- Open this folder in **Claude Code** or **Codex CLI**.
- The rules live in **one place**, `AGENTS.md`. **Codex** reads `AGENTS.md` and **Claude Code** reads `CLAUDE.md` (which points to `AGENTS.md`) at the start of each session — both behave **identically**. (See "The AGENTS.md manual" below.)

### 3. (optional) Set up collection keys
To fetch paywalled full text (Elsevier / Wiley / Springer) by DOI:
```bash
cp secrets/api-keys.example.json secrets/api-keys.json
# open the file and add your keys. This file is never committed (gitignored).
```
> **Without keys**, arXiv papers and open-access (OA) copies still download. For anything you still can't get, drop the PDF into `papers/` and ingest works the same.

> **Search keys (optional)** go in the same file — `semantic_scholar` (free, eases rate limits) and `scopus` (search; **runs on the Elsevier key above**, institutional network required). Without them, those sources are simply skipped and the rest still search. Details in `secrets/api-keys.example.json`.

> **IEEE full text**: Playwright is already installed in step 1. On the campus network / KAIST VPN it downloads without login; otherwise run `python scripts/fetch_ieee.py login` once.

### 4. Add your first paper — get the PDF first
```bash
# A — search by topic/keyword (arXiv·OpenAlex·Semantic Scholar·Scopus candidates → pick what to fetch)
python scripts/search.py "vision language action humanoid"

# B — fetch directly by identifier (DOI tries OA first → then publisher APIs)
python scripts/fetch_paper.py 10.1016/j.trf.2025.103482   # DOI
python scripts/fetch_paper.py 2406.09246                  # arXiv id

# C — IEEE etc. that need no key (browser; Playwright optional, campus/VPN recommended)
python scripts/fetch_ieee.py fetch 10.1109/JSEN.2022.3156971

# D — just copy a PDF into papers/ (no key needed)
```
Then tell the agent:
> **"Ingest this PDF"**

→ The agent renames it by the stem rule → `sources/` summary → `wiki/` structured note → `overviews/` synthesis.

> Collection scripts use **only the standard library** (no install). Only IEEE (`fetch_ieee.py`) and figure extraction (`extract_figures.py`) need extra packages (Playwright / pymupdf).

---

## Folder structure

```
my-wiki/
├── AGENTS.md          ← AI operating manual (the single source of rules). Read first each session
├── CLAUDE.md          ← entry-point pointer (→ AGENTS.md)
├── README.md          ← this file
│
├── papers/            ← original PDFs (flat). filename = stem rule
├── sources/           ← one summary .md per paper (flat)
├── wiki/
│   ├── <category>/    ← topic categories (assigned from content, split as they grow)
│   ├── concepts/      ← cross-cutting concept notes
│   ├── methods/       ← cross-cutting method notes
│   └── overviews/     ← per-category synthesis hubs (backlink collections)
│
├── scripts/             ← collection & curation (stdlib only; IEEE/figures need extra pkgs)
│   ├── search.py        ← topic/keyword → arXiv·OpenAlex·Semantic Scholar·Scopus candidates
│   ├── make_shortlist.py← candidates → clickable selection checklist (shortlist.html)
│   ├── fetch_paper.py   ← DOI·arXiv id → full-text PDF (OA first → publisher APIs)
│   ├── fetch_ieee.py    ← IEEE etc. that need no key (browser, optional)
│   ├── extract_figures.py ← PDF figure extraction for review cards (advanced, pymupdf)
│   └── _wiki.py         ← shared helpers (key loading · Crossref · stem)
└── secrets/
    └── api-keys.example.json  ← key template (real keys go in api-keys.json, gitignored)
```

Knowledge chain: `PDF → sources/ summary → wiki/ structured note → overviews/ synthesis → my research`

---

## The AGENTS.md manual

`AGENTS.md` is the **single source of truth** for how the AI agent operates this wiki — the agent's standing manual, not a doc humans need to read line by line.

- **Cross-agent by design.** `AGENTS.md` follows the emerging `agents.md` convention that AI coding agents read on their own. **Codex** reads it natively; **Claude Code** reads `CLAUDE.md`, which simply points to `AGENTS.md`. So one file drives **both** agents identically — no Claude-only "skills" that Codex can't see.
- **What's inside.** A start-of-session checklist, the folder structure and stem rule, the collection workflow (**find → pick → fetch**), topic-classification principles, note frontmatter, the **4 core rules**, the language policy, transferable operating principles, and the **HTML review-card recipe (§8)**.
- **Why one file.** Behavior stays consistent across sessions and across agents, and there's exactly one place to change it. To make the agent behave differently (a different output path, deeper cards, a new search source), you **edit `AGENTS.md`** instead of repeating instructions in every prompt.
- **You rarely touch it.** Day to day you just give short prompts ("find papers on X", "ingest this", "make review cards from these two") — the agent fills in the rest from `AGENTS.md`.

---

## Core rules (full details in `AGENTS.md`)

- **Classify by topic** — by the paper's content, not by research group. Don't predefine categories; split as they accumulate.
- **Shared stem** — the same filename (`{author}{year}-{keyword}`) across `papers/`, `sources/`, and `wiki/`.
- **No web search by default** — answer from your own wiki. If unknown, say `unknown`; if material is missing, ask for the PDF.
- **End each note with "next steps"** — always pin follow-up analysis/questions.

---

## One-month roadmap (guideline)

- **Week 1** — set up + ingest 3–5 key papers. Get a feel for the ingest flow, stems, and backlinks.
- **Weeks 2–3** — 10–20 papers in your main area to form categories. Start concepts/methods notes.
- **Week 4** — 1–2 synthesis hubs in `overviews/`. Try "ask and answer from my wiki alone".
- After that, switch to group integration (covered separately).

---

*TUPA Lab · System guide: https://hyunchul176.github.io/tupa-system/*
