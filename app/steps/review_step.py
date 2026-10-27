"""Étape Review : l'humain décide ce qui est masqué, puis lance la pseudonymisation.

Entrées : detections, source_text et les décisions dans l'état de session ; le style de
jetons de la barre latérale.
Sorties : group_decisions (une décision par mention), manual_entities (valeurs ajoutées à la
main), puis pseudo_result et le passage à l'étape Restore.
Place dans le pipeline : entre la détection et pseudonymize.tokens ; c'est l'étape où
l'humain garde la main.
"""

import re
from dataclasses import dataclass, replace

import streamlit as st

from app.components.highlight import render_highlighted, render_legend
from app.i18n import t
from app.state import (
    KEY_DETECTIONS,
    KEY_GROUP_DECISIONS,
    KEY_MANUAL_ENTITIES,
    KEY_PSEUDO_RESULT,
    KEY_RESTORE_RESULT,
    KEY_SIGNATURE,
    KEY_SOURCE_TEXT,
    KEY_TABLE_ERROR,
    KEY_TOKEN_STYLE,
    KEY_UPLOADED_TABLE,
    STEP_IMPORT,
    STEP_RESTORE,
    go_to,
)
from app.ui_common import entity_label
from huisclos.models import Detection, EntityGroup, EntityType, Source, TokenStyle
from huisclos.pseudonymize.grouping import group_mentions
from huisclos.pseudonymize.tokens import pseudonymize
from huisclos.text_utils import fold, fold_same_length

# Clés propres à cet écran. Le numéro de version fait partie de la clé du tableau : il
# change après chaque modification, ce qui donne un tableau neuf (voir _commit_change).
KEY_TABLE_VERSION = "review_table_version"
TABLE_KEY_PREFIX = "review_table_"
KEY_FILTER = "review_filter"
KEY_MANUAL_TEXT = "review_manual_text"
KEY_MANUAL_TYPE = "review_manual_type"
KEY_MANUAL_NOTICE = "review_manual_notice"
COLUMNS = ("mask", "text", "type", "occurrences", "variants", "confidence", "source", "note")
PREVIEW_VARIANTS = 3
TEXT_HEIGHT = 420

Span = tuple[int, int]


@dataclass(frozen=True)
class Decision:
    """Choix de l'humain pour une mention : la masquer ou non, et un type imposé éventuel."""

    masked: bool = True
    entity_type: EntityType | None = None


def _decisions() -> dict[Span, Decision]:
    """Renvoie le dictionnaire des décisions de la session, clé = position (début, fin).

    Les décisions portent sur les positions, pas sur les groupes : un groupe est recalculé
    à chaque ajout ou changement de type, une position reste la même.
    """
    return st.session_state[KEY_GROUP_DECISIONS]


def overlaps(first: Detection, second: Detection) -> bool:
    """Dit si deux détections se recouvrent, ne serait-ce que d'un caractère."""
    return first.start < second.end and second.start < first.end


def current_detections() -> list[Detection]:
    """Construit les détections de travail : détection automatique, ajouts et types imposés.

    Un ajout manuel remplace les détections automatiques qu'il recouvre : la pseudonymisation
    refuse les chevauchements, et le choix explicite de l'humain l'emporte.
    """
    manual = st.session_state[KEY_MANUAL_ENTITIES]
    kept = [d for d in st.session_state[KEY_DETECTIONS] if not any(overlaps(d, m) for m in manual)]
    result = []
    for detection in sorted([*kept, *manual], key=lambda d: (d.start, d.end)):
        forced = _decisions().get((detection.start, detection.end), Decision()).entity_type
        result.append(replace(detection, entity_type=forced) if forced else detection)
    return result


def is_masked(detection: Detection) -> bool:
    """Dit si la mention sera remplacée par un jeton (vrai tant que l'humain ne l'a pas rejetée)."""
    return _decisions().get((detection.start, detection.end), Decision()).masked


def find_occurrences(text: str, value: str) -> list[Span]:
    """Trouve toutes les occurrences d'une valeur, sans casse, sans accents, mots entiers.

    Paramètres : text, le texte d'origine ; value, la valeur saisie par l'humain.
    Valeur retournée : les positions (début, fin) dans le texte d'origine. Le repli des
    accents garde la longueur du texte, donc les positions trouvées sont valides ; les
    blancs de la valeur correspondent à n'importe quel blanc du texte, retour à la ligne
    compris. Exemple : find_occurrences("Le CLIENT a écrit", "client") donne [(3, 9)].
    """
    folded = fold(value)
    if not folded:
        return []
    body = r"\s+".join(re.escape(word) for word in folded.split(" "))
    before = r"(?<!\w)" if re.match(r"\w", folded[0]) else ""
    after = r"(?!\w)" if re.match(r"\w", folded[-1]) else ""
    pattern = re.compile(f"{before}{body}{after}")
    return [match.span() for match in pattern.finditer(fold_same_length(text))]


def add_manual(text: str, value: str, entity_type: EntityType) -> tuple[int, int]:
    """Ajoute chaque occurrence de la valeur comme détection manuelle de score 1,0.

    Une occurrence déjà comprise dans une valeur masquée est laissée de côté : elle est
    protégée, et la remplacer ferait perdre une partie de la valeur plus longue (le nom
    "DUPONT" dans "Jean DUPONT" ne doit pas libérer "Jean"). Une occurrence qui recouvre
    une valeur rejetée ou une détection partielle la remplace, et les décisions de ces
    positions sont effacées. Renvoie (occurrences ajoutées, occurrences déjà couvertes).
    """
    spans = find_occurrences(text, value)
    protected = [(d.start, d.end) for d in current_detections() if is_masked(d)]
    fresh = [s for s in spans if not any(a <= s[0] and s[1] <= b for a, b in protected)]
    added = [Detection(s, e, entity_type, 1.0, Source.MANUAL, text[s:e]) for s, e in fresh]
    kept = [
        m for m in st.session_state[KEY_MANUAL_ENTITIES] if not any(overlaps(m, a) for a in added)
    ]
    st.session_state[KEY_MANUAL_ENTITIES] = [*kept, *added]
    for span in [s for s in _decisions() if any(s[0] < a.end and a.start < s[1] for a in added)]:
        del _decisions()[span]
    return len(added), len(spans) - len(added)


def _bump_table() -> None:
    """Change la clé du tableau, donc repart d'un éditeur sans modification en attente."""
    st.session_state[KEY_TABLE_VERSION] = st.session_state.get(KEY_TABLE_VERSION, 0) + 1


def _commit_change() -> None:
    """Enregistre qu'une décision a changé : tableau neuf, résultats périmés effacés.

    Sans cela, les modifications en attente de l'éditeur, repérées par numéro de ligne,
    s'appliqueraient à des lignes devenues différentes après un nouveau regroupement. La
    pseudonymisation déjà faite ne correspond plus aux décisions : elle est retirée.
    """
    _bump_table()
    st.session_state[KEY_PSEUDO_RESULT] = None
    st.session_state[KEY_RESTORE_RESULT] = None


def _column_names() -> dict[str, str]:
    """Renvoie le titre affiché de chaque colonne du tableau."""
    return {column: t(f"review.column.{column}") for column in COLUMNS}


def _variants_preview(variants: tuple[str, ...]) -> str:
    """Résume les variantes d'un groupe : les premières, puis le nombre de celles qui restent."""
    shown = ", ".join(variants[:PREVIEW_VARIANTS])
    hidden = len(variants) - PREVIEW_VARIANTS
    return f"{shown}, {t('review.variants.more', count=hidden)}" if hidden > 0 else shown


def _group_rows(groups: list[EntityGroup], detections: list[Detection]) -> list[dict[str, object]]:
    """Construit une ligne de tableau par groupe, dans l'ordre d'apparition.

    La case Mask n'est cochée que si toutes les mentions du groupe sont masquées ; la
    confiance est le score le plus bas du groupe, celui qui mérite le plus d'attention.
    """
    names = _column_names()
    by_span = {(d.start, d.end): d for d in detections}
    rows: list[dict[str, object]] = []
    for group in groups:
        members = [by_span[span] for span in group.mention_spans]
        rows.append(
            {
                names["mask"]: all(is_masked(d) for d in members),
                names["text"]: group.canonical,
                names["type"]: entity_label(group.entity_type),
                names["occurrences"]: len(members),
                names["variants"]: _variants_preview(group.variants),
                names["confidence"]: min(d.score for d in members),
                names["source"]: ", ".join(sorted({d.source.value for d in members})),
                names["note"]: t("review.note.ambiguous") if group.ambiguous_with else "",
            }
        )
    return rows


def _apply_edits(
    groups: list[EntityGroup], before: list[dict[str, object]], after: list[dict[str, object]]
) -> bool:
    """Reporte sur toutes les mentions d'un groupe les cases et types modifiés dans le tableau.

    Paramètres : les groupes affichés, les lignes envoyées à l'éditeur et celles qu'il
    renvoie. Valeur retournée : vrai si au moins une décision a changé.
    """
    names = _column_names()
    kinds = {entity_label(kind): kind for kind in EntityType}
    changed = False
    for group, old, new in zip(groups, before, after, strict=True):
        changes: dict[str, object] = {}
        if new[names["mask"]] != old[names["mask"]]:
            changes["masked"] = bool(new[names["mask"]])
        if new[names["type"]] != old[names["type"]] and new[names["type"]] in kinds:
            changes["entity_type"] = kinds[str(new[names["type"]])]
        if not changes:
            continue
        for span in group.mention_spans:
            _decisions()[span] = replace(_decisions().get(span, Decision()), **changes)
        changed = True
    return changed


def _render_counts(groups: list[EntityGroup], detections: list[Detection]) -> None:
    """Affiche les totaux et, par type, le nombre d'occurrences masquées et rejetées."""
    masked = sum(is_masked(d) for d in detections)
    first, second, third = st.columns(3)
    first.metric(t("review.counts.masked"), masked)
    second.metric(t("review.counts.rejected"), len(detections) - masked)
    third.metric(t("review.counts.groups"), len(groups))
    rows = []
    for kind in EntityType:
        of_kind = [d for d in detections if d.entity_type is kind]
        if of_kind:
            kept = sum(is_masked(d) for d in of_kind)
            rows.append(
                {
                    t("review.counts.type"): entity_label(kind),
                    t("review.counts.type_masked"): kept,
                    t("review.counts.type_rejected"): len(of_kind) - kept,
                }
            )
    if rows:
        st.dataframe(rows, hide_index=True)


def _render_text(text: str, detections: list[Detection]) -> None:
    """Affiche la légende puis le texte surligné, dans un cadre qui défile."""
    st.subheader(t("review.text.heading"))
    st.html(render_legend(detections))
    flags = {span: decision.masked for span, decision in _decisions().items()}
    with st.container(height=TEXT_HEIGHT, border=True):
        st.html(render_highlighted(text, detections, flags))


def _table_config(names: dict[str, str]) -> dict[str, object]:
    """Décrit les colonnes : cases à cocher, liste de types et nombres formatés."""
    return {
        names["mask"]: st.column_config.CheckboxColumn(names["mask"]),
        names["type"]: st.column_config.SelectboxColumn(
            names["type"], options=[entity_label(kind) for kind in EntityType], required=True
        ),
        names["occurrences"]: st.column_config.NumberColumn(names["occurrences"], format="%d"),
        names["confidence"]: st.column_config.NumberColumn(names["confidence"], format="%.2f"),
    }


def _render_table(groups: list[EntityGroup], detections: list[Detection]) -> None:
    """Affiche le tableau de décision et applique les modifications de l'humain.

    Quand une ligne change, les décisions sont mises à jour puis la page est relancée : le
    tableau, le texte surligné et les compteurs repartent alors des mêmes décisions.
    """
    st.subheader(t("review.table.heading"))
    st.caption(t("review.table.help"))
    present = [kind for kind in EntityType if any(g.entity_type is kind for g in groups)]
    st.session_state[KEY_FILTER] = [k for k in st.session_state.get(KEY_FILTER, []) if k in present]
    st.multiselect(
        t("review.filter.label"),
        options=present,
        format_func=entity_label,
        key=KEY_FILTER,
        on_change=_bump_table,
    )
    chosen = st.session_state[KEY_FILTER]
    shown = [g for g in groups if not chosen or g.entity_type in chosen]
    if not shown:
        st.info(t("review.table.nothing"))
        return
    names = _column_names()
    rows = _group_rows(shown, detections)
    edited = st.data_editor(
        rows,
        key=f"{TABLE_KEY_PREFIX}{st.session_state.get(KEY_TABLE_VERSION, 0)}",
        hide_index=True,
        column_order=list(names.values()),
        column_config=_table_config(names),
        disabled=[names[c] for c in COLUMNS if c not in ("mask", "type")],
    )
    if _apply_edits(shown, rows, edited):
        _commit_change()
        st.rerun()


def _manual_label(kind: EntityType) -> str:
    """Libellé d'un type dans la liste d'ajout manuel : CUSTOM se lit "Other identifier"."""
    return t("review.manual.custom") if kind is EntityType.CUSTOM else entity_label(kind)


def _on_add_manual() -> None:
    """Rappel du bouton d'ajout : cherche la valeur, l'ajoute et garde le résultat à afficher."""
    value = st.session_state[KEY_MANUAL_TEXT].strip()
    signature = st.session_state[KEY_SIGNATURE]
    if not value:
        st.session_state[KEY_MANUAL_NOTICE] = (signature, "empty", 0, 0)
        return
    kind = st.session_state[KEY_MANUAL_TYPE]
    added, covered = add_manual(st.session_state[KEY_SOURCE_TEXT], value, kind)
    if added:
        _commit_change()
        st.session_state[KEY_MANUAL_TEXT] = ""
    outcome = "added" if added else ("covered" if covered else "none")
    st.session_state[KEY_MANUAL_NOTICE] = (signature, outcome, added, covered)


def _render_notice() -> None:
    """Affiche le résultat du dernier ajout manuel, sauf s'il date d'un autre document."""
    notice = st.session_state.get(KEY_MANUAL_NOTICE)
    if not notice or notice[0] != st.session_state[KEY_SIGNATURE]:
        return
    _, outcome, added, covered = notice
    if outcome == "added":
        key = "review.manual.added_covered" if covered else "review.manual.added"
        st.success(t(key, count=added, covered=covered))
    elif outcome == "covered":
        st.info(t("review.manual.covered", covered=covered))
    else:
        st.warning(t(f"review.manual.{outcome}"))


def _render_manual() -> None:
    """Affiche le formulaire d'ajout d'une valeur oubliée par la détection."""
    st.subheader(t("review.manual.heading"))
    st.session_state.setdefault(KEY_MANUAL_TYPE, EntityType.CUSTOM)
    st.text_input(t("review.manual.text"), key=KEY_MANUAL_TEXT)
    st.selectbox(
        t("review.manual.type"),
        options=list(EntityType),
        format_func=_manual_label,
        key=KEY_MANUAL_TYPE,
    )
    st.button(t("review.manual.button"), key="review_add_manual", on_click=_on_add_manual)
    _render_notice()


def _pseudonymize(text: str, detections: list[Detection]) -> None:
    """Pseudonymise les mentions masquées, garde le résultat et passe à l'étape Restore."""
    style = TokenStyle(language=st.session_state[KEY_TOKEN_STYLE])
    try:
        with st.spinner(t("review.pseudonymize.spinner")):
            result = pseudonymize(text, [d for d in detections if is_masked(d)], style)
    except ValueError:
        st.error(t("review.error.pseudonymize"))
        return
    st.session_state[KEY_PSEUDO_RESULT] = result
    st.session_state[KEY_RESTORE_RESULT] = None
    go_to(STEP_RESTORE)
    st.session_state[KEY_UPLOADED_TABLE] = None
    st.session_state[KEY_TABLE_ERROR] = None
    st.rerun()


def _render_actions(text: str, detections: list[Detection]) -> None:
    """Affiche le bouton Pseudonymize, son avertissement éventuel et le retour à Import."""
    if not any(is_masked(d) for d in detections):
        st.warning(t("review.nothing_masked"))
    st.caption(t("review.pseudonymize.note"))
    if st.button(t("review.pseudonymize"), key="review_pseudonymize", type="primary"):
        _pseudonymize(text, detections)
    st.button(t("review.back"), key="review_back", on_click=go_to, args=(STEP_IMPORT,))


def render() -> None:
    """Affiche l'étape Review, ou l'état vide quand aucune détection n'a été faite."""
    st.header(t("review.title"))
    if st.session_state[KEY_DETECTIONS] is None:
        st.info(t("review.empty"))
        st.button(t("review.back"), key="review_back", on_click=go_to, args=(STEP_IMPORT,))
        return
    text = st.session_state[KEY_SOURCE_TEXT]
    detections = current_detections()
    groups = group_mentions(text, detections)
    st.markdown(t("review.intro"))
    st.caption(t("review.summary", count=len(detections), groups=len(groups)))
    _render_counts(groups, detections)
    _render_text(text, detections)
    if groups:
        _render_table(groups, detections)
    _render_manual()
    _render_actions(text, detections)
