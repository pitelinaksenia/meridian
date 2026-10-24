"""Plain text of an uploaded book or collection file, for full-text search."""

import html
import io
import logging
import re
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

PLAIN_EXT = {"txt", "md", "markdown"}
MARKUP_EXT = {"fb2", "html", "htm", "xml"}
PDF_EXT = {"pdf"}


def decode(data: bytes) -> str:
    """UTF-16 by BOM, then UTF-8, then the charset the file declares, then Windows-1251."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    declared = re.search(rb'(?:encoding|charset)=["\']?([\w-]+)', data[:1024])
    if declared:
        try:
            return data.decode(declared.group(1).decode("ascii"))
        except (LookupError, UnicodeDecodeError):
            pass
    return data.decode("cp1251", errors="replace")


def strip_markup(text: str) -> str:
    # fb2 keeps the cover and illustrations as base64 inside <binary>
    text = re.sub(r"<binary\b.*?</binary>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text(field_file) -> str:
    """Text of a FileField value; empty for audio, epub, docx and unreadable files."""
    if not field_file:
        return ""
    ext = PurePosixPath(field_file.name).suffix.lower().lstrip(".")
    if ext not in PLAIN_EXT | MARKUP_EXT | PDF_EXT:
        return ""
    try:
        with field_file.open("rb") as f:
            data = f.read()
        if ext in PDF_EXT:
            text = pdf_text(data)
        else:
            text = decode(data)
            if ext in MARKUP_EXT:
                text = strip_markup(text)
    except Exception:
        # a broken file must not break saving in the admin
        logger.exception("Could not extract text from %s", field_file.name)
        return ""
    # NUL is not allowed in PostgreSQL text
    return re.sub(r"[ \t\r\f\v]+", " ", text).replace("\x00", "").strip()
