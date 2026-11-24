"""Read-only newsletter smoke check. Never POSTs or creates subscribers."""
import argparse
import datetime as dt
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://positief-nieuws.nl'
HOSTED_FORM = 'https://positief-nieuws.kit.com/905971a843'
ACTION = 'https://app.kit.com/forms/10226383/subscriptions'
EVENTS = ('newsletter_view', 'newsletter_cta_click', 'newsletter_form_submit', 'newsletter_landing_view')
EXPECTED = {'/': {'home_hero', 'home_end'}, '/nieuwsbrief/': {'landing_main'}}

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.forms, self.scripts, self.ids, self.links = [], [], set(), []
        self.current = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag == 'a': self.links.append(a)
        if tag == 'form':
            self.current = {'attrs': a, 'inputs': []}
            self.forms.append(self.current)
        if tag in ('input', 'button') and self.current is not None:
            self.current['inputs'].append(a)
        if tag == 'script' and a.get('src'): self.scripts.append(a['src'])

    def handle_endtag(self, tag):
        if tag == 'form': self.current = None


def form_checks(text, path, expected=None):
    page = Page(text)
    rows = []
    for placement in sorted(EXPECTED[path] if expected is None else expected):
        forms = [f for f in page.forms if f['attrs'].get('data-newsletter-placement') == placement]
        rows.append((placement, 'formulier aanwezig (exact één)', len(forms) == 1))
        for f in forms:
            a, fields = f['attrs'], f['inputs']
            rows.extend([
                (placement, 'Kit action en POST', a.get('action') == ACTION and a.get('method', '').lower() == 'post'),
                (placement, 'emailveld', len([i for i in fields if i.get('name') == 'email_address']) == 1 and any(i.get('name') == 'email_address' and i.get('type') == 'email' and 'required' in i and 'disabled' not in i for i in fields)),
                (placement, 'verzendknop', any(i.get('type') == 'submit' and 'disabled' not in i for i in fields)),
                (placement, 'geen client-side succes of afwijkende redirect', not any(k in a for k in ('onsubmit', 'target')) and not any(i.get('name') in ('redirect', 'redirect_url', 'next', 'type') for i in fields)),
            ])
    for link in page.links:
        if link.get('data-newsletter-cta') and link.get('href', '').startswith('#'):
            rows.append(('link', 'formulieranker bestaat', link['href'][1:] in page.ids))
    rows.append(('alle', 'gedeelde meetcode gekoppeld', any(urllib.parse.urlsplit(s).path == '/edition-analytics.js' for s in page.scripts)))
    return rows



def inventory(root=Path('.')):
    """Discover actual forms AND independently required placements, so removal fails."""
    expected = {k: set(v) for k, v in EXPECTED.items()}
    for slug in ('mens', 'natuur-en-klimaat', 'gezondheid', 'energie-en-innovatie',
                 'wetenschap', 'cultuur', 'economie', 'sport'):
        expected['/' + slug + '/'] = {'topic_inline'}
    rows = []
    for file in sorted(root.rglob('*.html')):
        if '.git' in file.parts: continue
        relative = file.relative_to(root)
        path = '/' + (str(relative.parent) + '/' if relative.name == 'index.html' and str(relative.parent) != '.' else '' if relative.name == 'index.html' else str(relative))
        text = file.read_text()
        page = Page(text)
        required = 'article_end' if relative.parts[0] == 'artikelen' else 'special_end' if relative.parts[0] == 'specials' else None
        if required and relative.name == 'index.html': expected.setdefault(path, set()).add(required)
        for f in page.forms:
            a = f['attrs']
            if a.get('action') != ACTION and not a.get('data-newsletter-placement'): continue
            placement = a.get('data-newsletter-placement', 'MISSING')
            expected.setdefault(path, set()).add(placement)
            rows.append(dict(page=path, kind='form', placement=placement, code=str(relative),
                             action=a.get('action'), method=a.get('method'), fields=f['inputs']))
        for a in page.links:
            if a.get('data-newsletter-cta') or 'nieuwsbrief' in a.get('href', ''):
                rows.append(dict(page=path, kind='link', placement=a.get('data-newsletter-cta', ''),
                                 code=str(relative), target=a.get('href')))
    return expected, rows

def get(url, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'PositiefNieuws-ReadOnlyMonitor/1.0', **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200: raise ValueError('Geen HTTP 200')
        if urllib.parse.urlsplit(response.url).hostname != urllib.parse.urlsplit(url).hostname:
            raise ValueError('Onverwachte redirect naar ander domein')
        return response.read().decode('utf-8')


def check_hosted_form():
    """Read-only external check; access restrictions do not prove a broken form."""
    retryable = {408, 429, 500, 502, 503, 504}
    for attempt in range(1, 4):
        try:
            hosted = Page(get(HOSTED_FORM))
            ok = any(any(i.get('name') == 'email_address' for i in f['inputs']) for f in hosted.forms)
            return ('PASS' if ok else 'FAIL',
                    'HTTP 200; poging ' + str(attempt) +
                    ('; formulier gevonden; geen POST of bewijs van registratie' if ok else '; geen email_address-formulier gevonden'))
        except urllib.error.HTTPError as error:
            code = error.code
            detail = f'HTTP {code}; poging {attempt}/3'
            if code in retryable and attempt < 3:
                time.sleep(2 ** (attempt - 1))
                continue
            if code in (401, 403, 429):
                return 'MANUAL', detail + '; geautomatiseerde toegang geweigerd of begrensd; controleer handmatig'
            return 'FAIL', detail + '; externe pagina niet verifieerbaar'
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempt < 3:
                time.sleep(2 ** (attempt - 1))
                continue
            return 'FAIL', f'{type(error).__name__}; poging {attempt}/3; externe pagina niet bereikbaar'
        except Exception as error:
            return 'FAIL', f'{type(error).__name__}; poging {attempt}/3; externe pagina niet verifieerbaar'


def run(local=False):
    rows = []
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    def add(location, point, status, detail=''):
        rows.append(dict(date=now, location=location, checkpoint=point, status=status, detail=detail))
    texts = {}
    expected, _ = inventory()
    from concurrent.futures import ThreadPoolExecutor
    def read(path):
        try:
            file = Path(path.lstrip('/') or '.')
            if path.endswith('/'): file = file / 'index.html'
            return path, (file.read_text() if local else get(BASE + path)), None
        except Exception as error:
            return path, None, error
    with ThreadPoolExecutor(max_workers=4) as pool:
        loaded = list(pool.map(read, expected))
    for path, text, error in loaded:
        try:
            if error: raise error
            texts[path] = text
            add(path, 'pagina laden' if not local else 'bronbestand lezen', 'PASS')
            for placement, point, ok in form_checks(text, path, expected[path]):
                add(path + '#' + placement, point, 'PASS' if ok else 'FAIL')
        except Exception as e:
            add(path, 'pagina laden', 'FAIL', type(e).__name__)
    try:
        script = Path('edition-analytics.js').read_text() if local else get(BASE + '/edition-analytics.js')
        for event in EVENTS:
            add('alle formulieren', 'meetcode ' + event, 'PASS' if "track('" + event + "'" in script else 'FAIL', 'Broncontrole; geen bewijs van ontvangst')
    except Exception as e:
        add('alle formulieren', 'meetcode ophalen', 'FAIL', type(e).__name__)
    if not local:
        status, detail = check_hosted_form()
        add('Kit-formulier', 'GET bereikbaarheid en formulier', status, detail)
    # No credentials are created or copied from browser sessions.
    key = os.environ.get('SIMPLE_ANALYTICS_API_KEY')
    if local or not key:
        add('Simple Analytics', 'eventontvangst', 'MANUAL', 'Geen API-sleutel; controleer Events over de afgelopen 7 volledige dagen')
    else:
        end = dt.date.today() - dt.timedelta(days=1)
        start = end - dt.timedelta(days=6)
        for path in EXPECTED:
            params = urllib.parse.urlencode(dict(version=6, fields='pageviews', start=str(start), end=str(end), timezone='Europe/Amsterdam', events=','.join(EVENTS), pages=path.rstrip('/') or '/'))
            try:
                data = json.loads(get('https://simpleanalytics.com/positief-nieuws.nl.json?' + params, {'Api-Key': key}))
                if data.get('ok') is False or not isinstance(data.get('events'), list): raise ValueError('Ongeldig API-resultaat')
                counts = {e['name']: e['total'] for e in data['events']}
                for event in (EVENTS if path == '/nieuwsbrief/' else EVENTS[:3]):
                    count = counts.get(event, 0)
                    if not isinstance(count, (int, float)) or count < 0: raise ValueError('Ongeldige eventtelling')
                    add(path, 'ontvangen ' + event, 'PASS' if count > 0 else 'WARN', f'{start} t/m {end}: {count}; nul kan ook weinig verkeer betekenen')
            except Exception as e:
                add(path, 'eventontvangst', 'FAIL', type(e).__name__)
    add('Kit', 'Nederlandse bevestigingsmail en double opt-in', 'MANUAL', 'Geen account-API aangesloten; controleer maandelijks in dashboard')
    add('Kit + mailbox', 'inschrijven, mail, bevestigen en opruimen', 'MANUAL', 'Alleen met gecontroleerd testadres; nooit automatisch')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--output', default='newsletter-test-results')
    args = parser.parse_args()
    rows = run(args.local)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    _, entries = inventory()
    (out / 'inventory.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
    (out / 'results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    lines = ['# Nieuwsbriefcontrole', '', 'Broncontrole is geen end-to-endtest. Formulierinzending ≠ bevestigde abonnee.', '', '| Datum (UTC) | Locatie | Controlepunt | Status | Toelichting |', '| --- | --- | --- | --- | --- |']
    for r in rows:
        lines.append('| ' + ' | '.join(str(r[k]).replace('|', '/') for k in ('date','location','checkpoint','status','detail')) + ' |')
    report = '\n'.join(lines) + '\n'
    (out / 'report.md').write_text(report)
    print(report)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as f: f.write(report)
    hosted = next((r for r in rows if r['location'] == 'Kit-formulier'), None)
    if hosted and hosted['status'] == 'MANUAL':
        print('::warning::Kit-formulier niet automatisch verifieerbaar: ' + hosted['detail'])
    output = os.environ.get('GITHUB_OUTPUT')
    if output and hosted:
        with open(output, 'a') as f:
            f.write('hosted_verified=' + ('true' if hosted['status'] == 'PASS' else 'false') + '\n')
    # Warnings require review; MANUAL is explicitly partial, never a technical PASS.
    return 1 if any(r['status'] in ('FAIL', 'WARN') for r in rows) else 0

if __name__ == '__main__':
    raise SystemExit(main())
