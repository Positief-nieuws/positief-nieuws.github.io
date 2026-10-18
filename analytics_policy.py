"""Normalize existing tracking entry points without changing events or page content."""
from pathlib import Path
import re

TAG = '<script src="/analytics-loader.js?v=1"></script>'

def protect_markup(markup):
    # Legacy generated-page loader (metadata and event listeners stay in place).
    markup = re.sub(r'\(function \(\) \{\s*const analyticsScript = document.createElement\("script"\);.*?document.body.appendChild\(analyticsScript\);\s*\}\)\(\);',
                    'window.pnLoadAnalytics();', markup, flags=re.S)
    # Homepage loader: preserve pnSetEdition and metadata before the shared loader.
    markup = re.sub(r'const analyticsScript =\s*document.createElement\("script"\);.*?document.body.appendChild\(\s*analyticsScript\s*\);',
                    'window.pnLoadAnalytics();', markup, flags=re.S)
    # Handwritten contact, tip, search pages.
    markup = re.sub(r'<script\b[^>]*src="https://scripts.simpleanalyticscdn.com/latest.js"[^>]*></script>',
                    '<script>window.pnLoadAnalytics();</script>', markup)
    if 'pnLoadAnalytics()' in markup:
        markup = markup.replace(TAG, '')
        markup = re.sub(r'(<head\b[^>]*>)', lambda m: m[0] + TAG, markup, count=1, flags=re.I)
    return markup

def refresh(root=Path('.')):
    count = 0
    for path in root.rglob('*.html'):
        if any(part.startswith('.') for part in path.parts):
            continue
        old = path.read_text(encoding='utf-8')
        new = protect_markup(old)
        if old != new:
            path.write_text(new, encoding='utf-8')
            count += 1
    return count

if __name__ == '__main__':
    print('Analyticsbeleid toegepast op', refresh(), 'pagina’s')
