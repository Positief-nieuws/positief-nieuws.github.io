#!/usr/bin/env python3
"""Alleen Buttondown concept. Nooit versturen."""
import json, os, urllib.request
from pathlib import Path
import buttondown_draft as bd

api_key=os.environ.get("BUTTONDOWN_API_KEY","")
if not api_key: raise SystemExit("Buttondown API-key ontbreekt")
data,nl,world,headlines=bd.load_news()
if bd.raw_edition_date(data)!="2026-11-02": raise SystemExit("Verkeerde editie")
subject=bd.build_subject(data)
body=bd.build_body(data,nl,world,headlines)
preheader=bd.build_preheader(data,nl)
if body.count('class="story-card"')!=15: raise SystemExit("Niet precies 15 kaarten")
Path("buttondown-concept-2026-11-02.html").write_text(body,encoding="utf-8")
req=urllib.request.Request("https://api.buttondown.com/v1/emails?status=draft",headers={"Authorization":"Token "+api_key,"Accept":"application/json"})
with urllib.request.urlopen(req,timeout=30) as response: existing=json.load(response)
if any(x.get("subject")==subject and x.get("status")=="draft" for x in existing.get("results",[])):
    print("Bestaand concept aangetroffen; geen duplicaat aangemaakt")
else:
    result=bd.create_draft(api_key,subject,body,data,preheader)
    if result.get("status")!="draft": raise SystemExit("Onverwachte status na aanmaken")
    print("Buttondown concept aangemaakt, niet verzonden. ID:",result.get("id"))
if not (data.get("meta",{}).get("personal_note") or {}).get("text"):
    print("LET OP: persoonlijke noot ontbreekt. Vul voor verzending aan.")
