"""Central source configuration; no publication or external writes."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parent
FREQUENCIES = {'every_edition': 20, 'twice_weekly': 72, 'weekly': 168, 'manual': None}

def load_registry(path=None):
    data = json.loads(Path(path or ROOT / 'sources.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('sources'), list):
        raise ValueError('Ongeldig bronnenregister.')
    source_ids, channel_ids, register_ids = set(), set(), set()
    for source in data['sources']:
        sid = source['source_id']
        if sid in source_ids or source['category'] not in {'A','B','C'}:
            raise ValueError(f'Dubbele of ongeldige bron: {sid}')
        source_ids.add(sid)
        if source['check_frequency'] not in FREQUENCIES:
            raise ValueError(f'Ongeldige cadans: {sid}')
        if source['geography'] not in {'nl','int'}:
            raise ValueError(f'Ongeldig bereik: {sid}')
        for rid in source.get('register_ids', []):
            if rid in register_ids: raise ValueError(f'Dubbel bijlage-ID: {rid}')
            register_ids.add(rid)
        for channel in source['channels']:
            cid = channel['channel_id']
            if cid in channel_ids or channel['mode'] not in {'rss','google_site','curated_html'}:
                raise ValueError(f'Dubbel of ongeldig kanaal: {cid}')
            channel_ids.add(cid)
            target = channel.get('url') if channel['mode'] != 'google_site' else 'https://' + channel.get('domain','')
            parsed = urlsplit(target or '')
            if parsed.scheme not in {'http','https'} or not parsed.hostname:
                raise ValueError(f'Ongeldig adres: {cid}')
            if channel['mode'] == 'google_site' and (parsed.path or parsed.query or parsed.fragment):
                raise ValueError(f'Zoekkanaal vraagt alleen een domein: {cid}')
            if channel.get('language') not in {'nl','en','de'}:
                raise ValueError(f'Ongeldige taal: {cid}')
            if channel.get('enabled') and channel.get('origin') == 'new' and channel.get('verification_status') != 'verified':
                raise ValueError(f'Nieuw kanaal nog niet geverifieerd: {cid}')
    return data

def active_channels(registry=None):
    output = []
    for source in (registry or load_registry())['sources']:
        if not source.get('enabled') or source['category'] == 'C' or source['check_frequency'] == 'manual': continue
        for channel in source['channels']:
            if not channel.get('enabled'): continue
            output.append({**channel, 'source_id':source['source_id'], 'organization_id':source['organization_id'],
                'publisher':source['name'], 'region':source['geography'], 'source_category':source['category'],
                'priority':source['priority'], 'check_frequency':source['check_frequency']})
    return output

def canonical_url(url):
    p = urlsplit(str(url or '').strip())
    # Query parameters can identify an actual document. Only remove known tracking.
    query = [(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid','mc_cid','mc_eid'}]
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),urlencode(sorted(query)),''))

def load_history(directory=None):
    records = []
    editions=Path(directory or ROOT/'edities')
    for path in sorted(editions.glob('????-??-??.json')):
        # Fail visibly on corrupt history instead of silently weakening duplicate checks.
        data = json.loads(path.read_text(encoding='utf-8'))
        dossier_path=editions.parent/'redactie'/f'{path.stem}.json'
        dossier=json.loads(dossier_path.read_text(encoding='utf-8')) if dossier_path.exists() else {}
        for section in ('nl','int','headlines'):
            for index,item in enumerate(data.get(section,[])):
                key=section+':'+str(item.get('article_slug') or index)
                record=dossier.get('articles',{}).get(key,{})
                metadata={k:record[k] for k in ('topic_id','doi','report_id','organization_id') if record.get(k)}
                if record.get('evidence',{}).get('primary_url'):
                    metadata['primary_url']=record['evidence']['primary_url']
                records.append({**item,**metadata,'edition_date':path.stem,'section':section})
    return records

def history_matches(item, history):
    matches = []
    identifiers = {'topic_id','doi','report_id'}
    urls = {canonical_url(item.get(k)) for k in ('url','primary_url') if item.get(k)}
    for previous in history:
        same_url = bool(urls & {canonical_url(previous.get(k)) for k in ('url','primary_url') if previous.get(k)})
        same_id = any(item.get(k) and item.get(k)==previous.get(k) for k in identifiers)
        if same_url or same_id:
            matches.append({'edition_date':previous['edition_date'],'title':previous.get('title',''), 'kind':'url_or_id'})
    return matches

def due(channel, state, now):
    last = state.get('last_success_at')
    if not last: return True
    # Failed runs retry immediately. A cached channel remains usable during outage.
    if state.get('last_error'): return True
    try: stamp = datetime.fromisoformat(last.replace('Z','+00:00'))
    except (ValueError,TypeError): return True
    if stamp.tzinfo is None: return True
    return now - stamp >= timedelta(hours=FREQUENCIES[channel['check_frequency']])

def atomic_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
