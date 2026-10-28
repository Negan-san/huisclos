"""Contrôles B3 indépendants des fixtures ayant servi aux règles A1/A2.

Entrées : exemples fictifs nouveaux et réseau interdit.
Sorties : échecs explicites pour tout défaut métier établi.
Place : audit avant intégration A4, sans mesure d'un split réservé.
"""

import pytest

from scripts.audit_post_g7_invariants import CASES


@pytest.mark.parametrize("case", CASES)
def test_independent_invariant(case: str, no_network: None) -> None:
    """Vérifie chaque propriété de l'audit indépendant sur ses entrées fictives."""
    CASES[case]()
