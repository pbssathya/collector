from __future__ import annotations

import re
from urllib.parse import urljoin

import requests


DETAILS_URL = "https://result.keralalotteries.com/detailsofdrawweb.php"
LEGACY_REPORT_URL = "https://result.keralalotteries.com/reports/resultentryeport1.php"

# A legacy drawno proven by the official history index.
DRAWNO = 71996
LOTTERYDET = "102"  # STHREE SAKTHI


def summarize(label: str, response: requests.Response) -> None:
    print(f"\n--- {label} ---")
    print("status:", response.status_code)
    print("final url:", response.url)
    print("content-type:", response.headers.get("Content-Type"))
    print("content-length header:", response.headers.get("Content-Length"))
    print("location:", response.headers.get("Location"))
    print("bytes:", len(response.content))
    print("raw repr:", repr(response.content[:500]))

    text = response.text
    patterns = {
        "meta refresh": r"<meta[^>]+http-equiv=[\"']?refresh[^>]*>",
        "window location": r"(?:window\.)?location(?:\.href)?\s*=\s*[^;]+",
        "form action": r"<form[^>]+action=[\"'][^\"']+[\"']",
        "href": r"href=[\"'][^\"']+[\"']",
        "src": r"src=[\"'][^\"']+[\"']",
    }
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.I | re.S)
        if matches:
            print(name + ":")
            for match in matches[:10]:
                print("  ", " ".join(match.split())[:500])


def main() -> int:
    print("=== KERALA LEGACY RESULT TRANSPORT DIAGNOSTIC ===")
    print("preservation: NO")
    print("captcha solving/bypass: NO")
    print("purpose: inspect the exact 68-byte legacy response before declaring the transport unusable")
    print("drawno:", DRAWNO)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 Collector-LegacyTransportDiagnostic/1.0",
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        }
    )

    # Establish the same browsing/session context as the official history UI.
    landing = session.get(DETAILS_URL, timeout=30)
    landing.raise_for_status()
    selected = session.post(DETAILS_URL, data={"lotterydet": LOTTERYDET}, timeout=30)
    selected.raise_for_status()
    print("history session cookies:", session.cookies.get_dict())
    print("selected history bytes:", len(selected.content))
    print("legacy row present:", str(DRAWNO) in selected.text)

    params = {"drawno1": DRAWNO, "drawno": DRAWNO}

    direct = session.get(
        LEGACY_REPORT_URL,
        params=params,
        timeout=30,
        allow_redirects=False,
    )
    summarize("GET, no explicit Referer, redirects disabled", direct)

    referer_get = session.get(
        LEGACY_REPORT_URL,
        params=params,
        headers={"Referer": DETAILS_URL},
        timeout=30,
        allow_redirects=False,
    )
    summarize("GET with official Referer, redirects disabled", referer_get)

    post = session.post(
        LEGACY_REPORT_URL,
        data=params,
        headers={"Referer": DETAILS_URL},
        timeout=30,
        allow_redirects=False,
    )
    summarize("POST with official Referer, redirects disabled", post)

    # If any response advertises a normal HTTP redirect, inspect only that declared target.
    for label, response in (("direct", direct), ("referer", referer_get), ("post", post)):
        location = response.headers.get("Location")
        if not location:
            continue
        target = urljoin(response.url, location)
        followed = session.get(target, headers={"Referer": response.url}, timeout=30)
        summarize(f"declared redirect target from {label}", followed)

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
