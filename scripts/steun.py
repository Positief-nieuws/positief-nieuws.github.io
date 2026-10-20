#!/usr/bin/env python3
"""Switch support online/offline, rebuild and publish in one command."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import support_visibility as support


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('status', choices=['online', 'offline'])
    parser.add_argument('--local', action='store_true', help='Alleen lokaal wijzigen, zonder publicatie')
    args = parser.parse_args()
    os.chdir(ROOT)
    if not args.local:
        if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
            parser.error('Bewaar eerst andere lokale wijzigingen; publicatie vereist een schone checkout.')
        if subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip() != 'main':
            parser.error('Publiceer vanaf main.')
        subprocess.run(['git', 'pull', '--ff-only', 'origin', 'main'], check=True)
    online = args.status == 'online'
    if online:
        if not support.BACKUP.exists():
            parser.error('Herstelkopie ontbreekt; niets gewijzigd.')
        support.restore()
    support.STATE.write_text(json.dumps({'enabled': online}, indent=2) + '\n')
    subprocess.run([sys.executable, 'build_editions.py'], check=True)
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], check=True)
    worker = ROOT / 'service-worker.js'
    import re
    worker.write_text(re.sub(r'positief-nieuws-v(\d+)', lambda m: 'positief-nieuws-v' + str(int(m[1]) + 1), worker.read_text(), count=1))
    if not args.local:
        subprocess.run(['git', 'add', '-A'], check=True)
        if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode:
            subprocess.run(['git', 'commit', '-m', 'Zet steunonderdelen ' + args.status], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print('Gepubliceerd; GitHub Pages verwerkt de wijziging.')


if __name__ == '__main__':
    main()
