"""Plain text of an uploaded book or collection file, for full-text search."""

import html
import logging
import re
import shutil
import tempfile
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

PLAIN_EXT = {"txt", "md", "markdown"}
MARKUP_EXT = {"fb2", "html", "htm", "xml"}
PDF_EXT = {"pdf"}

# Enough for any book; protects the DB and memory from a pathological file
MAX_TEXT_CHARS = 5_000_000
# A text/fb2/html file larger than this is not a book anyway — read only the start
MAX_PLAIN_BYTES = 50 * 1024 * 1024


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


def pdf_text(stream) -> str:
    """Text of a PDF from a seekable file: pypdf loads objects on demand, not the whole file."""
    from pypdf import PdfReader

    parts, size = [], 0
    for page in PdfReader(stream).pages:
        # scans have little or no text; images are not decoded by extract_text
        text = page.extract_text() or ""
        parts.append(text)
        size += len(text)
        if size >= MAX_TEXT_CHARS:
            break
    return "\n".join(parts)


def extract_text(field_file) -> str:
    """Text of a FileField value; empty for audio, epub, docx and unreadable files."""
    if not field_file:
        return ""
    ext = PurePosixPath(field_file.name).suffix.lower().lstrip(".")
    if ext not in PLAIN_EXT | MARKUP_EXT | PDF_EXT:
        return ""
    try:
        with field_file.open("rb") as f:
            if ext in PDF_EXT:
                # a 200 MB scan must not sit in memory: copy it to disk in chunks
                with tempfile.TemporaryFile() as tmp:
                    shutil.copyfileobj(f, tmp, 1024 * 1024)
                    tmp.seek(0)
                    text = pdf_text(tmp)
            else:
                data = f.read(MAX_PLAIN_BYTES)
                if len(data) == MAX_PLAIN_BYTES:
                    # cut at a line break, not in the middle of a UTF-8 character
                    data = data[: data.rfind(b"\n") + 1] or data
                text = decode(data)
                if ext in MARKUP_EXT:
                    text = strip_markup(text)
    except Exception:
        # a broken file must not break saving in the admin
        logger.exception("Could not extract text from %s", field_file.name)
        return ""
    # NUL is not allowed in PostgreSQL text
    text = re.sub(r"[ \t\r\f\v]+", " ", text).replace("\x00", "").strip()
    return text[:MAX_TEXT_CHARS]
