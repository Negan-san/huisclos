"""Charge les documents de référence utilisés pour évaluer la détection.

Entrées : fichiers JSONL contenant textes et entités annotées.
Sorties : documents typés dont les positions et les valeurs sont contrôlées.
Ce module intervient avant le calcul des métriques, sans appel réseau.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from huisclos.models import EntityType

CORPUS_TYPES = frozenset(EntityType) - {EntityType.LOCATION}
SPLITS = frozenset({"dev", "test", "demo"})
CORPUS_DIR = Path(__file__).resolve().parents[3] / "corpus"


@dataclass(frozen=True)
class GoldEntity:
    """Décrit une annotation avec un début inclus et une fin exclue."""

    start: int
    end: int
    type: EntityType
    text: str

    def __post_init__(self) -> None:
        """Refuse les types, positions et longueurs incohérents de l'entité."""
        if type(self.start) is not int or type(self.end) is not int:
            raise ValueError("Les positions doivent être des entiers.")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Les positions doivent définir un span non vide et positif.")
        if not isinstance(self.text, str) or len(self.text) != self.end - self.start:
            raise ValueError("La longueur de l'entité ne correspond pas aux positions.")
        try:
            entity_type = EntityType(self.type)
        except (TypeError, ValueError) as error:
            raise ValueError("Type d'entité inconnu.") from error
        if entity_type not in CORPUS_TYPES:
            raise ValueError("Type d'entité non autorisé dans le corpus.")
        object.__setattr__(self, "type", entity_type)


@dataclass(frozen=True)
class CorpusDocument:
    """Réunit les métadonnées, le texte brut et les annotations d'un document."""

    id: str
    doc_type: str
    split: str
    title: str
    text: str
    entities: list[GoldEntity]

    def __post_init__(self) -> None:
        """Vérifie les métadonnées et chaque tranche du texte fourni."""
        for value in (self.id, self.doc_type, self.split, self.title):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Les métadonnées doivent être des chaînes non vides.")
        if self.split not in SPLITS:
            raise ValueError("Split inconnu.")
        if not isinstance(self.text, str):
            raise ValueError("Le texte doit être une chaîne.")
        if not isinstance(self.entities, list) or any(
            not isinstance(entity, GoldEntity) for entity in self.entities
        ):
            raise ValueError("Les entités doivent être une liste de GoldEntity.")
        previous_end = 0
        for entity in sorted(self.entities, key=lambda item: (item.start, item.end)):
            if entity.end > len(self.text) or self.text[entity.start : entity.end] != entity.text:
                raise ValueError("Le texte du span ne correspond pas au document.")
            if entity.start < previous_end:
                raise ValueError("Les annotations se chevauchent.")
            previous_end = entity.end


def load_corpus(path: str | Path) -> list[CorpusDocument]:
    """Charge path en JSONL ; renvoie les documents ou une erreur fichier:ligne."""
    path = Path(path)
    documents: list[CorpusDocument] = []
    identifiers: set[str] = set()
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                record = json.loads(line)
                entities = [GoldEntity(**entity) for entity in record.pop("entities")]
                document = CorpusDocument(**record, entities=entities)
                if document.id in identifiers:
                    raise ValueError("Identifiant de document dupliqué.")
            except (ValueError, TypeError, KeyError, AttributeError) as error:
                raise ValueError(
                    f"{path}:{line_number}: document JSONL invalide : {error}"
                ) from error
            identifiers.add(document.id)
            documents.append(document)
    return documents


def load_split(name: str) -> list[CorpusDocument]:
    """Charge le split dev ou test depuis le dossier corpus du dépôt."""
    if name not in {"dev", "test"}:
        raise ValueError("Le split chargé doit être dev ou test.")
    documents = load_corpus(CORPUS_DIR / f"{name}.jsonl")
    if any(document.split != name for document in documents):
        raise ValueError(f"{CORPUS_DIR / f'{name}.jsonl'}:1: split incohérent avec le fichier.")
    return documents
