# Evaluation summary

Partial matching, micro averages. Predictions use the selected threshold in detect().
Leakage measures uncovered reference characters across all evaluated prediction types.
LOCATION and CUSTOM are excluded. Macro averages include all eleven evaluated types
with zero for undefined ratios; macro counts are arithmetic means of type counts.
Partial pairs are assigned by descending overlap, then positions, one to one.
Development errors use exact matching and include 30 characters on each side.

| Split | Configuration | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | patterns_only | 0.30 | 1.0000 | 0.9844 | 0.9875 | 0.0142 | 3 |
| dev | ner_only | 0.30 | 0.9072 | 0.4583 | 0.5087 | 0.6937 | 101 |
| dev | hybrid_no_propagation | 0.30 | 0.9648 | 1.0000 | 0.9928 | 0.0085 | 0 |
| dev | hybrid | 0.30 | 0.9648 | 1.0000 | 0.9928 | 0.0085 | 0 |
| dev | hybrid_camembert | 0.30 | 0.9648 | 1.0000 | 0.9928 | 0.0085 | 0 |

