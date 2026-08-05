# Step 6: Validate & Write Parquet (Raw Text)

## What this step does
1. **Language verification:** Checks for Sinhala Unicode characters (U+0D80–U+0DFF)
   in the body. Rejects articles with fewer than 20 Sinhala characters in the
   first 500 chars. (`langdetect` does not support Sinhala.)
2. **Schema validation:** Each article is validated against the pydantic
   `Article` model (Layer 1 fields required, Layer 3 fields null).
3. **Write:** Saves the final corpus as a dated Parquet file.

## No text cleaning applied
Text is stored **raw as-is from the source** — no `ftfy`, no Unicode
normalization, no whitespace stripping. This is intentional: the corpus is
meant for annotation first. Text cleaning (ftfy, NFC normalization) will be
applied in a later phase after annotation is complete.

## Why
- Sinhala Unicode range check catches any misclassified articles that slipped through.
- Pydantic validation guarantees every record conforms to the schema.
- Raw text preserves the original content exactly as annotators will see it.

## Result
- **Before:** 2,000
- **After:** 2,000
- **Language rejections:** 0
- **Output:** `corpus/articles_2026-07-26.parquet`

## Language rejections (examples)
None — all articles confirmed as Sinhala.

## Final corpus schema
| Field | Type | Example |
|-------|------|---------|
| article_id | str | `54b2c406-5cfc-5961-8b15-84c621f5f7f5` |
| source_dataset | str | `lk_news` |
| publisher | str | `Ada` |
| published_at | datetime | `2025-08-05 00:00:00+00:00` |
| title | str | `මරණ තර්ජන කළ වෛද්‍යවරියගේ දියණිය කොන්දේසි විරහිතව සමාව ගැනීම...` |
| body_text | str | `මරණ තර්ජන කළ වෛද්‍යවරියගේ දියණිය කොන්දේසි විරහිතව සමාව ගැනීම...` (raw, uncleaned) |
| content_hash | str | `cac59993fbfcb19e...` |

## Final publisher & year distribution
- **Ada**: 500
- **BBC Sinhala**: 500
- **Lanka Deepa**: 500
- **Ada Derana Sinhala**: 500
