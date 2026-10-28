"""Sonde FIX2 : structures pièges fictives passées par les stades réels du harnais G8.

Entrées : textes fictifs construits ici, profils FR hybrid et hybrid_camembert, seuil 0,30.
Sorties : une ligne par fixture et profil (stade atteint, classe d'erreur, lieu dans le code).
Aucun corpus réservé n'est lu ; les valeurs étant fictives, le lieu exact peut être affiché.
"""

import json
import sys
import traceback
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from scripts import evaluate_robustness as pilot  # noqa: E402
from scripts import gate8_measure  # noqa: E402

BASE = (
    "Cabinet Valmorand Avocats\n12 rue des Tilleuls, 69003 Lyon\n"
    "Lyon, le 3 mars 2026\n\nObjet : dossier RG n° 24/01873\n\n"
    "Maître Irène CASTELVAUX, avocate de M. Basile ORTEGRANT, né le "
    "14/02/1981 à Nantes, demeurant 7 allée des Ormes, 44000 Nantes, "
    "téléphone 06 12 34 56 78, courriel basile.ortegrant@exemple.fr.\n"
    "La société Brivane Logistique SAS, SIRET 732 829 320 00074, IBAN "
    "FR76 3000 6000 0112 3456 7890 189, est représentée par Mme Odile "
    "FERNIQUE. M. Ortegrant et Mme Fernique se sont rencontrés chez Brivane.\n"
)


def fixtures() -> dict[str, str]:
    """Construit les structures pièges, toutes fictives, à partir d'un courrier type."""
    name = "Basile ORTEGRANT"
    return {
        "base": BASE,
        "crlf": BASE.replace("\n", "\r\n"),
        "cr_only": BASE.replace("\n", "\r"),
        "nbsp": BASE.replace(" ", " ", 40),
        "narrow_nbsp": BASE.replace(" ", " ", 40),
        "soft_hyphen_name": BASE.replace("ORTEGRANT", "ORTE­GRANT"),
        "zero_width_name": BASE.replace("ORTEGRANT", "ORTE​GRANT"),
        "bom_start": "﻿" + BASE,
        "nfd": BASE.replace("è", "è").replace("é", "é"),
        "combining_start": "́" + BASE,
        "ligature": BASE.replace("fi", "ﬁ"),
        "file_name": BASE + "Pièce : attestation_ORTEGRANT_Basile.pdf\n",
        "token_like": BASE + "Voir [PERSONNE_1] et [SOCIETE_A] du projet.\n",
        "token_adjacent": BASE.replace(name, "[" + name + "]"),
        "astral": BASE.replace("Objet", "\U0001f4c4 Objet") + "\U0001f600\n",
        "tabs_ff": BASE.replace("\n\n", "\n\t\f\v\n"),
        "line_sep": BASE.replace("\n", " "),
        "guillemets": BASE + "« Basile ORTEGRANT » a signé.\n",
        "start_end_entity": name + " " + BASE + " " + name,
        "only_entity": name,
        "no_entity": "Le présent courrier ne contient aucune donnée.\n",
        "whitespace_only": " \n\t ",
        "empty": "",
        "long_doc": BASE * 40,
        "long_word": BASE + "Clé : " + "AbCdEf0123" * 300 + "\n",
        "unknown_chars": BASE + "中文" * 400 + "\n",
        "repeated_case": BASE + "ORTEGRANT, Ortegrant, ortegrant, O R T E G R A N T.\n",
        "dash_variants": BASE.replace("06 12 34 56 78", "06‑12‑34‑56‑78"),
        "control_chars": BASE.replace("\n", "\x00\n", 2),
        "apostrophes": BASE + "L’avocat d’Irène CASTELVAUX l'a dit.\n",
    } | alias_fixtures()


def alias_fixtures() -> dict[str, str]:
    """Pièges déclarés par C2 sans valeur réservée : sigles, surnoms et noms de fichiers."""
    sigle = BASE.replace("Brivane Logistique SAS,", "Brivane Logistique SAS (ci-après « BL »),")
    nickname = BASE.replace("M. Basile ORTEGRANT,", "M. Basile ORTEGRANT, dit « Bazou »,")
    return {
        "sigle": sigle + "BL conteste. La société BL et BL SAS paient.\n",
        "nickname": nickname + "Bazou a payé. Bazou ORTEGRANT aussi.\n",
        "ambiguous_alias": sigle + "Bertin Lavaud SARL (ci-après « BL ») répond. BL signe.\n",
        "alias_is_person_part": BASE.replace(
            "Mme Odile FERNIQUE.", "Mme Odile FERNIQUE (ci-après « Odile »)."
        )
        + "Odile signe ; Mme Odile MARTEL aussi.\n",
        "alias_is_other_person": BASE.replace(
            "Brivane Logistique SAS,", "Brivane Logistique SAS (ci-après « Fernique »),"
        )
        + "Fernique paie.\n",
        "alias_same_as_origin_case": BASE.replace(
            "Brivane Logistique SAS,", "Brivane Logistique SAS (ci-après « BRIVANE »),"
        )
        + "BRIVANE et Brivane paient.\n",
        "alias_in_file": sigle + "Pièces : contrat_BL_2024.pdf, BL.pdf, CV_Bazou-ORTEGRANT.docx.\n",
        "nested_alias": nickname.replace(
            "Brivane Logistique SAS,", "Brivane Logistique SAS (ci-après « Bazou »),"
        )
        + "Bazou proteste.\n",
        "alias_quotes_ascii": BASE.replace(
            "Brivane Logistique SAS,", 'Brivane Logistique SAS (ci-après dénommée "BLX"),'
        )
        + "BLX, BLX-France et blx.fr répondent.\n",
        "diminutive": BASE + "Basile, dit « Bas », et Irène, dite « Irè ».\n",
    }


def location(error: BaseException) -> str:
    """Dernier cadre de la pile situé dans le dépôt : chemin relatif, fonction et ligne."""
    frames = [
        frame
        for frame in traceback.extract_tb(error.__traceback__)
        if Path(frame.filename).resolve().is_relative_to(ROOT)
    ]
    if not frames:
        return "outside repository"
    frame = frames[-1]
    relative = Path(frame.filename).resolve().relative_to(ROOT).as_posix()
    return f"{relative}:{frame.name}:{frame.lineno}"


def probe(api: object, preset: str, text: str) -> dict[str, str]:
    """Exécute détection, substitution et contrôle final comme le worker G8, sans le capturer."""
    config, _ = pilot.configured(api.presets[preset], 0.3, "fr")
    lowered = replace(config, threshold=api.check_threshold(0.3))
    stage = "detection"
    try:
        detected = list(api.detect(text, config))
        stage = "pseudonymization"
        result = api.pseudonymize(text, detected)
        stage = "final_check"
        gate8_measure.final_alerts(api, result, text, lowered)
    except Exception as error:
        return {"stage": stage, "error": type(error).__name__, "where": location(error)}
    return {"stage": "done", "error": "", "where": ""}


def main() -> int:
    """Passe chaque fixture par les deux profils FR et écrit le registre JSON demandé."""
    api = pilot.load_api()
    rows = []
    for preset in ("hybrid", "hybrid_camembert"):
        for name, text in fixtures().items():
            rows.append({"profile": preset, "fixture": name} | probe(api, preset, text))
            print(json.dumps(rows[-1]), flush=True)
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out is not None:
        with out.open("x", encoding="utf-8") as handle:
            json.dump(rows, handle, indent=2)
            handle.write("\n")
    return int(any(row["error"] for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
