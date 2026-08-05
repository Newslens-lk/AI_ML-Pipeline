# Data Preparation — Corpus Building Documentation

## Overview

This document describes the full data preparation pipeline for the
Bias-Aware Sinhala News Aggregation Platform. The pipeline ingests ~125k
multilingual news articles from the `lk_news` dataset, filters down to
~30k Sinhala articles, applies quality and relevance filters, deduplicates,
and produces a stratified sample of **2,000 clean, bias-relevant Sinhala
articles** ready for annotation.

**Date:** 2026-07-26
**Script:** `build_corpus.py`
**Output:** `corpus/articles_2026-07-26.parquet`

---

## Data Source

| Property | Value |
|----------|-------|
| Dataset | `lk_news` by Nuwan Jaliyagoda |
| Repository | `https://github.com/nuuuwan/lk_news` (branch: `data`) |
| License | MIT |
| Total articles | 125,081 |
| Languages | Sinhala (30,564), Tamil (51,271), English (43,246) |
| Date range | 2021-09-12 to 2026-07-26 |
| Structure | One directory per article containing `doc.json` (metadata) and `doc.txt` (body text) |
| Index | `docs_all.tsv` — tab-separated, one row per article with fields: `doc_type`, `doc_id`, `num`, `date_str`, `description`, `url_metadata`, `lang`, `newspaper_id`, `time_ut` |

### Sinhala Publishers

| Publisher ID | Normalized Name | Article Count |
|-------------|----------------|---------------|
| `adaderanasinhalalk` | Ada Derana Sinhala | 13,658 |
| `adalk` | Ada | 12,012 |
| `lankadeepalk` | Lanka Deepa | 3,908 |
| `bbccomsinhala` | BBC Sinhala | 986 |

---

## Pipeline Summary

```
125,081 total articles
    │
    ▼ Step 1: Language filter (lang == "si")
30,564 Sinhala articles
    │
    ▼ Step 2: Quality filter (empty body, <200 chars)
29,799 articles
    │
    ▼ Step 3: Content relevance filter (weather, horoscopes, lottery, etc.)
27,971 articles
    │
    ▼ Step 4: Deduplicate (xxhash content hashing)
27,969 articles
    │
    ▼ Step 5: Stratified sample (publisher × year)
2,000 articles
    │
    ▼ Step 6: Text cleaning + schema validation + Parquet export
2,000 articles → corpus/articles_2026-07-26.parquet
```

Each step is documented in detail in its own file:
- [`step1_load_sinhala.md`](step1_load_sinhala.md)
- [`step2_quality_filter.md`](step2_quality_filter.md)
- [`step3_content_relevance.md`](step3_content_relevance.md)
- [`step4_deduplicate.md`](step4_deduplicate.md)
- [`step5_stratified_sample.md`](step5_stratified_sample.md)
- [`step6_clean_validate.md`](step6_clean_validate.md)

---

## Technologies & Libraries Used

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12 | Runtime |
| **pandas** | latest | DataFrame operations — loading TSV, filtering, sampling, aggregation |
| **Pydantic** | v2 | Schema definition and validation. Every article record is validated against the `Article` model before being written to the corpus |
| **xxhash** (`xxh64`) | latest | Fast non-cryptographic hashing of article body text for deduplication. Chosen over SHA/MD5 for speed on large text volumes |
| **ftfy** | latest | Fixes mojibake and encoding errors in scraped Sinhala text (e.g. double-encoded UTF-8, Windows-1252 artifacts) |
| **PyArrow / Parquet** | latest | Columnar storage format for the final corpus. Efficient compression, fast reads, schema-preserving |
| **unicodedata** (stdlib) | — | NFC Unicode normalization to ensure consistent representation of Sinhala characters (important because Sinhala uses combining marks) |

### Libraries Considered but Not Used

| Library | Reason for exclusion |
|---------|---------------------|
| **langdetect** | Does not support Sinhala (`si`). Throws `LangDetectException` on Sinhala text. Replaced with a Unicode range check (U+0D80–U+0DFF) |
| **trafilatura** | Not needed — `lk_news` provides clean text in `doc.txt`, not raw HTML |

---

## Methods & Techniques

### 1. Language Filtering
- **Method:** Direct filter on the `lang` column in the TSV index (set by the
  data source's own detection).
- **Rationale:** The source's language tags are reliable. This is more efficient
  than running language detection on 125k articles.

### 2. Quality Filtering
- **Method:** Read each article's `doc.txt`, drop if missing/empty or body
  length < 200 characters.
- **Threshold justification:** 200 characters is approximately 2–3 short
  sentences in Sinhala. Anything shorter is typically a headline stub, image
  caption, or scraping artifact with insufficient content for bias annotation.
- **Result:** 765 articles dropped (2.5% of Sinhala set).

### 3. Content Relevance Filtering (Keyword-Based)
- **Method:** Pattern matching against Sinhala keywords in the article title
  and first 500 characters of the body.
- **Categories filtered out:**
  - **Weather reports** (1,617 removed) — කාලගුණ, වර්ෂාපතනය, etc.
  - **Obituaries** (184 removed) — අභාවප්‍රාප්ත, අවමංගල, etc.
  - **Lottery results** (24 removed) — ලොතරැයි ප්‍රතිඵල, etc.
  - **Exchange rates** (3 removed) — විනිමය අනුපාතය, etc.
  - **Horoscopes** (0 found) — රාශි ඵල, ලග්න ඵල, etc.
- **Rationale:** These categories are formulaic, data-driven, or non-editorial
  content where media bias cannot manifest. They would waste annotation effort.
- **Design choice:** Keywords checked in title + first 500 chars (not full body)
  to avoid false positives from passing mentions of weather in political articles.

### 4. Deduplication
- **Method:** `xxhash.xxh64` hash of the full cleaned body text. Exact match
  deduplication (keep first occurrence).
- **Why xxhash:** ~10x faster than SHA-256 on large text, and collision
  resistance is sufficient for dedup (not cryptographic use).
- **Result:** Only 2 duplicates found — the dataset is already well-curated.

### 5. Equal-Publisher Stratified Sampling
- **Method:** Equal allocation of `target / n_publishers` (500) articles per
  publisher. If a publisher has fewer than 500 in the filtered pool, all its
  articles are taken and the shortfall is redistributed to publishers with
  surplus. Within each publisher's allocation, articles are sampled
  proportionally across years to maintain temporal spread. Random seed fixed
  at 42 for reproducibility.
- **Rationale:** A proportional sample would give Ada Derana 44% and BBC
  Sinhala only 3.5%, making cross-publisher bias comparisons unreliable.
  Equal allocation ensures every source has meaningful representation
  (~500 articles each) for bias annotation and analysis.
- **Final distribution:**
  - Ada Derana Sinhala: 500 (25.0%)
  - Ada: 500 (25.0%)
  - Lanka Deepa: 500 (25.0%)
  - BBC Sinhala: 500 (25.0%)

### 6. No Text Cleaning (Raw Text for Annotation)
**Text cleaning is intentionally deferred.** The corpus stores raw text
as-is from the source. Cleaning steps (`ftfy.fix_text()`, NFC normalization,
whitespace stripping) will be applied in a later phase after annotation is
complete. This ensures annotators see the text exactly as it appears in the
source and avoids any transformation artifacts influencing annotation decisions.

### 7. Language Verification (Final Safety Net)
- **Method:** Count Sinhala Unicode characters (U+0D80–U+0DFF) in the first
  500 characters of the body. Reject if fewer than 20 Sinhala characters.
- **Why not langdetect:** The `langdetect` library's underlying profiles do not
  include Sinhala. It throws `LangDetectException: No features in text` on
  pure Sinhala input. The Unicode range check is more reliable for this language.
- **Result:** 0 rejections — the TSV language tags are accurate.

### 8. Schema Validation (Pydantic)
- Every article is validated against the `Article` model defined in `schema.py`.
- **Layer 1 fields** (required): `article_id`, `source_dataset`, `publisher`,
  `url`, `published_at`, `title`, `body_text`, `language`, `content_hash`.
- **Layer 2 fields** (optional): `category`, `author`, `raw_path`.
- **Layer 3 fields** (reserved, null): `event_cluster_id`, `embedding_ref`,
  `bias_label`, `bias_confidence`, `annotator_id`, `annotation_timestamp`.
- **`article_id`:** Deterministic `UUID5` from `(source_dataset, url)` —
  ensures idempotent re-runs produce the same IDs.
- **`content_hash`:** `xxhash.xxh64` of cleaned body text — used for
  cross-source deduplication in future phases.

### 9. Publisher Name Normalization
Raw `newspaper_id` values from the source are mapped to human-readable names:

| Raw ID | Normalized Name |
|--------|----------------|
| `adaderanasinhalalk` | Ada Derana Sinhala |
| `adalk` | Ada |
| `lankadeepalk` | Lanka Deepa |
| `bbccomsinhala` | BBC Sinhala |

---

## Output Schema

The final Parquet file contains 18 columns conforming to the `Article` model:

| Column | Type | Status | Description |
|--------|------|--------|-------------|
| `article_id` | string | Required | UUID5 from (source_dataset, url) |
| `source_dataset` | string | Required | Always `"lk_news"` |
| `publisher` | string | Required | Normalized publisher name |
| `url` | string | Required | Original article URL |
| `published_at` | datetime (UTC) | Required | Publication date |
| `title` | string | Required | Raw title text (no cleaning applied) |
| `body_text` | string | Required | Raw body text (no cleaning applied) |
| `language` | string | Required | Always `"si"` |
| `content_hash` | string | Required | xxh64 of raw body text |
| `category` | string | Optional | Not available from source |
| `author` | string | Optional | Not available from source |
| `raw_path` | string | Optional | Path to original `doc.txt` |
| `event_cluster_id` | string | Null | Phase 2+ |
| `embedding_ref` | string | Null | Phase 2+ |
| `bias_label` | string | Null | Phase 2+ |
| `bias_confidence` | float | Null | Phase 2+ |
| `annotator_id` | string | Null | Phase 2+ |
| `annotation_timestamp` | datetime | Null | Phase 2+ |

---

## Reproducibility

- **Random seed:** `42` (used in `pd.DataFrame.sample()`)
- **Script:** `build_corpus.py` — re-runnable end-to-end
- **Deterministic IDs:** `article_id` is UUID5-based, so re-runs on the same
  data produce identical IDs
- **Dated output:** Parquet files are named `articles_YYYY-MM-DD.parquet` to
  track snapshots

---

## Known Limitations

1. **Keyword-based relevance filtering is approximate.** Some edge cases:
   - An article *about* weather policy (e.g. climate change legislation) may
     be incorrectly filtered if it mentions "කාලගුණ" prominently in the first
     500 characters.
   - Some irrelevant categories (e.g. sports score tables) may not have been
     captured if they don't match the keyword list.

2. **No near-duplicate detection.** Only exact body text matches are caught.
   Slightly reworded republications of the same story are treated as distinct
   articles.

3. **`langdetect` unsupported for Sinhala.** The Unicode range check is a
   pragmatic alternative but would not catch, say, a Sanskrit text using the
   same script range. In practice this is not an issue for this dataset.

4. **Year distribution is skewed.** The dataset has very few articles before
   2024 (70 out of 30,564). The sample inherits this skew proportionally.

5. **No category metadata.** The source does not provide article categories
   (politics, sports, business, etc.), so we cannot filter or stratify by
   topic — only by publisher and date.

---

## Annotation Split

**Script:** `split_annotations.py`
**Date:** 2026-07-27

### Design

The 2,000-article corpus is split for annotation by 3 team members:

1. **150 overlap articles** — shared across all 3 annotators for
   Inter-Annotator Agreement (IAA) calculation. These are shuffled into each
   annotator's set so annotators don't know which articles are shared.
2. **1,850 unique articles** — divided among 3 annotators with equal publisher
   balance within each split.

### Allocation

| Annotator | Unique | Overlap | Total | Notebook |
|-----------|--------|---------|-------|----------|
| Praveen | 650 | 150 | 800 | `notebooks/praveen.ipynb` |
| Ashini | 600 | 150 | 750 | `notebooks/ashini.ipynb` |
| Dinithi | 600 | 150 | 750 | `notebooks/dinithi.ipynb` |

### Publisher Balance (per annotator)

Each annotator's set has roughly equal representation from all 4 publishers
(~25% each), ensuring no single source dominates any annotator's experience.

| Annotator | Ada Derana Sinhala | Ada | BBC Sinhala | Lanka Deepa |
|-----------|-------------------|-----|-------------|-------------|
| Praveen (unique) | 163 | 163 | 162 | 162 |
| Ashini (unique) | 150 | 150 | 150 | 150 |
| Dinithi (unique) | 149 | 149 | 151 | 151 |
| Overlap | 38 | 38 | 37 | 37 |

### Bias Labels (5 buckets)

| Label | Description |
|-------|-------------|
| `far_left` | Strong left-leaning political framing |
| `left` | Moderate left-leaning tone or source selection |
| `center` | Balanced, neutral reporting |
| `right` | Moderate right-leaning tone or source selection |
| `far_right` | Strong right-leaning political framing |

### Annotation Workflow

1. Annotator clones the repo and sets up `.venv`
2. Receives their CSV file (`annotations/{name}.csv`)
3. Opens their notebook (`notebooks/{name}.ipynb`)
4. The notebook displays articles one at a time with:
   - Article metadata (publisher, date, ID)
   - Full title and body text
   - Dropdown for bias label selection
   - Save & Next / Skip / Back navigation
   - Flag checkbox for unclear articles
5. Labels are auto-saved to the CSV after each annotation
6. Progress persists across sessions — notebook resumes at first unlabeled article

### Output Files

```
annotations/
├── overlap_150.csv    # The 150 shared articles (reference copy)
├── praveen.csv        # Praveen's full set (650 unique + 150 overlap)
├── ashini.csv         # Ashini's full set (600 unique + 150 overlap)
└── dinithi.csv        # Dinithi's full set (600 unique + 150 overlap)
```

### IAA Plan

After annotation is complete, Inter-Annotator Agreement will be computed on
the 150 overlap articles using Fleiss' kappa (3 annotators, 5 categories).
This measures annotation reliability before trusting labels at scale.
