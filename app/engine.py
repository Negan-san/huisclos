"""Moteur de détection partagé par toutes les sessions de l'application.

Entrées : la DetectionConfig construite par la barre latérale.
Sorties : l'analyseur Presidio en cache, construit une seule fois par processus.
Place dans le pipeline : appelé par l'étape Import juste avant detect() ; seul le moteur est
mis en cache, jamais un texte ni un résultat de l'utilisateur.
"""

import streamlit as st
from presidio_analyzer import AnalyzerEngine

from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import build_analyzer


@st.cache_resource(show_spinner=False)
def _cached_analyzer(
    use_patterns: bool,
    use_heuristics: bool,
    use_spacy: bool,
    use_camembert: bool,
    spacy_model: str,
) -> AnalyzerEngine:
    """Garde l'analyseur d'une combinaison de sources pour tout le processus.

    Les paramètres sont ceux de build_analyzer : des valeurs simples, que Streamlit sait
    comparer. Sur le cloud, le chargement du modèle spaCy (plusieurs secondes et la majeure
    partie de la mémoire) n'a ainsi lieu qu'une fois, quel que soit le nombre de visiteurs.
    """
    return build_analyzer(use_patterns, use_heuristics, use_spacy, use_camembert, spacy_model)


def prepare_engine(config: DetectionConfig) -> AnalyzerEngine:
    """Renvoie l'analyseur partagé de config, en le construisant au premier appel.

    Paramètre : config, la configuration de détection de la session.
    Valeur retournée : le même objet que celui qu'utilise ensuite detect(), car build_analyzer
    garde aussi son résultat en mémoire.
    """
    return _cached_analyzer(
        config.use_patterns,
        config.use_heuristics,
        config.use_spacy,
        config.use_camembert,
        config.spacy_model,
    )
