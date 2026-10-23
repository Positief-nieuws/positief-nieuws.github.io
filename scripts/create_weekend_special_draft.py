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
    # Idempotency: do not create a duplicate if the draft already exists.
    next_url = URL + "?page_size=100"
    for _ in range(12):
        listing = request("GET", next_url, key)
        emails = listing.get("results", listing.get("data", [])) if isinstance(listing, dict) else listing
        if not isinstance(emails, list):
            raise RuntimeError("Onverwacht Buttondown API antwoord. Geen concept gemaakt.")
        for email in emails:
            if email.get("subject") == SUBJECT and email.get("status") in ("draft", "scheduled", "sent", "published"):
                print("Bestaat al:", email.get("id"), email.get("status"))
                return
        next_url = listing.get("next") if isinstance(listing, dict) else None
        if not next_url:
            break
    else:
        raise RuntimeError("Meer paginatie dan verwacht. Geen concept gemaakt om duplicaten te voorkomen.")
    payload = {"subject": SUBJECT, "body": body, "status": "draft",
               "template": "naked", "canonical_url": CANONICAL,
               "description": "Nieuwe Weekend Special, Nederland gaat óók vooruit en drie recente nieuwsverhalen."}
    draft = request("POST", URL, key, payload)
    if draft.get("status") != "draft":
        raise RuntimeError("Buttondown antwoordde zonder bevestigde conceptstatus: " + str(draft.get("status")))
    print("Buttondown concept aangemaakt:", draft.get("id"), draft.get("status"))

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        print("FOUT:", exc, file=sys.stderr)
        sys.exit(1)
