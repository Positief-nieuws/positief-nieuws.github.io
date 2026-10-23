#!/usr/bin/env python3
"""Create a single draft for the 23 October 2026 Weekend Special. Never send."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

URL = "https://api.buttondown.com/v1/emails"
SUBJECT = "Weekend Special | Waarom lijkt de wereld slechter dan hij is?"
HTML = Path(".github/buttondown-drafts/2026-10-23-weekend-special.html")
CANONICAL = "https://positief-nieuws.nl/specials/waarom-nieuws-zo-negatief-lijkt/"
MARKER = "pn-weekendspecial-2026-10-23"

def request(method, url, key, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Token {key}", "Accept": "application/json",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    key = os.environ.get("BUTTONDOWN_API_KEY")
    if not key:
        raise RuntimeError("BUTTONDOWN_API_KEY ontbreekt.")
    body = HTML.read_text(encoding="utf-8")
    if not all(s in body for s in ("Waarom lijkt de wereld slechter", "Nederland gaat óók vooruit", "kwelders-beschermen-kust")):
        raise RuntimeError("Nieuwsbrief mist een of meer inhoudsblokken.")
    # Update the existing, explicitly confirmed draft. Never create/send a duplicate.
    draft_id = "em_24p4w79zca8xrvr1c6cve8g0a8"
    draft_url = f"{URL}/{draft_id}"
    existing = request("GET", draft_url, key)
    if existing.get("id") != draft_id or existing.get("subject") != SUBJECT:
        raise RuntimeError("Bestaand concept kon niet veilig worden geïdentificeerd.")
    if existing.get("status") != "draft":
        raise RuntimeError("Bestaand bericht is geen concept; niets bijgewerkt.")
    if "Help je mee om het nieuwslandschap" not in body or "sunrise-7713649" not in body:
        raise RuntimeError("Nieuwe tekst of kleurenfoto ontbreekt; niets bijgewerkt.")
    changed = request("PATCH", draft_url, key, {"body": body})
    if changed.get("status") != "draft":
        raise RuntimeError("Buttondown heeft geen conceptstatus teruggegeven.")
    check = request("GET", draft_url, key)
    if check.get("status") != "draft":
        raise RuntimeError("Concept is niet meer in draftstatus.")
    saved = str(check.get("body") or "")
    if "Help je mee om het nieuwslandschap" not in saved or "sunrise-7713649" not in saved:
        raise RuntimeError("De gewijzigde inhoud kon niet bevestigd worden.")
    print("Buttondown-concept veilig bijgewerkt:", draft_id, check.get("status"))

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        print("FOUT:", exc, file=sys.stderr)
        sys.exit(1)
