from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


START_URL = (
    "https://document.kerala.gov.in/deptdocumentdetails/en/"
    "ekw0bU5IRnJ5M2J0VUMvd1VrYVpGUT09/"
    "WVN1WGNJN3l1d1hUdWtxekpBR0tuQT09"
)
BASE_HOST = "document.kerala.gov.in"
TARGET_TERMS = (
    "lottery",
    "lotteries",
    "bumper",
    "draw",
    "state lottery",
    "ഭാഗ്യക്കുറി",
)
YEAR_TERMS = ("2017", "2016")


class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.scripts: list[str] = []
        self.forms: list[dict[str, object]] = []
        self._current_form: dict[str, object] | None = None
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()

        if tag == "a":
            self._anchor_href = attributes.get("href")
            self._anchor_text = []

        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"])

        if tag == "form":
            self._current_form = {
                "action": attributes.get("action", ""),
                "method": attributes.get("method", "get").lower(),
                "fields": [],
            }
            self.forms.append(self._current_form)

        if self._current_form is not None and tag in {"input", "select", "textarea", "button"}:
            name = attributes.get("name", "")
            if name:
                self._current_form["fields"].append(
                    {
                        "tag": tag,
                        "name": name,
                        "type": attributes.get("type", ""),
                        "value": attributes.get("value", ""),
                    }
                )

    def handle_data(self, data: str) -> None:
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._anchor_href is not None:
            text = " ".join("".join(self._anchor_text).split())
            self.links.append((self._anchor_href, text))
            self._anchor_href = None
            self._anchor_text = []
        if tag == "form":
            self._current_form = None


def same_origin(url: str) -> bool:
    parsed = urlparse(url)
    return not parsed.netloc or parsed.netloc == BASE_HOST


def normalize_space(text: str) -> str:
    return " ".join(unescape(text).split())


def relevant_snippets(text: str, width: int = 180) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    seen: set[str] = set()
    for term in TARGET_TERMS + YEAR_TERMS:
        start = 0
        while True:
            index = lowered.find(term.lower(), start)
            if index < 0:
                break
            left = max(0, index - width)
            right = min(len(text), index + len(term) + width)
            snippet = normalize_space(text[left:right])
            if snippet not in seen:
                seen.add(snippet)
                hits.append(snippet)
            start = index + len(term)
    return hits


def print_form(index: int, form: dict[str, object]) -> None:
    print(f"   form {index}: method={form['method']} action={form['action'] or '(same page)'}")
    for field in form["fields"]:
        print(
            "      ",
            f"{field['tag']} name={field['name']!r} type={field['type']!r} value={field['value']!r}",
        )


def main() -> int:
    print("=== GOVERNMENT DOCUMENT PORTAL — 2017 LOTTERY DISCOVERY PROBE ===")
    print("preservation: NO")
    print("form submission: NO")
    print("purpose: discover a stable official search/retrieval contract for pre-Aug 2017 lottery records\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 GovernmentDocumentPortalProbe"})

    try:
        response = session.get(START_URL, timeout=30)
        print("1. Taxes/Notifications surface")
        print("   status:", response.status_code)
        print("   final URL:", response.url)
        print("   bytes:", len(response.content))
        response.raise_for_status()
    except Exception as exc:
        print("\n=== DOCUMENT PORTAL DISCOVERY SUMMARY ===")
        print("official document portal reachable: NO")
        print("search contract discovered: NO")
        print("pre-Aug 2017 lottery retrieval route discovered: NO")
        print("failure:", repr(exc))
        print("No Collector result or Memory state was changed by this probe.")
        return 1

    text = response.text
    parser = SurfaceParser()
    parser.feed(text)

    print("\n2. Search forms exposed by the page")
    print("   forms:", len(parser.forms))
    for index, form in enumerate(parser.forms, start=1):
        print_form(index, form)

    print("\n3. Existing lottery/year evidence on this official surface")
    snippets = relevant_snippets(text)
    lottery_snippets = [s for s in snippets if any(term in s.lower() for term in ("lottery", "bumper", "draw"))]
    year_snippets = [s for s in snippets if "2017" in s or "2016" in s]
    print("   lottery-related snippets:", len(lottery_snippets))
    for snippet in lottery_snippets[:12]:
        print("      ", snippet[:500])
    print("   2017/2016 snippets:", len(year_snippets))
    for snippet in year_snippets[:12]:
        print("      ", snippet[:500])

    print("\n4. Candidate links")
    candidates: list[tuple[str, str]] = []
    for href, label in parser.links:
        absolute = urljoin(response.url, href)
        combined = f"{absolute} {label}".lower()
        if not same_origin(absolute):
            continue
        if any(token in combined for token in ("search", "document", "notification", "tax", "pdf", "lotter")):
            candidates.append((absolute, normalize_space(label)))
    unique_candidates: list[tuple[str, str]] = []
    seen_links: set[str] = set()
    for item in candidates:
        if item[0] in seen_links:
            continue
        seen_links.add(item[0])
        unique_candidates.append(item)
    print("   count:", len(unique_candidates))
    for url, label in unique_candidates[:30]:
        print("      ", url, "|", label)

    print("\n5. Candidate script contracts")
    script_hits: list[tuple[str, list[str]]] = []
    for raw_src in parser.scripts[:30]:
        script_url = urljoin(response.url, raw_src)
        if not same_origin(script_url):
            continue
        try:
            script_response = session.get(script_url, timeout=20)
            if script_response.status_code != 200:
                continue
            body = script_response.text
        except Exception:
            continue

        lower = body.lower()
        tokens = [
            token
            for token in ("ajax", "search", "fromdate", "todate", "keyword", "deptdocument", "documentdetails")
            if token in lower
        ]
        if tokens:
            script_hits.append((script_url, tokens))
            print("   script:", script_url)
            print("      tokens:", ", ".join(tokens))
            for match in re.findall(r"['\"]([^'\"]*(?:search|document)[^'\"]*)['\"]", body, flags=re.I)[:12]:
                if len(match) < 240:
                    print("      candidate:", match)

    print("\n=== DOCUMENT PORTAL DISCOVERY SUMMARY ===")
    print("official document portal reachable: YES")
    print("forms discovered:", len(parser.forms))
    print("candidate same-origin links:", len(unique_candidates))
    print("candidate scripts with search/document clues:", len(script_hits))
    print("lottery evidence already visible on page:", "YES" if lottery_snippets else "NO")
    print("2017 evidence already visible on page:", "YES" if any("2017" in s for s in year_snippets) else "NO")
    print("search contract discovered:", "YES" if parser.forms or script_hits else "NO")
    print("pre-Aug 2017 lottery retrieval route discovered: NOT YET — inspect the contract evidence above")
    print("No Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
