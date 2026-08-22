from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import requests


BASE = "https://www.lotteryagent.kerala.gov.in/"
CANDIDATES = (
    "robots.txt",
    "sitemap.xml",
    "sitemap_index.xml",
    "sitemap-index.xml",
)
RESULT_RE = re.compile(r"https?://[^\s<>'\"]+/results/[0-9a-f-]{36}", re.I)


def extract_result_urls(text: str) -> list[str]:
    return sorted(set(RESULT_RE.findall(text)))


def extract_sitemap_locations(raw: bytes) -> list[str]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    locations: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() != "loc":
            continue
        if element.text and element.text.strip():
            locations.append(element.text.strip())
    return locations


def summarize(response: requests.Response) -> dict[str, object]:
    return {
        "status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "bytes": len(response.content),
        "final_url": response.url,
    }


def main() -> int:
    print("=== CURRENT LOTIS ARCHIVE DISCOVERY PROBE ===")
    print("base:", BASE)
    print("preservation: NO")
    print("purpose: check standard public discovery surfaces for historical /results/{uuid} URLs\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LOTISArchiveDiscoveryProbe"})

    discovered_sitemaps: set[str] = set()
    discovered_results: set[str] = set()

    for relative in CANDIDATES:
        url = urljoin(BASE, relative)
        try:
            response = session.get(url, timeout=30, allow_redirects=True)
        except Exception as exc:
            print(relative, "ERROR", repr(exc))
            continue

        print(relative, summarize(response))
        text = response.text if response.content else ""

        for match in re.findall(r"(?im)^\s*Sitemap:\s*(\S+)\s*$", text):
            discovered_sitemaps.add(urljoin(BASE, match))

        for location in extract_sitemap_locations(response.content):
            if "/results/" in location:
                discovered_results.add(location)
            elif "sitemap" in location.lower():
                discovered_sitemaps.add(location)

        discovered_results.update(extract_result_urls(text))

        preview = " ".join(text.split())[:500]
        if preview:
            print("   preview:", preview)

    print("\nadditional sitemap urls discovered:", len(discovered_sitemaps))
    for sitemap_url in sorted(discovered_sitemaps):
        if urlparse(sitemap_url).netloc != urlparse(BASE).netloc:
            print("  external sitemap skipped:", sitemap_url)
            continue

        try:
            response = session.get(sitemap_url, timeout=30, allow_redirects=True)
        except Exception as exc:
            print("  ", sitemap_url, "ERROR", repr(exc))
            continue

        print("  ", sitemap_url, summarize(response))
        for location in extract_sitemap_locations(response.content):
            if "/results/" in location:
                discovered_results.add(location)
        discovered_results.update(extract_result_urls(response.text))

    print("\nhistorical/current result URLs discovered through standard surfaces:", len(discovered_results))
    for url in sorted(discovered_results)[:20]:
        print("  ", url)
    if len(discovered_results) > 20:
        print("  ...")
        for url in sorted(discovered_results)[-5:]:
            print("  ", url)

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
