"""Vérifie le paquet local dans des processus neufs aux caches vides.

Entrées : actifs A4 inchangés, textes fictifs et copie liée avec auxiliaire retiré.
Sorties : comptes d'allers-retours et refus explicites, sans table sur disque.
Toutes les connexions sont bloquées avant le premier import métier.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT.parent / "pilotage/post_g7_assets"
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def worker(language: str, missing: bool) -> dict[str, Any]:
    """Charge le vrai profil, ou exige le refus avant inférence si un fichier manque."""
    import socket

    from scripts.gate8_measure import refuse_network

    socket.socket.connect = socket.socket.connect_ex = refuse_network
    socket.socket.sendto = socket.getaddrinfo = socket.create_connection = refuse_network
    from huisclos.config import profile_config
    from huisclos.detection import gliner
    from huisclos.detection.pipeline import (
        ModelUnavailableError,
        analyzer_for,
        check_camembert_snapshot,
        detect,
    )
    from huisclos.pseudonymize.case_memory import find_known
    from huisclos.pseudonymize.mapping import Mapping
    from huisclos.pseudonymize.reidentify import restore
    from huisclos.pseudonymize.tokens import pseudonymize

    if missing:
        try:
            if language == "fr":
                check_camembert_snapshot()
            else:
                gliner.prepare()
        except ModelUnavailableError as error:
            assert error.code == ("missing" if language == "fr" else "local_missing")
            return {"missing_file_refused": True, "code": error.code}
        raise AssertionError("Missing file accepted")
    texts = {
        "fr": ("M. Lucien FALVERAC signe.", "M. Lucien FALVERAC appelle Mme Alice BRENOUX."),
        "en": ("Mr Nolan FALVERICK signs.", "Mr Nolan FALVERICK calls Ms Alice BRENWICK."),
    }[language]
    config = profile_config("enhanced", language)
    analyzer_for(config)
    if language == "en":
        gliner.prepare()
    else:
        from huisclos.detection.camembert import load_pipeline

        load_pipeline()
    import builtins
    import io

    original_open = builtins.open

    def readonly(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        """Interdit toute écriture après le chargement des modèles, table comprise."""
        if any(character in mode for character in "wax+"):
            raise AssertionError("Write forbidden during document processing")
        return original_open(file, mode, *args, **kwargs)

    builtins.open = io.open = readonly
    one = pseudonymize(texts[0], detect(texts[0], config))
    two = pseudonymize(
        texts[1], detect(texts[1], config, find_known(texts[1], one.mapping)), known=one.mapping
    )
    assert restore(one.text, one.mapping).text == texts[0]
    reloaded = Mapping.from_json(two.mapping.to_json())
    assert restore(two.text, reloaded).text == texts[1]
    assert [e.token for e in reloaded.entities] == ["[PERSONNE_1]", "[PERSONNE_2]"]
    answer = " / ".join(e.token for e in reloaded.entities)
    assert restore(answer, reloaded).text == " / ".join(e.canonical for e in reloaded.entities)
    return {
        "exact_roundtrips": 2,
        "stable_tokens": True,
        "mixed_reply_restored": True,
        "document_write_guard": True,
        "network_blocked": True,
    }


def main() -> None:
    """Lance quatre processus séparés et contrôle les caches avant leur suppression."""
    if len(sys.argv) == 3:
        print(json.dumps(worker(sys.argv[1], sys.argv[2] == "missing")))
        return
    results = {}
    for language in ("fr", "en"):
        for missing in (False, True):
            with (
                tempfile.TemporaryDirectory(prefix="g8-package-") as package_name,
                tempfile.TemporaryDirectory(prefix="g8-empty-cache-") as cache_name,
            ):
                package, cache = Path(package_name).resolve(), Path(cache_name).resolve()
                assert package.name.startswith("g8-package-") and cache.name.startswith(
                    "g8-empty-cache-"
                )
                if missing:
                    (package / "manifest.json").write_bytes((ASSETS / "manifest.json").read_bytes())
                    for source in (ASSETS / "models").rglob("*"):
                        if source.is_file():
                            target = package / source.relative_to(ASSETS)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            os.link(source, target)
                    absent = (
                        package
                        / "models"
                        / (
                            "camembert_ner/sentencepiece.bpe.model"
                            if language == "fr"
                            else "mdeberta_v3_base/spm.model"
                        )
                    )
                    assert absent.resolve().is_relative_to(package)
                    absent.unlink()
                else:
                    package = ASSETS
                environment = os.environ | {
                    "PYTHONUTF8": "1",
                    "HUISCLOS_MODELS_DIR": str(package),
                    "HF_HOME": str(cache),
                    "HF_HUB_CACHE": str(cache / "hub"),
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "OMP_NUM_THREADS": "2",
                    "MKL_NUM_THREADS": "2",
                    "TOKENIZERS_PARALLELISM": "false",
                }
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        language,
                        "missing" if missing else "complete",
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                if completed.returncode:
                    raise RuntimeError(f"Offline probe failed: {language}, missing={missing}")
                key = language + ("_missing" if missing else "_complete")
                results[key] = json.loads(completed.stdout.strip().splitlines()[-1])
                assert not [p for p in cache.rglob("*") if p.is_file()]
                results[key]["cache_files"] = 0
                print(f"Offline {key}: OK", flush=True)
    path = Path(__file__).with_name("offline_guarded.json")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
