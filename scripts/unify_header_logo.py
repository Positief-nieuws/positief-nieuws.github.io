#!/usr/bin/env python3
"""Houd het zichtbare Positief Nieuws-logo oranje, ook na nieuwe builds."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build_editions.py"
LOGO = "/sun-orange.svg"
code = SOURCE.read_text(encoding="utf-8")
old = code
code = code.replace('<img class="brand-sun" src="/sun-icon-512.png"', '<img class="brand-sun" src="/sun-orange.svg"')
lines = code.splitlines(keepends=True)
normalizer = '''        markup = re.sub(r'(<img class="brand-sun" src=")[^"]+(")', r'\\g<1>/sun-orange.svg\\2', markup)\n'''
if not any('markup = re.sub' in x and 'sun-orange.svg' in x and 'r"\\g<1>' in x for x in lines):
    matches = [i for i, line in enumerate(lines) if 'markup = re.sub(' in line and '<svg class="brand-sun"' in line]
    if len(matches) != 1:
        raise SystemExit(f"Headernormalizer ontbreekt of is ambigu: {len(matches)}")
    lines.insert(matches[0] + 1, normalizer)
code = "".join(lines)
if code != old:
    SOURCE.write_text(code, encoding="utf-8")
    print("Headergenerator blijvend gecorrigeerd.")

count = 0
changed = 0
for page in sorted(ROOT.rglob("*.html")):
    if any(part.startswith(".") or part in ("node_modules", ".venv") for part in page.relative_to(ROOT).parts):
        continue
    source = page.read_text(encoding="utf-8")
    if 'brand-sun' not in source:
        continue
    count += 1
    result = re.sub(
        r'<svg class="brand-sun".*?</svg>',
        '<img class="brand-sun" src="/sun-orange.svg" width="32" height="32" alt="" aria-hidden="true">',
        source, flags=re.S
    )
    result = re.sub(
        r'(<img class="brand-sun" src=")[^"]+(")',
        r'\g<1>/sun-orange.svg\2',
        result
    )
    if '<img class="brand-sun" src="/sun-orange.svg"' not in result:
        raise SystemExit(f"Kan logo niet gelijktrekken: {page}")
    if result != source:
        page.write_text(result, encoding="utf-8")
        changed += 1
print(f"{count} headerlogo's gecontroleerd, {changed} pagina's aangepast.")
if count < 50:
    raise SystemExit("Te weinig pagina's gecontroleerd.")
