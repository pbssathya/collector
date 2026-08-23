from __future__ import annotations

import re
import sys
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from document_portal_search_contract_gate import (
    BASE_HOST,
    ContractParser,
    START_URL,
    build_payload,
    norm,
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
RESULT_MARKERS = (
    "lottery no",
    "draw held on",
    "draw held",
    "1st prize",
    "first prize",
    "ticket no",
)
TOKEN_STOP = {
    "document",
    "documents",
    "details",
    "government",
    "kerala",
    "lottery",
    "lotteries",
    "date",
    "download",
    "view",
    "more",
}


def strict_same_origin(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc == BASE_HOST


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


def target_dates(text: str) -> list[date]:
    return [value for value in parse_dates(text) if TARGET_START <= value <= TARGET_END]


def lottery_evidence(text: str) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in LOTTERY_TERMS)


def strong_result_evidence(text: str) -> bool:
    lower = text.lower()
    return lottery_evidence(text) and any(marker in lower for marker in RESULT_MARKERS)


def strip_html(fragment: str) -> str:
    without_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", fragment, flags=re.I | re.S)
    without_style = re.sub(r"<style\b[^>]*>.*?</style>", " ", without_script, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", without_style)).split())


def enclosing_fragment(html_text: str, match_start: int, match_end: int) -> str:
    for tag in ("tr", "li", "div"):
        left = html_text.rfind(f"<{tag}", 0, match_start)
        right = html_text.find(f"</{tag}>", match_end)
        if left >= 0 and right >= 0 and right - left <= 12000:
            return html_text[left : right + len(tag) + 3]
    left = max(0, match_start - 1200)
    right = min(len(html_text), match_end + 1200)
    return html_text[left:right]


def search_result_details(base_url: str, html_text: str) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"href=[\"']([^\"']*/documentdetails/[^\"'#?]+(?:[?#][^\"']*)?)[\"']",
        flags=re.I,
    )
    for match in pattern.finditer(html_text):
        absolute = urljoin(base_url, match.group(1))
        if not strict_same_origin(absolute) or absolute in seen:
            continue
        seen.add(absolute)
        context = strip_html(enclosing_fragment(html_text, match.start(), match.end()))
        results.append(
            {
                "url": absolute,
                "context": context,
                "lottery": lottery_evidence(context),
                "dates": target_dates(context),
            }
        )
    return results


def direct_pdf_links(base_url: str, html_text: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    pattern = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", flags=re.I)
    for match in pattern.finditer(html_text):
        absolute = urljoin(base_url, match.group(1))
        if not strict_same_origin(absolute):
            continue
        lower = absolute.lower()
        if not (
            lower.endswith(".pdf")
            or "/porteddata/extensionpdf/" in lower
            or ("/documents/" in lower and ".pdf" in lower)
        ):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        context = strip_html(enclosing_fragment(html_text, match.start(), match.end()))
        results.append({"url": absolute, "context": context})
    return results


def significant_tokens(text: str) -> set[str]:
    tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9\u0D00-\u0D7F'-]{4,}", text)
    }
    return {token for token in tokens if token not in TOKEN_STOP and not token.isdigit()}


def context_overlap(left: str, right: str) -> int:
    return len(significant_tokens(left) & significant_tokens(right))


def pdf_text(content: bytes) -> str:
    structure = extract_pdf_structure(content)
    return "\n".join(str(line.get("text", "")) for line in iter_pdf_lines(structure))


def main() -> int:
    print("=== GOVERNMENT DOCUMENT PORTAL — FOCUSED RETRIEVAL ROUTE GATE ===")
    print("preservation: NO")
    print("mutation: NO")
    print("retrieval: read-only official HTTP(S) routes only")
    print("target window: 2017-01-01 -> 2017-08-22")
    print("confirmation requires target evidence in the search row + lottery-result evidence in the PDF\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 GovernmentDocumentPortalFocusedGate"})

    surface = session.get(START_URL, timeout=30)
    print("1. Surface:", surface.status_code, surface.url, len(surface.content), "bytes")
    surface.raise_for_status()

    parser = ContractParser()
    parser.feed(surface.text)
    if not parser.forms:
        raise SystemExit("No search form discovered on the official portal surface.")

    form = parser.forms[0]
    action = urljoin(surface.url, str(form.get("action") or surface.url))
    if not strict_same_origin(action):
        raise SystemExit(f"Refusing non-HTTP(S) or cross-origin search action: {action}")

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

    details = search_result_details(result.url, result.text)
    contextual = [item for item in details if item["lottery"] and item["dates"]]

    print("\n3. Search-result document routes")
    print("   document-detail routes:", len(details))
    print("   rows with lottery + target-window date evidence:", len(contextual))
    for item in contextual[:30]:
        print("      TARGET ROW")
        print("         url:", item["url"])
        print("         dates:", ", ".join(d.isoformat() for d in item["dates"][:8]))
        print("         row context:", str(item["context"])[:900])

    print("\n4. Focused detail/PDF validation")
    confirmed: list[dict[str, object]] = []
    reachable_details = 0
    candidate_pdfs = 0
    fetched_pdfs = 0
    parsed_pdfs = 0
    textless_pdfs = 0
    rejected_pdfs = 0
    failures: list[str] = []

    for item in contextual:
        detail_url = str(item["url"])
        try:
            response = session.get(detail_url, timeout=30)
        except Exception as exc:
            failures.append(f"{detail_url} | {exc!r}")
            continue
        if response.status_code != 200:
            failures.append(f"{detail_url} | HTTP {response.status_code}")
            continue

        reachable_details += 1
        pdf_links = direct_pdf_links(response.url, response.text)
        candidate_pdfs += len(pdf_links)

        ranked: list[tuple[int, dict[str, str]]] = []
        for pdf in pdf_links:
            score = context_overlap(str(item["context"]), pdf["context"])
            ranked.append((score, pdf))
        ranked.sort(key=lambda pair: pair[0], reverse=True)

        # A generic category/list page may expose dozens of unrelated current PDFs.
        # Only inspect links whose local metadata overlaps the target search row.
        selected = [pair for pair in ranked if pair[0] > 0][:3]
        if not selected and len(ranked) == 1:
            selected = ranked

        print("   target detail:", detail_url)
        print("      direct PDFs on page:", len(pdf_links))
        print("      PDFs selected by row-context overlap:", len(selected))

        for score, pdf in selected:
            pdf_url = pdf["url"]
            fetched_pdfs += 1
            try:
                pdf_response = session.get(pdf_url, timeout=30)
            except Exception as exc:
                failures.append(f"{pdf_url} | {exc!r}")
                continue
            if pdf_response.status_code != 200:
                failures.append(f"{pdf_url} | HTTP {pdf_response.status_code}")
                continue
            is_pdf = pdf_response.content.startswith(b"%PDF") or "application/pdf" in (
                pdf_response.headers.get("content-type") or ""
            ).lower()
            if not is_pdf:
                failures.append(f"{pdf_url} | not a PDF response")
                continue

            try:
                text = pdf_text(pdf_response.content)
            except Exception as exc:
                failures.append(f"{pdf_url} | PDF parse {exc!r}")
                continue
            parsed_pdfs += 1
            compact_pdf = norm(text)
            if not compact_pdf:
                textless_pdfs += 1
                print("      TEXTLESS PDF candidate:", pdf_response.url)
                continue

            pdf_dates = target_dates(compact_pdf)
            strong_pdf = strong_result_evidence(compact_pdf)
            if not strong_pdf:
                rejected_pdfs += 1
                print("      rejected non-result PDF:", pdf_response.url, "| overlap:", score)
                continue

            evidence_dates = pdf_dates or list(item["dates"])
            confirmed.append(
                {
                    "detail_url": detail_url,
                    "pdf_url": pdf_response.url,
                    "dates": evidence_dates,
                    "row_context": item["context"],
                    "overlap": score,
                    "pdf_text_chars": len(compact_pdf),
                }
            )
            print("   CONFIRMED RESULT ROUTE")
            print("      detail:", detail_url)
            print("      pdf:", pdf_response.url)
            print("      row overlap:", score)
            print("      dates:", ", ".join(d.isoformat() for d in evidence_dates[:8]))
            print("      PDF text chars:", len(compact_pdf))

    unique_confirmed: list[dict[str, object]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for item in confirmed:
        pair = (str(item["detail_url"]), str(item["pdf_url"]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        unique_confirmed.append(item)

    print("\n5. Confirmed target-window lottery-result retrieval evidence")
    print("   confirmed result routes:", len(unique_confirmed))
    for item in unique_confirmed[:30]:
        print("      detail URL:", item["detail_url"])
        print("      PDF URL:", item["pdf_url"])
        print("      target dates:", ", ".join(d.isoformat() for d in item["dates"][:10]))
        print("      row context:", str(item["row_context"])[:700])
        print("      row/PDF context overlap:", item["overlap"])
        print("      PDF text chars:", item["pdf_text_chars"])

    print("\n=== RETRIEVAL ROUTE GATE SUMMARY ===")
    print("official portal reachable: YES")
    print("same-origin search accepted: YES")
    print("document-detail routes returned:", len(details))
    print("search-result rows with lottery + target date:", len(contextual))
    print("reachable target document-detail routes:", reachable_details)
    print("direct PDF links exposed on target pages:", candidate_pdfs)
    print("PDFs fetched after row-context filtering:", fetched_pdfs)
    print("PDFs parsed with existing extractor:", parsed_pdfs)
    print("PDFs with no extractable text:", textless_pdfs)
    print("non-result PDFs rejected:", rejected_pdfs)
    print("confirmed pre-Aug 2017 lottery-result routes:", len(unique_confirmed))
    print("failures:", len(failures))
    for failure in failures[:12]:
        print("   ", failure)

    if unique_confirmed:
        verdict = "YES"
    elif contextual:
        verdict = "PARTIAL — official target search rows exist, but no lottery-result PDF was confirmed"
    else:
        verdict = "NO — prior page-level signal was not tied to target lottery result rows"
    print("pre-Aug 2017 official lottery-result retrieval route proven:", verdict)
    print("No Collector result or Memory state was changed by this gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
