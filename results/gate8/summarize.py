"""Assemble une synthèse pure des agrégats G8 déjà enregistrés.

Entrées : rapports aveugles et historiques, sans texte ni annotation individuelle.
Sorties : tableaux séparés par langue, coûts et comparaison historique marginale.
Aucun détecteur n'est importé ni réexécuté par ce rapport.
"""

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def read(path: Path) -> Any:
    """Lit exclusivement un rapport agrégé existant."""
    return json.loads(path.read_text(encoding="utf-8"))


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    """Présente des valeurs agrégées dans une table Markdown."""
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
        *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        "",
    ]


def interval(value: float, bounds: dict[str, float]) -> str:
    """Formate une estimation et son intervalle bootstrap à 95 %."""
    return f"{value:.4f} [{bounds['lower']:.4f}, {bounds['upper']:.4f}]"


def profile_summary(report: dict[str, Any], name: str) -> dict[str, Any]:
    """Rassemble tous les stades et dénominateurs d'un profil déjà mesuré."""
    partial = next(
        r
        for r in report["metrics_by_type"]
        if r["config"] == name and r["type"] == "micro" and r["mode"] == "partial"
    )
    exact = next(
        r
        for r in report["metrics_by_type"]
        if r["config"] == name and r["type"] == "micro" and r["mode"] == "exact"
    )
    coverage = next(
        r
        for r in report["coverage"]
        if r["config"] == name and r["scope"] == "evaluated" and r["stage"] == "pseudonymization"
    )
    separate = next(
        r
        for r in report["coverage"]
        if r["config"] == name
        and r["scope"] == "custom_location"
        and r["stage"] == "pseudonymization"
    )
    return {
        "partial": partial,
        "exact": exact,
        "coverage": coverage,
        "custom_location": separate,
        "historical_intervals": next(
            r for r in report["bootstrap_intervals"] if r["config"] == name
        ),
        "coverage_intervals": {
            r["metric"]: r
            for r in report["coverage_intervals"]
            if r["config"] == name and r["stage"] == "pseudonymization"
        },
        "alerts": next(r for r in report["final_check"] if r["config"] == name),
        "resources": report["metadata"]["profiles"][name]["resources"],
    }


def main() -> None:
    """Produit les tables depuis les seuls rapports, sans nouvelle mesure ni seuil."""
    from huisclos.evaluation.comparison import compare_result_folders

    for split in ("test", "challenge"):
        if (OUT / f"complete_{split}.json").is_file():
            compare_result_folders(
                OUT / "g7_archive", OUT / split, split, OUT / "historical_comparison"
            )
        else:
            assert (OUT / f"failed_{split}.json").is_file()
    summary = {}
    lines = [
        "# G8 : résultats agrégés et provenance",
        "",
        "Verdict global : NO-GO. Enhanced EN échoue à la marge de précision préenregistrée.",
        "Le challenge historique n'a pas de rapport exploitable ; son essai n'est pas répété.",
        "Les contrôles techniques et les gains FR mesurés sont conservés ; EN reste expérimental.",
        "G8-01 : panne injectée, prédictions perdues, xfail strict ; cause challenge inconnue.",
        "Détails et replis : docs/DECISIONS.md, D-G8-1.",
        "",
        (
            "Mesure indépendante du 28 octobre 2026, code métier gelé A4 dc5b041, HEAD "
            "de mesure e3d13bd."
        ),
        "Plans et harnais enregistrés avant tout chiffre réservé dans registration.json.",
        (
            "Les fichiers G7 sont conservés intégralement dans g7_archive, sans "
            "nouvelle mesure de leurs anciens splits."
        ),
        "",
        (
            "Une détection principale par document/profil/code, toutes les propositions "
            "substituées automatiquement."
        ),
        (
            "Les prédictions en mémoire alimentent métriques exactes/partielles, F2, "
            "couverture, fuite et intervalles."
        ),
        "Les relectures du contrôle final sont mesurées séparément ; les alertes ne masquent rien.",
        (
            "Bootstrap par document, 2000 tirages, graine 45 ; mêmes tirages pour les "
            "différences appariées."
        ),
        (
            "Aucun humain connaissant le gold n'est simulé. Aucun seuil n'est rechoisi "
            "après mesure aveugle."
        ),
        "",
        "G7 ne propose pas de véritable profil anglais : aucune référence EN G7 n'est publiée.",
        (
            "Les onze types historiques et le périmètre CUSTOM/LOCATION sont séparés. "
            "Aucun LOCATION dans C3."
        ),
        (
            "Les intervalles de précision/rappel/F2 sont ceux du mode partiel ; les "
            "métriques exactes sont ponctuelles."
        ),
        "",
    ]
    for dataset, title in (
        ("blind_fr", "Lot neuf FR"),
        ("blind_en", "Lot neuf EN"),
        ("test", "Test historique FR, quatrième mesure"),
        ("challenge", "Challenge historique FR, série G8 unique"),
    ):
        if not (OUT / dataset / "robustness.json").is_file():
            summary[dataset] = {"available": False, "failure": read(OUT / f"failed_{dataset}.json")}
            lines += [
                f"## {title}",
                "",
                "Non disponible : essai unique en échec (code 2).",
                "Aucun rapport courant exploitable ; aucune nouvelle détection autorisée.",
                "Agrégats G7 archivés ; aucun chiffre courant ni intervalle inventé.",
                "",
            ]
            continue
        report = read(OUT / dataset / "robustness.json")
        profiles = {name: profile_summary(report, name) for name in report["metadata"]["profiles"]}
        summary[dataset] = {
            "profiles": profiles,
            "metadata": report["metadata"],
            "criteria": report["engineering_criteria"],
            "paired_differences": report["paired_differences"],
        }
        lines += [
            f"## {title}",
            "",
            f"{report['metadata']['document_count']} documents ; corpus SHA-256 : "
            f"`{next(iter(report['metadata']['corpus_sha256'].values()))}`.",
            "",
        ]
        rows, coverage_rows, separate_rows, alert_rows, resource_rows = [], [], [], [], []
        for name, profile in profiles.items():
            partial, exact = profile["partial"], profile["exact"]
            bounds, coverage = profile["historical_intervals"], profile["coverage"]
            cis = profile["coverage_intervals"]
            rows.append(
                [
                    name,
                    f"{exact['precision']:.4f}",
                    f"{exact['recall']:.4f}",
                    interval(partial["precision"], bounds["precision"]),
                    interval(partial["recall"], bounds["recall"]),
                    interval(partial["f2"], bounds["f2"]),
                ]
            )
            coverage_rows.append(
                [
                    name,
                    f"{coverage['entities_fully_covered']}/{coverage['reference_entities']}",
                    interval(coverage["full_coverage_rate"], cis["full_coverage_rate"]),
                    f"{coverage['leaked_characters']}/{coverage['reference_characters']}",
                    interval(coverage["leaked_character_rate"], cis["leaked_character_rate"]),
                    f"{coverage['entities_partially_exposed']}/{coverage['entities_fully_exposed']}",
                    coverage["documents_with_any_exposure"],
                    f"{coverage['non_sensitive_characters_masked']}/{coverage['non_sensitive_characters']}",
                    interval(
                        coverage["non_sensitive_masked_rate"], cis["non_sensitive_masked_rate"]
                    ),
                ]
            )
            separate = profile["custom_location"]
            separate_rows.append(
                [
                    name,
                    f"{separate['entities_fully_covered']}/{separate['reference_entities']}",
                    separate["leaked_characters"],
                    separate["entities_partially_exposed"],
                    separate["entities_fully_exposed"],
                ]
            )
            alerts = profile["alerts"]
            alert_rows.append(
                [
                    name,
                    alerts["alerts"],
                    alerts["alerts_on_visible_references"],
                    alerts["alerts_elsewhere"],
                    f"{alerts['exposed_entities_alerted']}/{alerts['exposed_entities']}",
                ]
            )
            costs = profile["resources"]
            resource_rows.append(
                [
                    name,
                    f"{costs['load_seconds']:.2f}",
                    f"{costs['inference_seconds']:.2f}",
                    f"{costs['substitution_seconds']:.2f}",
                    f"{costs['final_check_seconds']:.2f}",
                    f"{costs['peak_rss_bytes'] / 2**20:.1f}",
                    costs["main_detection_calls"],
                ]
            )
        lines += table(
            [
                "Profil",
                "P exacte",
                "R exact",
                "P partielle [IC95]",
                "R partiel [IC95]",
                "F2 [IC95]",
            ],
            rows,
        )
        lines += table(
            [
                "Profil",
                "Couverts",
                "Couverture [IC95]",
                "Caractères exposés",
                "Fuite [IC95]",
                "Entités partielles/entières exposées",
                "Documents exposés",
                "Surmasquage caractères",
                "Taux [IC95]",
            ],
            coverage_rows,
        )
        lines += ["CUSTOM/LOCATION, hors comparaison principale :", ""]
        lines += table(
            [
                "Profil",
                "Couverts",
                "Caractères exposés",
                "Entités partielles exposées",
                "Entités entièrement exposées",
            ],
            separate_rows,
        )
        lines += ["Alertes finales sans masquage :", ""]
        lines += table(
            [
                "Profil",
                "Alertes",
                "Sur références visibles",
                "Ailleurs",
                "Entités exposées alertées",
            ],
            alert_rows,
        )
        lines += [
            (
                "Coûts par processus neuf, CPU, OMP/MKL demandés à deux threads, RSS échantillonné "
                "toutes les 20 ms."
            ),
            (
                "Les imports métier sont inclus au chargement ; démarrage de Python et "
                "imports du harnais exclus."
            ),
            "",
        ]
        lines += table(
            [
                "Profil",
                "Chargement s",
                "Inférence s",
                "Substitution s",
                "Contrôle s",
                "Pic RSS Mio",
                "Appels principaux",
            ],
            resource_rows,
        )
        lines += [
            f"[Rapport complet]({dataset}/robustness.md), [JSON]({dataset}/robustness.json).",
            "",
        ]
    lines += [
        "## Comparaison historique",
        "",
        (
            "[Test](historical_comparison/test_comparison.md). "
            "Challenge courant non disponible : essai en échec."
        ),
        (
            "Seuls Standard et Enhanced sont remesurés, comme préenregistré ; les "
            "ablations G7 restent archivées."
        ),
        (
            "Aucun intervalle apparié n'est inventé entre les séries historiques. Les "
            "métriques nouvelles absentes de G7 sont non disponibles."
        ),
        "",
        "## Contrôles et limites",
        "",
        (
            "1680 tests passent avant la mesure réservée ; modèles et environnements "
            "inchangés, pip check conforme."
        ),
        (
            "C3 suit A4 sans modification de logique ; seize sources et les plans ont "
            "des empreintes vérifiées."
        ),
        (
            "Les parcours UI FR/EN et documents FR/EN, payload exact, révocations et "
            "absence de table envoyée sont testés."
        ),
        (
            "Le repli de langue hors session est limité à AppTest pour tester Review en "
            "français ; le code de production reste intact."
        ),
        (
            "Les sondes Enhanced FR/EN passent en processus neufs, caches vides, réseau "
            "et écritures des documents bloqués."
        ),
        (
            "L'audit des littéraux conserve sa classification préalable et ses comptes "
            "bruts ; des recouvrements génériques ne prouvent pas une copie spécifique."
        ),
        (
            "Les corpus sont petits, fictifs et liés au style d'un seul auteur/famille "
            "de modèle. Aucun score ne garantit anonymat ou fuite nulle."
        ),
        (
            "Les coûts sont indicatifs sur cette machine. Les détails de versions et de "
            "poids sont dans provenance.json et les métadonnées de chaque profil."
        ),
        "",
    ]
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("G8 summary written from aggregate reports; no detection repeated.")


if __name__ == "__main__":
    main()
