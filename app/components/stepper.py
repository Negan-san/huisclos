"""Indicateur d'étapes horizontal : pastilles numérotées, nom de l'étape et état écrit.

Entrées : la liste des étapes, l'étape courante et l'accessibilité de chacune.
Sorties : step_states() donne l'état de chaque étape ; stepper_html() en fait un bloc HTML
sûr, à afficher avec st.html.
Place dans le pipeline : en tête de la page Pseudonymize, au-dessus de l'étape courante.
"""

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Les quatre états possibles d'une étape. Chacun a sa classe CSS et sa mention écrite :
# l'état se lit sans la couleur.
DONE = "done"
CURRENT = "current"
AVAILABLE = "available"
LOCKED = "locked"


@dataclass(frozen=True)
class StepView:
    """Ce qu'affiche une étape : son numéro, son nom, son état et la mention qui le dit."""

    number: int
    name: str
    state: str
    note: str


def step_states(steps: Sequence[str], current: str, available: Mapping[str, bool]) -> list[str]:
    """Renvoie l'état de chaque étape, dans l'ordre du parcours.

    Paramètres : steps, les étapes dans l'ordre ; current, l'étape affichée ; available, vrai
    pour une étape accessible. Une étape inaccessible est verrouillée, même avant la courante ;
    une étape accessible est faite si elle précède la courante.
    Exemple : step_states(("a", "b", "c"), "b", {"a": True, "b": True, "c": False}) donne
    ["done", "current", "locked"].
    """
    position = steps.index(current)
    states = []
    for index, step in enumerate(steps):
        if step == current:
            states.append(CURRENT)
        elif not available.get(step, False):
            states.append(LOCKED)
        else:
            states.append(DONE if index < position else AVAILABLE)
    return states


def _step_html(view: StepView) -> str:
    """Construit l'élément de liste d'une étape ; chaque texte est échappé."""
    current = ' aria-current="step"' if view.state == CURRENT else ""
    # La pastille d'une étape faite porte une coche dessinée en CSS à la place du numéro.
    dot = "" if view.state == DONE else str(view.number)
    return (
        f'<li class="hc-step hc-step-{view.state}"{current}>'
        f'<span class="hc-step-dot" aria-hidden="true">{dot}</span>'
        f'<span class="hc-step-text"><span class="hc-step-name">{html.escape(view.name)}</span>'
        f'<span class="hc-step-note">{html.escape(view.note)}</span></span></li>'
    )


def stepper_html(views: Sequence[StepView], label: str) -> str:
    """Renvoie l'indicateur complet : une liste ordonnée nommée pour les lecteurs d'écran.

    Paramètres : views, une vue par étape ; label, le nom de la liste (attribut aria-label).
    Valeur retournée : le HTML, dont chaque texte variable est échappé.
    """
    items = "".join(_step_html(view) for view in views)
    # role="list" garde la sémantique de liste que certains lecteurs d'écran retirent
    # quand les puces sont masquées par le style.
    name = html.escape(label, quote=True)
    return f'<ol class="hc-stepper" role="list" aria-label="{name}">{items}</ol>'
