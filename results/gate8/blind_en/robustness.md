# Robustness report

Dataset gate8_blind_en: split challenge, 8 documents, document language en, mode gate.
Measurement code commit: e3d13bdc25839783eebe998c8f971862d78754d5. Plan SHA-256: d5240419d4683006ddb2615f1c1f4970a5fbd2f95ee072d99068426f4983df06.
Corpus SHA-256: {'challenge.jsonl': 'e3fd4886a2499563f6710cf1cfe57a3f27b3302be1e576e06ac67a4ddede5aea'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.8349 | 0.9100 | 0.8939 | 0.1028 | 6 | [0.7641, 0.9032] | [0.8518, 0.9496] | [0.0687, 0.1355] |
| enhanced | 0.30 | 0.7000 | 0.9100 | 0.8585 | 0.0503 | 5 | [0.6460, 0.7708] | [0.8750, 0.9457] | [0.0266, 0.0680] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 100 | 78 | 16 | 6 | 22 | 0.7800 | 235 | 0.1028 | 8 | 93 | 0.0045 |
| standard | pseudonymization | 100 | 78 | 16 | 6 | 22 | 0.7800 | 235 | 0.1028 | 8 | 93 | 0.0045 |
| standard | final_check | 100 | 78 | 16 | 6 | 22 | 0.7800 | 235 | 0.1028 | 8 | 93 | 0.0045 |
| enhanced | detection | 100 | 88 | 7 | 5 | 12 | 0.8800 | 115 | 0.0503 | 7 | 252 | 0.0121 |
| enhanced | pseudonymization | 100 | 88 | 7 | 5 | 12 | 0.8800 | 115 | 0.0503 | 7 | 252 | 0.0121 |
| enhanced | final_check | 100 | 88 | 7 | 5 | 12 | 0.8800 | 115 | 0.0503 | 7 | 252 | 0.0121 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 93 | 0.0045 |
| standard | pseudonymization | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 93 | 0.0045 |
| standard | final_check | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 93 | 0.0045 |
| enhanced | detection | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 252 | 0.0121 |
| enhanced | pseudonymization | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 252 | 0.0121 |
| enhanced | final_check | 8 | 2 | 2 | 4 | 6 | 0.2500 | 60 | 0.6897 | 6 | 252 | 0.0121 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [0.7241, 0.8367] | 0 |
| standard | detection | leaked_character_rate | [0.0687, 0.1355] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0020, 0.0075] | 0 |
| standard | pseudonymization | full_coverage_rate | [0.7241, 0.8367] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0687, 0.1355] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0020, 0.0075] | 0 |
| enhanced | detection | full_coverage_rate | [0.8384, 0.9271] | 0 |
| enhanced | detection | leaked_character_rate | [0.0266, 0.0680] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0078, 0.0166] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [0.8384, 0.9271] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0266, 0.0680] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0078, 0.0166] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 28 | 6 | 1 | 27 | 22 | 1 |
| enhanced | 0.1000 | 43 | 7 | 4 | 39 | 12 | 4 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | -0.1349 | [-0.2021, -0.0514] | 0 | yes |
| enhanced | standard | detection | recall | 0.0000 | [-0.0254, 0.0312] | 0 | no |
| enhanced | standard | detection | full_coverage_rate | 0.1000 | [0.0804, 0.1290] | 0 | yes |
| enhanced | standard | detection | leaked_character_rate | -0.0525 | [-0.0740, -0.0355] | 0 | yes |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0076 | [0.0034, 0.0123] | 0 | yes |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.1000 | [0.0804, 0.1290] | 0 | yes |
| enhanced | standard | pseudonymization | leaked_character_rate | -0.0525 | [-0.0740, -0.0355] | 0 | yes |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0076 | [0.0034, 0.0123] | 0 | yes |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | yes | yes | no | yes | no |
