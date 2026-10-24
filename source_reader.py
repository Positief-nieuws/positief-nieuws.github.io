"""Existing local newsroom's Google News resolver, reused for selected sources only."""
import html
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import urllib.error

def fetch(url,timeout=10,redirects=0):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http','https') or (parsed.hostname or '').lower() in ('localhost','127.0.0.1','::1'):raise ValueError('Bronlink is geen openbare HTTP(S)-URL')
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 PositiefNieuwsLocal/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.read(),r.geturl(),r.headers.get('Content-Type','')
    except urllib.error.HTTPError as e:
        if e.code==308 and e.headers.get('Location') and redirects<5:
            target=urllib.parse.urljoin(url,e.headers['Location'])
            if urllib.parse.urlsplit(target).scheme not in ('http','https'):raise ValueError('Ongeldige doorverwijzing')
            return fetch(target,timeout,redirects+1)
        raise
    except urllib.error.URLError:
        # macOS's bundled Python 3.9 has TLS failures on some public publishers.
        # The system curl uses a separate, validated TLS implementation.
        curl=shutil.which('curl')
        if not curl:raise
        p=subprocess.run([curl,'--silent','--show-error','--fail','--location','--max-time',str(timeout),'--proto','=https,http','--proto-redir','=https,http','--write-out','\n%{url_effective}\n%{content_type}',url],capture_output=True)
        if p.returncode:raise RuntimeError('Bron niet bereikbaar via beveiligde verbinding')
        body,final,kind=p.stdout.rsplit(b'\n',2)
        return body,final.decode(),kind.decode()

def google_original(url):
    """Resolve the opaque RSS wrapper; never treat search snippets as article evidence.

    Wire protocol documented by SSujitX/google-news-url-decoder (_parse.py).
    This independent stdlib adapter is best effort; Google can change its endpoint.
    """
    if urllib.parse.urlsplit(url).hostname!='news.google.com':return url
    identifier=urllib.parse.urlsplit(url).path.rstrip('/').split('/')[-1]
    page=fetch('https://news.google.com/rss/articles/'+identifier+'?hl=en-US&gl=US&ceid=US%3Aen',10)[0].decode(errors='replace')
    signature=re.search(r'data-n-a-sg="([^"]+)"',page);stamp=re.search(r'data-n-a-ts="([^"]+)"',page)
    if not signature or not stamp:raise ValueError('Google-verwijzing mist resolvergegevens')
    context=[['X','X',['X','X'],None,None,1,1,'US:en',None,1,None,None,None,None,None,0,1],'X','X',1,[1,1,1],1,1,None,0,0,None,0]
    request=['garturlreq',context,identifier,int(stamp.group(1)),html.unescape(signature.group(1))]
    body=urllib.parse.urlencode({'f.req':json.dumps([[['Fbv4je',json.dumps(request),None,'0']]])}).encode()
    req=urllib.request.Request('https://news.google.com/_/DotsSplashUi/data/batchexecute',data=body,headers={'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=10) as r:text=r.read().decode()
    for line in text.splitlines():
        if not line.startswith('[['):continue
        try:rows=json.loads(line)
        except ValueError:continue
        for row in rows:
            if isinstance(row,list) and len(row)>2 and row[1]=='Fbv4je':
                payload=json.loads(row[2])
                if payload[0]=='garturlres' and str(payload[1]).startswith('https://'):return payload[1]
    raise ValueError('Google-verwijzing kon niet worden opgelost')
