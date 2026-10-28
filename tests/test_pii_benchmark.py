"""Valide la mesure B3 avec de faux modèles et des décalages calculés à la main.

Entrées : textes fictifs, plans temporaires et sorties de modèles simulées.
Sorties : refus des expériences invalides et mesures de couverture vérifiables.
Place : contrôle du prototype, sans poids chargés ni réseau ni corpus réel.
"""

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from huisclos.models import Detection, EntityType, Source
from scripts import benchmark_post_g7_pii as benchmark
from scripts.audit_post_g7_invariants import summarize


class CharacterTokenizer:
    """Tokenizer fictif qui expose chaque caractère et une capacité bornée."""

    model_max_length = 256

    def num_special_tokens_to_add(self) -> int:
        """Réserve deux jetons spéciaux comme les modèles de l'expérience."""
        return 2

    def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Renvoie des positions exactes sans chercher les mentions dans le texte."""
        if isinstance(text, list):
            return {"input_ids": [list(range(sum(len(word) for word in row))) for row in text]}
        return {
            "input_ids": list(range(len(text))),
            "offset_mapping": [(n, n + 1) for n in range(len(text))],
        }


class FakeModel:
    """Faux NER qui conserve les positions, les répétitions et les options GLiNER."""

    def __init__(self) -> None:
        """Expose le contrat minimal du modèle installé, sans dépendance neuronale."""
        self.config = SimpleNamespace(max_len=384)
        self.data_processor = SimpleNamespace(
            words_splitter=lambda text: [
                (m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", text)
            ],
            prepare_inputs=lambda texts, labels: (texts, [0]),
        )
        self.calls: list[dict[str, Any]] = []

    def __call__(self, text: str) -> list[dict[str, Any]]:
        """Émet deux mentions projetables et une date générique à ignorer."""
        return [
            {"start": m.start(), "end": m.end(), "score": 0.85, "entity_group": "NOM_PERSONNE"}
            for m in re.finditer("Offiline Varenne", text)
        ] + [{"start": 0, "end": 1, "score": 0.99, "entity_group": "DATE"}]

    def predict_entities(self, text: str, labels: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        """Contrôle que les labels et le seuil minimal sont fournis explicitement."""
        self.calls.append({"labels": labels, **kwargs})
        return [
            {**item, "label": "person"}
            for item in self(text)
            if item["entity_group"] == "NOM_PERSONNE"
        ]


@pytest.mark.parametrize("gliner", [False, True])
def test_adapter_projects_repetitions_and_ignores_generic_date(
    gliner: bool, no_network: None
) -> None:
    """Une ligature et un invisible ne ramènent pas toutes les mentions à la première."""
    text = "O\ufb03line Va\u200brenne ; O\ufb03line Va\u200brenne"
    model = FakeModel()
    mapping = benchmark.LABELS if gliner else benchmark.ANONYM
    found = benchmark.proposals(text, (model, CharacterTokenizer(), mapping, {}), gliner)
    assert [(d.start, d.end, d.text) for d in found] == [(0, 15, text[:15]), (18, 33, text[18:33])]
    assert all(d.entity_type == EntityType.PERSON for d in found)
    if gliner:
        assert model.calls == [
            {
                "labels": list(benchmark.LABELS),
                "threshold": 0.3,
                "flat_ner": False,
                "multi_label": True,
            }
        ]


def test_adapter_refuses_gliner_truncation(no_network: None) -> None:
    """Une fenêtre dépassant la capacité de mots échoue au lieu de masquer une troncature."""
    model = FakeModel()
    model.config.max_len = 1
    with pytest.raises(ValueError, match="tronquée"):
        benchmark.proposals(
            "Offiline Varenne", (model, CharacterTokenizer(), benchmark.LABELS, {}), True
        )


def test_adapter_covers_a_repeated_name_crossing_a_window(no_network: None) -> None:
    """Le recouvrement A1 garde entière une mention située sur la coupure."""
    text = "x" * 248 + " Offiline Varenne ; Offiline Varenne"
    found = benchmark.proposals(
        text, (FakeModel(), CharacterTokenizer(), benchmark.ANONYM, {}), False
    )
    assert [(d.start, d.end, d.text) for d in found] == [
        (249, 265, "Offiline Varenne"),
        (268, 284, "Offiline Varenne"),
    ]


def test_mapping_keeps_policy_boundaries() -> None:
    """Ville, date ordinaire et numéro public ne sont pas requalifiés automatiquement."""
    assert not {"DATE", "VILLE", "CODE_POSTAL", "NOM_VOIE", "NUM_DOSSIER"} & benchmark.ANONYM.keys()
    assert benchmark.ANONYM["DOB"] == "BIRTH_DATE"
    assert "location" not in benchmark.LABELS


def test_pack_roundtrip_and_invalid_offsets() -> None:
    """Les positions répétées survivent à la sérialisation ; un span invalide est refusé."""
    text = "Agathe Agathe"
    values = [
        Detection(s, s + 6, EntityType.PERSON, 0.8, Source.NER_CAMEMBERT, "Agathe") for s in (0, 7)
    ]
    assert benchmark.unpack(text, benchmark.pack(values)) == values
    with pytest.raises(ValueError):
        benchmark.unpack(text, [[-1, 6, "PERSON", 0.8, "ner_camembert"]])


def test_replay_preserves_person_with_weak_company(no_network: None) -> None:
    """Le rejeu utilise réellement la fusion A1 et conserve le nom complet admissible."""
    text = "Agathe Vernois"
    raw = [
        Detection(0, len(text), EntityType.PERSON, 0.85, Source.NER_SPACY, text),
        Detection(0, 6, EntityType.ORGANIZATION, 0.1, Source.NER_CAMEMBERT, "Agathe"),
    ]
    result = benchmark.replay(text, raw, "fr", 0.3)
    assert [(d.start, d.end) for d in result] == [(0, len(text))]


@pytest.fixture
def experiment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Préenregistre un corpus jouet indépendant de tous les corpus du projet."""
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "manifest.json").write_text(json.dumps({"models": {}}), encoding="utf-8")
    corpus = tmp_path / "dev.jsonl"
    corpus.write_text(
        json.dumps(
            {
                "id": "toy",
                "doc_type": "letter",
                "split": "dev",
                "title": "Fiction",
                "text": "Agathe Vernois écrit.",
                "entities": [{"start": 0, "end": 14, "type": "PERSON", "text": "Agathe Vernois"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(benchmark, "ASSETS", assets)
    monkeypatch.setattr(benchmark, "CORPORA", {"fr": corpus, "en": corpus})
    monkeypatch.setattr(benchmark.subprocess, "check_output", lambda *a, **k: "fictional-sha")
    out = tmp_path / "results"
    benchmark.prepare(out)
    return out


def test_preregistration_cannot_be_overwritten(experiment: Path) -> None:
    """Le premier plan fait foi ; une seconde préparation refuse son écrasement."""
    assert benchmark.checked_plan(experiment)["grid"] == [0.3, 0.5, 0.7]
    with pytest.raises(FileExistsError):
        benchmark.prepare(experiment)


@pytest.mark.parametrize(
    "backend", ["camembert_ner", "anonym_ia_v2", "anonym_ia_v2+gliner_multi_pii_v1"]
)
def test_french_backends_are_refused_for_english(experiment: Path, backend: str) -> None:
    """Le worker ne transforme pas un renfort français en preuve de support anglais."""
    with pytest.raises(ValueError, match="matrice"):
        benchmark.extract(experiment, "en", backend, "candidate", 1)


def test_preregistration_detects_code_drift(
    experiment: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changer les labels du code ne permet pas de réutiliser silencieusement l'ancien plan."""
    monkeypatch.setattr(benchmark, "LABELS", {"person": "PERSON"})
    with pytest.raises(ValueError, match="Labels ou grille"):
        benchmark.checked_plan(experiment)


def test_production_windows_are_reserved_for_camembert(experiment: Path) -> None:
    """Le contrôle du comparateur historique ne change pas la grille des autres modèles."""
    with pytest.raises(ValueError, match="réservé"):
        benchmark.extract(experiment, "en", "standard", "baseline", 1, production_cam=True)


@pytest.mark.parametrize("filename", ["plan.json", "manifest.json", "dev.jsonl"])
def test_preregistration_detects_mutation(experiment: Path, filename: str) -> None:
    """Toute modification du plan, manifeste ou corpus invalide la mesure."""
    path = {
        "plan.json": experiment / filename,
        "manifest.json": benchmark.ASSETS / filename,
        "dev.jsonl": benchmark.CORPORA["en"],
    }[filename]
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError):
        benchmark.checked_plan(experiment)


def test_summary_counts_actual_substitution_offsets(experiment: Path, no_network: None) -> None:
    """La couverture compte les caractères d'origine, même si les jetons ont une autre taille."""
    for backend, environment, rows in [
        ("standard", "baseline", [[0, 6, "PERSON", 0.85, "ner_spacy"]]),
        ("gliner_multi_pii_v1", "candidate", [[0, 14, "PERSON", 0.85, "ner_camembert"]]),
    ]:
        for repeat in (1, 2):
            benchmark.save(
                experiment / f"en_{backend}_{environment}_{repeat}.json",
                {
                    "backend": backend,
                    "environment": environment,
                    "repeat": repeat,
                    "documents": [rows],
                    "plan_sha256": benchmark.digest(experiment / "plan.json"),
                },
            )
    summarize(experiment, "en")
    report = json.loads((experiment / "en_report.json").read_text(encoding="utf-8"))
    masked = [
        r
        for r in report["coverage"]
        if r["stage"] == "pseudonymization" and r["scope"] == "evaluated"
    ]
    assert [r["leaked_characters"] for r in masked] == [8, 0]
    assert report["engineering_criteria"][0]["met"] is True
    assert report["coverage_losses"][0]["characters"] == 0


def test_summary_refuses_incomplete_repetitions(experiment: Path, no_network: None) -> None:
    """Un worker absent ne se transforme pas en résultat ou coût supposé."""
    benchmark.save(
        experiment / "en_standard_baseline_1.json",
        {
            "backend": "standard",
            "environment": "baseline",
            "repeat": 1,
            "documents": [[]],
            "plan_sha256": benchmark.digest(experiment / "plan.json"),
        },
    )
    with pytest.raises(ValueError, match="Deux processus"):
        summarize(experiment, "en")
