# Step 3: Content Relevance Filter

## What this step does
Removes articles that are **not meaningful for bias analysis**. These are
formulaic, data-driven, or non-editorial content where media bias cannot
manifest.

Matches Sinhala keywords in the **title + first 500 characters of body**.

## Categories removed

### Weather — 1,617 removed
    - `2026-07-24-adalk-851c287e`: අද වැසි ස්වල්පයයි, වියළි කාලගුණයක්
    - `2026-07-14-adalk-cefb637d`: අද වැසි ස්වල්පයයි
    - `2026-07-13-adalk-c61d3e38`: බංග්ලාදේශයේ වැස්ස නිසා 51ක්

### Obituary — 184 removed
    - `2026-07-10-adalk-46452f53`: මරියසෙල් ගුණතිලක සමුගනියි
    - `2026-07-05-adalk-6f2440d2`: පියාගේ අවමංගල්‍ය උත්සවයටත් මොජ්තාබා එක්නොවෙයි
    - `2026-07-02-adalk-fee0fd01`: පෙබරවාරි 28 මිය ගිය අලි කමේනිගේ අවමංගල්‍ය ජුලි 4 සිට ජුලි 9 දා දක්වා

### Lottery — 24 removed
    - `2026-06-09-adalk-2a33db48`: සරණට වසර 16 ක බරපතල වැඩ සහිත සිර දඩුවම්
    - `2026-03-03-adalk-11108c65`: සරණ අප්‍රේල් 30 අසරණ වෙයිද ?
    - `2025-12-19-adalk-ab46c559`: ඇමෙරික්‍රාව ග්‍රීන් කාඩ් ලොතරැයිය අහෝසි කරයි

### Exchange_Rate — 3 removed
    - `2026-05-21-adalk-d6b7bccd`: ඩොලරයේ විකුණුම් මිල රු. 354 ඉක්මයි
    - `2024-10-02-adaderanasinhalalk-10f8234b`: ඩොලරය වේගයෙන් පහළට
    - `2024-06-19-adalk-2b2dba4b`: ඩොලර් ණය රුපියලට පරිවර්තනයේදී අසාමාන්‍ය අනුපාතයක් යොදාගෙන


## Keywords used

| Category | Keywords |
|----------|----------|
| Weather | කාලගුණ, කාලගුණය, වර්ෂාපතනය, උෂ්ණත්ව අනාවැකි, කාලගුණ විද්‍යා, කාලගුණ දෙපාර්තමේන්තුව |
| Horoscope | රාශි ඵල, ලග්න ඵල, කේන්දර, රාශි චක්‍රය, අද ලග්නය, සතිපල, දවසේ ලග්නය |
| Lottery | ලොතරැයි ප්‍රතිඵල, ලොතරැයිය, ජාතික ලොතරැයි, සංවර්ධන ලොතරැයි, වාසනාව අරන් |
| Obituary | අභාවප්‍රාප්ත, ශෝක පණිවිඩ, අවමංගල, පරලොක ප්‍රාප්ත |
| Exchange rate | විනිමය අනුපාතය, කොටස් වෙළඳපොල දර්ශක, ඩොලරයේ විකුණුම් මිල, මධ්‍යම බැංකු විනිමය |

## Result
- **Before:** 29,799
- **After:** 27,971
- **Dropped:** 1,828
