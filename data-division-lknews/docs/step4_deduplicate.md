# Step 4: Deduplicate

## What this step does
Computes an `xxhash.xxh64` hash of each article's body text. If two articles
have the **exact same hash**, only the first occurrence is kept.

## Why
The same article can appear multiple times if it was scraped on different days
or re-published. Duplicates would bias the sample and waste annotation effort.

## Result
- **Before:** 27,971
- **After:** 27,969
- **Duplicates removed:** 2

## Example duplicates found
- `2025-09-30-lankadeepalk-12baa591`: AI නිසා රැකෙයිද? නැසෙයි ද? (hash: `bdc5e5dcd9bf...`)
- `2024-07-21-adalk-ce977130`: මාතලේ ගොවිහු රැසක් වී වෙනුවට බඩඉරිගු වවයි (hash: `0822a6936cc6...`)

