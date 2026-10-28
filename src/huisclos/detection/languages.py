"""Profils de langue du document : modèle spaCy, étiquettes NER et listes d'exclusions.

Entrées : le code de langue du document (fr ou en), indépendant de la langue de l'interface
et du style des jetons. Sorties : un LanguageProfile immuable et des contrôles de cohérence.
Place dans le pipeline : lu par config, ner, pipeline et exclusions pour construire un moteur
propre à chaque langue ; une langue ne désigne ni une nationalité ni une juridiction.
"""

from dataclasses import dataclass
from pathlib import Path

DOCUMENT_LANGUAGES = ("fr", "en")
DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@dataclass(frozen=True)
class LanguageProfile:
    """Réglages linguistiques d'une langue de document.

    spacy_model est le modèle installé localement ; label_mapping convertit ses étiquettes
    en types Presidio ; labels_to_ignore écarte les autres ; exclusion_files sont lus dans
    l'ordre, le français d'abord pour garder les juridictions françaises citées en anglais.
    """

    code: str
    spacy_model: str
    label_mapping: dict[str, str]
    labels_to_ignore: tuple[str, ...]
    exclusion_files: tuple[Path, ...]


# Les étiquettes non converties sont ignorées : DATE n'est pas une date de naissance et un
# lieu seul n'est pas une adresse (politique des types, LOCATION désactivé par défaut).
PROFILES: dict[str, LanguageProfile] = {
    "fr": LanguageProfile(
        code="fr",
        spacy_model="fr_core_news_md",
        label_mapping={"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"},
        labels_to_ignore=("MISC",),
        exclusion_files=(DATA_DIR / "exclusions_fr.txt",),
    ),
    "en": LanguageProfile(
        code="en",
        spacy_model="en_core_web_sm",
        label_mapping={
            "PERSON": "PERSON",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "FAC": "LOCATION",
        },
        labels_to_ignore=(
            "DATE",
            "TIME",
            "CARDINAL",
            "ORDINAL",
            "MONEY",
            "PERCENT",
            "QUANTITY",
            "NORP",
            "EVENT",
            "WORK_OF_ART",
            "LAW",
            "LANGUAGE",
            "PRODUCT",
        ),
        exclusion_files=(DATA_DIR / "exclusions_fr.txt", DATA_DIR / "exclusions_en.txt"),
    ),
}


def check_language(language: str) -> str:
    """Vérifie un code de langue de document et le renvoie.

    Paramètre : language, le code demandé.
    Valeur retournée : le même code s'il vaut fr ou en.
    Lève ValueError sinon : traiter un document allemand avec les règles françaises
    donnerait une fausse impression de protection.
    """
    if language not in DOCUMENT_LANGUAGES:
        raise ValueError(f"document_language doit valoir fr ou en, reçu {language!r}")
    return language


def profile(language: str) -> LanguageProfile:
    """Renvoie le profil de la langue de document language (fr ou en)."""
    return PROFILES[check_language(language)]


def model_language(model_name: str) -> str:
    """Langue d'un modèle spaCy, lue dans son préfixe : "en_core_web_sm" donne "en"."""
    return model_name.split("_", 1)[0]


def default_model_for(language: str, model_name: str) -> str:
    """Remplace le modèle par défaut d'une autre langue par celui de language.

    Paramètres : language, la langue du document ; model_name, le modèle demandé.
    Valeur retournée : model_name, sauf s'il est le modèle par défaut d'une autre langue :
    dataclasses.replace(config, document_language="en") garde alors un moteur cohérent.
    Exemple : default_model_for("en", "fr_core_news_md") == "en_core_web_sm".
    """
    defaults = {item.spacy_model for item in PROFILES.values()}
    if model_name in defaults and model_language(model_name) != language:
        return profile(language).spacy_model
    return model_name
