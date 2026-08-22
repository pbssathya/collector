from __future__ import annotations

import json
import sys

import fitz  # PyMuPDF

from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"
DEFAULT_SOURCES = ["75357", "74290", "75170"]


def extract_structure(content: bytes) -> dict:
    document = fitz.open(stream=content, filetype="pdf")
    pages = []

    for page_number, page in enumerate(document, start=1):
        page_dict = page.get_text("dict")
        lines = []

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

    return {"pages": pages}


def interesting_lines(structure: dict) -> list[dict]:
    wanted = ("LOTTERY", "DRAW", "held on", "scheduled on", "Prize", "BUMPER")
    found = []

    for page in structure["pages"]:
        for line in page["lines"]:
            text = line["text"]
            if any(token.lower() in text.lower() for token in wanted):
                found.append({"page": page["page"], **line})

    return found


def main() -> int:
    sources = sys.argv[1:] or DEFAULT_SOURCES
    registry = DomainRegistry()
    connector = registry.get_connector(DOMAIN)
    if connector is None:
        raise SystemExit(f"Missing connector: {DOMAIN}")

    print("=== STRUCTURED PDF EXTRACTION PROBE ===")
    print("engine: PyMuPDF")
    print("sources:", ", ".join(sources))

    for source in sources:
        print(f"\n--- SOURCE {source} ---")
        document = connector.retrieve(source)
        if not document or document.error or not document.content:
            print("FAILED TO RETRIEVE")
            if document is not None:
                print("error:", document.error)
            continue

        structure = extract_structure(document.content)
        lines = interesting_lines(structure)
        print("pdf bytes:", len(document.content))
        print("pages:", len(structure["pages"]))
        print("interesting lines:")
        for item in lines[:80]:
            print(
                json.dumps(
                    {"page": item["page"], "text": item["text"], "bbox": item["bbox"]},
                    ensure_ascii=False,
                )
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
