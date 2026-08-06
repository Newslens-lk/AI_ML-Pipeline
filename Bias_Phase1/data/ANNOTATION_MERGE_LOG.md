# Annotation Merge Log

## Source Files

| File | Total Rows | Annotated Rows | Columns |
|------|-----------|----------------|---------|
| `praveen - praveen.csv` | 800 | 175 | article_id, publisher, url, published_at, title, body_text, bias_label |
| `ashini - ashini.csv` | 750 | 527* | article_id, publisher, url, published_at, title, body_text, bias_label |
| `dinithi - dinithi.csv` | 750 | 193 | article_id, publisher, url, published_at, title, body_text, bias_label, flags |

*Ashini's file had 528 rows with a bias_label value, but 1 was a duplicate header row (`bias_label` as the value) which was excluded.

## Data Cleaning Applied

1. **Duplicate header row**: Ashini's file contained a row where `bias_label` was literally "bias_label" (a duplicated header). This row was excluded.
2. **Label normalization**: Dinithi used "Far left" (lowercase 'l') instead of "Far Left". This was normalized to "Far Left" for consistency.
3. **Extra columns**: Dinithi's file had `flags` and an empty trailing column. The `flags` column had 3 entries (2 with value "flags" which appear to be artifacts, and 1 with value "done"). These were noted but not carried into the output.

## Labels Used

All annotators used the same 5-point scale: `Far Left`, `Left`, `Center`, `Right`, `Far Right`

## Output Files

### `annotated_merged.csv` (811 rows)

Contains all articles annotated by **exactly one** person. Columns:
- `article_id`, `publisher`, `url`, `published_at`, `title`, `body_text`, `bias_label`, `annotator`

The `annotator` column records who annotated each row (praveen, ashini, or dinithi).

### `annotated_conflicts.csv` (38 rows)

Contains articles annotated by **multiple annotators** (2 or 3 people). These are kept separate and NOT merged into the main file. Columns:
- `article_id`, `publisher`, `url`, `published_at`, `title`, `body_text`
- `bias_label_praveen`, `bias_label_ashini`, `bias_label_dinithi` (empty if that annotator didn't label it)
- `annotator_count`

### Conflict Summary

- **38 articles** were annotated by more than one person
- **15 AGREE** (all annotators gave the same label)
- **23 DISAGREE** (annotators gave different labels)
- 7 articles were annotated by all 3 annotators

## Total Annotation Count

| Annotator | Unique Only | In Conflicts | Total |
|-----------|------------|--------------|-------|
| Praveen   | 147        | 28           | 175   |
| Ashini    | 501        | 26           | 527   |
| Dinithi   | 163        | 22*          | ~193  |

Combined unique articles annotated: **849** (811 unique + 38 conflicts)
