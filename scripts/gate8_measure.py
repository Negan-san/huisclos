"""Complète le pilote B1 sans changer les détecteurs mesurés.

Entrées : mêmes corpus et plans figés, dans des processus séparés hors ligne.
Sorties : agrégats B1, coûts et identité complète des modèles réellement utilisés.
Le contrôle actuel relit aussi le contexte source, comme l'interface A3.
Les prédictions restent en mémoire et servent à toutes les métriques.
"""

import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import evaluate_robustness as pilot  # noqa: E402


def refuse_network(*args: Any, **kwargs: Any) -> None:
    """Refuse connexions, DNS et datagrammes avant tout import métier."""
    raise OSError("G8: network forbidden")


def final_alerts(api: Any, result: Any, text: str, lowered: Any) -> list[list[int]] | None:
    """Mesure le contrôle réel du code courant, ou celui de la référence inchangée."""
    if lowered is None:
        return None
    try:
        from huisclos.pseudonymize.outbound_check import compose, document_alerts
    except ImportError:
        found = api.final_check(result, lambda value: api.detect(value, lowered))
    else:
        found = document_alerts(
            compose(result.text, ""), result, lambda value: api.detect(value, lowered), text
        )
    return [[item.start, item.end] for item in found]


def stage_outputs(
    texts: list[str], preset: str, threshold: float, language: str, api: Any = None
) -> dict[str, Any]:
    """Détecte une fois par document et réutilise les sorties pour tous les comptes.

    Le chargement est séparé de l'inférence principale, des substitutions et du contrôle.
    RSS est échantillonné toutes les vingt millisecondes dans le processus du profil.
    Aucune valeur ou position n'est écrite sur disque par ce processus.
    """
    import psutil

    process, samples, stop = psutil.Process(), [], threading.Event()

    def sample() -> None:
        """Conserve seulement la consommation mémoire du processus courant."""
        while not stop.is_set():
            samples.append(process.memory_info().rss)
            stop.wait(0.02)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    started = time.perf_counter()
    try:
        api = api or pilot.load_api()
        config, language_field = pilot.configured(api.presets[preset], threshold, language)
        from huisclos.detection import pipeline

        if hasattr(pipeline, "analyzer_for"):
            pipeline.analyzer_for(config)
        else:
            pipeline.build_analyzer(
                config.use_patterns,
                config.use_heuristics,
                config.use_spacy,
                config.use_camembert,
                config.spacy_model,
            )
        if config.use_camembert:
            from huisclos.detection.camembert import load_pipeline

            load_pipeline()
        if getattr(config, "use_gliner", False):
            from huisclos.detection.gliner import prepare

            prepare()
        loaded = time.perf_counter() - started
        lowered = (
            replace(config, threshold=api.check_threshold(threshold)) if api.final_check else None
        )
        documents, inference, substitution, checking = [], 0.0, 0.0, 0.0
        for text in texts:
            begin = time.perf_counter()
            detected = list(api.detect(text, config))
            inference += time.perf_counter() - begin
            begin = time.perf_counter()
            result = api.pseudonymize(text, detected)
            substitution += time.perf_counter() - begin
            begin = time.perf_counter()
            alerts = final_alerts(api, result, text, lowered)
            checking += time.perf_counter() - begin
            documents.append(
                {
                    "detections": [
                        [d.start, d.end, d.entity_type.value, d.score, d.source.value]
                        for d in detected
                    ],
                    "occurrences": [[o.start, o.end, len(o.original)] for o in result.occurrences],
                    "alerts": alerts,
                }
            )
        metadata = pilot.measured_metadata(config, language_field, lowered)
        metadata["versions"].update(
            {
                name: pilot.package_version(name)
                for name in (
                    "gliner",
                    "tokenizers",
                    "sentencepiece",
                    "fr_core_news_md",
                    "en_core_web_sm",
                )
            }
        )
        metadata["runtime_identity"] = (
            pipeline.model_identity(config) if hasattr(pipeline, "model_identity") else None
        )
        metadata["resources"] = {
            "load_seconds": loaded,
            "inference_seconds": inference,
            "substitution_seconds": substitution,
            "final_check_seconds": checking,
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_bytes": max(samples + [process.memory_info().rss]),
            "main_detection_calls": len(documents),
            "cpu_threads": 2,
            "machine": platform.platform(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "network_blocked": True,
        }
        return {"documents": documents, "metadata": metadata}
    finally:
        stop.set()
        thread.join()


def worker(checkout: Path) -> None:
    """Charge exclusivement le code du checkout demandé et répond par un tube privé."""
    for owner, name in (
        (socket, "getaddrinfo"),
        (socket, "create_connection"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "sendto"),
    ):
        setattr(owner, name, refuse_network)
    sys.path.insert(0, str((checkout / "src").resolve()))
    import huisclos

    if not Path(huisclos.__file__).resolve().is_relative_to((checkout / "src").resolve()):
        raise RuntimeError("Wrong source checkout")
    request = json.loads(sys.stdin.read())
    answer, sys.stdout = sys.stdout, sys.stderr
    payload = stage_outputs(
        request["texts"], request["preset"], request["threshold"], request["language"]
    )
    answer.write(json.dumps(payload) + "\n")
    answer.flush()


def run_separate(
    profile: dict[str, Any], texts: list[str], language: str, mode: str
) -> dict[str, Any]:
    """Exécute un profil une seule fois ; aucune erreur de bibliothèque n'est affichée."""
    command = [
        profile.get("python", sys.executable),
        "-I",
        "-X",
        "utf8",
        str(Path(__file__).resolve()),
        "--worker",
        str(Path(profile.get("checkout", ROOT)).resolve()),
    ]
    environment = (
        os.environ
        | pilot.OFFLINE
        | {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "TOKENIZERS_PARALLELISM": "false"}
    )
    completed = subprocess.run(
        command,
        input=json.dumps(
            {
                "texts": texts,
                "preset": profile["preset"],
                "threshold": profile["threshold"],
                "language": language,
            }
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"G8 worker failed: exit {completed.returncode}; no reserved output shown"
        )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def main(arguments: list[str] | None = None) -> int:
    """Lance B1 avec le worker corrigé ; les plans et métriques restent inchangés."""
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) == 2 and arguments[0] == "--worker":
        worker(Path(arguments[1]))
        return 0
    pilot.run_separate = run_separate
    pilot.stage_outputs = stage_outputs
    return pilot.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
