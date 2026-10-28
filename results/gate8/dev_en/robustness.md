# Robustness report

Dataset gate8_dev_en: split dev, 8 documents, document language en, mode gate.
Measurement code commit: e3d13bdc25839783eebe998c8f971862d78754d5. Plan SHA-256: d5240419d4683006ddb2615f1c1f4970a5fbd2f95ee072d99068426f4983df06.
Corpus SHA-256: {'dev.jsonl': 'e8958f8ca5018d0f43935e34611985e5c56b00ca3a4a4dd495974ec8aeb34990'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.9313 | 0.8971 | 0.9037 | 0.0411 | 8 | [0.9008, 0.9565] | [0.8286, 0.9489] | [0.0197, 0.0639] |
| enhanced | 0.30 | 0.9323 | 0.9118 | 0.9158 | 0.0247 | 6 | [0.9032, 0.9571] | [0.8583, 0.9545] | [0.0088, 0.0403] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 136 | 124 | 4 | 8 | 12 | 0.9118 | 105 | 0.0411 | 6 | 48 | 0.0037 |
| standard | pseudonymization | 136 | 124 | 4 | 8 | 12 | 0.9118 | 105 | 0.0411 | 6 | 48 | 0.0037 |
| standard | final_check | 136 | 124 | 4 | 8 | 12 | 0.9118 | 105 | 0.0411 | 6 | 48 | 0.0037 |
| enhanced | detection | 136 | 126 | 4 | 6 | 10 | 0.9265 | 63 | 0.0247 | 5 | 48 | 0.0037 |
| enhanced | pseudonymization | 136 | 126 | 4 | 6 | 10 | 0.9265 | 63 | 0.0247 | 5 | 48 | 0.0037 |
| enhanced | final_check | 136 | 126 | 4 | 6 | 10 | 0.9265 | 63 | 0.0247 | 5 | 48 | 0.0037 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |
| standard | pseudonymization | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |
| standard | final_check | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |
| enhanced | detection | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |
| enhanced | pseudonymization | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |
| enhanced | final_check | 2 | 2 | 0 | 0 | 0 | 1.0000 | 0 | 0.0000 | 0 | 48 | 0.0037 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [0.8581, 0.9595] | 0 |
| standard | detection | leaked_character_rate | [0.0197, 0.0639] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0012, 0.0064] | 0 |
| standard | pseudonymization | full_coverage_rate | [0.8581, 0.9595] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0197, 0.0639] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0012, 0.0064] | 0 |
| enhanced | detection | full_coverage_rate | [0.8750, 0.9728] | 0 |
| enhanced | detection | leaked_character_rate | [0.0088, 0.0403] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0012, 0.0064] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [0.8750, 0.9728] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0088, 0.0403] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0012, 0.0064] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 0 | 0 | 0 | 0 | 12 | 0 |
| enhanced | 0.1000 | 29 | 8 | 1 | 28 | 10 | 1 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | 0.0010 | [0.0000, 0.0031] | 0 | no |
| enhanced | standard | detection | recall | 0.0147 | [0.0000, 0.0325] | 0 | no |
| enhanced | standard | detection | full_coverage_rate | 0.0147 | [0.0000, 0.0325] | 0 | no |
| enhanced | standard | detection | leaked_character_rate | -0.0165 | [-0.0376, 0.0000] | 0 | no |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.0147 | [0.0000, 0.0325] | 0 | no |
| enhanced | standard | pseudonymization | leaked_character_rate | -0.0165 | [-0.0376, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | yes | yes | yes | yes | yes |
