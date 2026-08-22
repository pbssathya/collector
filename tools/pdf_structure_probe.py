from __future__ import annotations

import json
import sys

from collector.domains.registry import DomainRegistry
from collector.extractors.pdf import extract_pdf_structure


DOMAIN = "games/chance/lottery/kerala"
DEFAULT_SOURCES = ["75357", "74290", "75170"]


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

        structure = extract_pdf_structure(document.content)
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
