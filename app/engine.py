"""Moteur de détection partagé par toutes les sessions de l'application.

Entrées : la DetectionConfig construite par la barre latérale.
Sorties : l'analyseur Presidio en cache, construit une seule fois par processus.
Place dans le pipeline : appelé par l'étape Import juste avant detect() ; seul le moteur est
mis en cache, jamais un texte ni un résultat de l'utilisateur.
"""

import streamlit as st
from presidio_analyzer import AnalyzerEngine

from app.ui_common import is_public_demo
from huisclos.config import DetectionConfig
from huisclos.detection.ner import LANGUAGE
from huisclos.detection.pipeline import ModelUnavailableError, build_analyzer


@st.cache_resource(show_spinner=False)
def _cached_analyzer(
    use_patterns: bool,
    use_heuristics: bool,
    use_spacy: bool,
    use_camembert: bool,
    spacy_model: str,
    document_language: str,
) -> AnalyzerEngine:
    """Garde l'analyseur d'une combinaison de sources et de langue pour tout le processus.

    Les paramètres sont ceux de build_analyzer : des valeurs simples, que Streamlit sait
    comparer. Sur le cloud, le chargement du modèle spaCy (plusieurs secondes et la majeure
    partie de la mémoire) n'a ainsi lieu qu'une fois, quel que soit le nombre de visiteurs.
    Pour le français, l'appel garde la forme à cinq valeurs de analyzer_for : detect()
    retrouve le même objet dans le cache de build_analyzer.
    """
    sources = (use_patterns, use_heuristics, use_spacy, use_camembert, spacy_model)
    if document_language == LANGUAGE:
        return build_analyzer(*sources)
    return build_analyzer(*sources, document_language)


def prepare_engine(config: DetectionConfig) -> AnalyzerEngine:
    """Renvoie l'analyseur partagé de config, en le construisant au premier appel.

    Paramètre : config, la configuration de détection de la session.
    Valeur retournée : le même objet que celui qu'utilise ensuite detect(), car build_analyzer
    garde aussi son résultat en mémoire. Lève ModelUnavailableError("public_demo") si la
    démonstration publique demande le modèle lourd, quelle que soit la valeur de session.
    """
    if config.use_camembert and is_public_demo():
        raise ModelUnavailableError("public_demo")
    return _cached_analyzer(
        config.use_patterns,
        config.use_heuristics,
        config.use_spacy,
        config.use_camembert,
        config.spacy_model,
        config.document_language,
    )
