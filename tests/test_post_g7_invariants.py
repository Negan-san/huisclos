"""Contrôles B3 indépendants des fixtures ayant servi aux règles A1/A2.

Entrées : exemples fictifs nouveaux et réseau interdit.
Sorties : échecs explicites, ou xfail strict pour un défaut métier établi.
Place : audit avant intégration A4, sans mesure d'un split réservé.
"""

import pytest

from scripts.audit_post_g7_invariants import CASES


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            name,
            marks=pytest.mark.xfail(
                strict=True,
                raises=AssertionError,
                reason="B3-01 : merge.trim retire '(' du PHONE américain reconnu en entier ; "
                "couverture intégrale impossible avant correction A4",
            ),
        )
        if name == "phone_bounds"
        else name
        for name in CASES
    ],
)
def test_independent_invariant(case: str, no_network: None) -> None:
    """Vérifie chaque propriété de l'audit indépendant sur ses entrées fictives."""
    CASES[case]()
