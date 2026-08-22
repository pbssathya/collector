from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


URL = "https://www.lotteryagent.kerala.gov.in/result/public/"
KEYWORDS = re.compile(r"result|download|draw|date|page|ajax|api|filter|search", re.I)


class PageProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, str | None]] = []
        self.inputs: list[dict[str, str | None]] = []
        self.selects: list[dict[str, str | None]] = []
        self.options: list[dict[str, str | None]] = []
        self.links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.inline_scripts: list[str] = []
        self._select_name: str | None = None
        self._option: dict[str, str | None] | None = None
        self._option_text: list[str] = []
        self._link: dict[str, str] | None = None
        self._link_text: list[str] = []
        self._in_script = False
        self._script_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "form":
            self.forms.append(
                {
                    "method": values.get("method"),
                    "action": values.get("action"),
                    "id": values.get("id"),
                    "name": values.get("name"),
                }
            )
        elif tag == "input":
            self.inputs.append(
                {
                    "type": values.get("type"),
                    "name": values.get("name"),
                    "value": values.get("value"),
                    "id": values.get("id"),
                }
            )
        elif tag == "select":
            self._select_name = values.get("name") or values.get("id")
            self.selects.append(
                {
                    "name": values.get("name"),
                    "id": values.get("id"),
                }
            )
        elif tag == "option":
            self._option = {
                "select": self._select_name,
                "value": values.get("value"),
                "text": "",
            }
            self._option_text = []
        elif tag == "a" and values.get("href"):
            self._link = {"href": urljoin(URL, values["href"]), "text": ""}
            self._link_text = []
        elif tag == "script":
            self._in_script = True
            self._script_text = []
            if values.get("src"):
                self.scripts.append(urljoin(URL, values["src"]))

    def handle_data(self, data: str) -> None:
        if self._option is not None:
            self._option_text.append(data)
        if self._link is not None:
            self._link_text.append(data)
        if self._in_script:
            self._script_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self._option is not None:
            self._option["text"] = html.unescape(" ".join("".join(self._option_text).split()))
            self.options.append(self._option)
            self._option = None
            self._option_text = []
        elif tag == "select":
            self._select_name = None
        elif tag == "a" and self._link is not None:
            self._link["text"] = html.unescape(" ".join("".join(self._link_text).split()))
            self.links.append(self._link)
            self._link = None
            self._link_text = []
        elif tag == "script" and self._in_script:
            text = "\n".join(self._script_text).strip()
            if text:
                self.inline_scripts.append(text)
            self._in_script = False
            self._script_text = []


def interesting_lines(text: str, limit: int = 80) -> list[str]:
    lines = []
    for raw in text.splitlines():
        clean = html.unescape(" ".join(re.sub(r"<[^>]+>", " ", raw).split()))
        if clean and KEYWORDS.search(clean):
            lines.append(clean[:500])
            if len(lines) >= limit:
                break
    return lines


def main() -> int:
    print("=== CURRENT OFFICIAL LOTIS HISTORY PROBE ===")
    print("url:", URL)
    print("preservation: NO")
    print("purpose: discover whether the current official LOTIS public result surface exposes historical navigation\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 CurrentLOTISHistoryProbe"})
    response = session.get(URL, timeout=30)
    response.raise_for_status()

    print("status:", response.status_code)
    print("content-type:", response.headers.get("Content-Type"))
    print("bytes:", len(response.content))

    parser = PageProbe()
    parser.feed(response.text)

    print("\nforms:")
    for item in parser.forms:
        print("  ", item)

    print("\ninputs:")
    for item in parser.inputs:
        print("  ", item)

    print("\nselects:")
    for item in parser.selects:
        print("  ", item)

    print("\noptions:")
    for item in parser.options[:80]:
        print("  ", item)

    print("\ninteresting links:")
    seen: set[str] = set()
    count = 0
    for item in parser.links:
        text = f"{item['text']} {item['href']}"
        if not KEYWORDS.search(text):
            continue
        key = item["href"]
        if key in seen:
            continue
        seen.add(key)
        print("  ", item)
        count += 1
        if count >= 80:
            break

    print("\nscript sources:")
    for script in parser.scripts:
        print("  ", script)

    print("\ninteresting inline script fragments:")
    shown = 0
    for script in parser.inline_scripts:
        for raw in script.splitlines():
            clean = " ".join(raw.split())
            if clean and KEYWORDS.search(clean):
                print("  ", clean[:700])
                shown += 1
                if shown >= 80:
                    break
        if shown >= 80:
            break

    print("\ninteresting HTML lines:")
    for line in interesting_lines(response.text):
        print("  ", line)

    # Inspect only same-origin JavaScript for route/API hints.
    origin = urlparse(URL).netloc
    print("\nscript route hints:")
    for script in parser.scripts:
        if urlparse(script).netloc != origin:
            continue
        try:
            asset = session.get(script, timeout=30)
            asset.raise_for_status()
        except Exception as exc:
            print("  ", script, "->", repr(exc))
            continue

        hints = []
        for raw in asset.text.splitlines():
            clean = " ".join(raw.split())
            if clean and KEYWORDS.search(clean):
                hints.append(clean[:700])
            if len(hints) >= 20:
                break
        if hints:
            print("  ", script)
            for hint in hints:
                print("     ", hint)

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
