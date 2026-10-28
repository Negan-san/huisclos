"""Configuration de la détection : sources activées, types retenus et seuil de confiance.

Entrées : éventuellement results/threshold.json, écrit par l'évaluation (D-13).
Sorties : la dataclass DetectionConfig et les configurations nommées PRESETS.
Place dans le pipeline : paramètre unique de detection.pipeline.detect, de l'interface et
des scripts d'évaluation, pour comparer les sources à conditions égales.
"""

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

from huisclos.detection.languages import check_language, default_model_for, model_language
from huisclos.models import DEFAULT_ENABLED_TYPES, EntityType

# Seuil de D-07, en vigueur tant que l'évaluation n'a pas écrit results/threshold.json.
FALLBACK_THRESHOLD = 0.40
THRESHOLD_PATH = Path(__file__).resolve().parents[2] / "results" / "threshold.json"


def default_threshold(path: Path | str | None = None) -> float:
    """Renvoie le seuil de confiance par défaut.

    Paramètre : path, le fichier JSON de la forme {"threshold": 0.55} (par défaut
    results/threshold.json).
    Valeur retournée : le seuil lu dans le fichier s'il existe, sinon 0,40.
    Lève ValueError si le fichier existe mais ne contient pas un seuil entre 0 et 1 : un
    seuil illisible ne doit pas être remplacé en silence par une autre valeur.
    """
    target = Path(path) if path is not None else THRESHOLD_PATH
    if not target.is_file():
        return FALLBACK_THRESHOLD
    try:
        value = json.loads(target.read_text(encoding="utf-8"))["threshold"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"fichier de seuil illisible : {target}") from error
    if isinstance(value, bool) or not isinstance(value, int | float) or not 0 <= value <= 1:
        raise ValueError(f"seuil hors de l'intervalle [0, 1] dans {target} : {value!r}")
    return float(value)


@dataclass(frozen=True)
class DetectionConfig:
    """Réglages d'une exécution de la détection.

    Les booléens use_* activent chaque source ou étape ; enabled_types limite les types
    signalés ; threshold écarte les détections de score inférieur ; spacy_model nomme le
    modèle spaCy installé localement ; document_language (fr ou en) est la langue du
    document, distincte de celle de l'interface et du style des jetons.
    """

    use_patterns: bool = True
    use_heuristics: bool = True
    use_spacy: bool = True
    use_camembert: bool = False
    use_propagation: bool = True
    use_exclusions: bool = True
    enabled_types: frozenset[EntityType] = DEFAULT_ENABLED_TYPES
    threshold: float = field(default_factory=default_threshold)
    spacy_model: str = "fr_core_news_md"
    document_language: str = "fr"

    def __post_init__(self) -> None:
        """Refuse un seuil, une langue ou un modèle incohérents.

        Le modèle par défaut suit la langue : replace(config, document_language="en")
        charge en_core_web_sm. Un modèle choisi explicitement doit porter le préfixe de la
        langue du document, car un modèle français lirait mal un document anglais.
        """
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"threshold doit être compris entre 0 et 1, reçu {self.threshold}")
        language = check_language(self.document_language)
        model = default_model_for(language, self.spacy_model)
        if model_language(model) != language:
            raise ValueError(f"le modèle spaCy {model} ne correspond pas à la langue {language}")
        object.__setattr__(self, "spacy_model", model)


_HYBRID = DetectionConfig()

# Configurations comparées par l'évaluation ; "hybrid" est celle de l'interface.
# hybrid_camembert ne fonctionne que si l'option CamemBERT est installée (D-06).
PRESETS: dict[str, DetectionConfig] = {
    "patterns_only": replace(_HYBRID, use_spacy=False, use_propagation=False),
    "ner_only": replace(_HYBRID, use_patterns=False, use_heuristics=False, use_propagation=False),
    "hybrid_no_propagation": replace(_HYBRID, use_propagation=False),
    "hybrid": _HYBRID,
    "hybrid_camembert": replace(_HYBRID, use_camembert=True),
}

# Profils de l'interface (D-AF-A3-1) : Standard reprend hybrid, Enhanced y ajoute le
# CamemBERT local, pour les seuls documents français tant que A4 n'a rien intégré d'autre.
PROFILE_STANDARD = "standard"
PROFILE_ENHANCED = "enhanced"
PROFILES = (PROFILE_STANDARD, PROFILE_ENHANCED)
PROFILE_LANGUAGES: dict[str, tuple[str, ...]] = {
    PROFILE_STANDARD: ("fr", "en"),
    PROFILE_ENHANCED: ("fr",),
}

# Modèle CamemBERT validé en A1 (docs/LOCAL_MODELS.md) : dépôt et révision figée. Le cache
# local doit résoudre cette révision ; une autre révision est refusée, jamais téléchargée.
CAMEMBERT_REPO = "Jean-Baptiste/camembert-ner"
CAMEMBERT_REVISION = "ef35fe7767c1dad71f5c853838cdd80d0b3441ed"


def profile_unavailable(profile: str, document_language: str, public_demo: bool) -> str | None:
    """Dit pourquoi un profil ne peut pas servir, ou renvoie None s'il le peut.

    Paramètres : profile, standard ou enhanced ; document_language, fr ou en ; public_demo,
    vrai sur la démonstration publique, où le modèle lourd est interdit (D-14).
    Valeur retournée : "unknown", "public_demo", "language" ou None.
    Exemple : profile_unavailable("enhanced", "en", False) == "language".
    """
    if profile not in PROFILES:
        return "unknown"
    if profile == PROFILE_ENHANCED and public_demo:
        return "public_demo"
    if check_language(document_language) not in PROFILE_LANGUAGES[profile]:
        return "language"
    return None


def profile_config(
    profile: str, document_language: str, public_demo: bool = False
) -> DetectionConfig:
    """Construit la configuration d'un profil pour une langue de document.

    Paramètres : profile, standard ou enhanced ; document_language, fr ou en ; public_demo,
    vrai sur la démonstration publique.
    Valeur retournée : hybrid dans la langue du document, avec CamemBERT pour Enhanced. Lève
    ValueError si le profil n'est pas disponible : aucun repli silencieux vers un autre profil.
    """
    reason = profile_unavailable(profile, document_language, public_demo)
    if reason is not None:
        raise ValueError(f"profil {profile!r} indisponible pour {document_language} : {reason}")
    # Le modèle spaCy par défaut suit la langue du document (D-AF-A2-1).
    return replace(
        _HYBRID, use_camembert=profile == PROFILE_ENHANCED, document_language=document_language
    )
