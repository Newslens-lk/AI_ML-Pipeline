# CLAUDE.md

Guidance for Claude Code (or any Claude instance) working in this repo.

## Project

Bias-Aware Sinhala News Aggregation Platform — a Ground News-style platform
for Sinhala news. Full pipeline: annotate articles for media bias, train a
classifier, generate LASER3 embeddings, cluster by event, produce bias-aware
multi-source summaries, extract linguistic/reporting features, serve via a
web app.

**We are only in Phase 1.** Do not build, scaffold, or suggest code for
later phases (classification, embeddings, clustering, summarization, web
app) unless explicitly asked. Keep all work scoped to what's described
below.

## Phase 1 Scope: Data Exploration, Cleaning, Annotation & Corpus Building

Phase 1 covers pipeline steps 1–2 from the project plan:

1. **Corpus preparation** — ingest and clean the lk_news Sinhala articles,
   build the base corpus in Parquet format.
2. **Bias annotation** — manually annotate 3,000 articles into 10 media
   bias buckets; guidelines and bucket definitions still TBD and must be
   grounded in media bias literature. Split across 3 annotators:
   - 900 articles per annotator, uniquely assigned (2,700 total, each
     article labeled once)
   - 300 shared overlap articles, annotated by *all three* annotators, for
     inter-annotator agreement (IAA)
   - 2,700 + 300 = 3,000 total distinct articles annotated

Everything from step 3 onward (ML/DL bias classifier, LASER3 embeddings,
embedding aggregation, clustering, summarization, linguistic feature
extraction, web app) is out of scope for now. Layer 3 schema fields
(`event_cluster_id`, `embedding_ref`, `bias_label`, `bias_confidence`,
`annotator_id`, `annotation_timestamp`) stay null — don't populate them
in Phase 1.

### What "done" looks like for Phase 1
- A cleaned, deduplicated, schema-validated corpus of ~30k articles in
  dated Parquet snapshots under `corpus/`.
- `docs/source_audit.md` documenting the real shape of the lk_news source.
- `docs/datasheet.md` drafted in Datasheets for Datasets format.
- Annotation guidelines + 10 bias bucket definitions, literature-grounded.
- 3,000 articles annotated: 900 unique per annotator (× 3) + 300 shared
  overlap articles labeled by all three annotators for IAA.
- IAA computed on the 300 overlap articles (e.g. Cohen's/Fleiss' kappa)
  before trusting the unique-annotator labels at scale.

## Data Source

Single source for now: **Nuwan's lk_news**
(`git clone --branch data --single-branch https://github.com/nuuuwan/lk_news.git`)
— ~30k Sinhala articles, daily updates, 2021-09-12 to present. Normalized
JSON per doc (title, date, source, language, hashes). MIT licensed.

## Unified Schema (`schema.py`)

Single source of truth is the pydantic `Article` model. **Always validate
ingested records against this model** — never write directly to the corpus
store without going through it.

- **Layer 1 (required):** `article_id`, `source_dataset`, `publisher`,
  `url`, `published_at`, `title`, `body_text`, `language`, `content_hash`
- **Layer 2 (optional):** `category`, `author`, `raw_path`
- **Layer 3 (reserved, null in Phase 1):** `event_cluster_id`,
  `embedding_ref`, `bias_label`, `bias_confidence`, `annotator_id`,
  `annotation_timestamp`

  Note: the 300 overlap articles will get *three* separate label records
  (one per annotator) for IAA purposes, not a single `Article` row update.
  Don't collapse these into one `bias_label` per article until IAA is
  resolved — that reconciliation step comes after Phase 1's raw annotation
  collection.

Do not add ad-hoc fields outside this schema without updating `schema.py`
first and telling both team members.

## Repo Structure

```
project/
├── schema.py              # pydantic Article model — source of truth
├── ingest/
│   └── lk_news.py          # ingestion script, yields Article objects
├── build_corpus.py         # runs ingestion, dedupes, writes parquet
├── corpus/                 # dated snapshots: articles_YYYY-MM-DD.parquet
├── raw/                     # raw HTML/source files, named {article_id}.html
├── notebooks/                # exploration only, not production pipeline code
└── docs/
    ├── source_audit.md      # per-source findings from inspection
    └── datasheet.md          # public-facing dataset documentation
```

## Conventions

- **Text cleaning pipeline, in order:**
  1. Extract clean text with `trafilatura` (only if raw HTML is all that's
     available)
  2. Fix encoding with `ftfy.fix_text()`
  3. Unicode-normalize with `unicodedata.normalize('NFC', text)`
  4. Language-check with `langdetect`
- **`article_id`**: `uuid5` seeded from `(source_dataset, url)` — never a
  random UUID, so re-runs stay idempotent.
- **`content_hash`**: `xxhash.xxh64` of the *cleaned* body text, used for
  cross-source dedup.
- **Publisher names**: normalize to one canonical string per outlet (e.g.
  "Hiru News", not "hirunews.lk" in some rows and "Hiru" in others). Check
  the shared lookup table before inventing a new mapping.
- **Never inline raw HTML** into the main corpus table — store it as a file
  in `raw/`, referenced by `raw_path`.
- **Corpus storage format**: Parquet, dated snapshots. Don't introduce a
  database or DVC unless snapshot files actually become unmanageable.
- **Terminology discipline**: use domain-standard terms from the media
  bias / framing literature for anything bias-related. Don't invent new
  umbrella terms (explicit mentor feedback — avoid vague labels like
  "reporting statistics" without a literature-backed definition).

## Workflow Rules

- Inspect a new source in a notebook first; don't write an `ingest/*.py`
  script until the source's real shape (fields, date range, quirks) is
  understood and logged in `docs/source_audit.md`.
- Test each ingestion script on a small sample (~20 records) before running
  it against the full source.
- After any ingestion script change, re-run `build_corpus.py` and
  spot-check ~20 random rows by hand before considering it done.
- Two people work in this repo — use branches per person/workstream and
  open PRs rather than pushing directly to `main`.

## Do Not

- Do not skip pydantic validation when writing new records into the
  corpus.
- Do not redistribute full article text publicly without confirming
  licensing per-source first — open legal question for the mentor, not a
  default-yes.
- Do not populate or reference Layer 3 schema fields as if they're live —
  they're reserved for later phases.
- Do not start scaffolding the classifier, embeddings, clustering,
  summarization, or web app code in this phase.