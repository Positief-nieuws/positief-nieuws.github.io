"""Shared, static invitations to tip the editorial team."""
import re

START = '<!-- tip-invitation:start -->'
END = '<!-- tip-invitation:end -->'

def block(placement):
    if placement not in ('home', 'article'):
        raise ValueError('Unknown tip placement')
    if placement == 'home':
        return (START + '<aside class="pn-tip-invitation" aria-label="Tip de redactie">'
                '<h2>Goed nieuws gezien?</h2>'
                '<p>Misschien verdient jouw ontdekking een plek in een volgende editie. Ook kleine verhalen zijn welkom.</p>'
                '<a href="/tip/" onclick="if(window.sa_event)window.sa_event(\'tip_redactie_click\',{placement:\'home\'})">Tip de redactie →</a></aside>' + END)
    width = 'max-width:700px;margin:26px 0'
    return (START + '<aside class="pn-tip-invitation" aria-label="Tip de redactie" '
            f'style="{width};box-sizing:border-box;padding:20px 22px;border:1px solid #dfe8e2;border-radius:16px;background:#fff;color:#182e35;text-align:left">'
            '<h2 style="font-size:1.2rem;line-height:1.25;margin:0 0 8px;color:#182e35">'
            '<img src="/sun-orange.svg" alt="" width="21" height="21" style="vertical-align:-3px;margin-right:7px">'
            'Goed nieuws gezien?</h2>'
            '<p style="font-size:.9rem;line-height:1.55;margin:0 0 12px;color:#536c64">Misschien verdient jouw ontdekking een plek in een volgende editie. Ook kleine verhalen zijn welkom.</p>'
            f'<a href="/tip/" onclick="if(window.sa_event)window.sa_event(\'tip_redactie_click\',{{placement:\'{placement}\'}})" '
            'style="display:inline-flex;align-items:center;min-height:44px;color:#176e5c;font-size:.9rem;font-weight:700;text-decoration:underline;text-underline-offset:3px">Tip de redactie →</a></aside>' + END)

def remove(markup):
    return re.sub(r'<!-- tip-invitation:start -->.*?<!-- tip-invitation:end -->', '', markup, flags=re.S)

def apply_home(markup):
    anchor = '<!-- social-share:home:end -->'
    if anchor not in markup:
        return markup
    return remove(markup).replace(anchor, anchor + block('home'), 1)

def apply_article(markup):
    anchor = '<p class="article-back">'
    if anchor not in markup:
        return markup
    return remove(markup).replace(anchor, block('article') + anchor, 1)
