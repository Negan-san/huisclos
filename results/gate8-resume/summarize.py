"""Assemble le verdict G8R2 depuis les seuls rapports agrégés.

Entrées : reçu courant et archives G7/G8 préservées, jamais un corpus.
Sorties : synthèse JSON et rapport séparant correction, technique et recommandation.
Les intervalles viennent des prédictions uniques du harnais, sans recalcul de détection.
"""

import json
from typing import Any

from controls import FIX, OUT, ROOT, digest, git, read, save


def profiles(report: dict[str, Any]) -> dict[str, Any]:
    """Extrait les agrégats par profil sans valeur, position ni identifiant de document."""
    result = {}
    for name in report["metadata"]["profiles"]:
        result[name] = {
            "partial": next(
                row
                for row in report["metrics_by_type"]
                if row["config"] == name and row["mode"] == "partial" and row["type"] == "micro"
            ),
            "coverage": next(
                row
                for row in report["coverage"]
                if row["config"] == name
                and row["stage"] == "pseudonymization"
                and row["scope"] == "evaluated"
            ),
            "custom_location": next(
                row
                for row in report["coverage"]
                if row["config"] == name
                and row["stage"] == "pseudonymization"
                and row["scope"] == "custom_location"
            ),
        }
    return result


def assert_aggregates(value: Any) -> None:
    """Refuse les clés de contenu ou de positions dans les exports JSON de cette reprise."""
    forbidden = {
        "document_id",
        "document_ids",
        "text",
        "texts",
        "reference_text",
        "visible_text",
        "context_before",
        "context_after",
        "original",
        "canonical",
        "variants",
        "occurrences",
        "detections",
        "start",
        "end",
        "mapping",
    }
    if isinstance(value, dict):
        assert not forbidden.intersection(value)
        for child in value.values():
            assert_aggregates(child)
    elif isinstance(value, list):
        for child in value:
            assert_aggregates(child)


def main() -> None:
    """Valide la provenance courante, compare les agrégats et publie le verdict limité."""
    completion = read("results/gate8-resume/complete_challenge.json")
    assert completion["cli_exit_code"] == 0 and completion["report_produced"]
    report = read("results/gate8-resume/challenge/robustness.json")
    metadata = report["metadata"]
    assert metadata["git_commit"] == FIX == git("rev-parse", "HEAD")
    assert metadata["dataset_id"] == "gate8_resume_challenge" and metadata["mode"] == "gate"
    assert metadata["document_language"] == "fr"
    registration = read("results/gate8-resume/registration.json")
    assert metadata["plan"] == registration["plan"]
    assert (
        metadata["corpus_sha256"]["challenge.jsonl"]
        == read("results/gate8-resume/challenge-provenance.json")["corpus_sha256"]
    )
    assert report["bootstrap_method"]["draws"] == 2000
    assert report["bootstrap_method"]["seed"] == 45
    for name, profile in metadata["profiles"].items():
        assert profile["git_commit"] == FIX
        assert profile["configuration"]["threshold"] == 0.3
        assert profile["final_check_threshold"] == 0.1
        assert profile["resources"]["main_detection_calls"] == metadata["document_count"]
        assert profile["resources"]["network_blocked"]
        assert profile["preset"] == registration["plan"]["profiles"][name]["preset"]
    current = profiles(report)
    criterion = next(
        row
        for row in report["engineering_criteria"]
        if row["candidate"] == "enhanced" and row["reference"] == "standard"
    )
    assert criterion["precision_margin"] == 0.02 and criterion["over_masking_margin"] == 0.01
    historical = {}
    for dataset in ("blind_fr", "blind_en", "test"):
        archive = read(f"results/gate8/{dataset}/robustness.json")
        historical[dataset] = {
            "measured_sha": archive["metadata"]["git_commit"],
            "new_measurement": False,
            "profiles": profiles(archive),
            "criteria": archive["engineering_criteria"],
        }
    g7 = read("results/gate8/g7_archive/results.json")
    assert (
        g7["metadata"]["corpus_sha256"]["challenge.jsonl"]
        == metadata["corpus_sha256"]["challenge.jsonl"]
    )
    comparison = {}
    for name, preset in (("standard", "hybrid"), ("enhanced", "hybrid_camembert")):
        old = next(
            row
            for row in g7["metrics_by_type"]
            if row["split"] == "challenge"
            and row["mode"] == "partial"
            and row["type"] == "micro"
            and row["config"] == preset
        )
        comparison[name] = {
            "historical_g7": old,
            "current": current[name]["partial"],
            "delta_current_minus_g7": {
                key: current[name]["partial"][key] - old[key]
                for key in ("precision", "recall", "leak_rate", "leaked_characters")
            },
            "g7_full_coverage_and_overmasking": "not recorded",
            "paired_current_g7_interval": "not available; no new G7 passage",
        }
    verdicts = {
        "fix3r_01": "CLOSED; GO FIX4",
        "technical_fr_en": "GO on fictional offline fixtures",
        "fr_standard": "GO within measured French scope; default with full human review",
        "fr_enhanced": "GO as local French option"
        if criterion["met"]
        else "NO-GO recommendation on resumed challenge; frozen criterion failed",
        "fr_scope": "GO correction and French measured criteria"
        if criterion["met"]
        else "GO correction; French recommendation criterion not fully met",
        "en_standard": "experimental with strong reservations; default fallback with full review",
        "en_enhanced": "experimental and not recommended; historical precision margin failed",
        "unreserved_bilingual_validation": False,
    }
    summary = {
        "measured_sha": FIX,
        "attempt_number": 4,
        "verdicts": verdicts,
        "current_challenge": {
            "profiles": current,
            "criteria": report["engineering_criteria"],
            "paired_differences": report["paired_differences"],
            "coverage_intervals": report["coverage_intervals"],
            "historical_metric_intervals": report["bootstrap_intervals"],
        },
        "historical_g7_comparison": comparison,
        "historical_g8": historical,
        "new_reserved_series": {"challenge": 1, "test": 0, "c3_fr": 0, "c3_en": 0},
        "fresh_blind_validation": False,
        "repeat_forbidden": True,
    }
    assert_aggregates(summary)
    save("summary.json", summary)
    lines = [
        "# G8R2 : recontrôle de FIX4 et reprise unique du challenge",
        "",
        f"Code mesuré : `{FIX}`. FIX3R-01 clos, **GO du correctif FIX4**.",
        "",
        f"Périmètre FR : **{verdicts['fr_scope']}**. {verdicts['fr_enhanced']}.",
        "",
        "Fonctionnement technique FR/EN : GO sur fixtures fictives hors ligne. Enhanced EN",
        "reste expérimental et non recommandé. Aucune validation bilingue sans réserve.",
        "",
        "## Périmètre et prérequis",
        "",
        "Arbre initial propre sur lane-b ; SHA dev enregistré puis fusionné en avance rapide,",
        "HEAD égal au SHA prévu. Diff depuis 4b8a686 : état, tests et documentation seulement.",
        "tokens.py, détection, modèles, configurations, corpus et dépendances inchangés.",
        "",
        "Huit AppTest indépendants : UI/document FR et EN, RuntimeError/ValueError, premier",
        "échec et retour réel Restore vers Review. Tous les résultats, bases, réponses, tables",
        "importées à Restore, contrôles, avis et autorisations précédents sont invalidés.",
        "Décisions, ajout manuel, table de dossier, consigne et réglages sont conservés.",
        "Chaque panne est suivie d'un succès et d'une restauration exacte ; aucune mention",
        "de la panne n'apparaît dans les messages ou journaux. Quatre vrais workers séparés",
        "passent sur un nom présent dans le texte et un nom de fichier : Standard/Enhanced,",
        "FR/EN. Douze fichiers de modèles retenus et versions conformes au manifeste A4.",
        "",
        "La suite complète sous garde FIX3R inclut ces sondes et les sept tests du lanceur ;",
        "roundtrip limité à dev, zéro ouverture réservée refusée. Ruff check/format, style et",
        "diff conformes. Les journaux preflight et final portent les commandes et résultats.",
        "Le premier précontrôle (preflight) a étendu à tort HUISCLOS_MODELS_DIR aux tests du",
        "cache : deux échecs de chemin attendus, 1747 réussites. Le lanceur seul a été corrigé",
        "pour limiter cette variable aux sondes worker. Les deux témoins passent ensuite, puis",
        "la suite complète est reprise dans preflight2, avant tout accès au challenge.",
        "",
        "Preuves FIX3R réutilisées : vingt cas Standard requis, six régressions avant/après,",
        "invariants Presidio et mémoire contrôlée. Pas de nouvelle exploration générale.",
        "Limites recevables conservées : D-FIX3-2, docstring _token_tables obsolète,",
        "surmasquage FR numérique isolé sans fuite, longueurs et avertissements connus.",
        "",
        "## Registre et méthode",
        "",
        "Quatrième exécution historique, diagnostics compris : G7 complète, G8 en échec,",
        "FIX2 diagnostique, puis G8R2. Registre et reçu créés exclusivement avant lancement ;",
        "un second essai est refusé avant tout accès réservé. Plan historique FR inchangé :",
        "hybrid et hybrid_camembert, seuil 0,30 ; contrôle 0,10, bootstrap apparié 2000 tirages,",
        "graine 45, marges précision 0,02 et surmasquage 0,01. Une seule exécution par profil ;",
        "les mêmes prédictions alimentent métriques et intervalles. Aucun autre CLI de mesure.",
        "",
        "Le script de provenance seul hache le challenge, identique au hash historique.",
        "Aucune lecture manuelle ; test et C3 ni ouverts, ni hachés, ni remesurés. Archives",
        "antérieures préservées. Aucune sortie brute du worker conservée. Ce challenge déjà",
        "connu ne constitue pas une nouvelle validation aveugle.",
        "",
        "## Challenge FR courant",
        "",
        "| Profil | Couverts | Fuite caractères | Précision partielle | Surmasquage caractères |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in current.items():
        coverage, partial = row["coverage"], row["partial"]
        lines.append(
            f"| {name} | {coverage['entities_fully_covered']}/{coverage['reference_entities']} | "
            f"{coverage['leaked_characters']}/{coverage['reference_characters']} | "
            f"{partial['precision']:.6f} | {coverage['non_sensitive_characters_masked']} |"
        )
    lines += ["", "Critères Enhanced contre Standard (plan figé) :", ""]
    for key in (
        "lower_leakage",
        "higher_full_coverage",
        "precision_within_margin",
        "over_masking_within_margin",
        "met",
    ):
        lines.append(f"- {key} : {criterion[key]}.")
    lines += [
        "",
        "Différences appariées, candidat Enhanced moins référence Standard :",
        "",
        "| Stade | Mesure | Différence | IC95 | Exclut zéro |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in report["paired_differences"]:
        lines.append(
            f"| {row['stage']} | {row['metric']} | {row['estimate']:.6f} | "
            f"[{row['lower']:.6f} ; {row['upper']:.6f}] | {row['excludes_zero']} |"
        )
    lines += [
        "",
        "Les intervalles marginaux, métriques exactes/partielles, CUSTOM/LOCATION, alertes",
        "et coûts par processus figurent dans [le rapport complet](challenge/robustness.md).",
        "Les alertes ne masquent rien. Aucun seuil n'est rechoisi.",
        "",
        "## Comparaison historique, sans nouvelle mesure G7",
        "",
        "| Profil | Précision G7 vers courant | Rappel G7 vers courant | Fuite G7 vers courant |",
        "| --- | --- | --- | --- |",
    ]
    for name, row in comparison.items():
        old, new = row["historical_g7"], row["current"]
        lines.append(
            f"| {name} | {old['precision']:.6f} vers {new['precision']:.6f} | "
            f"{old['recall']:.6f} vers {new['recall']:.6f} | "
            f"{old['leaked_characters']} vers {new['leaked_characters']} |"
        )
    lines += [
        "",
        "Même empreinte de corpus. G7 n'a pas enregistré couverture complète et surmasquage :",
        "ces valeurs et les intervalles appariés G7/courant restent indisponibles. Aucune",
        "reconstruction depuis les agrégats et aucune significativité entre rapports distincts.",
        "",
        "## Résultats G8 réutilisés comme histoire",
        "",
        "Code historique e3d13bd, aucun de ces chiffres n'est une nouvelle validation de FIX4.",
        "Sur C3 FR, Standard 95/105 couverts et 139/2042 caractères exposés ; Enhanced 96/105",
        "et 130/2042. Les trois critères comparatifs FR de G8 restent historiquement remplis.",
        "Test historique G8 : 93/93 couverts et 0/1889 exposés pour les deux profils.",
        "C3 EN : Standard 78/100 et 235/2285, Enhanced 88/100 et 115/2285. Précision partielle",
        "0,834862 vers 0,700000 : perte 0,134862, supérieure à 0,02. Enhanced EN conserve donc",
        "son NO-GO de recommandation ; Standard EN reste expérimental avec réserves fortes.",
        "",
        "Standard reste le repli, avec revue humaine complète et ajouts manuels. La",
        "pseudonymisation n'est pas une anonymisation et les résultats ne garantissent pas",
        "une absence de fuite sur tout document. Corpus fictifs petits, auteurs corrélés,",
        "challenge déjà connu et continuité des jetons limitée restent des réserves explicites.",
        "Aucun code applicatif corrigé pendant cette gate, aucun paquet installé, tag, push ou R8.",
        "",
    ]
    with (OUT / "report.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    old_hashes = read("results/gate8-resume/scope.json")["historical_artifacts_sha256"]
    assert all(digest(ROOT / path) == expected for path, expected in old_hashes.items())
    audited = []
    for path in sorted(OUT.rglob("*.json")):
        assert_aggregates(json.loads(path.read_text(encoding="utf-8")))
        audited.append(path.relative_to(ROOT).as_posix())
    save(
        "export-audit.json",
        {
            "aggregates_only": True,
            "audited_json": audited,
            "historical_artifacts_unchanged": len(old_hashes),
        },
    )
    print(json.dumps(verdicts, ensure_ascii=True))


if __name__ == "__main__":
    main()
