"""Idempotent newsletter enhancements, also applied after future site builds."""
from pathlib import Path
import re
from html import escape

def block(placement, title='Het goede nieuws, gewoon in je inbox.', topic=False):
    intro = 'Ontvang elke maandag en donderdag een selectie positieve ontwikkelingen.' if topic else 'Ontvang elke maandag en donderdag een selectie positief nieuws. Gratis, overzichtelijk en in een paar minuten gelezen.'
    return f'''<!-- newsletter:{placement}:start --><section class="pn-newsletter" aria-labelledby="{placement}-title"><div><h2 id="{placement}-title">{escape(title)}</h2><p>{intro}</p></div><form action="https://buttondown.com/api/emails/embed-subscribe/positiefnieuws" method="post" data-newsletter-placement="{placement}"><label for="{placement}-email">E-mailadres</label><div class="pn-newsletter-row"><input id="{placement}-email" type="email" name="email" autocomplete="email" placeholder="jij@voorbeeld.nl" required><button type="submit">Gratis aanmelden</button></div><input type="hidden" name="embed" value="1"><input type="hidden" name="metadata__signup_source" value="{placement}"><p class="pn-newsletter-note">Gratis. Afmelden kan altijd. Je bevestigt je inschrijving per e-mail.</p></form></section><!-- newsletter:{placement}:end -->'''

def apply(phase=3):
    for path in Path('.').rglob('index.html'):
        if '.git' in path.parts: continue
        s=path.read_text()
        if 'class="site-header"' not in s: continue
        home=path==Path('index.html')
        page='homepage' if home else 'article' if path.parts[0]=='artikelen' else 'special' if path.parts[0]=='specials' else 'topic' if 'topic-archive' in s else 'other'
        s=re.sub(r'<!-- newsletter:.*?:start -->.*?<!-- newsletter:.*?:end -->','',s,flags=re.S)
        s=re.sub(r'<link rel="stylesheet" href="/newsletter-conversion.css[^"]*">','',s)
        s=s.replace('</head>','<link rel="stylesheet" href="/newsletter-conversion.css?v=1"></head>',1)
        # Reuse the current menu, including its existing mobile toggle.
        s=re.sub(r'<a class="header-cta"[^>]*>.*?</a>', '<a class="header-cta" href="/#nieuwsbrief-boven" data-newsletter-cta="nav">Nieuwsbrief</a>',s,flags=re.S)
        if home and 'data-newsletter-cta="nav"' not in s:
            s=s.replace('<a id="nav-contact"','<a href="/#nieuwsbrief-boven" data-newsletter-cta="nav">Nieuwsbrief</a><a id="nav-contact"',1)
        if home:
            m=re.search(r'<section class="hero-intro".*?</section>',s,re.S)
            if m:s=s[:m.end()]+'<!-- newsletter:home_hero:start --><div id="nieuwsbrief-boven">'+block('home_hero')+'</div><!-- newsletter:home_hero:end -->'+s[m.end():]
            # Avoid nested markers in repeat runs.
            s=s.replace('<!-- newsletter:home_hero:start --><section','<section').replace('</section><!-- newsletter:home_hero:end --></div>','</section></div>')
        if phase>=2 and page=='article':
            m=re.search(r'<div class="article-meta".*?</div>',s,re.S)
            if m:s=s[:m.end()]+'<!-- newsletter:article_intro:start --><p class="pn-newsletter-link">Meer van dit soort nieuws? <a href="#nieuwsbrief" data-newsletter-cta="article_intro">Ontvang onze gratis nieuwsbrief.</a></p><!-- newsletter:article_intro:end -->'+s[m.end():]
        if phase>=2 and page=='topic':
            items=list(re.finditer(r'<article class="article".*?</article>',s,re.S))
            if items:
                i=min(5,len(items))-1
                s=s[:items[i].end()]+block('topic_inline','Ook het andere goede nieuws volgen?',True)+s[items[i].end():]
        if phase>=3 and page=='special':
            start=s.find('class="content-shell article-body"')
            end=s.find('class="article-growth"',start)
            headings=list(re.finditer(r'<h2\b',s[start:end if end!=-1 else len(s)])) if start!=-1 else []
            if len(headings)>=6:
                pos=start+headings[max(1,len(headings)//3)].start()
                s=s[:pos]+'<!-- newsletter:special_inline:start --><p class="pn-newsletter-link">Ook het andere goede nieuws volgen? <a href="#nieuwsbrief" data-newsletter-cta="special_inline">Ontvang elke maandag en donderdag onze gratis nieuwsbrief.</a></p><!-- newsletter:special_inline:end -->'+s[pos:]
        # Existing native POST remains intact, with one shared measurement listener.
        s=s.replace('onsubmit="if (window.sa_event) { sa_event(\'nieuwsbrief_inschrijving\'); }"','')
        s=s.replace("    track('nieuwsbrief_inschrijving');",'    // Newsletter submission is measured by edition-analytics.js.')
        path.write_text(s)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--phase',type=int,default=3);apply(p.parse_args().phase)
