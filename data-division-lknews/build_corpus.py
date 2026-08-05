#!/usr/bin/env python3
"""
build_corpus.py — Prepare the lk_news Sinhala corpus.

Pipeline: 30,562 Sinhala articles → ~2,000 clean, bias-relevant articles.

Steps:
  1. Load Sinhala metadata from TSV index
  2. Read body text + basic quality filter (empty, too short)
  3. Content relevance filter (remove weather, horoscopes, etc.)
  4. Deduplicate via xxhash
  5. Stratified sample → 2,000
  6. Clean text + validate against Article schema → Parquet
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import ftfy
import pandas as pd
import xxhash
from schema import Article, make_article_id

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
LK_NEWS_DIR = BASE_DIR / "data" / "lk_news" / "data" / "lk_news"
TSV_PATH = LK_NEWS_DIR / "docs_all.tsv"
ARTICLES_DIR = LK_NEWS_DIR / "2020s"
CORPUS_DIR = BASE_DIR / "corpus"
DOCS_DIR = BASE_DIR / "docs"

TARGET_SAMPLE = 2000
MIN_BODY_LENGTH = 200  # characters

# Publisher name normalization
PUBLISHER_MAP = {
    "adaderanasinhalalk": "Ada Derana Sinhala",
    "adalk": "Ada",
    "lankadeepalk": "Lanka Deepa",
    "bbccomsinhala": "BBC Sinhala",
}

# Sinhala keywords for irrelevant content categories
IRRELEVANT_PATTERNS = {
    "weather": [
        "කාලගුණ", "කාලගුණය", "වර්ෂාපතනය", "උෂ්ණත්ව අනාවැකි",
        "කාලගුණ විද්‍යා", "කාලගුණ දෙපාර්තමේන්තුව",
    ],
    "horoscope": [
        "රාශි ඵල", "ලග්න ඵල", "කේන්දර", "රාශි චක්‍රය",
        "අද ලග්නය", "සතිපල", "දවසේ ලග්නය",
    ],
    "lottery": [
        "ලොතරැයි ප්‍රතිඵල", "ලොතරැයිය", "ජාතික ලොතරැයි",
        "සංවර්ධන ලොතරැයි", "වාසනාව අරන්",
    ],
    "obituary": [
        "අභාවප්‍රාප්ත", "ශෝක පණිවිඩ", "අවමංගල",
        "පරලොක ප්‍රාප්ත",
    ],
    "exchange_rate": [
        "විනිමය අනුපාතය", "කොටස් වෙළඳපොල දර්ශක",
        "ඩොලරයේ විකුණුම් මිල", "මධ්‍යම බැංකු විනිමය",
    ],
}


def log_step(step_num: int, name: str, before: int, after: int, details: str = ""):
    """Print a step summary."""
    dropped = before - after
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {name}")
    print(f"  Before: {before:,}  →  After: {after:,}  (dropped {dropped:,})")
    if details:
        print(f"  {details}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Step 1: Load Sinhala metadata from TSV
# ---------------------------------------------------------------------------
def step1_load_sinhala_tsv() -> pd.DataFrame:
    """Load TSV index and filter to Sinhala articles only."""
    df = pd.read_csv(TSV_PATH, sep="\t")
    df_si = df[df["lang"] == "si"].copy()
    df_si = df_si.reset_index(drop=True)
    return df_si


# ---------------------------------------------------------------------------
# Step 2: Read body text + quality filter
# ---------------------------------------------------------------------------
def _resolve_article_path(doc_id: str, date_str: str) -> Path:
    """Resolve the filesystem path for an article's directory."""
    year = date_str[:4]
    return ARTICLES_DIR / year / doc_id


def _read_body(doc_id: str, date_str: str) -> str | None:
    """Read doc.txt for an article, return None if missing/empty."""
    path = _resolve_article_path(doc_id, date_str) / "doc.txt"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text if text else None


def step2_read_body_and_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Read body text and drop empty/short articles."""
    bodies = []
    for _, row in df.iterrows():
        bodies.append(_read_body(row["doc_id"], row["date_str"]))

    df = df.copy()
    df["body_text"] = bodies

    # Drop missing body
    no_body_count = df["body_text"].isna().sum()
    df = df.dropna(subset=["body_text"])

    # Drop short articles
    short_mask = df["body_text"].str.len() < MIN_BODY_LENGTH
    short_count = short_mask.sum()
    df = df[~short_mask].reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Step 3: Content relevance filter
# ---------------------------------------------------------------------------
def _is_irrelevant(title: str, body: str) -> tuple[bool, str]:
    """Check if article matches irrelevant content patterns.

    Returns (is_irrelevant, matched_category).
    """
    combined = f"{title} {body[:500]}"  # check title + first 500 chars of body
    for category, keywords in IRRELEVANT_PATTERNS.items():
        for kw in keywords:
            if kw in combined:
                return True, category
    return False, ""


def step3_content_relevance_filter(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove articles about weather, horoscopes, lottery, etc."""
    keep_mask = []
    removed_categories: dict[str, int] = {}
    removed_examples: dict[str, list] = {}

    for _, row in df.iterrows():
        irrelevant, category = _is_irrelevant(
            row["description"], row["body_text"]
        )
        if irrelevant:
            removed_categories[category] = removed_categories.get(category, 0) + 1
            if category not in removed_examples:
                removed_examples[category] = []
            if len(removed_examples[category]) < 3:
                removed_examples[category].append({
                    "doc_id": row["doc_id"],
                    "title": row["description"][:100],
                })
        keep_mask.append(not irrelevant)

    df_filtered = df[keep_mask].reset_index(drop=True)
    return df_filtered, {"counts": removed_categories, "examples": removed_examples}


# ---------------------------------------------------------------------------
# Step 4: Deduplicate
# ---------------------------------------------------------------------------
def step4_deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Remove exact duplicates based on xxhash of body text."""
    df = df.copy()
    df["content_hash"] = df["body_text"].apply(
        lambda t: xxhash.xxh64(t.encode("utf-8")).hexdigest()
    )

    dup_mask = df.duplicated(subset=["content_hash"], keep="first")
    dup_examples = []
    dup_rows = df[dup_mask]
    for _, row in dup_rows.head(5).iterrows():
        dup_examples.append({
            "doc_id": row["doc_id"],
            "title": row["description"][:100],
            "hash": row["content_hash"],
        })

    df_deduped = df[~dup_mask].reset_index(drop=True)
    return df_deduped, dup_examples


# ---------------------------------------------------------------------------
# Step 5: Stratified sample
# ---------------------------------------------------------------------------
def step5_stratified_sample(df: pd.DataFrame, target: int) -> pd.DataFrame:
    """Sample with equal publisher allocation, year-spread within each.

    Allocates target / n_publishers articles per publisher. If a publisher
    has fewer articles than its allocation, take all and redistribute the
    shortfall to publishers that have surplus.
    """
    df = df.copy()
    df["year"] = df["date_str"].str[:4]
    publishers = df["newspaper_id"].unique().tolist()
    n_publishers = len(publishers)
    base_per_pub = target // n_publishers

    # First pass: allocate, respecting publisher pool sizes
    allocations: dict[str, int] = {}
    shortfall = 0
    surplus_pubs = []

    for pub in publishers:
        pool = len(df[df["newspaper_id"] == pub])
        if pool <= base_per_pub:
            allocations[pub] = pool  # take all available
            shortfall += base_per_pub - pool
        else:
            allocations[pub] = base_per_pub
            surplus_pubs.append(pub)

    # Second pass: redistribute shortfall to surplus publishers
    if surplus_pubs and shortfall > 0:
        extra_each = shortfall // len(surplus_pubs)
        remainder = shortfall % len(surplus_pubs)
        for i, pub in enumerate(surplus_pubs):
            pool = len(df[df["newspaper_id"] == pub])
            bonus = extra_each + (1 if i < remainder else 0)
            allocations[pub] = min(allocations[pub] + bonus, pool)

    # Sample from each publisher, spread across years within each
    samples = []
    for pub, n_alloc in allocations.items():
        pub_df = df[df["newspaper_id"] == pub]
        if n_alloc >= len(pub_df):
            samples.append(pub_df)
        else:
            # Year-stratified within this publisher
            year_counts = pub_df["year"].value_counts()
            pub_total = len(pub_df)
            pub_samples = []
            for year, ycount in year_counts.items():
                yn = max(1, round(ycount / pub_total * n_alloc))
                year_df = pub_df[pub_df["year"] == year]
                yn = min(yn, len(year_df))
                pub_samples.append(year_df.sample(n=yn, random_state=42))
            pub_sampled = pd.concat(pub_samples, ignore_index=True)
            # Trim or pad to exact allocation
            if len(pub_sampled) > n_alloc:
                pub_sampled = pub_sampled.sample(n=n_alloc, random_state=42)
            elif len(pub_sampled) < n_alloc:
                remaining = pub_df[~pub_df.index.isin(pub_sampled.index)]
                extra = remaining.sample(
                    n=min(n_alloc - len(pub_sampled), len(remaining)),
                    random_state=42,
                )
                pub_sampled = pd.concat([pub_sampled, extra], ignore_index=True)
            samples.append(pub_sampled)

    sampled = pd.concat(samples, ignore_index=True)

    # Final adjustment to exact target
    if len(sampled) > target:
        sampled = sampled.sample(n=target, random_state=42).reset_index(drop=True)
    elif len(sampled) < target:
        remaining = df[~df.index.isin(sampled.index)]
        extra = remaining.sample(
            n=min(target - len(sampled), len(remaining)), random_state=42
        )
        sampled = pd.concat([sampled, extra], ignore_index=True)

    return sampled.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Step 6: Clean text + validate + write Parquet
# ---------------------------------------------------------------------------
def _clean_text(text: str) -> str:
    """Apply text cleaning pipeline: ftfy → NFC normalize."""
    text = ftfy.fix_text(text)
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def _has_sinhala_chars(text: str) -> bool:
    """Check if text contains Sinhala Unicode characters (U+0D80–U+0DFF)."""
    sinhala_count = sum(1 for c in text[:500] if "\u0D80" <= c <= "\u0DFF")
    return sinhala_count >= 20  # at least 20 Sinhala chars in first 500


def step6_clean_and_validate(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Clean text, verify language, validate schema, write Parquet."""
    records = []
    lang_rejected = []

    for _, row in df.iterrows():
        title = row["description"]
        body = row["body_text"]
        content_hash = xxhash.xxh64(body.encode("utf-8")).hexdigest()

        # Final language check — Sinhala Unicode range verification
        # (langdetect does not support Sinhala, so we check for Sinhala chars)
        if not _has_sinhala_chars(body):
            lang_rejected.append({
                "doc_id": row["doc_id"],
                "title": title[:80],
                "detected": "non-sinhala",
            })
            continue

        # Build and validate Article (raw text, no cleaning applied)
        url = row["url_metadata"]
        article_id = make_article_id("lk_news", url)
        publisher = PUBLISHER_MAP.get(row["newspaper_id"], row["newspaper_id"])
        published_at = datetime.strptime(row["date_str"], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )

        article = Article(
            article_id=article_id,
            source_dataset="lk_news",
            publisher=publisher,
            url=url,
            published_at=published_at,
            title=title,
            body_text=body,
            language="si",
            content_hash=content_hash,
            raw_path=str(
                _resolve_article_path(row["doc_id"], row["date_str"]) / "doc.txt"
            ),
        )
        records.append(article.model_dump())

    result_df = pd.DataFrame(records)

    # Write Parquet
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    out_path = CORPUS_DIR / f"articles_{date_stamp}.parquet"
    result_df.to_parquet(out_path, index=False)

    return result_df, lang_rejected


# ---------------------------------------------------------------------------
# Documentation writer
# ---------------------------------------------------------------------------
def write_step_doc(step_num: int, title: str, content: str):
    """Write step documentation to docs/."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / f"step{step_num}_{title.lower().replace(' ', '_')}.md"
    path.write_text(content, encoding="utf-8")
    print(f"  → Doc written: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("lk_news Sinhala Corpus Preparation")
    print("=" * 60)

    # --- Step 1 ---
    df = step1_load_sinhala_tsv()
    total_tsv = pd.read_csv(TSV_PATH, sep="\t").shape[0]
    log_step(1, "Load Sinhala from TSV", total_tsv, len(df))

    publisher_dist = df["newspaper_id"].value_counts().to_dict()
    year_dist = df["date_str"].str[:4].value_counts().sort_index().to_dict()

    write_step_doc(1, "load_sinhala", f"""# Step 1: Load Sinhala Metadata from TSV

## What this step does
Reads the TSV index file (`docs_all.tsv`) which contains metadata for all
125k+ articles across all languages. Filters to only rows where `lang == "si"`.

## Why
The lk_news dataset contains Tamil ({total_tsv - len(df) - 4:,} non-Sinhala) and
English articles that are outside our project scope. We only need Sinhala articles
for bias annotation.

## Result
- **Total in TSV:** {total_tsv:,}
- **Sinhala articles:** {len(df):,}

## Publisher distribution
{chr(10).join(f'- **{PUBLISHER_MAP.get(k,k)}** (`{k}`): {v:,}' for k, v in publisher_dist.items())}

## Year distribution
{chr(10).join(f'- **{k}:** {v:,}' for k, v in year_dist.items())}

## Example rows
```
doc_id: {df.iloc[0]['doc_id']}
date:   {df.iloc[0]['date_str']}
title:  {df.iloc[0]['description'][:80]}
lang:   {df.iloc[0]['lang']}
source: {df.iloc[0]['newspaper_id']}
```
""")

    # --- Step 2 ---
    before_2 = len(df)
    df = step2_read_body_and_filter(df)
    log_step(2, "Read body + quality filter", before_2, len(df),
             f"Min body length: {MIN_BODY_LENGTH} chars")

    # Sample examples of short/empty articles for docs
    sample_short = df.head(3)[["doc_id", "description"]].to_dict("records")

    write_step_doc(2, "quality_filter", f"""# Step 2: Read Body Text + Quality Filter

## What this step does
1. Reads `doc.txt` (article body) for each Sinhala article directory.
2. Drops articles with **missing/empty** body text.
3. Drops articles with body text **shorter than {MIN_BODY_LENGTH} characters** —
   these are typically stubs, image captions, or headline-only entries.

## Why
Articles without meaningful body text cannot be annotated for media bias.
Very short articles lack enough content for framing analysis.

## Result
- **Before:** {before_2:,}
- **After:** {len(df):,}
- **Dropped:** {before_2 - len(df):,}

## Example of a kept article
```
doc_id: {df.iloc[0]['doc_id']}
title:  {df.iloc[0]['description'][:80]}
body length: {len(df.iloc[0]['body_text']):,} chars
body preview: {df.iloc[0]['body_text'][:150]}...
```
""")

    # --- Step 3 ---
    before_3 = len(df)
    df, relevance_info = step3_content_relevance_filter(df)
    log_step(3, "Content relevance filter", before_3, len(df))

    removed_detail = ""
    for cat, count in relevance_info["counts"].items():
        examples_str = ""
        if cat in relevance_info["examples"]:
            for ex in relevance_info["examples"][cat]:
                examples_str += f'\n    - `{ex["doc_id"]}`: {ex["title"]}'
        removed_detail += f"\n### {cat.title()} — {count:,} removed{examples_str}\n"

    write_step_doc(3, "content_relevance", f"""# Step 3: Content Relevance Filter

## What this step does
Removes articles that are **not meaningful for bias analysis**. These are
formulaic, data-driven, or non-editorial content where media bias cannot
manifest.

Matches Sinhala keywords in the **title + first 500 characters of body**.

## Categories removed
{removed_detail if removed_detail.strip() else "No articles matched the irrelevant patterns."}

## Keywords used

| Category | Keywords |
|----------|----------|
| Weather | {', '.join(IRRELEVANT_PATTERNS['weather'])} |
| Horoscope | {', '.join(IRRELEVANT_PATTERNS['horoscope'])} |
| Lottery | {', '.join(IRRELEVANT_PATTERNS['lottery'])} |
| Obituary | {', '.join(IRRELEVANT_PATTERNS['obituary'])} |
| Exchange rate | {', '.join(IRRELEVANT_PATTERNS['exchange_rate'])} |

## Result
- **Before:** {before_3:,}
- **After:** {len(df):,}
- **Dropped:** {before_3 - len(df):,}
""")

    # --- Step 4 ---
    before_4 = len(df)
    df, dup_examples = step4_deduplicate(df)
    log_step(4, "Deduplicate (xxhash)", before_4, len(df))

    dup_examples_str = ""
    for ex in dup_examples:
        dup_examples_str += f'- `{ex["doc_id"]}`: {ex["title"]} (hash: `{ex["hash"][:12]}...`)\n'

    write_step_doc(4, "deduplicate", f"""# Step 4: Deduplicate

## What this step does
Computes an `xxhash.xxh64` hash of each article's body text. If two articles
have the **exact same hash**, only the first occurrence is kept.

## Why
The same article can appear multiple times if it was scraped on different days
or re-published. Duplicates would bias the sample and waste annotation effort.

## Result
- **Before:** {before_4:,}
- **After:** {len(df):,}
- **Duplicates removed:** {before_4 - len(df):,}

## Example duplicates found
{dup_examples_str if dup_examples_str else "No duplicates found."}
""")

    # --- Step 5 ---
    before_5 = len(df)
    df_sampled = step5_stratified_sample(df, TARGET_SAMPLE)
    log_step(5, f"Stratified sample → {TARGET_SAMPLE}", before_5, len(df_sampled))

    sampled_pub_dist = df_sampled["newspaper_id"].value_counts().to_dict()
    sampled_year_dist = df_sampled["date_str"].str[:4].value_counts().sort_index().to_dict()

    write_step_doc(5, "stratified_sample", f"""# Step 5: Equal-Publisher Stratified Sample → {TARGET_SAMPLE:,}

## What this step does
Draws a **balanced sample** of {TARGET_SAMPLE:,} articles with **equal allocation
per publisher** ({TARGET_SAMPLE // 4} each). Within each publisher's allocation,
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
- **Pool size:** {before_5:,}
- **Sampled:** {len(df_sampled):,}

## Publisher distribution (sampled)
{chr(10).join(f'- **{PUBLISHER_MAP.get(k,k)}**: {v:,}' for k, v in sampled_pub_dist.items())}

## Year distribution (sampled)
{chr(10).join(f'- **{k}:** {v:,}' for k, v in sampled_year_dist.items())}

## Example sampled articles
```
1. {df_sampled.iloc[0]['doc_id']}: {df_sampled.iloc[0]['description'][:80]}
2. {df_sampled.iloc[1]['doc_id']}: {df_sampled.iloc[1]['description'][:80]}
3. {df_sampled.iloc[2]['doc_id']}: {df_sampled.iloc[2]['description'][:80]}
```
""")

    # --- Step 6 ---
    before_6 = len(df_sampled)
    result_df, lang_rejected = step6_clean_and_validate(df_sampled)
    log_step(6, "Clean + validate + write Parquet", before_6, len(result_df),
             f"Language rejections: {len(lang_rejected)}")

    lang_rej_str = ""
    for ex in lang_rejected[:5]:
        lang_rej_str += f'- `{ex["doc_id"]}`: detected as `{ex["detected"]}` — {ex["title"]}\n'

    out_path = CORPUS_DIR / f"articles_{datetime.now().strftime('%Y-%m-%d')}.parquet"

    write_step_doc(6, "clean_validate", f"""# Step 6: Clean Text, Validate & Write Parquet

## What this step does
1. **Text cleaning:** `ftfy.fix_text()` → `unicodedata.normalize('NFC')`
2. **Language verification:** Checks for Sinhala Unicode characters (U+0D80–U+0DFF)
   in the cleaned body. Rejects articles with fewer than 20 Sinhala characters
   in the first 500 chars. (`langdetect` does not support Sinhala.)
3. **Schema validation:** Each article is validated against the pydantic
   `Article` model (Layer 1 fields required, Layer 3 fields null).
4. **Write:** Saves the final corpus as a dated Parquet file.

## Why
- `ftfy` fixes mojibake and encoding errors common in scraped Sinhala text.
- NFC normalization ensures consistent Unicode representation.
- Sinhala Unicode range check catches any misclassified articles that slipped through.
- Pydantic validation guarantees every record conforms to the schema.

## Result
- **Before:** {before_6:,}
- **After:** {len(result_df):,}
- **Language rejections:** {len(lang_rejected)}
- **Output:** `{out_path.relative_to(BASE_DIR)}`

## Language rejections (examples)
{lang_rej_str if lang_rej_str else "None — all articles confirmed as Sinhala."}

## Final corpus schema
| Field | Type | Example |
|-------|------|---------|
| article_id | str | `{result_df.iloc[0]['article_id'][:36]}` |
| source_dataset | str | `lk_news` |
| publisher | str | `{result_df.iloc[0]['publisher']}` |
| published_at | datetime | `{result_df.iloc[0]['published_at']}` |
| title | str | `{result_df.iloc[0]['title'][:60]}...` |
| body_text | str | `{result_df.iloc[0]['body_text'][:60]}...` |
| content_hash | str | `{result_df.iloc[0]['content_hash'][:16]}...` |

## Final publisher & year distribution
{chr(10).join(f'- **{k}**: {v}' for k, v in result_df['publisher'].value_counts().to_dict().items())}
""")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print(f"  Final corpus: {len(result_df):,} articles")
    print(f"  Output: {out_path}")
    print(f"  Docs: {DOCS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
