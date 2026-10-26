#!/usr/bin/env python3
"""Create or update the Oct 26 layout test as a Buttondown draft, never send."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from buttondown_draft import (
    BUTTONDOWN_URL, build_body, build_preheader, edition_url, load_news, raw_edition_date,
)

TEST_SUBJECT = "[ONTWERPTEST] Positief nieuws · maandag 26 oktober 2026"
EXPECTED_DATE = "2026-10-26"
MARKER = "pn-layout-test-2026-10-26"

def request(method, uri, api_key, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        uri, data=body, method=method,
        headers={
            "Authorization": f"Token {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    token = os.environ.get("BUTTONDOWN_API_KEY")
    if not token:
        raise RuntimeError("BUTTONDOWN_API_KEY ontbreekt")

    data, nl, international, headlines = load_news()
    if raw_edition_date(data) != EXPECTED_DATE:
        raise RuntimeError("Editiedatum komt niet overeen. Test afgebroken.")
    if not data.get("meta", {}).get("publication_authorized"):
        raise RuntimeError("Editie niet redactioneel geautoriseerd.")
    if not data.get("meta", {}).get("personal_note", {}).get("text"):
        raise RuntimeError("Persoonlijke noot ontbreekt.")

    html = build_body(data, nl, international, headlines)
    for must in ('class="pn-edition-bar"', "#d6a13a",
                 "images/redactie/tom-portret-weergave.svg",
                 "Wat niet in de krant komt", "unsubscribe_url",
                 "Goed nieuws uit de wereld"):
        if must not in html:
            raise RuntimeError(f"Ontwerpcontrole faalt: {must}")
    if 'class="email-title"' in html:
        raise RuntimeError("Dubbele editie-kop aanwezig.")

    # Only draft creation or draft modification. Never send, schedule or publish.
    payload = {
        "subject": TEST_SUBJECT,
        "body": html,
        "status": "draft",
        "template": "naked",
        "canonical_url": edition_url(data),
        "description": build_preheader(data, nl),
        "metadata": {"pn_test_marker": MARKER},
    }

    params = urllib.parse.urlencode({
        "status": "draft",
        "creation_date__start": "2026-10-25",
        "excluded_fields": "body",
    })
    listing = request("GET", f"{BUTTONDOWN_URL}?{params}", token)
    matches = [
        item for item in listing.get("results", [])
        if item.get("subject") == TEST_SUBJECT and item.get("status") == "draft"
    ]
    if len(matches) > 1:
        raise RuntimeError("Meerdere layout-testconcepten gevonden; niet wijzigen.")
    if matches:
        draft_id = matches[0]["id"]
        result = request("PATCH", f"{BUTTONDOWN_URL}/{draft_id}", token, payload)
        action = "bijgewerkt"
    else:
        result = request("POST", BUTTONDOWN_URL, token, payload)
        draft_id = result.get("id")
        action = "aangemaakt"

    if not draft_id:
        raise RuntimeError("Buttondown gaf geen concept-ID terug.")
    check = request("GET", f"{BUTTONDOWN_URL}/{draft_id}", token)
    if check.get("status") != "draft" or check.get("subject") != TEST_SUBJECT:
        raise RuntimeError("Conceptstatus of onderwerp kon niet bevestigd worden.")
    actual_body = str(check.get("body") or "")
    if 'pn-edition-bar' not in actual_body or 'tom-portret-weergave.svg' not in actual_body:
        raise RuntimeError("Ontwerp niet bevestigd in Buttondown.")

    print(f"SUCCES: Buttondown-ontwerpconcept {action}")
    print(f"ID: {draft_id}")
    print(f"STATUS: {check['status']}")
    print(f"SUBJECT: {TEST_SUBJECT}")
    print(f"HTML-LENGTE: {len(actual_body)}")
    print("VERZONDEN: nee")
    print(f"BUTTONDOWN: https://buttondown.com/emails/{draft_id}")

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        sys.exit(1)
