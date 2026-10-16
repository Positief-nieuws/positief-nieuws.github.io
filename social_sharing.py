"""Shared social metadata and progressive sharing for current and future pages.

No network, external social scripts, changes to canonical/schema, or email sends.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
from urllib.parse import quote, urlsplit

SITE = 'https://positief-nieuws.nl'
DEFAULT_IMAGE = SITE + '/images/social/positief-nieuws-v1.png'
DEFAULT_ALT = 'Positief nieuws. Dit gebeurt ook. Nieuws uit Nederland en de wereld.'


class Head(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.meta = {}; self.canonical = ''; self.title = ''; self.in_title = False
        self.feed(markup.split('</head>', 1)[0])

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('property') or attrs.get('name')] = attrs.get('content', '')
        elif tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href', '')
        elif tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False

    def handle_data(self, text):
        if self.in_title: self.title += text


def dimensions(path):
    """Read PNG/JPEG dimensions without adding a build dependency."""
    try:
        data = Path(path).read_bytes()
        if data[:8] == b'\x89PNG\r\n\x1a\n': return struct.unpack('>II', data[16:24])
        if data[:2] != b'\xff\xd8': return None
        pos = 2
        while pos + 9 < len(data):
            if data[pos] != 255: return None
            marker = data[pos + 1]; pos += 2
            length = int.from_bytes(data[pos:pos + 2], 'big')
            if marker in (0xc0, 0xc1, 0xc2):
                height, width = struct.unpack('>HH', data[pos + 3:pos + 7]); return width, height
            if length < 2: return None
            pos += length
    except (OSError, ValueError, struct.error):
        return None
    return None


def image_for(markup, head, kind):
    # Existing editorial images are used only when locally hosted and large enough.
    # Specials without their own local cover receive the neutral brand fallback.
    if kind in ('article', 'edition'):
        images = [head.meta.get('og:image', '')]
        images += re.findall(r'<img\b[^>]*src=[\'"]([^\'"]+)[\'"]', markup)
        for src in images:
            src = unescape(src)
            if src.startswith('/'): src = SITE + src
            parsed = urlsplit(src)
            if parsed.netloc != 'positief-nieuws.nl' or not parsed.path.startswith('/images/artikelen/'):
                continue
            path = Path(parsed.path.lstrip('/'))
            if '..' in path.parts: continue
            size = dimensions(path)
            if size and size[0] >= 600 and size[1] >= 315:
                match = re.search(r'<img\b[^>]*src=[\'"]' + re.escape(parsed.path) + r'[\'"][^>]*alt=[\'"]([^\'"]*)', markup)
                alt = unescape(match[1]) if match else head.meta.get('og:title', head.title)
                return src, alt, size
    return DEFAULT_IMAGE, DEFAULT_ALT, (1200, 630)


def metadata(markup, kind):
    head = Head(markup)
    title = head.meta.get('og:title') or head.title
    description = head.meta.get('description') or head.meta.get('og:description') or title
    image, alt, size = image_for(markup, head, kind)
    values = {
        'og:title': title, 'og:description': description, 'og:url': head.canonical,
        'og:type': 'article' if kind in ('article', 'special', 'edition') else 'website',
        'og:site_name': 'Positief nieuws', 'og:locale': 'nl_NL',
        'og:image': image, 'og:image:secure_url': image, 'og:image:alt': alt,
        'og:image:width': str(size[0]), 'og:image:height': str(size[1]),
        'twitter:card': 'summary_large_image', 'twitter:title': title,
        'twitter:description': description, 'twitter:image': image, 'twitter:image:alt': alt,
    }
    markup = re.sub(r'<!-- social-meta:start -->.*?<!-- social-meta:end -->', '', markup, flags=re.S)
    markup = re.sub(r'<meta\b[^>]*(?:name|property)\s*=\s*[\'"](?:og:|twitter:)[^\'"]*[\'"][^>]*>', '', markup, flags=re.I)
    tags = ''.join('<meta ' + ('property' if key.startswith('og:') else 'name') + '="' + key + '" content="' + escape(value, quote=True) + '">' for key, value in values.items())
    markup = re.sub(r'(?m)^[ \t]+$', '', markup)
    return markup.replace('</head>', '<!-- social-meta:start -->' + tags + '<!-- social-meta:end --></head>', 1)


def share_block(kind, url, title, home=False):
    name = 'de nieuwsbrief' if kind == 'newsletter' else 'deze editie'
    group = 'home' if home else kind
    whatsapp = 'https://wa.me/?text=' + quote(title + '\n\n' + url, safe='')
    button_id = ' id="share-edition"' if home else ''
    return f'''<!-- social-share:{group}:start --><section class="pn-share{' pn-share-home' if home else ''}" data-share-type="{kind}"{' data-share-home="true"' if home else ''} aria-label="Deel {name}"><h2>Deel {name}.</h2><div class="pn-share-buttons"><a href="{escape(whatsapp, quote=True)}" target="_blank" rel="noopener noreferrer" data-share-channel="whatsapp">WhatsApp</a><button type="button" data-share-action="copy">Kopieer link</button><button{button_id} type="button" data-share-action="native" hidden>Meer deelopties</button></div><p class="pn-share-status" role="status" aria-live="polite"></p><div class="pn-share-fallback" hidden><label for="{group}-share-url">Link om te delen</label><input id="{group}-share-url" value="{escape(url, quote=True)}" readonly></div></section><!-- social-share:{group}:end -->'''


def migrate_article_script(markup):
    """Retain newsletter listeners, replace only the former sharing listeners."""
    def update(match):
        script = match[0]
        start = script.find("  block.querySelectorAll('[data-share-channel]')")
        if start != -1 and "'#article-copy-link'" in script:
            return script[:start] + '})();\n</script>'
        return script
    return re.sub(r'<script\b[^>]*>.*?</script>', update, markup, flags=re.S)


def enhance(markup, path):
    path = Path(path)
    head = Head(markup)
    if not head.canonical.startswith(SITE + '/') or 'class="site-header"' not in markup:
        return markup
    if re.search(r'<meta\b[^>]*name="robots"[^>]*noindex', markup): return markup
    parts = path.parts
    kind = ('homepage' if path == Path('index.html') else 'article' if parts[0] == 'artikelen'
            else 'special' if parts[0] == 'specials' else 'newsletter' if parts[0] == 'nieuwsbrief'
            else 'edition' if re.fullmatch(r'edities/\d{4}-\d{2}-\d{2}/index.html', str(path)) else 'other')
    markup = metadata(markup, kind)
    title = Head(markup).meta['og:title']
    if kind in ('article', 'special'):
        markup = migrate_article_script(markup)
    elif kind == 'homepage':
        start = markup.find('    function setupShareButtons() {')
        end = markup.find('    let deferredInstallPrompt', start)
        if start != -1 and end != -1:
            markup = markup[:start] + '    function setupShareButtons() { /* social-sharing.js handles the controls. */ }\n\n' + markup[end:]
        group = share_block('edition', head.canonical, title, home=True)
        marker = r'<!-- social-share:home:start -->.*?<!-- social-share:home:end -->'
        if re.search(marker, markup, re.S):
            markup = re.sub(marker, lambda _: group, markup, flags=re.S)
        else:
            markup = re.sub(r'<button id="share-edition"[^>]*>.*?</button>', lambda _: group, markup, count=1, flags=re.S)
    elif kind in ('newsletter', 'edition'):
        marker = rf'<!-- social-share:{kind}:start -->.*?<!-- social-share:{kind}:end -->'
        group = share_block(kind, head.canonical, title)
        if re.search(marker, markup, re.S):
            markup = re.sub(marker, lambda _: group, markup, flags=re.S)
        elif kind == 'newsletter':
            markup = markup.replace('</main>', group + '</main>', 1)
        else:
            markup = re.sub(r'(<section class="end">.*?)(</div></section>)', lambda m: m[1] + group + m[2], markup, count=1, flags=re.S)
    markup = re.sub(r'<!-- social-assets:start -->.*?<!-- social-assets:end -->', '', markup, flags=re.S)
    if kind in ('homepage', 'article', 'special', 'newsletter', 'edition'):
        markup = markup.replace('</head>', '<!-- social-assets:start --><link rel="stylesheet" href="/social-sharing.css?v=1"><script src="/social-sharing.js?v=1" defer></script><!-- social-assets:end --></head>', 1)
    return markup


def apply():
    count = 0
    for path in Path('.').rglob('index.html'):
        if any(part.startswith('.') or part == 'work' for part in path.parts): continue
        original = path.read_text(encoding='utf-8')
        updated = enhance(original, path)
        if updated != original:
            path.write_text(updated, encoding='utf-8'); count += 1
    print(f'Deelmetadata en componenten bijgewerkt op {count} pagina’s.')


if __name__ == '__main__':
    apply()
