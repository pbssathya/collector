from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests


URL = "https://www.lotteryagent.kerala.gov.in/result/public/"
RESULT_ROUTE = "https://www.lotteryagent.kerala.gov.in/results/{item_id}"


class ResultRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, object]] = []
        self._in_row = False
        self._text: list[str] = []
        self._attrs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._in_row = True
            self._text = []
            self._attrs = []
            return
        if not self._in_row:
            return
        for key, value in attrs:
            if value is not None:
                self._attrs.append((tag, key, value))

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "tr" or not self._in_row:
            return
        text = html.unescape(" ".join("".join(self._text).split()))
        self.rows.append({"text": text, "attrs": list(self._attrs)})
        self._in_row = False
        self._text = []
        self._attrs = []


def candidate_item_ids(attrs: list[tuple[str, str, str]]) -> list[int]:
    found: set[int] = set()
    for _tag, key, value in attrs:
        lower = f"{key} {value}".lower()
        if not any(token in lower for token in ("download", "result", "item", "onclick", "data-", "value")):
            continue
        for match in re.findall(r"(?<!\d)(\d{1,10})(?!\d)", value):
            found.add(int(match))
    return sorted(found)


def summarize_response(response: requests.Response) -> dict[str, object]:
    ctype = response.headers.get("Content-Type", "")
    return {
        "status": response.status_code,
        "content_type": ctype,
        "bytes": len(response.content),
        "starts_pdf": response.content.startswith(b"%PDF"),
        "final_url": response.url,
    }


def main() -> int:
    print("=== CURRENT LOTIS ITEM-ID / DOWNLOAD ROUTE PROBE ===")
    print("page:", URL)
    print("preservation: NO")
    print("purpose: discover row item IDs and whether the official /results/{itemId} route is directly usable\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 CurrentLOTISItemProbe"})
    page = session.get(URL, timeout=30)
    page.raise_for_status()

    parser = ResultRowParser()
    parser.feed(page.text)

    data_rows: list[dict[str, object]] = []
    for row in parser.rows:
        text = str(row["text"])
        if "Download" not in text:
            continue
        attrs = list(row["attrs"])
        ids = candidate_item_ids(attrs)
        data_rows.append({"text": text, "attrs": attrs, "candidate_ids": ids})

    print("download rows:", len(data_rows))
    print("\nfirst rows:")
    for row in data_rows[:5]:
        print("  text:", row["text"][:220])
        print("  candidate ids:", row["candidate_ids"])
        print("  relevant attrs:")
        for tag, key, value in row["attrs"]:
            lower = f"{key} {value}".lower()
            if any(token in lower for token in ("download", "result", "item", "onclick", "data-", "value")):
                print("    ", (tag, key, value))

    print("\nlast rows:")
    for row in data_rows[-5:]:
        print("  text:", row["text"][:220])
        print("  candidate ids:", row["candidate_ids"])
        print("  relevant attrs:")
        for tag, key, value in row["attrs"]:
            lower = f"{key} {value}".lower()
            if any(token in lower for token in ("download", "result", "item", "onclick", "data-", "value")):
                print("    ", (tag, key, value))

    single_ids: list[int] = []
    for row in data_rows:
        ids = list(row["candidate_ids"])
        if len(ids) == 1:
            single_ids.append(ids[0])

    print("\nrows with exactly one candidate item id:", len(single_ids))
    if single_ids:
        print("candidate id range:", min(single_ids), "→", max(single_ids))

        # Probe only the visible extremes plus a very small bounded window immediately
        # before the oldest visible item ID. This does not mutate source or Memory.
        visible_probe_ids = sorted({single_ids[0], single_ids[-1]})
        oldest = min(single_ids)
        bounded_older = [value for value in range(max(1, oldest - 3), oldest)]
        probe_ids = sorted(set(visible_probe_ids + bounded_older))

        print("\ndirect /results/{itemId} checks:")
        for item_id in probe_ids:
            try:
                response = session.get(RESULT_ROUTE.format(item_id=item_id), timeout=30, allow_redirects=True)
                print("  ", item_id, summarize_response(response))
            except Exception as exc:
                print("  ", item_id, "ERROR", repr(exc))
    else:
        print("No unambiguous item IDs were discovered from row attributes.")

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
