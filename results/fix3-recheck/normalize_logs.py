"""Normalise les journaux Windows sans perdre leurs octets d'origine.

Entrées : seuls les fichiers .log de ce dossier de recontrôle.
Sorties : copie brute .raw et journal UTF-8/LF sans espaces de fin de ligne.
Aucun résultat, compte ou message n'est remplacé pendant la normalisation.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent


def normalize() -> None:
    """Conserve les captures brutes puis écrit les copies lisibles pour diff --check."""
    for path in OUT.glob("*.log"):
        data = path.read_bytes()
        text = data.decode("utf-16" if data.startswith(b"\xff\xfe") else "utf-8")
        clean = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
        if clean.encode("utf-8") == data:
            continue
        raw = path.with_suffix(".log.raw")
        if not raw.exists():
            raw.write_bytes(data)
        path.write_text(clean, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    normalize()
