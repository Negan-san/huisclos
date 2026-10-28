"""Décrit les limites de l'extraction avant la détection des identifiants.

Entrées : pages extraites ou octets d'un DOCX local, jamais une pièce liée.
Sorties : état de complétude et codes d'avertissement sans contenu du document.
Ces informations accompagnent le texte transmis à la revue humaine.
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Literal
from xml.etree import ElementTree
from zipfile import ZipFile

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SHORT_PAGE_CHARS = 20


@dataclass(frozen=True)
class ReadQuality:
    """Décrit la complétude, les pages douteuses et les structures omises.

    Les pages commencent à un. Un état inconnu ne garantit jamais la complétude.
    L'état partiel désigne des structures DOCX que le lecteur ne restitue pas.
    """

    status: Literal["complete", "partial", "unknown"] = "unknown"
    empty_pages: tuple[int, ...] = ()
    short_pages: tuple[int, ...] = ()
    unsupported_structures: tuple[str, ...] = ()

    def warning_codes(self) -> tuple[str, ...]:
        """Renvoie des codes stables, avec seulement des numéros de pages en paramètre."""
        warnings = []
        for code, pages in (
            ("pdf_empty_pages", self.empty_pages),
            ("pdf_short_pages", self.short_pages),
        ):
            if pages:
                warnings.append(f"{code}:{','.join(str(page) for page in pages)}")
        warnings.extend(f"docx_{name}" for name in self.unsupported_structures)
        return tuple(warnings)


def pdf_quality(useful_counts: list[int]) -> ReadQuality:
    """Classe les pages selon leur texte utile, sans conclure qu'une page est un scan."""
    return ReadQuality(
        empty_pages=tuple(index for index, count in enumerate(useful_counts, 1) if count == 0),
        short_pages=tuple(
            index for index, count in enumerate(useful_counts, 1) if 0 < count < SHORT_PAGE_CHARS
        ),
    )


def docx_quality(data: bytes) -> ReadQuality:
    """Repère dans le ZIP local les structures connues que l'extraction ne couvre pas.

    Seuls les XML Word internes sont inspectés ; aucune relation externe n'est suivie.
    Les erreurs ZIP et XML remontent au lecteur, qui les traduit en docx_invalid.
    """
    found: set[str] = set()
    revisions = {
        "ins",
        "del",
        "moveFrom",
        "moveTo",
        "cellIns",
        "cellDel",
        "cellMerge",
        "numberingChange",
        "tblGridChange",
    }
    with ZipFile(BytesIO(data)) as archive:
        for name in archive.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            for element in ElementTree.fromstring(archive.read(name)).iter():
                if not element.tag.startswith(f"{{{WORD_NS}}}"):
                    continue
                tag = element.tag.split("}", 1)[1]
                if tag in {"footnoteReference", "endnoteReference"} or (
                    tag in {"footnote", "endnote"}
                    and element.get(f"{{{WORD_NS}}}type")
                    not in {"separator", "continuationSeparator"}
                ):
                    found.add("notes")
                if tag in {"comment", "commentReference", "commentRangeStart", "commentRangeEnd"}:
                    found.add("comments")
                if tag == "txbxContent":
                    found.add("text_boxes")
                if (
                    tag in revisions
                    or tag.endswith("PrChange")
                    or tag.startswith(
                        (
                            "moveFromRange",
                            "moveToRange",
                            "customXmlInsRange",
                            "customXmlDelRange",
                            "customXmlMoveFromRange",
                            "customXmlMoveToRange",
                        )
                    )
                ):
                    found.add("revisions")
                if tag in {"altChunk", "object", "sdt"}:
                    found.add("embedded_content")
    return ReadQuality(
        status="partial" if found else "unknown", unsupported_structures=tuple(sorted(found))
    )


def warning_parameters(warning: str) -> tuple[str, dict[str, str]]:
    """Sépare un code de ses pages validées pour la traduction de l'interface.

    Les anciennes alertes sans paramètre sont conservées. Aucun extrait utilisateur
    ne peut être introduit comme paramètre d'un avertissement de pages.
    """
    code, separator, pages = warning.partition(":")
    if separator and code in {"pdf_empty_pages", "pdf_short_pages"}:
        numbers = pages.split(",")
        if all(number.isascii() and number.isdecimal() and int(number) > 0 for number in numbers):
            return code, {"pages": ", ".join(numbers)}
    return warning, {}
