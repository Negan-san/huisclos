"""Texte surligné, légende et texte restauré, produits sous forme de HTML sûr.

Entrées : le texte d'origine, les détections (sans chevauchement) et les décisions de
l'humain ; pour l'étape Restore, le texte restauré et les valeurs de la table.
Sorties : des chaînes HTML, à afficher avec st.html, et rien d'autre.
Place dans le pipeline : étapes Review et Restore ; le texte de l'utilisateur n'entre dans
le HTML qu'après html.escape, ce qui interdit toute injection.
"""

import html
import re
from collections.abc import Mapping, Sequence

from app.i18n import t
from app.ui_common import ENTITY_STYLES, entity_badge_html, entity_label
from huisclos.models import Detection, EntityType

# Décisions par mention : la clé est la position (début, fin), la valeur dit si la mention
# est masquée. Une mention absente du dictionnaire est masquée.
Decisions = Mapping[tuple[int, int], bool]

# Les styles sont écrits ici, et non dans style.css, pour que le composant reste lisible
# même si la feuille de style n'a pas été injectée. Les couleurs viennent de la charte.
# L'interligne laisse la place au libellé de type ; box-decoration-break répète le fond et
# le trait sur chaque ligne d'une mention coupée par un retour à la ligne.
_DOCUMENT_STYLE = (
    "white-space:pre-wrap;overflow-wrap:anywhere;line-height:2.2;font-size:0.9375rem;"
    "color:var(--hc-ink,#1B1F24)"
)
_INK = "var(--hc-ink,#1B1F24)"
_MUTED = "var(--hc-muted,#596270)"
_MARK_STYLE = (
    f"color:{_INK};padding:2px 4px;border-radius:4px;"
    "box-decoration-break:clone;-webkit-box-decoration-break:clone"
)
_REJECTED_STYLE = (
    f"background:var(--hc-surface,#F1F3F6);color:{_MUTED};"
    "text-decoration:line-through;padding:2px 4px;border-radius:4px;"
    "box-decoration-break:clone;-webkit-box-decoration-break:clone"
)
# Le libellé est en petites capitales, plus petit que le texte, et ne porte jamais la
# couleur seule : le type reste lisible en noir et blanc.
_TAG_STYLE = (
    "font-variant:small-caps;font-size:0.6875em;font-weight:700;letter-spacing:0.06em;"
    "margin:0 8px 0 4px;color:{color}"
)


def _hover_text(detection: Detection, masked: bool) -> str:
    """Construit l'infobulle d'une mention : type, score et source, avec le rejet éventuel."""
    key = "review.hover" if masked else "review.hover.rejected"
    return t(
        key,
        kind=entity_label(detection.entity_type),
        score=f"{detection.score:.2f}",
        source=detection.source.value,
    )


def _entity_html(shown: str, detection: Detection, masked: bool) -> str:
    """Construit l'élément mark d'une mention, suivi de son libellé écrit.

    Paramètres : shown, le texte exact de la mention ; detection ; masked, faux si l'humain
    l'a rejetée. Valeur retournée : le HTML, dont chaque valeur variable est échappée.
    """
    title = html.escape(_hover_text(detection, masked), quote=True)
    escaped = html.escape(shown)
    kind = detection.entity_type
    if not masked:
        tag = html.escape(t("review.rejected"))
        return (
            f'<mark class="hc-rejected" title="{title}" style="{_REJECTED_STYLE}">{escaped}</mark>'
            f'<span style="{_TAG_STYLE.format(color=_MUTED)}">{tag}</span>'
        )
    return _type_mark(escaped, kind, title)


def _type_mark(escaped: str, kind: EntityType, title: str) -> str:
    """Construit la marque colorée d'une valeur déjà échappée, suivie du libellé de son type."""
    style = ENTITY_STYLES[kind]
    color = html.escape(style.color, quote=True)
    strong = html.escape(style.strong, quote=True)
    tag = html.escape(t(f"review.tag.{kind.value}"))
    return (
        f'<mark class="hc-hl-{kind.value}" title="{title}" '
        f'style="background:{color};box-shadow:inset 0 -2px 0 {strong};{_MARK_STYLE}">'
        f"{escaped}</mark>"
        f'<span style="{_TAG_STYLE.format(color=strong)}">{tag}</span>'
    )


def _value_pattern(values: Mapping[str, EntityType]) -> re.Pattern[str] | None:
    """Expression qui trouve chaque valeur en mot entier, la plus longue d'abord."""
    pieces = []
    for value in sorted((v for v in values if v.strip()), key=len, reverse=True):
        before = r"(?<!\w)" if re.match(r"\w", value[0]) else ""
        after = r"(?!\w)" if re.match(r"\w", value[-1]) else ""
        pieces.append(f"{before}{re.escape(value)}{after}")
    return re.compile("|".join(pieces)) if pieces else None


def render_restored(text: str, values: Mapping[str, EntityType]) -> str:
    """Renvoie le texte restauré en HTML, chaque vraie valeur de la table étant surlignée.

    Paramètres : text, le texte restauré ; values, les formes réelles remises par la
    restauration et leur type. Une valeur déjà écrite en clair dans la réponse est aussi
    surlignée : c'est bien une donnée réelle du dossier.
    Exemple : render_restored("Voir Jean.", {"Jean": EntityType.PERSON}) surligne "Jean".
    """
    pattern = _value_pattern(values)
    pieces: list[str] = []
    cursor = 0
    for match in pattern.finditer(text) if pattern else ():
        kind = values[match.group()]
        title = html.escape(t("restore.hover", kind=entity_label(kind)), quote=True)
        pieces.append(html.escape(text[cursor : match.start()]))
        pieces.append(_type_mark(html.escape(match.group()), kind, title))
        cursor = match.end()
    pieces.append(html.escape(text[cursor:]))
    return f'<div class="hc-document" style="{_DOCUMENT_STYLE}">{"".join(pieces)}</div>'


def render_highlighted(text: str, detections: Sequence[Detection], decisions: Decisions) -> str:
    """Renvoie le texte en HTML, chaque mention étant surlignée et suivie de son libellé.

    Paramètres : text, le texte d'origine ; detections, les détections à montrer ;
    decisions, la décision par position (début, fin), vrai pour masquer.
    Valeur retournée : un bloc HTML qui conserve les retours à la ligne. Le texte affiché
    est toujours celui du texte d'origine (jamais Detection.text), et une détection qui
    recouvre la précédente ou sort du texte est ignorée : l'affichage ne peut pas dupliquer
    ni perdre de caractère.
    """
    pieces: list[str] = []
    cursor = 0
    for detection in sorted(detections, key=lambda item: (item.start, item.end)):
        if detection.start < cursor or detection.end > len(text):
            continue
        pieces.append(html.escape(text[cursor : detection.start]))
        masked = decisions.get((detection.start, detection.end), True)
        pieces.append(_entity_html(text[detection.start : detection.end], detection, masked))
        cursor = detection.end
    pieces.append(html.escape(text[cursor:]))
    return f'<div class="hc-document" style="{_DOCUMENT_STYLE}">{"".join(pieces)}</div>'


def render_legend(detections: Sequence[Detection]) -> str:
    """Renvoie la légende : une pastille colorée et le nom de chaque type présent.

    Seuls les types qui figurent dans les détections sont listés, dans l'ordre de
    l'énumération EntityType.
    """
    present = {detection.entity_type for detection in detections}
    badges = "".join(entity_badge_html(kind) for kind in EntityType if kind in present)
    return f'<div class="hc-legend">{badges}</div>'
