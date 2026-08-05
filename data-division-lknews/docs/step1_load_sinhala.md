# Step 1: Load Sinhala Metadata from TSV

## What this step does
Reads the TSV index file (`docs_all.tsv`) which contains metadata for all
125k+ articles across all languages. Filters to only rows where `lang == "si"`.

## Why
The lk_news dataset contains Tamil (94,513 non-Sinhala) and
English articles that are outside our project scope. We only need Sinhala articles
for bias annotation.

## Result
- **Total in TSV:** 125,081
- **Sinhala articles:** 30,564

## Publisher distribution
- **Ada Derana Sinhala** (`adaderanasinhalalk`): 13,658
- **Ada** (`adalk`): 12,012
- **Lanka Deepa** (`lankadeepalk`): 3,908
- **BBC Sinhala** (`bbccomsinhala`): 986

## Year distribution
- **2021:** 4
- **2022:** 16
- **2023:** 50
- **2024:** 17,453
- **2025:** 10,247
- **2026:** 2,794

## Example rows
```
doc_id: 2026-07-26-adalk-dd31e5d7
date:   2026-07-26
title:  අධික උෂ්ණත්වය හා බඩඉරිගු හිඟතාවය නිසා බිත්තර නිෂ්පාදනය අඩුවෙලා
lang:   si
source: adalk
```
