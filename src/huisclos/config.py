"""Configuration de la détection : sources activées, types retenus et seuil de confiance.

Entrées : éventuellement results/threshold.json, écrit par l'évaluation (D-13).
Sorties : la dataclass DetectionConfig et les configurations nommées PRESETS.
Place dans le pipeline : paramètre unique de detection.pipeline.detect, de l'interface et
des scripts d'évaluation, pour comparer les sources à conditions égales.
"""

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

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
    modèle spaCy installé localement.
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

    def __post_init__(self) -> None:
        """Refuse un seuil hors de l'intervalle [0, 1]."""
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"threshold doit être compris entre 0 et 1, reçu {self.threshold}")


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
