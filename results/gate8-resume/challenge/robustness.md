# Robustness report

Dataset gate8_resume_challenge: split challenge, 8 documents, document language fr, mode gate.
Measurement code commit: 930c414dd7ae1e7128b292bfa7bac1e45f27b1e9. Plan SHA-256: 747c37211f92a02d4eef473e1019b894a88c5d83fff163acebe4975501394da2.
Corpus SHA-256: {'challenge.jsonl': 'c47502d65bf05b6f3e0bd7e0bf9ccd9e58b046787fa2252e6a49ece85a03d609'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.8039 | 0.8632 | 0.8506 | 0.0903 | 22 | [0.7395, 0.8692] | [0.7596, 0.9438] | [0.0511, 0.1457] |
| enhanced | 0.30 | 0.8018 | 0.9368 | 0.9063 | 0.0606 | 9 | [0.7281, 0.8713] | [0.9096, 0.9618] | [0.0381, 0.0894] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 190 | 157 | 11 | 22 | 33 | 0.8263 | 325 | 0.0903 | 8 | 366 | 0.0235 |
| standard | pseudonymization | 190 | 157 | 11 | 22 | 33 | 0.8263 | 325 | 0.0903 | 8 | 366 | 0.0235 |
| standard | final_check | 190 | 157 | 11 | 22 | 33 | 0.8263 | 325 | 0.0903 | 8 | 366 | 0.0235 |
| enhanced | detection | 190 | 170 | 11 | 9 | 20 | 0.8947 | 218 | 0.0606 | 8 | 379 | 0.0244 |
| enhanced | pseudonymization | 190 | 170 | 11 | 9 | 20 | 0.8947 | 218 | 0.0606 | 8 | 379 | 0.0244 |
| enhanced | final_check | 190 | 170 | 11 | 9 | 20 | 0.8947 | 218 | 0.0606 | 8 | 379 | 0.0244 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 366 | 0.0235 |
| standard | pseudonymization | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 366 | 0.0235 |
| standard | final_check | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 366 | 0.0235 |
| enhanced | detection | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 379 | 0.0244 |
| enhanced | pseudonymization | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 379 | 0.0244 |
| enhanced | final_check | 13 | 7 | 1 | 5 | 6 | 0.5385 | 72 | 0.4966 | 6 | 379 | 0.0244 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [0.7360, 0.8956] | 0 |
| standard | detection | leaked_character_rate | [0.0511, 0.1457] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0113, 0.0401] | 0 |
| standard | pseudonymization | full_coverage_rate | [0.7360, 0.8956] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0511, 0.1457] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0113, 0.0401] | 0 |
| enhanced | detection | full_coverage_rate | [0.8619, 0.9213] | 0 |
| enhanced | detection | leaked_character_rate | [0.0381, 0.0894] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0117, 0.0416] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [0.8619, 0.9213] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0381, 0.0894] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0117, 0.0416] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 22 | 6 | 10 | 12 | 33 | 10 |
| enhanced | 0.1000 | 18 | 7 | 4 | 14 | 20 | 4 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | -0.0021 | [-0.0211, 0.0182] | 0 | no |
| enhanced | standard | detection | recall | 0.0737 | [0.0108, 0.1667] | 0 | yes |
| enhanced | standard | detection | full_coverage_rate | 0.0684 | [0.0000, 0.1667] | 0 | no |
| enhanced | standard | detection | leaked_character_rate | -0.0297 | [-0.0618, -0.0065] | 0 | yes |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0008 | [0.0000, 0.0018] | 0 | no |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.0684 | [0.0000, 0.1667] | 0 | no |
| enhanced | standard | pseudonymization | leaked_character_rate | -0.0297 | [-0.0618, -0.0065] | 0 | yes |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0008 | [0.0000, 0.0018] | 0 | no |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | yes | yes | yes | yes | yes |
