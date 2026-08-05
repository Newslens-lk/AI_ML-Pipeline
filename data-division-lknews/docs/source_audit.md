# Source Audit: lk_news

**Audited:** 2026-07-26
**Source:** `https://github.com/nuuuwan/lk_news` (branch: `data`)
**License:** MIT

---

## Dataset Structure

```
data/lk_news/data/lk_news/
├── docs_all.tsv              # Full index (125,081 rows)
├── docs_last100.tsv          # Recent 100 articles
├── docs_last1000.tsv         # Recent 1,000 articles
├── docs_last10000.tsv        # Recent 10,000 articles
├── summary.json              # Dataset metadata
├── docs_by_month_and_lang.png # Distribution chart
├── hugging_face_data/        # HuggingFace export (not used)
├── README.md
└── 2020s/
    ├── 2021/                 # ~4 Sinhala articles
    ├── 2022/                 # ~16 Sinhala articles
    ├── 2023/                 # ~50 Sinhala articles
    ├── 2024/                 # ~17,453 Sinhala articles
    ├── 2025/                 # ~10,247 Sinhala articles
    └── 2026/                 # ~2,794 Sinhala articles (partial year)
```

Each article is a directory named `{date}-{newspaper_id}-{hash}` containing:
- **`doc.json`** — metadata (doc_type, doc_id, num, date_str, description,
  url_metadata, lang, newspaper_id, time_ut)
- **`doc.txt`** — extracted article body text (plain text, not HTML)

## TSV Index Fields

| Field | Type | Description |
|-------|------|-------------|
| `doc_type` | string | Always `"lk_news"` |
| `doc_id` | string | `{date}-{newspaper_id}-{hash}` |
| `num` | string | `{newspaper_id}-{hash}` |
| `date_str` | string | `YYYY-MM-DD` |
| `description` | string | Article title |
| `url_metadata` | string | Original article URL |
| `lang` | string | `si`, `en`, or `ta` |
| `newspaper_id` | string | Source identifier |
| `time_ut` | float | Unix timestamp |

## Language Distribution

| Language | Count | Percentage |
|----------|-------|------------|
| Tamil (`ta`) | 51,271 | 41.0% |
| English (`en`) | 43,246 | 34.6% |
| Sinhala (`si`) | 30,564 | 24.4% |
| Unknown | 4 | <0.01% |
| **Total** | **125,081** | |

## Sinhala Publishers

| newspaper_id | Publisher | Count | Date Range | Notes |
|-------------|-----------|-------|------------|-------|
| `adaderanasinhalalk` | Ada Derana (Sinhala) | 13,658 | 2024–2026 | Largest Sinhala source. `sinhala.adaderana.lk` |
| `adalk` | Ada | 12,012 | 2021–2026 | `www.ada.lk`. Broadest date range |
| `lankadeepalk` | Lanka Deepa | 3,908 | 2024–2026 | `www.lankadeepa.lk` |
| `bbccomsinhala` | BBC Sinhala | 986 | 2023–2026 | `www.bbc.com/sinhala`. International perspective |

## Quirks & Observations

1. **Body text is in `doc.txt`, not in JSON.** The `doc.json` only has the
   title (as `description`) and metadata. Must read `doc.txt` separately.

2. **Heavy temporal skew.** 97.7% of Sinhala articles are from 2024–2026.
   Only 70 articles exist before 2024. The dataset appears to have started
   Sinhala collection seriously around early 2024.

3. **Title duplication in body.** Many `doc.txt` files begin with the title
   repeated as the first line, then the body follows.

4. **765 empty/stub articles (2.5%).** Some `doc.txt` files are empty or
   contain fewer than 200 characters — likely scraping failures or
   headline-only entries.

5. **Very few duplicates.** Only 2 exact-body duplicates found across 27,971
   filtered articles. The dataset is well-maintained.

6. **Weather articles are disproportionately frequent.** 1,617 weather reports
   (5.4% of Sinhala articles) — mostly from Ada, which publishes daily weather
   updates.

7. **Language tags are reliable.** All articles tagged `lang=si` contain
   Sinhala Unicode text. No misclassification observed in spot checks.

8. **No category/section metadata.** The source does not provide topic
   categories (politics, crime, business, etc.). This limits our ability to
   do topic-based stratification.

9. **URL encoding.** Sinhala article URLs contain percent-encoded Sinhala
   characters. URLs are stored in their original encoded form.

10. **`newspaper_id` values are URL slugs**, not human-readable names.
    Normalization mapping is applied during ingestion (see `build_corpus.py`).
