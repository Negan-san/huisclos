# Before/after comparison: challenge

Partial matching, micro averages, each report at its selected threshold.
Delta = current - reference (proportions, except exposed entity counts).
Missing configurations or intervals are marked 'Not recorded'.
Marginal 95% intervals do not provide an interval or a significance test for the delta.

reference: commit 8c47a7634a408155086257095aed47b2a27b1067, threshold 0.3, documents 8, corpus SHA-256 5ad31106b23143c97fbc7f1796da28f907e110d7ded7272468584df405999a23.
current: commit b86a977bb30370f913f96189b55b8143e72813b3, threshold 0.3, documents 8, corpus SHA-256 c47502d65bf05b6f3e0bd7e0bf9ccd9e58b046787fa2252e6a49ece85a03d609.
Warning: corpus_sha256_different.

| Configuration | Metric | Reference | Current | Reference 95% interval | Current 95% interval | Delta |
| --- | --- | ---: | ---: | --- | --- | ---: |
| hybrid | precision | 0.7488 | 0.7921 | [0.7054, 0.7990] | [0.7238, 0.8614] | +0.0433 |
| hybrid | recall | 0.8316 | 0.8421 | [0.7158, 0.9231] | [0.7463, 0.9231] | +0.0105 |
| hybrid | f2 | 0.8136 | 0.8316 | [0.7163, 0.8917] | [0.7517, 0.9047] | +0.0180 |
| hybrid | leak_rate | 0.1758 | 0.1283 | [0.1344, 0.2296] | [0.0780, 0.1822] | -0.0475 |
| hybrid | exposed_entities | 27.0000 | 26.0000 | Not recorded | Not recorded | -1.0000 |
| hybrid_camembert | precision | 0.7489 | 0.7955 | [0.7087, 0.7888] | [0.7197, 0.8643] | +0.0465 |
| hybrid_camembert | recall | 0.9105 | 0.9211 | [0.8802, 0.9460] | [0.8945, 0.9514] | +0.0105 |
| hybrid_camembert | f2 | 0.8729 | 0.8929 | [0.8457, 0.9065] | [0.8569, 0.9285] | +0.0200 |
| hybrid_camembert | leak_rate | 0.1328 | 0.0969 | [0.1028, 0.1669] | [0.0591, 0.1347] | -0.0358 |
| hybrid_camembert | exposed_entities | 13.0000 | 12.0000 | Not recorded | Not recorded | -1.0000 |
| hybrid_no_propagation | precision | 0.7629 | 0.8128 | [0.7178, 0.8122] | [0.7539, 0.8743] | +0.0499 |
| hybrid_no_propagation | recall | 0.7789 | 0.8000 | [0.6782, 0.8706] | [0.7129, 0.8871] | +0.0211 |
| hybrid_no_propagation | f2 | 0.7757 | 0.8025 | [0.6879, 0.8579] | [0.7243, 0.8820] | +0.0269 |
| hybrid_no_propagation | leak_rate | 0.2094 | 0.1581 | [0.1610, 0.2634] | [0.1010, 0.2167] | -0.0514 |
| hybrid_no_propagation | exposed_entities | 37.0000 | 34.0000 | Not recorded | Not recorded | -3.0000 |
| ner_only | precision | 0.6825 | 0.7073 | [0.6000, 0.7717] | [0.6325, 0.7823] | +0.0248 |
| ner_only | recall | 0.4526 | 0.4579 | [0.3694, 0.5506] | [0.3804, 0.5517] | +0.0053 |
| ner_only | f2 | 0.4853 | 0.4926 | [0.3995, 0.5818] | [0.4137, 0.5825] | +0.0073 |
| ner_only | leak_rate | 0.6347 | 0.6114 | [0.5578, 0.6986] | [0.5319, 0.6725] | -0.0233 |
| ner_only | exposed_entities | 94.0000 | 94.0000 | Not recorded | Not recorded | +0.0000 |
| patterns_only | precision | 0.9313 | 0.9635 | [0.8947, 0.9690] | [0.9304, 1.0000] | +0.0322 |
| patterns_only | recall | 0.6421 | 0.6947 | [0.5454, 0.7374] | [0.6087, 0.7865] | +0.0526 |
| patterns_only | f2 | 0.6846 | 0.7358 | [0.5961, 0.7684] | [0.6567, 0.8161] | +0.0512 |
| patterns_only | leak_rate | 0.3217 | 0.2489 | [0.2695, 0.3771] | [0.1876, 0.3050] | -0.0728 |
| patterns_only | exposed_entities | 67.0000 | 57.0000 | Not recorded | Not recorded | -10.0000 |
