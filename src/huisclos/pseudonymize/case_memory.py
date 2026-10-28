"""Mémoire de dossier : reprendre la table de correspondance d'un document précédent.

Entrées : le fichier .mapping.json exporté par l'étape Restore, puis le texte d'un nouveau
document du même dossier et ses groupes de mentions.
Sorties : la table validée, les valeurs connues retrouvées dans le texte (source
"case_table"), l'entrée de table de chaque groupe connu et la table fusionnée du dossier.
Place dans le pipeline : avant la détection, puis à l'attribution des jetons (D-S24-2). La
table reste en mémoire : rien n'est écrit sur le disque.
"""

import re
from collections.abc import Iterable
from dataclasses import replace

from huisclos.models import (
    LETTER_INDEXED,
    TOKEN_LABELS,
    Detection,
    EntityGroup,
    EntityType,
    Source,
    TokenStyle,
)
from huisclos.pseudonymize.grouping import may_abbreviate, normalized_key, person_words
from huisclos.pseudonymize.mapping import Mapping, MappingEntry, MappingError
from huisclos.text_utils import fold, fold_same_length

# Une table de dossier tient en quelques dizaines de kilo-octets : 2 Mo laissent une large
# marge et refusent d'emblée un fichier sans rapport.
MAX_TABLE_BYTES = 2_000_000
# Une valeur de la table a été validée par l'humain sur un document précédent, comme un
# ajout manuel (barème D-07).
KNOWN_SCORE = 1.0


class TableFileError(MappingError):
    """Fichier de table refusé ; code vaut "too_large", "encoding" ou "invalid"."""

    def __init__(self, code: str, detail: str = "") -> None:
        """Garde le code, qui choisit le message affiché, et le détail technique."""
        super().__init__(detail or code)
        self.code = code


def token_number(token: str, entity_type: EntityType, style: TokenStyle) -> int | None:
    """Rang d'un jeton dans son type, ou None si le jeton n'a pas la forme attendue.

    Paramètres : token, le jeton de la table ; entity_type, son type ; style, la forme des
    jetons de la table.
    Exemple : token_number("[SOCIETE_AB]", EntityType.ORGANIZATION, TokenStyle()) == 28.
    """
    label = TOKEN_LABELS[entity_type][0 if style.language == "fr" else 1]
    index = r"([A-Z]{1,3})" if entity_type in LETTER_INDEXED else r"([1-9]\d{0,5})"
    pattern = re.escape(f"{style.open_bracket}{label}_") + index + re.escape(style.close_bracket)
    match = re.fullmatch(pattern, token)
    if match is None:
        return None
    if entity_type not in LETTER_INDEXED:
        return int(match[1])
    number = 0
    for letter in match[1]:
        number = number * 26 + ord(letter) - ord("A") + 1
    return number


def read_table_file(data: bytes, max_bytes: int = MAX_TABLE_BYTES) -> Mapping:
    """Lit et valide un fichier .mapping.json téléversé, sans rien écrire sur le disque.

    Paramètres : data, le contenu brut du fichier ; max_bytes, la taille admise.
    Valeur retournée : la table, au format exporté par l'étape Restore.
    Lève TableFileError : "too_large" au-delà de max_bytes, "encoding" si le texte n'est
    pas en UTF-8, "invalid" si le schéma, un jeton ou une valeur ne conviennent pas.
    """
    if len(data) > max_bytes:
        raise TableFileError("too_large")
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise TableFileError("encoding") from error
    try:
        mapping = Mapping.from_json(raw)
    except (MappingError, ValueError, TypeError, RecursionError) as error:
        raise TableFileError("invalid", str(error)) from error
    for entry in mapping.entities:
        number = token_number(entry.token, entry.entity_type, mapping.token_style)
        if number is None or not entry.canonical.strip():
            raise TableFileError("invalid", f"jeton ou valeur invalide : {entry.token!r}")
    return mapping


def find_value(text: str, value: str) -> list[tuple[int, int]]:
    """Positions de value dans text : casse, accents et blancs tolérés, mots entiers.

    Paramètres : text, le texte où chercher ; value, l'écriture cherchée.
    Valeur retournée : les positions (début, fin) dans text. Le repli garde la longueur du
    texte, donc les positions trouvées valent dans le texte d'origine.
    Exemple : find_value("Vu pierre vernolac.", "Pierre VERNOLAC") == [(3, 18)].
    """
    folded = fold(value)
    if not folded:
        return []
    body = r"\s+".join(re.escape(word) for word in folded.split(" "))
    before = r"(?<!\w)" if re.match(r"\w", folded[0]) else ""
    after = r"(?!\w)" if re.match(r"\w", folded[-1]) else ""
    pattern = re.compile(f"{before}{body}{after}")
    return [match.span() for match in pattern.finditer(fold_same_length(text))]


def entry_forms(entry: MappingEntry, mapping: Mapping) -> list[str]:
    """Écritures connues d'une entité : forme canonique, variantes et textes remplacés."""
    originals = [o.original for o in mapping.occurrences if o.token == entry.token]
    return [form for form in dict.fromkeys([entry.canonical, *entry.variants, *originals]) if form]


def find_known(text: str, mapping: Mapping) -> list[Detection]:
    """Propose comme détections les écritures connues de la table présentes dans text.

    Paramètres : text, le nouveau document ; mapping, la table d'un document précédent.
    Valeur retournée : des détections de score 1,0 et de source "case_table", triées et sans
    chevauchement. Les écritures longues sont cherchées d'abord : "Pierre VERNOLAC" est pris
    en entier avant "VERNOLAC".
    """
    forms = [(form, e.entity_type) for e in mapping.entities for form in entry_forms(e, mapping)]
    found: list[Detection] = []
    for form, kind in sorted(forms, key=lambda item: (-len(fold(item[0])), item[0])):
        for start, end in find_value(text, form):
            if any(start < d.end and d.start < end for d in found):
                continue
            found.append(
                Detection(start, end, kind, KNOWN_SCORE, Source.CASE_TABLE, text[start:end])
            )
    return sorted(found, key=lambda d: (d.start, d.end))


def _keys(entity_type: EntityType, forms: Iterable[str]) -> set[str]:
    """Clés de comparaison (grouping.normalized_key) d'un ensemble d'écritures."""
    return {normalized_key(entity_type, form) for form in forms}


def _abbreviates(group: EntityGroup, entry: MappingEntry, mapping: Mapping) -> bool:
    """Dit si chaque écriture d'une personne (nom seul, initiales) abrège un nom de l'entrée."""
    full = [words for words in map(person_words, entry_forms(entry, mapping)) if len(words) >= 2]
    partial = [words for words in map(person_words, group.variants) if words]
    return bool(partial) and all(any(may_abbreviate(w, f) for f in full) for w in partial)


def match_entry(group: EntityGroup, mapping: Mapping) -> MappingEntry | None:
    """Entrée de la table qui désigne la même entité que group, ou None dans le doute.

    Une écriture de même clé de comparaison suffit : "pierre vernolac" retrouve
    "Pierre VERNOLAC". À défaut, une personne écrite par son seul nom ou par des initiales
    est rattachée à l'unique nom complet compatible. Plusieurs candidats : None, car un
    jeton neuf vaut mieux qu'une confusion entre deux personnes.
    """
    same_type = [e for e in mapping.entities if e.entity_type is group.entity_type]
    keys = _keys(group.entity_type, group.variants)
    candidates = [e for e in same_type if keys & _keys(e.entity_type, entry_forms(e, mapping))]
    if not candidates and group.entity_type is EntityType.PERSON:
        candidates = [e for e in same_type if _abbreviates(group, e, mapping)]
    return candidates[0] if len(candidates) == 1 else None


def merge_tables(known: Mapping, current: Mapping) -> Mapping:
    """Table du dossier : entités connues, variantes complétées, puis entités nouvelles.

    Paramètres : known, la table chargée ; current, la table du document courant, dont les
    jetons connus ont été repris de known.
    Valeur retournée : une table qui restaure aussi les jetons des documents précédents. Les
    occurrences et l'empreinte sont celles du document courant : le mode exact (D-10)
    s'applique toujours à son texte, et le mode tolérant à une réponse qui mêle plusieurs
    documents. La forme canonique connue est gardée, pour une restauration stable.
    """
    current_by_token = {entry.token: entry for entry in current.entities}
    entities = []
    for entry in known.entities:
        found = current_by_token.get(entry.token)
        if found is not None:
            entry = replace(entry, variants=tuple(sorted({*entry.variants, *found.variants})))
        entities.append(entry)
    known_tokens = {entry.token for entry in known.entities}
    entities.extend(entry for entry in current.entities if entry.token not in known_tokens)
    return Mapping(
        created_at=current.created_at,
        token_style=known.token_style,
        entities=tuple(entities),
        occurrences=current.occurrences,
        pseudonymized_sha256=current.pseudonymized_sha256,
    )
