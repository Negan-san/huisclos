"""Texte surligné et légende de l'écran de revue, produits sous forme de HTML sûr.

Entrées : le texte d'origine, les détections (sans chevauchement) et les décisions de l'humain.
Sorties : deux chaînes HTML, à afficher avec st.html, et rien d'autre.
Place dans le pipeline : étape Review ; le texte de l'utilisateur n'entre dans le HTML
qu'après html.escape, ce qui interdit toute injection.
"""

import html
from collections.abc import Mapping, Sequence

from app.i18n import t
from app.ui_common import ENTITY_STYLES, entity_badge_html, entity_label
from huisclos.models import Detection, EntityType

# Décisions par mention : la clé est la position (début, fin), la valeur dit si la mention
# est masquée. Une mention absente du dictionnaire est masquée.
Decisions = Mapping[tuple[int, int], bool]

# Les styles sont écrits ici, et non dans style.css, pour que le composant reste lisible
# même si la feuille de style n'a pas été injectée. Les couleurs viennent de la charte.
_DOCUMENT_STYLE = "white-space:pre-wrap;overflow-wrap:anywhere;line-height:2.2"
_INK = "var(--hc-ink,#1B1F24)"
_MUTED = "var(--hc-muted,#596270)"
_MARK_STYLE = f"color:{_INK};padding:2px 4px;border-radius:4px"
_REJECTED_STYLE = (
    f"background:var(--hc-surface,#F4F5F7);color:{_MUTED};"
    "text-decoration:line-through;padding:2px 4px;border-radius:4px"
)
# Le libellé est en petites capitales, plus petit que le texte, et ne porte jamais la
# couleur seule : le type reste lisible en noir et blanc.
_TAG_STYLE = (
    "font-variant:small-caps;font-size:0.75em;font-weight:600;letter-spacing:0.05em;"
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
    color = html.escape(ENTITY_STYLES[kind].color, quote=True)
    tag = html.escape(t(f"review.tag.{kind.value}"))
    return (
        f'<mark class="hc-hl-{kind.value}" title="{title}" '
        f'style="background:{color};{_MARK_STYLE}">{escaped}</mark>'
        f'<span style="{_TAG_STYLE.format(color=_INK)}">{tag}</span>'
    )


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
