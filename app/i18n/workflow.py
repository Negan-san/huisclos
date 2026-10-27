"""Textes du parcours Import, Review et Restore, en anglais et en français.

Entrées : dictionnaires des trois étapes, séparés pour rester lisibles.
Sorties : EN et FR, conservés comme point d'accès commun au parcours.
Place dans le pipeline : fusion des textes avant leur lecture par app.i18n.
"""

from app.i18n import workflow_import, workflow_restore, workflow_review

EN: dict[str, str] = {
    **workflow_import.EN,
    **workflow_review.EN,
    **workflow_restore.EN,
}
FR: dict[str, str] = {
    **workflow_import.FR,
    **workflow_review.FR,
    **workflow_restore.FR,
}
