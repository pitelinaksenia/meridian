"""Lossless repacking of uploaded PDFs for page-by-page loading on the site."""

import logging
import os

logger = logging.getLogger(__name__)

# a repacked file a bit larger than the original is still fine; much larger means a bad result
MAX_GROWTH = 1.05
# for a tiny PDF the object stream overhead is more than 5%, and irrelevant
GROWTH_ALLOWANCE = 64 * 1024


def optimize_pdf(src: str, dst: str) -> bool:
    """
    Writes `src` to `dst` with small objects grouped into object streams.

    The site reader (pdf.js) opens a PDF with range requests and, on open,
    reads the dictionary of every page. In a typical PDF those dictionaries
    sit between the page images all over the file: for a 250 MB scan it
    meant 135 requests and 39 MB before the first page. In object streams
    they take a couple of chunks: 12 requests and 8.5 MB, i.e. only the
    images of the pages on screen. Content and quality do not change.

    False — keep the original: the file is broken, encrypted, or the result is larger.
    """
    import pikepdf

    try:
        with pikepdf.open(src) as pdf:
            pdf.save(dst, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    except Exception:
        logger.exception("Could not repack PDF")
        return False
    size = os.path.getsize(src)
    return os.path.getsize(dst) <= max(size * MAX_GROWTH, size + GROWTH_ALLOWANCE)
