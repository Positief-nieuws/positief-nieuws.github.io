"""Shared, visible Simple Analytics footer badge for existing and generated pages."""
from pathlib import Path
import re

START = '<!-- simple-analytics-badge:start -->'
END = '<!-- simple-analytics-badge:end -->'


def badge_html():
    # Official badges#builder embed; both modes retain the requested brand colors.
    query = 'counter=false&amp;radius=4&amp;background=%23F0F5EE&amp;text=%23182E35&amp;logo=%23176E5C'
    return f'''{START}
<div class="simple-analytics-badge" style="display:block;text-align:center;margin-top:16px">
  <a href="https://www.simpleanalytics.com?utm_source=positief-nieuws.nl&amp;utm_content=badge" referrerpolicy="origin" target="_blank" rel="noopener noreferrer" style="display:inline-block;line-height:0">
    <picture>
      <source srcset="https://simpleanalyticsbadges.com/positief-nieuws.nl?mode=dark&amp;{query}" media="(prefers-color-scheme: dark)" />
      <img src="https://simpleanalyticsbadges.com/positief-nieuws.nl?mode=light&amp;{query}" alt="Privacyvriendelijke webstatistieken door Simple Analytics" loading="lazy" referrerpolicy="no-referrer" crossorigin="anonymous" style="display:block;max-width:100%;height:auto" />
    </picture>
  </a>
</div>
{END}'''


def add_badge(markup):
    """Preserve all existing footer content and keep repeat builds idempotent."""
    markup = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', markup, flags=re.S)
    return re.sub(r'</footer\s*>', lambda _: badge_html() + '</footer>', markup, flags=re.I)


def apply(root=Path('.')):
    changed = 0
    for path in sorted(Path(root).rglob('*.html')):
        if any(part.startswith(('.', '_')) for part in path.relative_to(root).parts):
            continue
        before = path.read_text(encoding='utf-8')
        after = add_badge(before)
        if after != before:
            path.write_text(after, encoding='utf-8')
            changed += 1
    return changed


if __name__ == '__main__':
    print(f'Footerbadge bijgewerkt op {apply()} pagina’s.')
