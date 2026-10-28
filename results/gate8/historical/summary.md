# Evaluation summary

Partial matching, micro averages. Predictions use the selected threshold in detect().
Leakage measures uncovered reference characters across all evaluated prediction types.
LOCATION and CUSTOM are excluded. Macro averages include all eleven evaluated types
with zero for undefined ratios; macro counts are arithmetic means of type counts.
Partial pairs are assigned by descending overlap, then positions, one to one.
Development errors use exact matching and include 30 characters on each side.

| Split | Configuration | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | hybrid | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 |
| dev | hybrid_camembert | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 |

## 95% bootstrap intervals

Document resampling with replacement, 2,000 draws, random.Random seed 45.
Percentiles 2.5 and 97.5 use linear interpolation; the threshold stays fixed.
Ratios are recomputed from summed document counts (partial matching, micro).
Undefined ratios are zero. A single document gives a collapsed interval.
These intervals do not account for corpus bias or threshold selection.

| Split | Configuration | Threshold | Documents | Precision | Recall | F2 | Leak rate |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| dev | hybrid | 0.30 | 20 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.9959, 1.0000] | [0.0000, 0.0000] |
| dev | hybrid_camembert | 0.30 | 20 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.9959, 1.0000] | [0.0000, 0.0000] |

## Development error categories

Exact FN/FP rows for hybrid; one boundary or type error can produce two rows.
Overlapping unmatched spans: type confusion takes priority over boundary errors.

| Category | Error rows |
| --- | ---: |
| missed | 0 |
| extra | 3 |
| boundary | 0 |
| type_confusion | 0 |

