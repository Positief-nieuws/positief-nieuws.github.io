"""Reversible publication switch for support content (backup excluded by Jekyll)."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'support-settings.json'
BACKUP = ROOT / '_offline/steun/content.json'
PATTERNS = [
    r'<section\b[^>]*class="(?:support|support-teaser)"[^>]*>.*?</section>',
    r'<p\b[^>]*>\s*<a\b[^>]*href="/steun/"[^>]*>.*?</a>\s*</p>',
    r'(?:\s*·\s*)?<a\b[^>]*href="/steun/"[^>]*>.*?</a>',
    r'<h2>Vrijwillige bijdragen</h2>\s*<p>.*?</p>',
]


def enabled():
    return not STATE.exists() or json.loads(STATE.read_text())['enabled']


def hide(markup, fragments):
    def replace(match):
        fragment = match.group()
        key = hashlib.sha256(fragment.encode()).hexdigest()
        fragments[key] = fragment
        return '<!-- support-offline:' + key + ' -->'
    for pattern in PATTERNS:
        markup = re.sub(pattern, replace, markup, flags=re.S)
    return markup


def apply():
    if enabled():
        return
    backup = json.loads(BACKUP.read_text()) if BACKUP.exists() else {'fragments': {}}
    page = ROOT / 'steun/index.html'
    if page.exists():
        backup['page'] = page.read_text()
        page.unlink()
    for path in ROOT.rglob('*.html'):
        if '.git' in path.parts or '_offline' in path.parts:
            continue
        original = path.read_text()
        changed = hide(original, backup['fragments'])
        if changed != original:
            path.write_text(changed)
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(json.dumps(backup, ensure_ascii=False, indent=2) + '\n')


def restore():
    backup = json.loads(BACKUP.read_text())
    def replace(match):
        return backup['fragments'][match.group(1)]
    for path in ROOT.rglob('*.html'):
        if '.git' in path.parts or '_offline' in path.parts:
            continue
        original = path.read_text()
        changed = re.sub(r'<!-- support-offline:([a-f0-9]{64}) -->', replace, original)
        if changed != original:
            path.write_text(changed)
    page = ROOT / 'steun/index.html'
    page.parent.mkdir(exist_ok=True)
    page.write_text(backup['page'])
