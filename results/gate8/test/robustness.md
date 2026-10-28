# Robustness report

Dataset gate8_test: split test, 6 documents, document language fr, mode gate.
Measurement code commit: e3d13bdc25839783eebe998c8f971862d78754d5. Plan SHA-256: 747c37211f92a02d4eef473e1019b894a88c5d83fff163acebe4975501394da2.
Corpus SHA-256: {'test.jsonl': '12a7852e765d98c10be74025e684c15280ccb47615017529ee320370faa4cd4d'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.9789 | 1.0000 | 0.9957 | 0.0000 | 0 | [0.9560, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |
| enhanced | 0.30 | 0.9789 | 1.0000 | 0.9957 | 0.0000 | 0 | [0.9560, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 20 | 0.0017 |
| standard | pseudonymization | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 20 | 0.0017 |
| standard | final_check | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 20 | 0.0017 |
| enhanced | detection | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 25 | 0.0021 |
| enhanced | pseudonymization | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 25 | 0.0021 |
| enhanced | final_check | 93 | 93 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 25 | 0.0021 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 20 | 0.0017 |
| standard | pseudonymization | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 20 | 0.0017 |
| standard | final_check | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 20 | 0.0017 |
| enhanced | detection | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 25 | 0.0021 |
| enhanced | pseudonymization | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 25 | 0.0021 |
| enhanced | final_check | 6 | 2 | 0 | 4 | 4 | 0.3333 | 40 | 0.7018 | 4 | 25 | 0.0021 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| standard | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0000, 0.0037] | 0 |
| standard | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0037] | 0 |
| enhanced | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| enhanced | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0004, 0.0041] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0004, 0.0041] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 0 | 0 | 0 | 0 | 0 | 0 |
| enhanced | 0.1000 | 1 | 1 | 0 | 1 | 0 | 0 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0004 | [0.0000, 0.0013] | 0 | no |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0004 | [0.0000, 0.0013] | 0 | no |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | no | no | yes | yes | no |
