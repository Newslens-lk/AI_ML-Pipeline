"""
Krippendorff's Alpha (ordinal) with bootstrapped 95% CI
for Phase 2 annotation conflict data.

Usage:  python krippendorff_alpha.py
"""

import numpy as np
import pandas as pd
import krippendorff
from itertools import combinations

# ── Config ──────────────────────────────────────────────────────────
DATA_PATH = "data/annotated_conflicts.csv"
ANNOTATOR_COLS = ["bias_label_praveen", "bias_label_ashini", "bias_label_dinithi"]
LABEL_ORDER = ["Far Left", "Left", "Center", "Right", "Far Right"]
LABEL_MAP = {label: i + 1 for i, label in enumerate(LABEL_ORDER)}  # 1-5
N_BOOTSTRAP = 1000
SEED = 42

# ── Load & reshape ─────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
n_items = len(df)
n_annotators = len(ANNOTATOR_COLS)

# Map labels → 1..5, NaN stays NaN
reliability_df = df[ANNOTATOR_COLS].replace(LABEL_MAP)
# Ensure unmapped values (should be none) become NaN
for col in ANNOTATOR_COLS:
    reliability_df[col] = pd.to_numeric(reliability_df[col], errors="coerce")

# krippendorff expects shape (n_annotators, n_items) with np.nan for missing
reliability_matrix = reliability_df.values.T.astype(float)

# ── Summary stats ──────────────────────────────────────────────────
total_cells = n_items * n_annotators
missing_cells = int(np.isnan(reliability_matrix).sum())
missing_pct = missing_cells / total_cells * 100

print("=" * 60)
print("KRIPPENDORFF'S ALPHA — ORDINAL")
print("=" * 60)
print(f"Items:             {n_items}")
print(f"Annotators:        {n_annotators}")
print(f"Total cells:       {total_cells}")
print(f"Missing cells:     {missing_cells} ({missing_pct:.1f}%)")
print(f"Label mapping:     {LABEL_MAP}")
print()

# ── Compute alpha ──────────────────────────────────────────────────
alpha = krippendorff.alpha(
    reliability_data=reliability_matrix,
    level_of_measurement="ordinal",
)
print(f"Krippendorff's alpha (ordinal): {alpha:.4f}")

# ── Bootstrap 95% CI (resample at item level) ─────────────────────
rng = np.random.default_rng(SEED)
boot_alphas = []

for _ in range(N_BOOTSTRAP):
    # Resample item indices (columns) with replacement
    idx = rng.choice(n_items, size=n_items, replace=True)
    boot_matrix = reliability_matrix[:, idx]
    try:
        a = krippendorff.alpha(
            reliability_data=boot_matrix,
            level_of_measurement="ordinal",
        )
        boot_alphas.append(a)
    except Exception:
        continue

boot_alphas = np.array(boot_alphas)
ci_lo, ci_hi = np.percentile(boot_alphas, [2.5, 97.5])

print(f"95% Bootstrap CI:               [{ci_lo:.4f}, {ci_hi:.4f}]")
print(f"  (based on {len(boot_alphas)} successful resamples)")
print()

# ── Pairwise breakdown ─────────────────────────────────────────────
print("-" * 60)
print("PAIRWISE BREAKDOWN")
print("-" * 60)

for a1, a2 in combinations(range(n_annotators), 2):
    col1, col2 = ANNOTATOR_COLS[a1], ANNOTATOR_COLS[a2]
    name1, name2 = col1.split("_")[-1], col2.split("_")[-1]

    # Subset to items where both annotated
    v1 = reliability_matrix[a1]
    v2 = reliability_matrix[a2]
    mask = ~np.isnan(v1) & ~np.isnan(v2)
    v1_clean, v2_clean = v1[mask], v2[mask]
    n_pair = int(mask.sum())

    if n_pair == 0:
        print(f"\n{name1} vs {name2}: no overlapping items")
        continue

    # Pairwise alpha (ordinal)
    pair_matrix = np.array([v1_clean, v2_clean])
    pair_alpha = krippendorff.alpha(
        reliability_data=pair_matrix,
        level_of_measurement="ordinal",
    )

    # Exact and adjacent agreement
    exact = int((v1_clean == v2_clean).sum())
    exact_pct = exact / n_pair * 100
    adjacent = int((np.abs(v1_clean - v2_clean) <= 1).sum())
    adjacent_pct = adjacent / n_pair * 100
    mean_dist = np.abs(v1_clean - v2_clean).mean()

    print(f"\n{name1} vs {name2} (n={n_pair}):")
    print(f"  Pairwise alpha (ordinal): {pair_alpha:.4f}")
    print(f"  Exact agreement:          {exact}/{n_pair} ({exact_pct:.1f}%)")
    print(f"  Adjacent agreement (±1):  {adjacent}/{n_pair} ({adjacent_pct:.1f}%)")
    print(f"  Mean label distance:      {mean_dist:.2f}")

print()
print("=" * 60)
print("INTERPRETATION GUIDE")
print("=" * 60)
print("""
  alpha >= 0.800  →  good reliability
  alpha >= 0.667  →  tentative conclusions acceptable
  alpha <  0.667  →  data should not be used for firm conclusions
  alpha ~  0.000  →  agreement is at chance level
  alpha <  0.000  →  systematic disagreement (worse than chance)

  'ordinal' metric penalises Far Left↔Far Right (distance 4)
  much more than Left↔Center (distance 1).
""")
