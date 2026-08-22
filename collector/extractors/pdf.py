"""Structured PDF extraction.

This module preserves document layout observations (pages, lines, spans, and
coordinates) without assigning domain meaning to them.
"""

from __future__ import annotations

from typing import Any, Iterator

import pymupdf


def extract_pdf_structure(content: bytes) -> dict[str, Any]:
    """Extract a PDF into a page/line/span representation."""
    document = pymupdf.open(stream=content, filetype="pdf")
    pages: list[dict[str, Any]] = []

    try:
        for page_number, page in enumerate(document, start=1):
            page_dict = page.get_text("dict")
            lines: list[dict[str, Any]] = []

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    text = "".join(span.get("text", "") for span in spans).strip()
                    if not text:
                        continue

                    lines.append(
                        {
                            "text": text,
                            "bbox": line.get("bbox"),
                            "spans": [
                                {
                                    "text": span.get("text", ""),
                                    "bbox": span.get("bbox"),
                                    "size": span.get("size"),
                                    "font": span.get("font"),
                                }
                                for span in spans
                            ],
                        }
                    )

            pages.append({"page": page_number, "lines": lines})
    finally:
        document.close()

    return {"pages": pages}


def iter_pdf_lines(structure: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield text lines from an extracted PDF in reading order."""
    for page in structure.get("pages", []):
        page_number = page.get("page")
        for line in page.get("lines", []):
            yield {"page": page_number, **line}
