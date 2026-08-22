from __future__ import annotations

import html
import re
from html.parser import HTMLParser

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


def row_mentions_download(row: dict[str, object]) -> bool:
    text = str(row["text"])
    if "download" in text.lower():
        return True
    for _tag, key, value in row["attrs"]:
        if "download" in f"{key} {value}".lower():
            return True
    return False


def candidate_item_ids(attrs: list[tuple[str, str, str]]) -> list[int]:
    """Return numeric candidates from attributes that look tied to result/download actions."""
    found: set[int] = set()
    for _tag, key, value in attrs:
        lower = f"{key} {value}".lower()
        if not any(
            token in lower
            for token in (
                "download",
                "result",
                "item",
                "onclick",
                "data-",
                "value",
                "/results/",
            )
        ):
            continue
        for match in re.findall(r"(?<!\d)(\d{1,10})(?!\d)", value):
            found.add(int(match))
    return sorted(found)


def interesting_attrs(attrs: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    result = []
    for item in attrs:
        tag, key, value = item
        lower = f"{key} {value}".lower()
        if any(
            token in lower
            for token in (
                "download",
                "result",
                "item",
                "onclick",
                "data-",
                "value",
                "/results/",
            )
        ):
            result.append((tag, key, value))
    return result


def raw_download_fragments(page_text: str) -> list[str]:
    """Show compact raw HTML/script fragments near download/item/result route clues."""
    patterns = [
        r".{0,180}download.{0,260}",
        r".{0,180}itemId.{0,260}",
        r".{0,180}/results/.{0,260}",
    ]
    fragments: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, page_text, flags=re.I | re.S):
            fragment = " ".join(match.group(0).split())
            if fragment in seen:
                continue
            seen.add(fragment)
            fragments.append(fragment[:700])
            if len(fragments) >= 20:
                return fragments
    return fragments


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
    print("purpose: discover the official row item IDs and test the public /results/{itemId} route\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 CurrentLOTISItemProbe"})
    page = session.get(URL, timeout=30)
    page.raise_for_status()

    parser = ResultRowParser()
    parser.feed(page.text)

    data_rows: list[dict[str, object]] = []
    for row in parser.rows:
        if not row_mentions_download(row):
            continue
        attrs = list(row["attrs"])
        ids = candidate_item_ids(attrs)
        data_rows.append({"text": row["text"], "attrs": attrs, "candidate_ids": ids})

    print("table rows parsed:", len(parser.rows))
    print("download/action rows:", len(data_rows))

    print("\nraw download/item fragments:")
    for fragment in raw_download_fragments(page.text):
        print("  ", fragment)

    print("\nfirst rows:")
    for row in data_rows[:5]:
        print("  text:", str(row["text"])[:260])
        print("  candidate ids:", row["candidate_ids"])
        print("  relevant attrs:")
        for attr in interesting_attrs(list(row["attrs"])):
            print("    ", attr)

    print("\nlast rows:")
    for row in data_rows[-5:]:
        print("  text:", str(row["text"])[:260])
        print("  candidate ids:", row["candidate_ids"])
        print("  relevant attrs:")
        for attr in interesting_attrs(list(row["attrs"])):
            print("    ", attr)

    single_ids: list[int] = []
    for row in data_rows:
        ids = list(row["candidate_ids"])
        if len(ids) == 1:
            single_ids.append(ids[0])

    print("\nrows with exactly one candidate item id:", len(single_ids))
    if single_ids:
        print("candidate id range:", min(single_ids), "→", max(single_ids))

        # Probe only visible extremes plus three immediately lower candidate addresses.
        # No state is written by this tool.
        visible_probe_ids = sorted({single_ids[0], single_ids[-1]})
        oldest = min(single_ids)
        bounded_older = [value for value in range(max(1, oldest - 3), oldest)]
        probe_ids = sorted(set(visible_probe_ids + bounded_older))

        print("\ndirect /results/{itemId} checks:")
        for item_id in probe_ids:
            try:
                response = session.get(
                    RESULT_ROUTE.format(item_id=item_id),
                    timeout=30,
                    allow_redirects=True,
                )
                print("  ", item_id, summarize_response(response))
            except Exception as exc:
                print("  ", item_id, "ERROR", repr(exc))
    else:
        print("No unambiguous item IDs were discovered from action-row attributes.")

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
