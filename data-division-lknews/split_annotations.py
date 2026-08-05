#!/usr/bin/env python3
"""
split_annotations.py — Split the corpus into annotation sets.

- 150 overlap articles (all 3 annotators, for IAA)
- 1850 remaining split: Praveen 650, Ashini 600, Dinithi 600
- All splits balanced across 4 publishers
- Outputs CSVs to annotations/ folder
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
CORPUS_PATH = BASE_DIR / "corpus" / "articles_2026-07-26.parquet"
OUT_DIR = BASE_DIR / "annotations"

OVERLAP_SIZE = 150
SPLITS = {
    "praveen": 650,
    "ashini": 600,
    "dinithi": 600,
}

ANNOTATION_COLUMNS = [
    "article_id",
    "publisher",
    "url",
    "published_at",
    "title",
    "body_text",
    "bias_label",
]


def balanced_sample(df: pd.DataFrame, n: int, random_state: int) -> pd.DataFrame:
    """Sample n articles balanced across publishers."""
    publishers = df["publisher"].unique()
    per_pub = n // len(publishers)
    remainder = n % len(publishers)

    samples = []
    for i, pub in enumerate(sorted(publishers)):
        pub_df = df[df["publisher"] == pub]
        pub_n = per_pub + (1 if i < remainder else 0)
        pub_n = min(pub_n, len(pub_df))
        samples.append(pub_df.sample(n=pub_n, random_state=random_state))

    result = pd.concat(samples, ignore_index=True)

    # If we're short (a publisher didn't have enough), fill from remaining
    if len(result) < n:
        used_ids = set(result["article_id"])
        remaining = df[~df["article_id"].isin(used_ids)]
        extra = remaining.sample(n=n - len(result), random_state=random_state)
        result = pd.concat([result, extra], ignore_index=True)

    return result


def main():
    df = pd.read_parquet(CORPUS_PATH)
    print(f"Loaded corpus: {len(df)} articles")
    print(f"Publishers: {df['publisher'].value_counts().to_dict()}\n")

    # --- Overlap set ---
    overlap = balanced_sample(df, OVERLAP_SIZE, random_state=42)
    overlap_ids = set(overlap["article_id"])
    print(f"Overlap set: {len(overlap)} articles")
    print(f"  Publisher mix: {overlap['publisher'].value_counts().to_dict()}")

    # --- Remaining pool ---
    remaining = df[~df["article_id"].isin(overlap_ids)].copy()
    print(f"\nRemaining pool: {len(remaining)} articles")

    # --- Split remaining into 3 annotator sets ---
    used_ids = set()
    annotator_sets = {}

    for name, size in SPLITS.items():
        pool = remaining[~remaining["article_id"].isin(used_ids)]
        split = balanced_sample(pool, size, random_state=hash(name) % 2**31)
        annotator_sets[name] = split
        used_ids.update(split["article_id"])
        print(f"\n{name.title()}: {len(split)} unique + {len(overlap)} overlap = {len(split) + len(overlap)} total")
        print(f"  Publisher mix: {split['publisher'].value_counts().to_dict()}")

    # --- Write CSVs ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Overlap CSV
    overlap_out = overlap[ANNOTATION_COLUMNS[:-1]].copy()
    overlap_out["bias_label"] = ""
    overlap_out.to_csv(OUT_DIR / "overlap_150.csv", index=False)
    print(f"\nWritten: {OUT_DIR / 'overlap_150.csv'}")

    # Per-annotator CSVs (unique + overlap combined)
    for name, unique_df in annotator_sets.items():
        combined = pd.concat([unique_df, overlap], ignore_index=True)
        combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
        out = combined[ANNOTATION_COLUMNS[:-1]].copy()
        out["bias_label"] = ""
        out_path = OUT_DIR / f"{name}.csv"
        out.to_csv(out_path, index=False)
        print(f"Written: {out_path} ({len(out)} articles)")

    # --- Summary ---
    print("\n" + "=" * 50)
    print("SPLIT SUMMARY")
    print("=" * 50)
    print(f"  Overlap (IAA):  {len(overlap)} articles (in all 3 sets)")
    for name, unique_df in annotator_sets.items():
        total = len(unique_df) + len(overlap)
        print(f"  {name.title():12s}:  {len(unique_df)} unique + {len(overlap)} overlap = {total} total")
    print(f"  Total distinct: {len(overlap) + sum(len(s) for s in annotator_sets.values())} articles")


if __name__ == "__main__":
    main()
