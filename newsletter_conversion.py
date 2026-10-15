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
        if path == Path('nieuwsbrief/index.html'): continue
        s=path.read_text()
        if 'class="site-header"' not in s: continue
        # Buttondown may append a second '?' to a redirect containing a query.
        # Remove the email before any analytics script or page router runs.
        s=re.sub(r'<script id="newsletter-redirect-cleanup">.*?</script>', '', s, flags=re.S)
        cleanup = """<script id="newsletter-redirect-cleanup">(function(){var q=location.search.replace('?email_address=','&email_address=');var p=new URLSearchParams(q);if(p.has('email_address')){p.delete('email_address');history.replaceState(null,'',location.pathname+(p.toString()?'?'+p.toString():'')+location.hash);}})();</script>"""
        s=s.replace('<head>', '<head>'+cleanup, 1)
        home=path==Path('index.html')
        page='homepage' if home else 'article' if path.parts[0]=='artikelen' else 'special' if path.parts[0]=='specials' else 'topic' if 'topic-archive' in s else 'other'
        s=re.sub(r'<!-- newsletter:.*?:start -->.*?<!-- newsletter:.*?:end -->','',s,flags=re.S)
        s=re.sub(r'<link rel="stylesheet" href="/newsletter-conversion.css[^"]*">','',s)
        s=s.replace('</head>','<link rel="stylesheet" href="/newsletter-conversion.css?v=1"></head>',1)
        # Reuse the current menu, including its existing mobile toggle.
        s=re.sub(r'<a class="header-cta"[^>]*>.*?</a>', '<a class="header-cta" href="/nieuwsbrief/" data-newsletter-cta="nav">Nieuwsbrief</a>',s,flags=re.S)
        if home and 'data-newsletter-cta="nav"' not in s:
            s=s.replace('<a id="nav-contact"','<a href="/nieuwsbrief/" data-newsletter-cta="nav">Nieuwsbrief</a><a id="nav-contact"',1)
        s=re.sub(r'<a\b[^>]*data-newsletter-cta="nav"[^>]*>', lambda m: re.sub(r'href="[^"]*"', 'href="/nieuwsbrief/"', m.group()), s)
        if home:
            m=re.search(r'<section class="homepage-top"[^>]*>.*?</section>',s,re.S)
            if m:s=s[:m.end()]+'<!-- newsletter:home_hero:start --><div id="nieuwsbrief-boven">'+block('home_hero')+'</div><!-- newsletter:home_hero:end -->'+s[m.end():]
            # Preserve the same form node while news is refreshed dynamically.
            if 'const homeNewsletter =' not in s:
                s=s.replace("      grid.innerHTML = ''; grid.hidden", "      const homeNewsletter = type === 'nl' ? document.getElementById('nieuwsbrief-boven') : null;\n      grid.innerHTML = ''; grid.hidden", 1)
                s=s.replace('top.appendChild(side); grid.appendChild(top);', 'top.appendChild(side); grid.appendChild(top);\n        if (homeNewsletter) grid.appendChild(homeNewsletter);', 1)
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
    render_landing()

def render_landing():
    """Dedicated public signup destination using existing PN components."""
    import json
    from build_editions import header_html, BASE_CSS, analytics_html, fmt_date
    news=json.loads(Path('nieuws.json').read_text())
    date=(news.get('meta') or {}).get('edition_date','')
    stories=(news.get('nl') or [])[:2]+(news.get('int') or [])[:1]
    preview=''.join('<li><span>'+escape(item.get('category',''))+'</span><h3>'+escape(item.get('title',''))+'</h3><p>'+escape(item.get('teaser',''))+'</p></li>' for item in stories)
    header=header_html()
    header=re.sub(r'<a class="header-cta"[^>]*>.*?</a>', '<a class="header-cta is-active" aria-current="page" href="/nieuwsbrief/" data-newsletter-cta="nav">Nieuwsbrief</a>', header, flags=re.S)
    form=block('landing_main','Meld je gratis aan.')
    form=re.sub(r'(<h2[^>]*>.*?</h2>)<p>.*?</p>',r'\1',form,count=1,flags=re.S)
    css="""
.skip{position:absolute;left:-9999px;top:0}.skip:focus{left:12px;top:12px;z-index:100;padding:12px;background:#fff}body{background:#fffcf7;color:#182e35;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}.nl-shell{max-width:1120px;padding:0 28px;margin:auto}.nl-hero{display:grid;grid-template-columns:1.1fr 1fr;gap:64px;align-items:center;padding:68px 0 58px}.nl-tag{display:inline-flex;align-items:center;gap:8px;color:#176e5c;background:#edf5ee;border:1px solid #dce8df;border-radius:99px;padding:7px 12px;font-size:12px;font-weight:750}.nl-hero h1{font-family:inherit;font-weight:850;font-size:clamp(36px,4.6vw,57px);line-height:1.07;letter-spacing:-.05em;margin:22px 0}.nl-hero h1 span{color:#176e5c}.nl-lead{font-size:17px;line-height:1.7;color:#536c64;margin:0 0 24px;max-width:540px}.nl-benefits{padding:0;list-style:none;display:grid;gap:12px;margin:24px 0 0}.nl-benefits li{font-size:14px;line-height:1.6}.nl-benefits li:before{content:'✓';color:#176e5c;font-weight:850;margin-right:11px}.nl-signup .pn-newsletter{display:block;margin:0;background:#fff;border:1px solid #dfe8e2;border-radius:18px;padding:30px}.nl-signup .pn-newsletter h2{font-family:inherit;font-size:25px;margin:0 0 22px}.nl-signup .pn-newsletter-row{flex-direction:column;gap:10px}.nl-signup .pn-newsletter button{width:100%}.nl-signup .pn-newsletter-note{margin-top:14px}.nl-form-footer{font-size:12px;line-height:1.6;color:#64777a;margin:14px 8px 0}.nl-form-footer a{text-decoration:underline}.nl-preview{border-top:1px solid #dfe8e2;padding:42px 0 56px;display:grid;grid-template-columns:.8fr 1.2fr;gap:64px}.nl-preview h2,.nl-faq h2{font-family:inherit;font-size:29px;line-height:1.2;letter-spacing:-.035em;margin:12px 0 16px}.nl-preview-intro p{font-size:15px;line-height:1.7;color:#536c64}.nl-preview-intro a{display:inline-block;color:#176e5c;font-size:14px;font-weight:750;text-decoration:underline;text-underline-offset:4px;margin-top:10px}.nl-edition{background:#fff;border:1px solid #dfe8e2;border-radius:17px;padding:26px}.nl-edition-mast{display:flex;justify-content:space-between;align-items:center;padding-bottom:15px;border-bottom:1px solid #dfe8e2;font-size:17px;font-weight:850}.nl-edition-mast span{font-size:28px;color:#d6a141}.nl-edition-date{font-size:12px;color:#64777a;margin:15px 0}.nl-edition ul{margin:0;padding:0;list-style:none}.nl-edition li{padding:16px 0;border-bottom:1px solid #edf1ed}.nl-edition li:last-child{padding-bottom:0;border:0}.nl-edition li span{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#176e5c}.nl-edition h3{font-family:inherit;font-size:17px;line-height:1.35;letter-spacing:-.025em;margin:7px 0}.nl-edition li p{font-size:13px;line-height:1.6;color:#536c64;margin:0}.nl-faq{border-top:1px solid #dfe8e2;padding:36px 0 58px}.nl-faq-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:30px}.nl-faq h3{font-family:inherit;font-size:16px;margin:10px 0}.nl-faq p{font-size:14px;line-height:1.7;color:#536c64}.nl-footer{background:#f0f5ee;border-top:1px solid #dfe8e2;padding:28px;text-align:center;color:#64777a;font-size:12px}.nl-footer a{text-decoration:underline}#landing_main-email{scroll-margin-top:100px}@media(max-width:760px){.nl-shell{padding:0 19px}.nl-hero{grid-template-columns:1fr;gap:28px;padding:32px 0 38px}.nl-hero h1{font-size:39px;margin:17px 0}.nl-lead{font-size:15px;margin-bottom:18px}.nl-benefits{gap:8px;margin-top:18px}.nl-signup .pn-newsletter{padding:23px 20px}.nl-preview{grid-template-columns:1fr;gap:20px;padding:32px 0 36px}.nl-preview h2,.nl-faq h2{font-size:26px}.nl-edition{padding:21px}.nl-faq-grid{grid-template-columns:1fr;gap:8px}.nl-faq{padding:26px 0 34px}}
"""
    title='Gratis nieuwsbrief | Positief nieuws in je inbox'
    desc='Elke maandag en donderdag 12 positieve verhalen en 3 ontwikkelingen om bij te blijven. Gratis, overzichtelijk en in een paar minuten gelezen.'
    markup=f'''<!DOCTYPE html><html lang="nl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="https://positief-nieuws.nl/nieuwsbrief/"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="https://positief-nieuws.nl/nieuwsbrief/"><meta property="og:type" content="website"><meta property="og:site_name" content="Positief nieuws"><meta name="twitter:card" content="summary"><link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/site-theme.css?v=20261010b"><link rel="stylesheet" href="/newsletter-conversion.css?v=1"><style>{BASE_CSS}{css}</style><script src="/edition-analytics.js?v=1" data-page-type="newsletter" defer></script></head><body><a class="skip" href="#main">Ga naar inhoud</a>{header}<main class="nl-shell" id="main"><section class="nl-hero"><div><span class="nl-tag">Gratis nieuwsbrief · maandag &amp; donderdag</span><h1>Het goede nieuws.<br><span>Gewoon in je inbox.</span></h1><p class="nl-lead">Er gaat meer goed dan je denkt. Ontvang twee keer per week een rustige selectie nieuws uit Nederland en de wereld. In een paar minuten ben je weer bij.</p><ul class="nl-benefits"><li>12 positieve verhalen + 3 ontwikkelingen om bij te blijven</li><li>Met bronnen, context en ruimte voor nuance</li><li>Gratis en zonder advertenties. Afmelden kan altijd.</li></ul></div><div class="nl-signup">{form}<p class="nl-form-footer">Na het aanmelden ontvang je een bevestigingsmail. Eén klik en je doet mee. <a href="/#privacy">Zo gaan we met je gegevens om.</a></p></div></section><section class="nl-preview" aria-labelledby="preview-title"><div class="nl-preview-intro"><p class="kicker">Even proeven</p><h2 id="preview-title">Dit soort nieuws<br>krijg je in je inbox.</h2><p>Van natuur die herstelt tot ontwikkelingen die het dagelijks leven beter maken. We selecteren concrete vooruitgang, zonder het belangrijke nieuws weg te laten.</p><p>Hier zie je drie verhalen uit een echte editie. De volledige editie bevat zes verhalen uit Nederland, zes uit de wereld en drie korte actualiteiten.</p><a href="/edities/{escape(date)}/">Bekijk de volledige voorbeeldeditie →</a></div><div class="nl-edition"><div class="nl-edition-mast">Positief nieuws<span aria-hidden="true">☀</span></div><p class="nl-edition-date">Uit de editie van {escape(fmt_date(date))}</p><ul>{preview}</ul></div></section><section class="nl-faq" aria-labelledby="faq-title"><p class="kicker">Goed om te weten</p><h2 id="faq-title">Een paar minuten. Daarna weer verder.</h2><div class="nl-faq-grid"><div><h3>Is het echt gratis?</h3><p>Ja. De nieuwsbrief is gratis en zonder advertenties. Je hoeft nergens voor te betalen.</p></div><div><h3>Wanneer krijg ik de nieuwsbrief?</h3><p>Elke maandag en donderdag. Twee overzichtelijke edities per week, zonder eindeloze nieuwsstroom.</p></div><div><h3>Kan ik makkelijk stoppen?</h3><p>Zeker. Onderaan elke nieuwsbrief staat een afmeldlink. Eén klik en je bent weer afgemeld.</p></div></div></section></main><footer class="nl-footer">Positief nieuws · Dit gebeurt ook. · <a href="/over/">Over</a> · <a href="/contact/">Contact</a> · <a href="/#privacy">Privacy</a></footer>{analytics_html({'page_type':'newsletter'})}</body></html>'''
    target=Path('nieuwsbrief/index.html');target.parent.mkdir(exist_ok=True);target.write_text(markup)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--phase',type=int,default=3);apply(p.parse_args().phase)
