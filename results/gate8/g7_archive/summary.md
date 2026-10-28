# Evaluation summary

Partial matching, micro averages. Predictions use the selected threshold in detect().
Leakage measures uncovered reference characters across all evaluated prediction types.
LOCATION and CUSTOM are excluded. Macro averages include all eleven evaluated types
with zero for undefined ratios; macro counts are arithmetic means of type counts.
Partial pairs are assigned by descending overlap, then positions, one to one.
Development errors use exact matching and include 30 characters on each side.

| Split | Configuration | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | patterns_only | 0.30 | 1.0000 | 0.9743 | 0.9793 | 0.0155 | 8 |
| dev | ner_only | 0.30 | 0.8599 | 0.4341 | 0.4818 | 0.6956 | 167 |
| dev | hybrid_no_propagation | 0.30 | 0.9904 | 0.9968 | 0.9955 | 0.0030 | 1 |
| dev | hybrid | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 |
| dev | hybrid_camembert | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 |
| test | patterns_only | 0.30 | 1.0000 | 1.0000 | 1.0000 | 0.0196 | 0 |
| test | ner_only | 0.30 | 0.9091 | 0.4301 | 0.4808 | 0.6945 | 51 |
| test | hybrid_no_propagation | 0.30 | 0.9789 | 1.0000 | 0.9957 | 0.0196 | 0 |
| test | hybrid | 0.30 | 0.9789 | 1.0000 | 0.9957 | 0.0196 | 0 |
| test | hybrid_camembert | 0.30 | 0.9789 | 1.0000 | 0.9957 | 0.0196 | 0 |
| challenge | patterns_only | 0.30 | 0.9635 | 0.6947 | 0.7358 | 0.2489 | 57 |
| challenge | ner_only | 0.30 | 0.7073 | 0.4579 | 0.4926 | 0.6114 | 94 |
| challenge | hybrid_no_propagation | 0.30 | 0.8128 | 0.8000 | 0.8025 | 0.1581 | 34 |
| challenge | hybrid | 0.30 | 0.7921 | 0.8421 | 0.8316 | 0.1283 | 26 |
| challenge | hybrid_camembert | 0.30 | 0.7955 | 0.9211 | 0.8929 | 0.0969 | 12 |

## 95% bootstrap intervals

Document resampling with replacement, 2,000 draws, random.Random seed 45.
Percentiles 2.5 and 97.5 use linear interpolation; the threshold stays fixed.
Ratios are recomputed from summed document counts (partial matching, micro).
Undefined ratios are zero. A single document gives a collapsed interval.
These intervals do not account for corpus bias or threshold selection.

| Split | Configuration | Threshold | Documents | Precision | Recall | F2 | Leak rate |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| dev | patterns_only | 0.30 | 20 | [1.0000, 1.0000] | [0.9479, 0.9967] | [0.9578, 0.9974] | [0.0014, 0.0331] |
| dev | ner_only | 0.30 | 20 | [0.7952, 0.9198] | [0.3863, 0.4783] | [0.4325, 0.5267] | [0.6508, 0.7429] |
| dev | hybrid_no_propagation | 0.30 | 20 | [0.9800, 1.0000] | [0.9899, 1.0000] | [0.9894, 0.9994] | [0.0000, 0.0074] |
| dev | hybrid | 0.30 | 20 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.9959, 1.0000] | [0.0000, 0.0000] |
| dev | hybrid_camembert | 0.30 | 20 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.9959, 1.0000] | [0.0000, 0.0000] |
| test | patterns_only | 0.30 | 6 | [1.0000, 1.0000] | [1.0000, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0606] |
| test | ner_only | 0.30 | 6 | [0.8400, 0.9773] | [0.3542, 0.4839] | [0.4028, 0.5344] | [0.6052, 0.7991] |
| test | hybrid_no_propagation | 0.30 | 6 | [0.9560, 1.0000] | [1.0000, 1.0000] | [0.9909, 1.0000] | [0.0000, 0.0606] |
| test | hybrid | 0.30 | 6 | [0.9560, 1.0000] | [1.0000, 1.0000] | [0.9909, 1.0000] | [0.0000, 0.0606] |
| test | hybrid_camembert | 0.30 | 6 | [0.9560, 1.0000] | [1.0000, 1.0000] | [0.9909, 1.0000] | [0.0000, 0.0606] |
| challenge | patterns_only | 0.30 | 8 | [0.9304, 1.0000] | [0.6087, 0.7865] | [0.6567, 0.8161] | [0.1876, 0.3050] |
| challenge | ner_only | 0.30 | 8 | [0.6325, 0.7823] | [0.3804, 0.5517] | [0.4137, 0.5825] | [0.5319, 0.6725] |
| challenge | hybrid_no_propagation | 0.30 | 8 | [0.7539, 0.8743] | [0.7129, 0.8871] | [0.7243, 0.8820] | [0.1010, 0.2167] |
| challenge | hybrid | 0.30 | 8 | [0.7238, 0.8614] | [0.7463, 0.9231] | [0.7517, 0.9047] | [0.0780, 0.1822] |
| challenge | hybrid_camembert | 0.30 | 8 | [0.7197, 0.8643] | [0.8945, 0.9514] | [0.8569, 0.9285] | [0.0591, 0.1347] |

Challenge was written blind after the detection rules were frozen.
It uses the threshold selected on dev, without tuning on challenge.

## Development error categories

Exact FN/FP rows for hybrid; one boundary or type error can produce two rows.
Overlapping unmatched spans: type confusion takes priority over boundary errors.

| Category | Error rows |
| --- | ---: |
| boundary | 0 |
| extra | 3 |
| missed | 0 |
| type_confusion | 0 |

