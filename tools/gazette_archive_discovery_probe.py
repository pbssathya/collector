from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


COMPOSE_HOME = "https://compose.kerala.gov.in/home.jsp"
GAZETTE_HOME = "https://gazette.kerala.gov.in/"
TIMEOUT = 30


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.forms: list[dict[str, object]] = []
        self.scripts: list[str] = []
        self._current_form: dict[str, object] | None = None
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = {str(k).lower(): str(v or "") for k, v in attrs}

        if tag == "a":
            self._anchor_href = attrs_dict.get("href") or None
            self._anchor_text = []

        if tag == "form":
            self._current_form = {
                "method": (attrs_dict.get("method") or "GET").upper(),
                "action": attrs_dict.get("action") or "",
                "inputs": [],
                "selects": [],
            }
            self.forms.append(self._current_form)

        if self._current_form is not None and tag == "input":
            self._current_form["inputs"].append(
                {
                    "name": attrs_dict.get("name", ""),
                    "type": attrs_dict.get("type", ""),
                    "value": attrs_dict.get("value", ""),
                }
            )

        if self._current_form is not None and tag == "select":
            self._current_form["selects"].append(
                {
                    "name": attrs_dict.get("name", ""),
                    "id": attrs_dict.get("id", ""),
                }
            )

        if tag == "script" and attrs_dict.get("src"):
            self.scripts.append(attrs_dict["src"])

    def handle_data(self, data: str) -> None:
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href is not None:
            text = " ".join("".join(self._anchor_text).split())
            self.links.append((self._anchor_href, text))
            self._anchor_href = None
            self._anchor_text = []
        elif tag == "form":
            self._current_form = None


def fetch(session: requests.Session, url: str):
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        return response, None
    except Exception as exc:  # diagnostic tool: report exact transport failure
        return None, f"{type(exc).__name__}: {exc}"


def inspect_page(label: str, response: requests.Response) -> PageInspector:
    print(f"\n--- {label} ---")
    print("requested/final URL:", response.url)
    print("status:", response.status_code)
    print("content-type:", response.headers.get("content-type"))
    print("bytes:", len(response.content))

    inspector = PageInspector()
    content_type = (response.headers.get("content-type") or "").lower()
    if "html" in content_type or response.text.lstrip().startswith("<"):
        inspector.feed(response.text)

    print("forms:", len(inspector.forms))
    for idx, form in enumerate(inspector.forms[:20], start=1):
        print(
            f"  form {idx}: method={form['method']} action={form['action']!r} "
            f"inputs={form['inputs']} selects={form['selects']}"
        )

    keywords = (
        "archive",
        "search",
        "gazette",
        "weekly",
        "extra",
        "2017",
        "year",
        "date",
        "pdf",
    )
    relevant_links = []
    for href, text in inspector.links:
        haystack = f"{href} {text}".lower()
        if any(keyword in haystack for keyword in keywords):
            relevant_links.append((href, text))

    print("relevant links:", len(relevant_links))
    for href, text in relevant_links[:80]:
        print("  ", text or "(no text)", "->", urljoin(response.url, href))

    if inspector.scripts:
        print("script srcs:")
        for src in inspector.scripts[:40]:
            print("  ", urljoin(response.url, src))

    return inspector


def same_origin(base: str, candidate: str) -> bool:
    left = urlparse(base)
    right = urlparse(candidate)
    return left.scheme == right.scheme and left.netloc == right.netloc


def main() -> int:
    print("=== KERALA GOVERNMENT GAZETTE ARCHIVE DISCOVERY PROBE ===")
    print("preservation: NO")
    print("purpose: test the official pre-02/10/2021 Gazette archive before using any third-party source")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 KeralaGazetteArchiveProbe"})

    compose, compose_error = fetch(session, COMPOSE_HOME)
    if compose_error:
        print("\nCOMPOSE transport error:", compose_error)
    else:
        compose_inspector = inspect_page("Official COMPOSE home", compose)
        archive_links = [
            urljoin(compose.url, href)
            for href, text in compose_inspector.links
            if "gazette.kerala.gov.in" in urljoin(compose.url, href)
            or "archive" in text.lower()
        ]
        print("official archive pointers found:", len(archive_links))
        for link in archive_links[:20]:
            print("  ", link)

    gazette, gazette_error = fetch(session, GAZETTE_HOME)
    if gazette_error:
        print("\nGAZETTE transport error:", gazette_error)
        print("\n=== GAZETTE DISCOVERY SUMMARY ===")
        print("official archive endpoint reachable: NO")
        print("archive navigation contract discovered: NO")
        print("2017 retrieval route discovered: NO")
        print("No Collector result or Memory state was changed by this probe.")
        return 0

    inspector = inspect_page("Historical Gazette archive", gazette)

    # Follow only a small number of same-origin links that the official landing page
    # itself exposes and whose labels/URLs look like archive/search/year navigation.
    follow_keywords = ("archive", "search", "weekly", "gazette", "year", "2017")
    followed = 0
    seen: set[str] = {gazette.url}
    discovered_2017 = False

    for href, text in inspector.links:
        absolute = urljoin(gazette.url, href)
        if absolute in seen or not same_origin(gazette.url, absolute):
            continue
        haystack = f"{absolute} {text}".lower()
        if not any(keyword in haystack for keyword in follow_keywords):
            continue
        seen.add(absolute)
        followed += 1
        response, error = fetch(session, absolute)
        if error:
            print(f"\nfollow error: {absolute} -> {error}")
            continue
        child = inspect_page(f"same-origin discovery link {followed}", response)
        page_haystack = (response.url + " " + response.text[:200000]).lower()
        if "2017" in page_haystack:
            discovered_2017 = True
        if followed >= 8:
            break

    root_has_2017 = "2017" in gazette.text[:500000]
    has_navigation = bool(inspector.forms or inspector.links)

    print("\n=== GAZETTE DISCOVERY SUMMARY ===")
    print("official archive endpoint reachable: YES")
    print("archive navigation contract discovered:", "YES" if has_navigation else "NO")
    print("2017 clue on root/followed pages:", "YES" if root_has_2017 or discovered_2017 else "NO")
    print("same-origin discovery links followed:", followed)
    print("No form was submitted; no CAPTCHA was solved or bypassed.")
    print("No Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
