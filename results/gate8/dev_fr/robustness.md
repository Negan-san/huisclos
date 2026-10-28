# Robustness report

Dataset gate8_dev_fr: split dev, 20 documents, document language fr, mode gate.
Measurement code commit: e3d13bdc25839783eebe998c8f971862d78754d5. Plan SHA-256: 8355f1282fa430fc9952ece7e576613f6b3a31eafdedc4be8783abc9687a6494.
Corpus SHA-256: {'dev.jsonl': '4ef66d76ca10b70f8bc0b86d0066d52fb8a69a69467b3926b06510b216cac5c6'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |
| enhanced | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |
| g7_standard | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |
| g7_enhanced | 0.30 | 0.9904 | 1.0000 | 0.9981 | 0.0000 | 0 | [0.9801, 1.0000] | [1.0000, 1.0000] | [0.0000, 0.0000] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| standard | pseudonymization | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| standard | final_check | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| enhanced | detection | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| enhanced | pseudonymization | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| enhanced | final_check | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_standard | detection | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_standard | pseudonymization | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_standard | final_check | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_enhanced | detection | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_enhanced | pseudonymization | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |
| g7_enhanced | final_check | 311 | 311 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 7 | 0.0002 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| standard | pseudonymization | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| standard | final_check | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| enhanced | detection | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| enhanced | pseudonymization | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| enhanced | final_check | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_standard | detection | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_standard | pseudonymization | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_standard | final_check | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_enhanced | detection | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_enhanced | pseudonymization | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |
| g7_enhanced | final_check | 50 | 46 | 0 | 4 | 4 | 0.9200 | 48 | 0.0970 | 4 | 7 | 0.0002 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| standard | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| standard | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| enhanced | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| enhanced | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| g7_standard | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| g7_standard | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| g7_standard | detection | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| g7_standard | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| g7_standard | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| g7_standard | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| g7_enhanced | detection | full_coverage_rate | [1.0000, 1.0000] | 0 |
| g7_enhanced | detection | leaked_character_rate | [0.0000, 0.0000] | 0 |
| g7_enhanced | detection | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |
| g7_enhanced | pseudonymization | full_coverage_rate | [1.0000, 1.0000] | 0 |
| g7_enhanced | pseudonymization | leaked_character_rate | [0.0000, 0.0000] | 0 |
| g7_enhanced | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0006] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 0 | 0 | 0 | 0 | 0 | 0 |
| enhanced | 0.1000 | 2 | 1 | 0 | 2 | 0 | 0 |
| g7_standard | 0.1000 | 0 | 0 | 0 | 0 | 0 | 0 |
| g7_enhanced | 0.1000 | 2 | 1 | 0 | 2 | 0 | 0 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | pseudonymization | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | pseudonymization | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | full_coverage_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | leaked_character_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | no | no | yes | yes | no |
| standard | g7_standard | no | no | yes | yes | no |
| enhanced | g7_enhanced | no | no | yes | yes | no |
