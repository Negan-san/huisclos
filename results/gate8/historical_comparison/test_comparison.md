# Before/after comparison: test

Partial matching, micro averages, each report at its selected threshold.
Delta = current - reference (proportions, except exposed entity counts).
Missing configurations or intervals are marked 'Not recorded'.
Marginal 95% intervals do not provide an interval or a significance test for the delta.

reference: commit b86a977bb30370f913f96189b55b8143e72813b3, threshold 0.3, documents 6, corpus SHA-256 12a7852e765d98c10be74025e684c15280ccb47615017529ee320370faa4cd4d.
current: commit e3d13bdc25839783eebe998c8f971862d78754d5, threshold 0.3, documents 6, corpus SHA-256 12a7852e765d98c10be74025e684c15280ccb47615017529ee320370faa4cd4d.

| Configuration | Metric | Reference | Current | Reference 95% interval | Current 95% interval | Delta |
| --- | --- | ---: | ---: | --- | --- | ---: |
| hybrid | precision | 0.9789 | 0.9789 | [0.9560, 1.0000] | [0.9560, 1.0000] | +0.0000 |
| hybrid | recall | 1.0000 | 1.0000 | [1.0000, 1.0000] | [1.0000, 1.0000] | +0.0000 |
| hybrid | f2 | 0.9957 | 0.9957 | [0.9909, 1.0000] | [0.9909, 1.0000] | +0.0000 |
| hybrid | leak_rate | 0.0196 | 0.0000 | [0.0000, 0.0606] | [0.0000, 0.0000] | -0.0196 |
| hybrid | exposed_entities | 0.0000 | 0.0000 | Not recorded | Not recorded | +0.0000 |
| hybrid_camembert | precision | 0.9789 | 0.9789 | [0.9560, 1.0000] | [0.9560, 1.0000] | +0.0000 |
| hybrid_camembert | recall | 1.0000 | 1.0000 | [1.0000, 1.0000] | [1.0000, 1.0000] | +0.0000 |
| hybrid_camembert | f2 | 0.9957 | 0.9957 | [0.9909, 1.0000] | [0.9909, 1.0000] | +0.0000 |
| hybrid_camembert | leak_rate | 0.0196 | 0.0000 | [0.0000, 0.0606] | [0.0000, 0.0000] | -0.0196 |
| hybrid_camembert | exposed_entities | 0.0000 | 0.0000 | Not recorded | Not recorded | +0.0000 |
| hybrid_no_propagation | precision | 0.9789 | Not recorded | [0.9560, 1.0000] | Not recorded | Not recorded |
| hybrid_no_propagation | recall | 1.0000 | Not recorded | [1.0000, 1.0000] | Not recorded | Not recorded |
| hybrid_no_propagation | f2 | 0.9957 | Not recorded | [0.9909, 1.0000] | Not recorded | Not recorded |
| hybrid_no_propagation | leak_rate | 0.0196 | Not recorded | [0.0000, 0.0606] | Not recorded | Not recorded |
| hybrid_no_propagation | exposed_entities | 0.0000 | Not recorded | Not recorded | Not recorded | Not recorded |
| ner_only | precision | 0.9091 | Not recorded | [0.8400, 0.9773] | Not recorded | Not recorded |
| ner_only | recall | 0.4301 | Not recorded | [0.3542, 0.4839] | Not recorded | Not recorded |
| ner_only | f2 | 0.4808 | Not recorded | [0.4028, 0.5344] | Not recorded | Not recorded |
| ner_only | leak_rate | 0.6945 | Not recorded | [0.6052, 0.7991] | Not recorded | Not recorded |
| ner_only | exposed_entities | 51.0000 | Not recorded | Not recorded | Not recorded | Not recorded |
| patterns_only | precision | 1.0000 | Not recorded | [1.0000, 1.0000] | Not recorded | Not recorded |
| patterns_only | recall | 1.0000 | Not recorded | [1.0000, 1.0000] | Not recorded | Not recorded |
| patterns_only | f2 | 1.0000 | Not recorded | [1.0000, 1.0000] | Not recorded | Not recorded |
| patterns_only | leak_rate | 0.0196 | Not recorded | [0.0000, 0.0606] | Not recorded | Not recorded |
| patterns_only | exposed_entities | 0.0000 | Not recorded | Not recorded | Not recorded | Not recorded |
