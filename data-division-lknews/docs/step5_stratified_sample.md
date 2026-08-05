# Step 5: Equal-Publisher Stratified Sample → 2,000

## What this step does
Draws a **balanced sample** of 2,000 articles with **equal allocation
per publisher** (500 each). Within each publisher's allocation,
articles are sampled proportionally across years to maintain temporal spread.
If a publisher has fewer articles than its allocation, all its articles are taken
and the shortfall is redistributed to surplus publishers.

## Why
- Equal allocation ensures every publisher has meaningful representation for
  cross-source bias analysis.
- A proportional sample would give dominant sources ~44% while minority sources
  get only ~3.5%, making cross-publisher comparisons unreliable.
- Temporal spread within each publisher is preserved via year-stratified sampling.

## Result
- **Pool size:** 27,969
- **Sampled:** 2,000

## Publisher distribution (sampled)
- **Ada**: 500
- **BBC Sinhala**: 500
- **Lanka Deepa**: 500
- **Ada Derana Sinhala**: 500

## Year distribution (sampled)
- **2021:** 1
- **2022:** 2
- **2023:** 7
- **2024:** 977
- **2025:** 882
- **2026:** 131

## Example sampled articles
```
1. 2025-08-05-adalk-159b5c9f: මරණ තර්ජන කළ වෛද්‍යවරියගේ දියණිය කොන්දේසි විරහිතව සමාව ගැනීමට සූදානම්
2. 2024-03-25-adalk-00fd1a88: අගමැතිගේ  ඇමතිධූරවල වැඩ බැලීමට ජනක පත්කරයි
3. 2025-09-15-adalk-95588209: රු. 2000 නෝට්ටුව ගැන මහ බැංකුවෙන් දැනුම් දීමක්
```
