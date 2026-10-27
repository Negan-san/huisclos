"""Modèles de données partagés : types d'entités, sources de détection et Detection.

Entrées : aucune. Sorties : énumérations, dataclass Detection et constantes de jetons.
Place dans le pipeline : contrat commun à la détection, à la revue, à la pseudonymisation
et à l'évaluation.
"""

from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):  # noqa: UP042 (contrat exigé : str + Enum)
    """Type d'entité détectable ; chaque valeur est égale à son nom."""

    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    ADDRESS = "ADDRESS"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    IBAN = "IBAN"
    NIR = "NIR"
    SIREN = "SIREN"
    SIRET = "SIRET"
    BIRTH_DATE = "BIRTH_DATE"
    CASE_NUMBER = "CASE_NUMBER"
    LOCATION = "LOCATION"
    CUSTOM = "CUSTOM"


class Source(str, Enum):  # noqa: UP042 (contrat exigé : str + Enum)
    """Origine d'une détection, utile pour expliquer son score à l'utilisateur."""

    CHECKSUM = "checksum"
    PATTERN = "pattern"
    HEURISTIC = "heuristic"
    NER_SPACY = "ner_spacy"
    NER_CAMEMBERT = "ner_camembert"
    PROPAGATION = "propagation"
    MANUAL = "manual"


@dataclass(frozen=True)
class Detection:
    """Une valeur sensible repérée dans un texte.

    Les positions suivent la convention Python : start inclus, end exclu. Le champ text
    doit être exactement texte[start:end], ce que __post_init__ vérifie.
    """

    start: int
    end: int
    entity_type: EntityType
    score: float
    source: Source
    text: str

    def __post_init__(self) -> None:
        """Refuse les positions, scores et textes incohérents."""
        if self.start < 0:
            raise ValueError(f"start doit être positif ou nul, reçu {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) doit dépasser start ({self.start})")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score doit être compris entre 0 et 1, reçu {self.score}")
        if len(self.text) != self.end - self.start:
            raise ValueError("la longueur de text doit être égale à end - start")

    @property
    def length(self) -> int:
        """Nombre de caractères couverts par la détection."""
        return self.end - self.start


# Libellé de jeton par type : (français, anglais). Exemple : [PERSONNE_1] ou [PERSON_1].
TOKEN_LABELS: dict[EntityType, tuple[str, str]] = {
    EntityType.PERSON: ("PERSONNE", "PERSON"),
    EntityType.ORGANIZATION: ("SOCIETE", "COMPANY"),
    EntityType.ADDRESS: ("ADRESSE", "ADDRESS"),
    EntityType.EMAIL: ("EMAIL", "EMAIL"),
    EntityType.PHONE: ("TELEPHONE", "PHONE"),
    EntityType.IBAN: ("IBAN", "IBAN"),
    EntityType.NIR: ("NIR", "NIR"),
    EntityType.SIREN: ("SIREN", "SIREN"),
    EntityType.SIRET: ("SIRET", "SIRET"),
    EntityType.BIRTH_DATE: ("DATE_NAISSANCE", "BIRTH_DATE"),
    EntityType.CASE_NUMBER: ("DOSSIER", "CASE"),
    EntityType.LOCATION: ("LIEU", "PLACE"),
    EntityType.CUSTOM: ("AUTRE", "OTHER"),
}

# Types numérotés par lettres (A, B, ..., AA) plutôt que par chiffres, pour les distinguer
# des personnes : [SOCIETE_A].
LETTER_INDEXED: frozenset[EntityType] = frozenset({EntityType.ORGANIZATION})

# LOCATION est désactivé par défaut : les villes seules gênent plus qu'elles ne protègent.
DEFAULT_ENABLED_TYPES: frozenset[EntityType] = frozenset(EntityType) - {EntityType.LOCATION}
