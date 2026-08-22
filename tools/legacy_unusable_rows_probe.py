from __future__ import annotations

import re
from urllib.parse import urljoin

import requests

from collector.domains.games.chance.lottery.kerala.parser import Parser
from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines


LEGACY_REPORT_URL = "https://result.keralalotteries.com/reports/resultentryeport1.php"

# These are the rows the live 2020 catalog probe could not turn into a usable
# parsed result. Keep the probe bounded to the exact evidence; do not widen it
# into another archive crawl.
CASES = [
    (83, 71455, "Karunya Plus KN-324"),
    (83, 70544, "Karunya Plus KN-309"),
    (133, 71396, "Monsoon Bumper 2020 BR-74"),
    (102, 71356, "Sthree Sakthi SS-217"),
    (102, 70520, "Sthree Sakthi SS-202"),
    (132, 70397, "Summer Bumper 2020 BR-72"),
    (117, 58868, "X'Mas New Year Bumper 2017-18 BR-59"),
]


def script_location(raw: bytes) -> str | None:
    text = raw.decode("utf-8", errors="replace")
    match = re.search(
        r"(?:document\.)?location\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        flags=re.I,
    )
    return match.group(1) if match else None


def response_summary(response: requests.Response) -> dict[str, object]:
    return {
        "status": response.status_code,
        "content_type": response.headers.get("Content-Type"),
        "bytes": len(response.content),
        "starts_pdf": response.content.startswith(b"%PDF"),
        "final_url": response.url,
    }


def structured_preview(content: bytes, limit: int = 18) -> list[str]:
    try:
        structure = extract_pdf_structure(content)
        result = []
        for item in iter_pdf_lines(structure):
            text = " ".join(str(item.get("text", "")).split())
            if text:
                result.append(text)
            if len(result) >= limit:
                break
        return result
    except Exception as exc:
        return [f"EXTRACTION ERROR: {exc!r}"]


def inspect_pdf(parser: Parser, response: requests.Response) -> None:
    print("pdf:", response_summary(response))
    if not response.content.startswith(b"%PDF"):
        print("raw preview:", repr(response.content[:240]))
        return

    print("structured first lines:")
    for index, line in enumerate(structured_preview(response.content), start=1):
        print(f"  {index:02d}: {line}")

    try:
        parsed = parser.parse(response.content)
    except Exception as exc:
        print("parser error:", repr(exc))
        return

    if not parsed:
        print("parser result: NONE")
        return

    print("parsed lottery name:", " ".join(str(parsed.lottery_name).split()))
    print("parsed draw date:", parsed.draw_date)
    print("parsed prize tiers:", len(parsed.prize_tiers))


def main() -> int:
    print("=== KERALA LEGACY UNUSABLE-ROW DIAGNOSTIC ===")
    print("preservation: NO")
    print("purpose: explain the exact seven rows excluded by the 2020 catalog probe before productionizing the bridge\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyUnusableDiagnostic"})
    parser = Parser()

    for option, drawno, label in CASES:
        print(f"--- {label} | lotterydet={option} | drawno={drawno} ---")
        redirector = session.get(
            LEGACY_REPORT_URL,
            params={"drawno1": drawno, "drawno": drawno},
            timeout=30,
            allow_redirects=False,
        )
        print("redirector:", response_summary(redirector))
        print("redirector raw:", repr(redirector.content[:240]))

        location = script_location(redirector.content)
        print("script location:", location)

        tested: set[str] = set()
        urls = []
        if location:
            urls.append(urljoin(redirector.url, location))

        # The working legacy transport consistently names the target PDF this way.
        # Test that same source-derived convention even when the redirector itself is
        # malformed or empty; this is diagnostic only, not production fallback yet.
        urls.append(urljoin(LEGACY_REPORT_URL, f"draw/tmp{drawno}.pdf"))

        for pdf_url in urls:
            if pdf_url in tested:
                continue
            tested.add(pdf_url)
            print("candidate pdf url:", pdf_url)
            try:
                pdf = session.get(pdf_url, timeout=30, allow_redirects=True)
            except Exception as exc:
                print("pdf fetch error:", repr(exc))
                continue
            inspect_pdf(parser, pdf)

        print()

    print("No Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
