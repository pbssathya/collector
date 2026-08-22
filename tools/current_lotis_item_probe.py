from __future__ import annotations

import html
import re
from html.parser import HTMLParser

import requests


URL = "https://www.lotteryagent.kerala.gov.in/result/public/"
RESULT_ROUTE = "https://www.lotteryagent.kerala.gov.in/results/{item_id}"
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


class DownloadLinkParser(HTMLParser):
    """Collect current LOTIS download anchors without relying on valid table markup."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, object]] = []
        self._current: dict[str, object] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return

        values = dict(attrs)
        item_id = values.get("data-item-id")
        classes = values.get("class", "")
        onclick = values.get("onclick", "")

        if not item_id and "download" not in classes.lower() and "captcha" not in onclick.lower():
            return

        self._current = {
            "item_id": item_id,
            "attrs": list(attrs),
            "text": "",
        }
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current is None:
            return

        self._current["text"] = html.unescape(" ".join("".join(self._text).split()))
        self.links.append(self._current)
        self._current = None
        self._text = []


def context_for_item(page_text: str, item_id: str, radius: int = 220) -> str:
    index = page_text.find(item_id)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(page_text), index + len(item_id) + radius)
    fragment = page_text[start:end]
    return html.unescape(" ".join(fragment.split()))


def summarize_response(response: requests.Response) -> dict[str, object]:
    ctype = response.headers.get("Content-Type", "")
    location = response.headers.get("Location")
    return {
        "status": response.status_code,
        "content_type": ctype,
        "bytes": len(response.content),
        "starts_pdf": response.content.startswith(b"%PDF"),
        "final_url": response.url,
        "location": location,
    }


def main() -> int:
    print("=== CURRENT LOTIS UUID ITEM / DOWNLOAD ROUTE PROBE ===")
    print("page:", URL)
    print("preservation: NO")
    print("captcha solving/bypass: NO")
    print("purpose: extract official UUID item IDs and test only visible public result routes\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 CurrentLOTISItemProbe"})
    page = session.get(URL, timeout=30)
    page.raise_for_status()

    parser = DownloadLinkParser()
    parser.feed(page.text)

    links = []
    seen: set[str] = set()
    for item in parser.links:
        raw_item_id = item.get("item_id")
        if not isinstance(raw_item_id, str) or not UUID_RE.match(raw_item_id):
            continue
        if raw_item_id in seen:
            continue
        seen.add(raw_item_id)
        links.append(item)

    print("download anchors with UUID item IDs:", len(links))

    if links:
        print("\nfirst visible items:")
        for item in links[:5]:
            item_id = str(item["item_id"])
            print("  item id:", item_id)
            print("  anchor text:", item["text"])
            print("  context:", context_for_item(page.text, item_id)[:500])

        print("\nlast visible items:")
        for item in links[-5:]:
            item_id = str(item["item_id"])
            print("  item id:", item_id)
            print("  anchor text:", item["text"])
            print("  context:", context_for_item(page.text, item_id)[:500])

        # UUIDs are opaque identifiers, not an ordered address space. Probe only
        # two IDs that the official page itself currently publishes. Do not guess
        # neighbouring UUIDs and do not attempt captcha verification or bypass.
        probe_ids = [str(links[0]["item_id"])]
        if len(links) > 1:
            probe_ids.append(str(links[-1]["item_id"]))

        print("\ndirect visible /results/{itemId} checks:")
        for item_id in probe_ids:
            try:
                response = session.get(
                    RESULT_ROUTE.format(item_id=item_id),
                    timeout=30,
                    allow_redirects=False,
                )
                print("  ", item_id, summarize_response(response))
                if response.is_redirect or response.is_permanent_redirect:
                    target = response.headers.get("Location")
                    print("      redirect target:", target)
            except Exception as exc:
                print("  ", item_id, "ERROR", repr(exc))
    else:
        print("No UUID item IDs were discovered from official download anchors.")

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
