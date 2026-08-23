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
TARGET_START = "01-01-2017"
TARGET_END = "22-08-2017"


class ContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, object]] = []
        self.scripts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._form: dict[str, object] | None = None
        self._select: dict[str, object] | None = None
        self._option: dict[str, str] | None = None
        self._option_text: list[str] = []
        self._anchor: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()

        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])

        if tag == "a":
            self._anchor = a.get("href", "")
            self._anchor_text = []

        if tag == "form":
            self._form = {
                "action": a.get("action", ""),
                "method": a.get("method", "get").lower(),
                "fields": [],
            }
            self.forms.append(self._form)
            return

        if self._form is None:
            return

        if tag in {"input", "textarea", "button"}:
            self._form["fields"].append(
                {
                    "tag": tag,
                    "name": a.get("name", ""),
                    "id": a.get("id", ""),
                    "type": a.get("type", ""),
                    "value": a.get("value", ""),
                    "placeholder": a.get("placeholder", ""),
                }
            )

        if tag == "select":
            self._select = {
                "tag": "select",
                "name": a.get("name", ""),
                "id": a.get("id", ""),
                "type": "",
                "value": "",
                "placeholder": "",
                "options": [],
            }
            self._form["fields"].append(self._select)

        if tag == "option" and self._select is not None:
            self._option = {"value": a.get("value", ""), "selected": "selected" if "selected" in a else ""}
            self._option_text = []

    def handle_data(self, data: str) -> None:
        if self._anchor is not None:
            self._anchor_text.append(data)
        if self._option is not None:
            self._option_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._anchor is not None:
            self.links.append((self._anchor, " ".join("".join(self._anchor_text).split())))
            self._anchor = None
            self._anchor_text = []
        if tag == "option" and self._option is not None and self._select is not None:
            self._option["text"] = " ".join("".join(self._option_text).split())
            self._select["options"].append(self._option)
            self._option = None
            self._option_text = []
        if tag == "select":
            self._select = None
        if tag == "form":
            self._form = None


def same_origin(url: str) -> bool:
    p = urlparse(url)
    return (not p.netloc) or p.netloc == BASE_HOST


def norm(text: str) -> str:
    return " ".join(unescape(text).split())


def field_identity(field: dict[str, object]) -> str:
    return " ".join(
        str(field.get(k, "")) for k in ("name", "id", "placeholder", "type")
    ).lower()


def build_payload(form: dict[str, object], date_format: str) -> tuple[dict[str, str], list[str]]:
    payload: dict[str, str] = {}
    decisions: list[str] = []

    if date_format == "dmy-dash":
        start, end = TARGET_START, TARGET_END
    elif date_format == "dmy-slash":
        start, end = TARGET_START.replace("-", "/"), TARGET_END.replace("-", "/")
    else:
        start, end = "2017-01-01", "2017-08-22"

    for raw in form["fields"]:
        field = dict(raw)
        name = str(field.get("name") or "")
        if not name:
            continue
        ident = field_identity(field)
        ftype = str(field.get("type") or "").lower()
        value = str(field.get("value") or "")

        if ftype == "hidden":
            payload[name] = value
            continue

        if field.get("tag") == "select":
            options = field.get("options") or []
            selected = next((str(o.get("value", "")) for o in options if o.get("selected")), None)
            if selected is not None:
                payload[name] = selected
            elif options:
                payload[name] = str(options[0].get("value", ""))
            continue

        if any(token in ident for token in ("keyword", "search", "query", "key word")):
            payload[name] = "lottery"
            decisions.append(f"{name}=lottery")
            continue

        if ("from" in ident or "start" in ident) and any(token in ident for token in ("date", "dt", "from")):
            payload[name] = start
            decisions.append(f"{name}={start}")
            continue

        if ("to" in ident or "end" in ident) and any(token in ident for token in ("date", "dt", "to")):
            payload[name] = end
            decisions.append(f"{name}={end}")
            continue

        if ftype in {"submit", "button", "reset"}:
            continue

        if value:
            payload[name] = value

    return payload, decisions


def evidence(text: str) -> tuple[list[str], list[str]]:
    compact = norm(text)
    snippets: list[str] = []
    urls: list[str] = []
    lower = compact.lower()
    for token in ("lottery", "bumper", "भाग्य", "ഭാഗ്യ", "2017"):
        start = 0
        while True:
            i = lower.find(token.lower(), start)
            if i < 0:
                break
            snippet = compact[max(0, i - 160): min(len(compact), i + 280)]
            if snippet not in snippets:
                snippets.append(snippet)
            start = i + len(token)
    for match in re.findall(r"(?:href|src)=[\"']([^\"']+)[\"']", text, flags=re.I):
        absolute = urljoin(START_URL, match)
        if same_origin(absolute) and any(t in absolute.lower() for t in ("pdf", "document", "download", "file")):
            if absolute not in urls:
                urls.append(absolute)
    return snippets, urls


def main() -> int:
    print("=== GOVERNMENT DOCUMENT PORTAL — SEARCH CONTRACT GATE ===")
    print("preservation: NO")
    print("mutation: NO")
    print("search submissions: read-only, same-origin only")
    print("target window: 2017-01-01 -> 2017-08-22\n")

    s = requests.Session()
    s.headers.update({"User-Agent": "Collector/1.0 GovernmentDocumentPortalContractGate"})
    r = s.get(START_URL, timeout=30)
    print("1. Surface:", r.status_code, r.url, len(r.content), "bytes")
    r.raise_for_status()

    p = ContractParser()
    p.feed(r.text)
    print("\n2. Exact form contract")
    print("   forms:", len(p.forms))
    for i, form in enumerate(p.forms, 1):
        print(f"   form {i}: method={form['method']} action={form['action'] or '(same page)'}")
        for field in form["fields"]:
            print(
                "      ",
                field.get("tag"),
                f"name={field.get('name')!r}",
                f"id={field.get('id')!r}",
                f"type={field.get('type')!r}",
                f"placeholder={field.get('placeholder')!r}",
                f"value={field.get('value')!r}",
            )
            if field.get("tag") == "select":
                print("         options:", field.get("options", [])[:12])

    print("\n3. Script-side contract evidence")
    script_hits = 0
    for src in p.scripts:
        u = urljoin(r.url, src)
        if not same_origin(u):
            continue
        try:
            sr = s.get(u, timeout=20)
        except Exception:
            continue
        if sr.status_code != 200:
            continue
        body = sr.text
        if not any(t in body.lower() for t in ("ajax", "search", "keyword", "fromdate", "todate", "deptdocument")):
            continue
        script_hits += 1
        print("   script:", u)
        for m in re.finditer(r".{0,220}(?:ajax|search|keyword|fromdate|todate|deptdocument).{0,360}", body, flags=re.I | re.S):
            snippet = norm(m.group(0))
            if len(snippet) <= 700:
                print("      ", snippet)
        if script_hits >= 7:
            break

    print("\n4. Conservative live search gate")
    if not p.forms:
        print("   no form available; live search not attempted")
        return 2

    form = p.forms[0]
    action = urljoin(r.url, str(form.get("action") or r.url))
    if not same_origin(action):
        print("   refusing cross-origin form action:", action)
        return 3

    method = str(form.get("method") or "get").lower()
    successful_response: requests.Response | None = None
    successful_format = ""

    for fmt in ("dmy-dash", "dmy-slash", "ymd"):
        payload, decisions = build_payload(form, fmt)
        print(f"   attempt {fmt}: method={method} action={action}")
        print("      filled:", ", ".join(decisions) if decisions else "NO RECOGNIZED SEARCH FIELDS")
        if not decisions:
            continue
        try:
            if method == "post":
                out = s.post(action, data=payload, timeout=30)
            else:
                out = s.get(action, params=payload, timeout=30)
        except Exception as exc:
            print("      request failed:", repr(exc))
            continue
        print("      status:", out.status_code, "final:", out.url, "bytes:", len(out.content))
        if out.status_code != 200:
            continue
        snippets, urls = evidence(out.text)
        print("      lottery/year evidence snippets:", len(snippets))
        for item in snippets[:12]:
            print("         ", item[:650])
        print("      candidate document/pdf URLs:", len(urls))
        for u in urls[:20]:
            print("         ", u)
        successful_response = out
        successful_format = fmt
        if snippets:
            break

    print("\n=== SEARCH CONTRACT GATE SUMMARY ===")
    print("official portal reachable: YES")
    print("exact form contract captured:", "YES" if p.forms else "NO")
    print("script-side search evidence:", "YES" if script_hits else "NO")
    print("same-origin search submitted:", "YES" if successful_response is not None else "NO")
    print("accepted date format:", successful_format or "UNKNOWN")
    if successful_response is not None:
        snippets, urls = evidence(successful_response.text)
        pre_aug_signal = any("2017" in x and any(k in x.lower() for k in ("lottery", "bumper", "draw")) for x in snippets)
        print("pre-Aug 2017 lottery evidence returned:", "YES" if pre_aug_signal else "NO")
        print("candidate retrieval URLs returned:", len(urls))
    else:
        print("pre-Aug 2017 lottery evidence returned: UNKNOWN")
        print("candidate retrieval URLs returned: 0")
    print("No Collector result or Memory state was changed by this gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
