# Evaluation summary

Partial matching, micro averages. Predictions use the selected threshold in detect().
Leakage measures uncovered reference characters across all evaluated prediction types.
LOCATION and CUSTOM are excluded. Macro averages include all eleven evaluated types
with zero for undefined ratios; macro counts are arithmetic means of type counts.
Partial pairs are assigned by descending overlap, then positions, one to one.
Development errors use exact matching and include 30 characters on each side.

| Split | Configuration | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | patterns_only | 0.30 | 1.0000 | 0.8906 | 0.9105 | 0.1426 | 21 |
| dev | ner_only | 0.30 | 0.7838 | 0.4531 | 0.4949 | 0.7124 | 101 |
| dev | hybrid_no_propagation | 0.30 | 0.8942 | 0.9688 | 0.9529 | 0.0548 | 5 |
| dev | hybrid | 0.30 | 0.8942 | 0.9688 | 0.9529 | 0.0548 | 5 |

hybrid_camembert omitted: local recognizer or transformers is unavailable.
