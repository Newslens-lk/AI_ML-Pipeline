# Step 2: Read Body Text + Quality Filter

## What this step does
1. Reads `doc.txt` (article body) for each Sinhala article directory.
2. Drops articles with **missing/empty** body text.
3. Drops articles with body text **shorter than 200 characters** —
   these are typically stubs, image captions, or headline-only entries.

## Why
Articles without meaningful body text cannot be annotated for media bias.
Very short articles lack enough content for framing analysis.

## Result
- **Before:** 30,564
- **After:** 29,799
- **Dropped:** 765

## Example of a kept article
```
doc_id: 2026-07-26-adalk-dd31e5d7
title:  අධික උෂ්ණත්වය හා බඩඉරිගු හිඟතාවය නිසා බිත්තර නිෂ්පාදනය අඩුවෙලා
body length: 2,357 chars
body preview: අධික උෂ්ණත්වය හා බඩඉරිගු හිඟතාවය නිසා බිත්තර නිෂ්පාදනය අඩුවෙලා

මේ දිනවල පවත්නා. අධික උෂ්ණත්වය හා බඩඉරිගු හිඟතාවය හේතුවෙන් බිත්තර නිෂ්පාදනය අවප්‍රමාණය...
```
