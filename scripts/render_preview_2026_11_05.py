"""Render only this draft for review. Does not publish, send email, or approve evidence."""
import json
import os
import re
import shutil
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
import build_editions as site
import buttondown_draft as bd
from analytics_policy import protect_markup
from social_sharing import enhance as sharing_markup
from article_layout import order_article_actions

DATE='2026-11-05'
news=json.loads(Path('nieuws.json').read_text())
assert news['meta']['edition_date']==DATE
assert news['meta']['status']=='draft'
assert news['meta']['publication_authorized'] is False
site.validate_positive_articles(news)
cache=site._load_pixabay_cache()
# Existing licensed files can be reused without a new API request.
for item in news['nl']+news['int']:
    query=item['image_query']
    if query.startswith('id:'):
        pid=int(query[3:])
        current=cache.get(f'{DATE}/{item["article_slug"]}')
        existing=current if current and current.get('pixabay_id')==pid and Path(current.get('image_path','').lstrip('/')).is_file() else next((v for v in cache.values() if v.get('pixabay_id')==pid and Path(v.get('image_path','').lstrip('/')).is_file()),None)
        if existing:
            cache[f'{DATE}/{item["article_slug"]}']={**existing,'query':query}
site._write_pixabay_cache(cache)
pages=site.write_article_pages([(DATE,news)])
site.update_homepage(news)
edition_dir=Path('edities')/DATE
edition_dir.mkdir(exist_ok=True)
edition_markup=site.render_edition(news,DATE)
note=news['meta']['personal_note']
note_markup=f'<section class="section"><div class="shell"><h2>{site.esc(note["title"])}</h2><p>{site.esc(note["text"])}</p><p><strong>Tom</strong></p></div></section>'
edition_markup=edition_markup.replace('<main>','<main>'+note_markup,1)
(edition_dir/'index.html').write_text(edition_markup)
# Apply the normal article finishing passes only to this edition, preserving older pages.
for path in [Path('index.html'),edition_dir/'index.html',*Path('artikelen',DATE).glob('*/index.html')]:
    markup=path.read_text()
    markup=re.sub(r'<link rel="stylesheet" href="/site-theme.css[^"]*">','',markup)
    markup=markup.replace('</head>',f'<link rel="stylesheet" href="{site.SITE_THEME_HREF}"></head>',1)
    markup=markup.replace('/sun-icon-512.png','/sun-orange.svg')
    markup=protect_markup(order_article_actions(sharing_markup(markup,path)))
    path.write_text(markup)
# Run the established signup finishing pass in an isolated scope. Its normal
# all-pages traversal must not rewrite historical pages for this concept.
from newsletter_conversion import apply as finish_signup
scoped=[Path('index.html'),edition_dir/'index.html',*Path('artikelen',DATE).glob('*/index.html')]
with tempfile.TemporaryDirectory(prefix='pn-concept-forms-') as temp:
    scope=Path(temp)
    for path in [*scoped,Path('nieuws.json')]:
        target=scope/path
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    os.chdir(scope)
    try:
        site.refresh_edition_analytics()
        finish_signup()
    finally:
        os.chdir(ROOT)
    for path in scoped:shutil.copy2(scope/path,path)
out=Path('concepten')/DATE
out.mkdir(parents=True,exist_ok=True)
(out/'nieuwsbrief.html').write_text(bd.build_body(news,news['nl'],news['int'],news['headlines']))
(out/'onderwerp.txt').write_text(bd.build_subject(news)+'\n')

# Package a separate preview tree. Existing articles/styles are copied unchanged.
preview=Path('.preview-site')
if preview.exists():shutil.rmtree(preview)
preview.mkdir()
for p in ROOT.iterdir():
    if p.name.startswith('.') or p.name in {'kandidaten.json','source_state.json','source_health.json','selectie','redactie','scripts','tests','concepten'}:continue
    if p.is_file() and p.suffix in {'.html','.css','.js','.png','.svg','.ico','.json','.webmanifest'}:shutil.copy2(p,preview/p.name)
for name in ['artikelen','images','edities','nieuwsbrief','over','contact','zoeken','onderwerpen','specials']:
    if Path(name).exists():shutil.copytree(name,preview/name,dirs_exist_ok=True)
(preview/'data').mkdir(exist_ok=True)
shutil.copy2('data/pixabay-images.json',preview/'data/pixabay-images.json')
shutil.copytree(out,preview/'concepten'/DATE,dirs_exist_ok=True)
for p in preview.rglob('*.html'):
    markup=p.read_text()
    # All preview navigations stay on the preview host, without changing production canonical URLs.
    markup=re.sub(r'(href=["\'])https://positief-nieuws.nl/(artikelen|edities)/',r'\1/\2/',markup)
    markup=markup.replace('</head>','<meta name="robots" content="noindex,nofollow"></head>',1)
    if p==preview/'index.html':
        markup=markup.replace('<body', '<body',1)
        markup=re.sub(r'(<body\b[^>]*>)',r'\1<div style="padding:10px;text-align:center;background:#fff1c9;color:#17382b;font:14px Arial">Concept 5 november. Nog niet publicatieklaar.</div>',markup,count=1)
    p.write_text(markup)
cache=site._load_pixabay_cache()
images=[]
for item in news['nl']+news['int']:
    entry=cache.get(f'{DATE}/{item["article_slug"]}')
    images.append({'slug':item['article_slug'],'query':item['image_query'],'found':bool(entry),'image':entry})
manifest={'edition_date':DATE,'status':'draft','article_pages':len(pages),'images_found':sum(x['found'] for x in images),'images':images,'published':False,'email_sent':False}
(out/'beeldcontrole.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(out/'beeldcontrole.json',preview/'concepten'/DATE/'beeldcontrole.json')
print(json.dumps({k:v for k,v in manifest.items() if k!='images'},ensure_ascii=False))
