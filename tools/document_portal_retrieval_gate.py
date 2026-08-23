from __future__ import annotations

import re
from collections import deque
from datetime import date, datetime
from urllib.parse import urljoin

import requests

from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines
from tools.document_portal_search_contract_gate import (
    BASE_HOST,
    ContractParser,
    START_URL,
    build_payload,
    norm,
    same_origin,
)

TARGET_START = date(2017, 1, 1)
TARGET_END = date(2017, 8, 22)
LOTTERY_TERMS = (
    "lottery",
    "lotteries",
    "bumper",
    "state lottery",
    "draw",
    "ഭാഗ്യക്കുറി",
)


def parse_dates(text: str) -> list[date]:
    found: list[date] = []
    seen: set[date] = set()
    patterns = (
        (r"\b(\d{2})[-/.](\d{2})[-/.](2017)\b", "dmy"),
        (r"\b(2017)[-/.](\d{2})[-/.](\d{2})\b", "ymd"),
    )
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text):
            try:
                if kind == "dmy":
                    day, month, year = map(int, match.groups())
                else:
                    year, month, day = map(int, match.groups())
                value = date(year, month, day)
            except ValueError:
                continue
            if value not in seen:
                seen.add(value)
                found.append(value)
    return sorted(found)


def target_date_evidence(text: str) -> list[date]:
    return [value for value in parse_dates(text) if TARGET_START <= value <= TARGET_END]


def lottery_evidence(text: str) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in LOTTERY_TERMS)


def candidate_links(base_url: str, html_text: str) -> list[str]:
    parser = ContractParser()
    parser.feed(html_text)
    urls: list[str] = []
    seen: set[str] = set()
    for href, label in parser.links:
        absolute = urljoin(base_url, href)
        if not same_origin(absolute):
            continue
        combined = f"{absolute} {label}".lower()
        if not any(
            token in combined
            for token in (
                "document",
                "deptdocument",
                "details",
                "download",
                "pdf",
                "file",
            )
        ):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        urls.append(absolute)
    return urls


def pdf_text(content: bytes) -> str:
    structure = extract_pdf_structure(content)
    return "\n".join(str(line.get("text", "")) for line in iter_pdf_lines(structure))


def main() -> int:
    print("=== GOVERNMENT DOCUMENT PORTAL — RETRIEVAL ROUTE GATE ===")
    print("preservation: NO")
    print("mutation: NO")
    print("retrieval: read-only same-origin GET/POST only")
    print("target window: 2017-01-01 -> 2017-08-22\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 GovernmentDocumentPortalRetrievalGate"})

    surface = session.get(START_URL, timeout=30)
    print("1. Surface:", surface.status_code, surface.url, len(surface.content), "bytes")
    surface.raise_for_status()

    parser = ContractParser()
    parser.feed(surface.text)
    if not parser.forms:
        raise SystemExit("No search form discovered on the official portal surface.")

    form = parser.forms[0]
    action = urljoin(surface.url, str(form.get("action") or surface.url))
    if not same_origin(action):
        raise SystemExit(f"Refusing cross-origin search action: {action}")

    payload, decisions = build_payload(form, "ymd")
    method = str(form.get("method") or "get").lower()
    print("2. Search contract")
    print("   method:", method)
    print("   action:", action)
    print("   filled:", ", ".join(decisions))

    if method == "post":
        result = session.post(action, data=payload, timeout=30)
    else:
        result = session.get(action, params=payload, timeout=30)
    print("   status:", result.status_code)
    print("   final URL:", result.url)
    print("   bytes:", len(result.content))
    result.raise_for_status()

    initial = candidate_links(result.url, result.text)
    print("\n3. Candidate retrieval routes from search response")
    print("   candidates:", len(initial))
    for url in initial[:25]:
        print("      ", url)

    queue: deque[tuple[str, int]] = deque((url, 0) for url in initial)
    visited: set[str] = set()
    confirmed: list[dict[str, object]] = []
    reachable = 0
    html_pages = 0
    pdfs = 0
    failures: list[str] = []
    max_fetches = 120

    print("\n4. Read-only route validation")
    while queue and len(visited) < max_fetches:
        url, depth = queue.popleft()
        if url in visited or not same_origin(url):
            continue
        visited.add(url)

        try:
            response = session.get(url, timeout=30)
        except Exception as exc:
            failures.append(f"{url} | {exc!r}")
            continue

        if response.status_code != 200:
            failures.append(f"{url} | HTTP {response.status_code}")
            continue

        reachable += 1
        content_type = (response.headers.get("content-type") or "").lower()
        is_pdf = response.content.startswith(b"%PDF") or "application/pdf" in content_type

        if is_pdf:
            pdfs += 1
            try:
                text = pdf_text(response.content)
            except Exception as exc:
                failures.append(f"{url} | PDF parse {exc!r}")
                continue

            dates = target_date_evidence(text)
            if lottery_evidence(text) and dates:
                confirmed.append(
                    {
                        "url": response.url,
                        "type": "pdf",
                        "dates": dates,
                        "snippet": norm(text)[:900],
                    }
                )
                print(
                    "   CONFIRMED PDF:",
                    response.url,
                    "| dates:",
                    ", ".join(d.isoformat() for d in dates[:6]),
                )
            continue

        html_pages += 1
        text = response.text
        dates = target_date_evidence(norm(text))
        if lottery_evidence(norm(text)) and dates:
            confirmed.append(
                {
                    "url": response.url,
                    "type": "html",
                    "dates": dates,
                    "snippet": norm(text)[:900],
                }
            )
            print(
                "   CONFIRMED HTML:",
                response.url,
                "| dates:",
                ", ".join(d.isoformat() for d in dates[:6]),
            )

        if depth < 1:
            for nested in candidate_links(response.url, text):
                if nested not in visited:
                    queue.append((nested, depth + 1))

    unique_confirmed: list[dict[str, object]] = []
    seen_confirmed: set[str] = set()
    for item in confirmed:
        key = str(item["url"])
        if key in seen_confirmed:
            continue
        seen_confirmed.add(key)
        unique_confirmed.append(item)

    print("\n5. Confirmed target-window lottery retrieval evidence")
    print("   confirmed routes:", len(unique_confirmed))
    for item in unique_confirmed[:30]:
        print("      type:", item["type"])
        print("      url:", item["url"])
        print("      target dates:", ", ".join(d.isoformat() for d in item["dates"][:10]))
        print("      snippet:", item["snippet"][:700])

    print("\n=== RETRIEVAL ROUTE GATE SUMMARY ===")
    print("official portal reachable: YES")
    print("same-origin search accepted: YES")
    print("candidate retrieval URLs from search:", len(initial))
    print("unique routes fetched:", len(visited))
    print("reachable routes:", reachable)
    print("HTML routes:", html_pages)
    print("PDF routes:", pdfs)
    print("confirmed pre-Aug 2017 lottery routes:", len(unique_confirmed))
    print("direct confirmed PDFs:", sum(1 for x in unique_confirmed if x["type"] == "pdf"))
    print("failures:", len(failures))
    for item in failures[:12]:
        print("   ", item)
    print(
        "pre-Aug 2017 official retrieval route proven:",
        "YES" if unique_confirmed else "NO",
    )
    print("No Collector result or Memory state was changed by this gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
