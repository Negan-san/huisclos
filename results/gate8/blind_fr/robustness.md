# Robustness report

Dataset gate8_blind_fr: split challenge, 8 documents, document language fr, mode gate.
Measurement code commit: e3d13bdc25839783eebe998c8f971862d78754d5. Plan SHA-256: 8355f1282fa430fc9952ece7e576613f6b3a31eafdedc4be8783abc9687a6494.
Corpus SHA-256: {'challenge.jsonl': 'df179266f4866128c5b4aaa770559d4ebedfd06c5a0cf47a9f6490ab51d89d6f'}.

Stages: detection lists proposals; pseudonymization substitutes every proposal automatically; final check reports alerts on the pseudonymized text.
Alerts do not mask anything: leakage after the final check equals leakage after pseudonymization. No stage simulates a reviewer who knows the annotations.
Coverage counts characters replaced by any substitution, whatever the predicted type. Historical metrics are unchanged and never credit a wrong label.
Full coverage means every character of a reference is masked; one visible character prevents it. Over-masking counts masked characters outside every annotation.
The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.
n/a means not applicable (no denominator); it is not a guarantee of zero leakage.

## Historical metrics (detection stage, partial matching, micro)

| Profile | Threshold | Precision | Recall | F2 | Leak rate | Exposed entities | Precision 95% | Recall 95% | Leak rate 95% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.30 | 0.8922 | 0.8667 | 0.8716 | 0.0681 | 7 | [0.8473, 0.9500] | [0.8367, 0.8915] | [0.0480, 0.1030] |
| enhanced | 0.30 | 0.8824 | 0.8571 | 0.8621 | 0.0637 | 7 | [0.8370, 0.9494] | [0.8316, 0.8833] | [0.0414, 0.1020] |
| g7_standard | 0.30 | 0.8922 | 0.8667 | 0.8716 | 0.0837 | 7 | [0.8473, 0.9500] | [0.8367, 0.8915] | [0.0506, 0.1225] |
| g7_enhanced | 0.30 | 0.8824 | 0.8571 | 0.8621 | 0.0793 | 7 | [0.8370, 0.9494] | [0.8316, 0.8833] | [0.0506, 0.1131] |

## Full coverage, eleven evaluated types

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 105 | 95 | 3 | 7 | 10 | 0.9048 | 139 | 0.0681 | 8 | 27 | 0.0013 |
| standard | pseudonymization | 105 | 95 | 3 | 7 | 10 | 0.9048 | 139 | 0.0681 | 8 | 27 | 0.0013 |
| standard | final_check | 105 | 95 | 3 | 7 | 10 | 0.9048 | 139 | 0.0681 | 8 | 27 | 0.0013 |
| enhanced | detection | 105 | 96 | 2 | 7 | 9 | 0.9143 | 130 | 0.0637 | 8 | 27 | 0.0013 |
| enhanced | pseudonymization | 105 | 96 | 2 | 7 | 9 | 0.9143 | 130 | 0.0637 | 8 | 27 | 0.0013 |
| enhanced | final_check | 105 | 96 | 2 | 7 | 9 | 0.9143 | 130 | 0.0637 | 8 | 27 | 0.0013 |
| g7_standard | detection | 105 | 94 | 4 | 7 | 11 | 0.8952 | 171 | 0.0837 | 8 | 27 | 0.0013 |
| g7_standard | pseudonymization | 105 | 94 | 4 | 7 | 11 | 0.8952 | 171 | 0.0837 | 8 | 27 | 0.0013 |
| g7_standard | final_check | 105 | 94 | 4 | 7 | 11 | 0.8952 | 171 | 0.0837 | 8 | 27 | 0.0013 |
| g7_enhanced | detection | 105 | 95 | 3 | 7 | 10 | 0.9048 | 162 | 0.0793 | 8 | 27 | 0.0013 |
| g7_enhanced | pseudonymization | 105 | 95 | 3 | 7 | 10 | 0.9048 | 162 | 0.0793 | 8 | 27 | 0.0013 |
| g7_enhanced | final_check | 105 | 95 | 3 | 7 | 10 | 0.9048 | 162 | 0.0793 | 8 | 27 | 0.0013 |

## CUSTOM and LOCATION, separate scope

| Profile | Stage | Entities | Fully covered | Partially exposed | Fully exposed | Any exposure | Full coverage rate | Leaked characters | Leaked character rate | Documents with exposure | Non-sensitive masked | Over-masking rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard | detection | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| standard | pseudonymization | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| standard | final_check | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| enhanced | detection | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| enhanced | pseudonymization | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| enhanced | final_check | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_standard | detection | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_standard | pseudonymization | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_standard | final_check | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_enhanced | detection | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_enhanced | pseudonymization | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |
| g7_enhanced | final_check | 7 | 2 | 1 | 4 | 5 | 0.2857 | 53 | 0.6625 | 5 | 27 | 0.0013 |

## Coverage 95% bootstrap intervals

| Profile | Stage | Metric | Interval | Undefined draws |
| --- | --- | --- | --- | --- |
| standard | detection | full_coverage_rate | [0.8764, 0.9268] | 0 |
| standard | detection | leaked_character_rate | [0.0480, 0.1030] | 0 |
| standard | detection | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| standard | pseudonymization | full_coverage_rate | [0.8764, 0.9268] | 0 |
| standard | pseudonymization | leaked_character_rate | [0.0480, 0.1030] | 0 |
| standard | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| enhanced | detection | full_coverage_rate | [0.8837, 0.9350] | 0 |
| enhanced | detection | leaked_character_rate | [0.0414, 0.1020] | 0 |
| enhanced | detection | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| enhanced | pseudonymization | full_coverage_rate | [0.8837, 0.9350] | 0 |
| enhanced | pseudonymization | leaked_character_rate | [0.0414, 0.1020] | 0 |
| enhanced | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| g7_standard | detection | full_coverage_rate | [0.8609, 0.9259] | 0 |
| g7_standard | detection | leaked_character_rate | [0.0506, 0.1225] | 0 |
| g7_standard | detection | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| g7_standard | pseudonymization | full_coverage_rate | [0.8609, 0.9259] | 0 |
| g7_standard | pseudonymization | leaked_character_rate | [0.0506, 0.1225] | 0 |
| g7_standard | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| g7_enhanced | detection | full_coverage_rate | [0.8764, 0.9268] | 0 |
| g7_enhanced | detection | leaked_character_rate | [0.0506, 0.1131] | 0 |
| g7_enhanced | detection | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |
| g7_enhanced | pseudonymization | full_coverage_rate | [0.8764, 0.9268] | 0 |
| g7_enhanced | pseudonymization | leaked_character_rate | [0.0506, 0.1131] | 0 |
| g7_enhanced | pseudonymization | non_sensitive_masked_rate | [0.0000, 0.0021] | 0 |

## Final check alerts (alerts mask nothing)

| Profile | Check threshold | Alerts | Documents with alerts | On visible references | Elsewhere | Exposed entities | Exposed entities alerted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| standard | 0.1000 | 3 | 2 | 1 | 2 | 10 | 1 |
| enhanced | 0.1000 | 2 | 1 | 0 | 2 | 9 | 0 |
| g7_standard | 0.1000 | 3 | 2 | 1 | 2 | 11 | 1 |
| g7_enhanced | 0.1000 | 2 | 1 | 0 | 2 | 10 | 0 |

## Paired differences (candidate minus reference, same draws)

| Candidate | Reference | Stage | Metric | Estimate | 95% interval | Undefined draws | Excludes zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | detection | precision | -0.0098 | [-0.0265, 0.0000] | 0 | no |
| enhanced | standard | detection | recall | -0.0095 | [-0.0261, 0.0000] | 0 | no |
| enhanced | standard | detection | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| enhanced | standard | detection | leaked_character_rate | -0.0044 | [-0.0125, 0.0000] | 0 | no |
| enhanced | standard | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| enhanced | standard | pseudonymization | leaked_character_rate | -0.0044 | [-0.0125, 0.0000] | 0 | no |
| enhanced | standard | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | detection | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| standard | g7_standard | detection | leaked_character_rate | -0.0157 | [-0.0445, 0.0000] | 0 | no |
| standard | g7_standard | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| standard | g7_standard | pseudonymization | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| standard | g7_standard | pseudonymization | leaked_character_rate | -0.0157 | [-0.0445, 0.0000] | 0 | no |
| standard | g7_standard | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | precision | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | recall | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| enhanced | g7_enhanced | detection | leaked_character_rate | -0.0157 | [-0.0445, 0.0000] | 0 | no |
| enhanced | g7_enhanced | detection | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | full_coverage_rate | 0.0095 | [0.0000, 0.0275] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | leaked_character_rate | -0.0157 | [-0.0445, 0.0000] | 0 | no |
| enhanced | g7_enhanced | pseudonymization | non_sensitive_masked_rate | 0.0000 | [0.0000, 0.0000] | 0 | no |

## Engineering criterion (not a legal threshold)

| Candidate | Reference | Lower leakage | Higher full coverage | Precision within 2 points | Over-masking within 1 point | Recommended |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | standard | yes | yes | yes | yes | yes |
| standard | g7_standard | yes | yes | yes | yes | yes |
| enhanced | g7_enhanced | yes | yes | yes | yes | yes |
