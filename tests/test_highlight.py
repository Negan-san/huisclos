"""Tests du surlignage : HTML échappé, libellé écrit par entité, légende des types présents."""

from html.parser import HTMLParser

import pytest

from app import i18n
from app.components.highlight import render_highlighted, render_legend, render_restored
from app.ui_common import ENTITY_STYLES, entity_label
from huisclos.models import Detection, EntityType, Source

ALLOWED_TAGS = {"div", "mark", "span"}


class _Page(HTMLParser):
    """Relève les balises, leurs attributs et le texte d'un fragment HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.attributes: list[tuple[str, dict[str, str | None]]] = []
        self.marks: list[str] = []
        self.labels: list[str] = []
        self.text: list[str] = []
        self._open: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        self.attributes.append((tag, dict(attrs)))
        self._open.append(tag)

    def handle_endtag(self, tag: str) -> None:
        self._open.pop()

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self._open and self._open[-1] == "mark":
            self.marks.append(data)
        elif self._open and self._open[-1] == "span":
            self.labels.append(data)


def parse(fragment: str) -> _Page:
    """Analyse un fragment HTML."""
    page = _Page()
    page.feed(fragment)
    page.close()
    return page


def detection(
    text: str, value: str, kind: EntityType = EntityType.PERSON, score: float = 0.85
) -> Detection:
    """Crée la détection de la première occurrence de value dans text."""
    start = text.index(value)
    return Detection(start, start + len(value), kind, score, Source.NER_SPACY, value)


def test_script_and_quotes_only_produce_escaped_html() -> None:
    text = 'Voir <script>alert(1)</script> puis la société "Alpha" & fils <b>gras</b>.'
    entity = detection(text, '"Alpha" & fils <b>gras</b>', EntityType.ORGANIZATION)
    fragment = render_highlighted(text, [entity], {})
    assert "<script" not in fragment
    assert "<b>" not in fragment
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in fragment
    assert "&quot;Alpha&quot; &amp; fils &lt;b&gt;gras&lt;/b&gt;" in fragment
    page = parse(fragment)
    assert set(page.tags) <= ALLOWED_TAGS
    assert page.marks == ['"Alpha" & fils <b>gras</b>']


def test_title_attribute_is_escaped_and_complete() -> None:
    text = "Jean DUPONT"
    fragment = render_highlighted(text, [detection(text, text, score=0.9)], {})
    mark = next(attrs for tag, attrs in parse(fragment).attributes if tag == "mark")
    assert mark["title"] == "Person, score 0.90, source ner_spacy"
    assert 'title="Person, score 0.90, source ner_spacy"' in fragment


def test_every_entity_type_carries_a_text_label() -> None:
    for kind in EntityType:
        text = "avant valeur après"
        fragment = render_highlighted(text, [detection(text, "valeur", kind)], {})
        page = parse(fragment)
        assert page.marks == ["valeur"], kind
        assert page.labels == [i18n.EN[f"review.tag.{kind.value}"]], kind
        assert f"background:{ENTITY_STYLES[kind].color}" in fragment, kind
        assert f'class="hc-hl-{kind.value}"' in fragment, kind
    assert i18n.EN["review.tag.PERSON"] == "PERSON"
    assert i18n.EN["review.tag.ORGANIZATION"] == "COMPANY"
    assert i18n.EN["review.tag.ADDRESS"] == "ADDRESS"


def test_label_follows_the_mark_and_uses_small_caps() -> None:
    text = "Jean DUPONT"
    fragment = render_highlighted(text, [detection(text, text)], {})
    assert "</mark><span" in fragment
    assert "font-variant:small-caps" in fragment
    assert ">PERSON</span>" in fragment


def test_rejected_entity_is_struck_through_grey_and_labelled() -> None:
    text = "Jean DUPONT"
    entity = detection(text, text)
    fragment = render_highlighted(text, [entity], {(0, len(text)): False})
    page = parse(fragment)
    assert page.labels == ["REJECTED"]
    assert "line-through" in fragment
    assert ENTITY_STYLES[EntityType.PERSON].color not in fragment
    assert "PERSON" not in page.labels
    mark = next(attrs for tag, attrs in page.attributes if tag == "mark")
    assert mark["title"] is not None
    assert "rejected" in mark["title"]


def test_masked_decision_and_missing_decision_look_the_same() -> None:
    text = "Jean DUPONT"
    entity = detection(text, text)
    assert render_highlighted(text, [entity], {(0, 11): True}) == render_highlighted(
        text, [entity], {}
    )


def test_text_is_rebuilt_without_losing_or_repeating_a_character() -> None:
    text = "Ligne un <i>\nJean DUPONT & Marie PETIT\tfin"
    entities = [detection(text, "Jean DUPONT"), detection(text, "Marie PETIT")]
    page = parse(render_highlighted(text, entities, {}))
    assert (
        "".join(page.text)
        == "Ligne un <i>\nJean DUPONT" + "PERSON" + " & Marie PETIT" + "PERSON" + "\tfin"
    )
    shown = "".join(piece for piece in page.text if piece not in page.labels)
    assert shown == text
    assert "white-space:pre-wrap" in render_highlighted(text, entities, {})


def test_overlapping_or_out_of_range_detections_cannot_duplicate_text() -> None:
    text = "Jean DUPONT"
    first = detection(text, "Jean DUPONT")
    inside = detection(text, "DUPONT")
    outside = Detection(5, 40, EntityType.PERSON, 0.5, Source.MANUAL, "x" * 35)
    page = parse(render_highlighted(text, [inside, first, outside], {}))
    assert page.marks == ["Jean DUPONT"]


def test_text_comes_from_the_source_not_from_the_detection() -> None:
    text = "Jean DUPONT"
    forged = Detection(0, 4, EntityType.PERSON, 0.9, Source.MANUAL, "<i>x")
    fragment = render_highlighted(text, [forged], {})
    assert "<i>" not in fragment
    assert parse(fragment).marks == ["Jean"]


def test_empty_text_and_no_detection() -> None:
    assert parse(render_highlighted("", [], {})).text == []
    assert parse(render_highlighted("abc <d>", [], {})).text == ["abc <d>"]


def test_legend_lists_only_the_types_present() -> None:
    text = "Jean DUPONT paie par FR76 7526 9226 4948 5938 1774 654"
    entities = [
        detection(text, "Jean DUPONT"),
        detection(text, "FR76 7526 9226 4948 5938 1774 654", EntityType.IBAN),
    ]
    legend = render_legend(entities)
    assert 'class="hc-legend"' in legend
    assert f'class="hc-badge hc-hl-{EntityType.PERSON.value}"' in legend
    assert f'class="hc-badge hc-hl-{EntityType.IBAN.value}"' in legend
    assert entity_label(EntityType.PERSON) in legend
    assert entity_label(EntityType.IBAN) in legend
    for kind in set(EntityType) - {EntityType.PERSON, EntityType.IBAN}:
        assert f"hc-hl-{kind.value}" not in legend, kind
        assert entity_label(kind) not in legend, kind


def test_legend_is_empty_without_detection_and_counts_each_type_once() -> None:
    assert "hc-badge" not in render_legend([])
    text = "a b c"
    twice = [detection(text, "a"), detection(text, "b")]
    assert render_legend(twice).count("hc-badge") == 1


@pytest.mark.parametrize("kind", list(EntityType))
def test_label_texts_exist_for_every_type(kind: EntityType) -> None:
    assert i18n.EN[f"review.tag.{kind.value}"]


def test_restored_values_are_marked_with_their_type_label() -> None:
    values = {"Jean DUPONT": EntityType.PERSON, "DUPONT": EntityType.PERSON}
    fragment = render_restored("Voir Jean DUPONT, puis DUPONTEL et DUPONT.", values)
    page = parse(fragment)
    assert set(page.tags) <= ALLOWED_TAGS
    # La valeur la plus longue l'emporte, et un mot plus long n'est jamais coupé.
    assert page.marks == ["Jean DUPONT", "DUPONT"]
    assert page.labels == ["PERSON", "PERSON"]
    assert "".join(page.text).replace("PERSON", "") == "Voir Jean DUPONT, puis DUPONTEL et DUPONT."
    assert f"background:{ENTITY_STYLES[EntityType.PERSON].color}" in fragment
    assert 'title="Person, real value from the mapping table"' in fragment


def test_restored_text_is_escaped_and_works_without_values() -> None:
    values = {'"Alpha" & <b>': EntityType.ORGANIZATION}
    fragment = render_restored('<script>x</script> "Alpha" & <b> fin', values)
    assert "<script" not in fragment
    assert "<b>" not in fragment
    assert parse(fragment).marks == ['"Alpha" & <b>']
    assert parse(render_restored("abc <d>", {})).text == ["abc <d>"]
    assert parse(render_restored("abc", {"  ": EntityType.PERSON})).marks == []
