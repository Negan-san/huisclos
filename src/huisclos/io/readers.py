"""Lit localement les documents avant la détection des données sensibles.

Les octets TXT, DOCX et PDF natifs deviennent un texte Unicode normalisé.
Les limites et les erreurs sont renvoyées à l'interface par des codes stables.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal
from unicodedata import normalize

from docx import Document
from docx.blkcntnr import BlockItemContainer
from docx.document import Document as DocumentObject
from docx.table import Table
from pypdf import PdfReader

from huisclos.io.read_quality import ReadQuality, docx_quality, pdf_quality

SourceType = Literal["txt", "docx", "pdf", "paste"]
ErrorCode = Literal[
    "unsupported_type",
    "too_large",
    "too_long",
    "empty",
    "encoding",
    "docx_invalid",
    "pdf_encrypted",
    "pdf_no_text",
    "pdf_invalid",
]
MAX_CHARS = 200_000


@dataclass(frozen=True)
class ReadResult:
    """Contient le texte prêt pour la détection et les informations de lecture."""

    text: str
    source_type: SourceType
    warnings: tuple[str, ...]
    char_count: int
    quality: ReadQuality = ReadQuality()


class DocumentReadError(Exception):
    """Signale une lecture refusée par un code que l'interface peut traduire."""

    def __init__(self, code: ErrorCode, quality: ReadQuality | None = None) -> None:
        """Conserve le code reçu sans inclure le contenu du document dans l'erreur."""
        self.code = code
        self.quality = quality if quality is not None else ReadQuality()
        self.warnings = self.quality.warning_codes()
        super().__init__(code)


def _normalize_text(text: str) -> str:
    """Renvoie le texte en NFC avec des sauts de ligne LF, sans changer les espaces."""
    return normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def _result(
    text: str,
    source_type: SourceType,
    max_chars: int,
    warnings: tuple[str, ...] = (),
    quality: ReadQuality | None = None,
) -> ReadResult:
    """Normalise le texte reçu et renvoie le résultat après contrôle de sa longueur."""
    text = _normalize_text(text)
    quality = quality if quality is not None else ReadQuality(status="complete")
    if len(text) > max_chars:
        raise DocumentReadError("too_long")
    if not text.strip():
        raise DocumentReadError("empty", quality)
    return ReadResult(text, source_type, warnings, len(text), quality)


def _read_txt(data: bytes) -> tuple[str, tuple[str, ...]]:
    """Décode les octets en UTF-8, sinon en cp1252 avec un code d'avertissement."""
    try:
        return data.decode("utf-8-sig"), ()
    except UnicodeDecodeError:
        try:
            return data.decode("cp1252"), ("encoding_cp1252",)
        except UnicodeDecodeError as exc:
            raise DocumentReadError("encoding") from exc


def _container_lines(container: DocumentObject | BlockItemContainer) -> list[str]:
    """Renvoie paragraphes et tableaux du conteneur reçu dans leur ordre XML."""
    lines: list[str] = []
    for block in container.iter_inner_content():
        lines.extend(_table_lines(block) if isinstance(block, Table) else [block.text])
    return lines


def _table_lines(table: Table) -> list[str]:
    """Renvoie les lignes d'un tableau, avec chaque cellule fusionnée lue une fois."""
    lines: list[str] = []
    seen_cells: set[object] = set()
    for row in table.rows:
        values: list[str] = []
        for cell in row.cells:
            # Word répète une même cellule XML aux positions qu'elle occupe.
            if cell._tc in seen_cells:
                continue
            seen_cells.add(cell._tc)
            values.append("\n".join(_container_lines(cell)))
        if values:
            lines.append(" | ".join(values))
    return lines


def _read_docx(data: bytes) -> tuple[str, ReadQuality]:
    """Extrait le corps, les tableaux et les en-têtes des octets DOCX reçus."""
    try:
        quality = docx_quality(data)
        document = Document(BytesIO(data))
        lines = _container_lines(document)
        seen_headers: set[str] = set()
        for section in document.sections:
            # Les variantes première page et pages paires peuvent contenir des noms.
            for container in (
                section.header,
                section.first_page_header,
                section.even_page_header,
                section.footer,
                section.first_page_footer,
                section.even_page_footer,
            ):
                text = _normalize_text("\n".join(_container_lines(container)))
                # Les sections partagent souvent la même définition d'en-tête.
                if text.strip() and text not in seen_headers:
                    seen_headers.add(text)
                    lines.append(text)
        return "\n".join(lines), quality
    except Exception as exc:
        # Les fichiers mal formés provoquent des erreurs ZIP, XML ou de structure.
        raise DocumentReadError("docx_invalid") from exc


def _read_pdf(data: bytes, max_chars: int) -> tuple[str, ReadQuality]:
    """Extrait le texte natif et signale les pages douteuses sans effectuer d'OCR."""
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise DocumentReadError("pdf_encrypted")
        pages: list[str] = []
        char_count = 0
        useful_counts: list[int] = []
        for page in reader.pages:
            text = _normalize_text(page.extract_text() or "")
            char_count += len(text) + (2 if pages else 0)
            if char_count > max_chars:
                raise DocumentReadError("too_long")
            useful_counts.append(sum(char.isprintable() and not char.isspace() for char in text))
            pages.append(text)
        if not any(useful_counts):
            raise DocumentReadError("pdf_no_text", pdf_quality(useful_counts))
        return "\n\n".join(pages), pdf_quality(useful_counts)
    except DocumentReadError:
        raise
    except Exception as exc:
        raise DocumentReadError("pdf_invalid") from exc


def read_document(
    filename: str,
    data: bytes,
    max_bytes: int = 5_000_000,
    max_chars: int = MAX_CHARS,
) -> ReadResult:
    """Lit les octets du fichier nommé et renvoie le texte contrôlé pour le pipeline.

    Les limites portent sur les octets reçus puis sur le texte normalisé.
    Les avertissements sont des codes destinés à être traduits par l'interface.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".docx", ".pdf"}:
        raise DocumentReadError("unsupported_type")
    if len(data) > max_bytes:
        raise DocumentReadError("too_large")
    if not data:
        raise DocumentReadError("empty")
    if suffix == ".txt":
        text, warnings = _read_txt(data)
        return _result(text, "txt", max_chars, warnings)
    if suffix == ".docx":
        text, quality = _read_docx(data)
        return _result(text, "docx", max_chars, quality.warning_codes(), quality)
    text, quality = _read_pdf(data, max_chars)
    return _result(text, "pdf", max_chars, quality.warning_codes(), quality)


def read_pasted_text(text: str, max_chars: int = MAX_CHARS) -> ReadResult:
    """Renvoie le texte collé normalisé, non vide et limité comme un fichier lu."""
    return _result(text, "paste", max_chars)
