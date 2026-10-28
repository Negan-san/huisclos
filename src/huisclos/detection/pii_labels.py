"""Politique figée du renfort local GLiNER, commune aux deux langues.

Entrées : labels du modèle et manifeste local produit par prepare_local_models.
Sorties : types existants et identités immuables des deux snapshots nécessaires.
Place : contrat du backend facultatif, avant la fusion des candidats.
"""

LABELS: dict[str, str] = {
    "person": "PERSON",
    "organization": "ORGANIZATION",
    "address": "ADDRESS",
    "email": "EMAIL",
    "phone number": "PHONE",
    "date of birth": "BIRTH_DATE",
}
WINDOW_TOKENS = 256
OVERLAP_TOKENS = 64
SNAPSHOTS = {
    "gliner_multi_pii_v1": (
        "urchade/gliner_multi_pii-v1",
        "1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d",
        {
            "gliner_config.json": (
                "2088bee85f50849dea2ab4cf411ab5cf3aaaf7c8a45c23412035978b2bc02801"
            ),
            "pytorch_model.bin": "3003753fba99e40645cf088c7367a2c6211fc174897dc64f1f9c147c29d18d2d",
        },
    ),
    "mdeberta_v3_base": (
        "microsoft/mdeberta-v3-base",
        "a0484667b22365f84929a935b5e50a51f71f159d",
        {
            "config.json": "bcffcd343dc5efa5ef2d5a58d2b405eed108f01cc45b48d0a907b333ec41801f",
            "spm.model": "13c8d666d62a7bc4ac8f040aab68e942c861f93303156cc28f5c7e885d86d6e3",
            "tokenizer_config.json": (
                "3f3978e0c036f2c2588cac34a6047cbb0af0b0dc1814254e291028529805496d"
            ),
        },
    ),
}
