#!/usr/bin/env python3
"""Read-only installation check and handoff for the pn go editorial command."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'AGENTS.md', 'redactie/PN_WORKFLOW.md', 'redactie/weeknotities.md',
    'REDACTIE.txt', 'selection_preferences.json', 'editorial_policy.json',
    'sources.json', 'kandidaten.json', 'source_health.json', 'source_state.json',
    'selection_check.py', 'editorial_check.py', 'prepare_dossier.py',
    'build_editions.py', 'buttondown_draft.py', 'docs/analytics-testing.md',
    'images/redactie/manifest.json',
)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['go'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    errors = []
    for name in REQUIRED:
        path = ROOT / name
        if not path.is_file() or not path.read_bytes():
            errors.append(name)
        else:
            print(f'GEVONDEN {name}')
    try:
        manifest = json.loads((ROOT/'images/redactie/manifest.json').read_text())
        if len(manifest['portraits']) != 2:
            raise ValueError('Er moeten twee portretten zijn')
        for entry in manifest['portraits']:
            content = (ROOT/entry['path']).read_bytes()
            if not content.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(content).hexdigest() != entry['sha256']:
                raise ValueError(f"Ongeldig portret: {entry['path']}")
            print(f"PORTRET OK {entry['path']}")
        pool = json.loads((ROOT/'kandidaten.json').read_text())
        meta = pool['meta']
        print(f"KANDIDATEN {meta.get('generated_at')}; aantal={len(pool['all_candidates'])}; collection_complete={meta.get('collection_complete')}")
        if meta.get('registry_sha256') != hashlib.sha256((ROOT/'sources.json').read_bytes()).hexdigest():
            print('LET OP bronregister gewijzigd: verversen vereist')
        if meta.get('collection_complete') is not True:
            print('LET OP onvolledige bronrun: fouten/dekking onderzoeken bij volledige proef')
        print('ACTUALITEIT bij volledige proef toetsen aan gekozen editiedag; deze check doet geen scouting.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if errors:
        print('INSTALLATIE NIET GEREED: ' + '; '.join(errors))
        return 1
    print('INSTALLATIE OK — uitsluitend vindbaarheid/integriteit; geen journalistieke proef afgerond.')
    print('Geen bestanden geschreven, netwerk aangeroepen, build gestart of externe actie uitgevoerd.')
    if not args.dry_run:
        print('AI-REDACTEUR: lees nu alle instructies en weeknotities en voer de volledige lokale proef uit volgens redactie/PN_WORKFLOW.md. Deze launcher doet dat onderzoek niet zelf.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
