"""Keep article actions in reading order, preserving existing components verbatim."""
from html.parser import HTMLParser
import re

class Blocks(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=False)
        self.markup = markup
        self.offsets = [0]
        for line in markup.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.stack = []
        self.blocks = {}
        self.feed(markup)

    def absolute_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag not in ('section', 'div'): return
        classes = set(dict(attrs).get('class', '').split())
        self.stack.append((tag, self.absolute_offset(), classes))

    def handle_endtag(self, tag):
        if tag not in ('section', 'div') or not self.stack: return
        start_tag, start, classes = self.stack.pop()
        if start_tag != tag: raise ValueError('Unbalanced article component')
        end = self.markup.index('>', self.absolute_offset()) + 1
        for name in classes & {'article-share', 'article-newsletter', 'article-related', 'article-growth'}:
            self.blocks[name] = (start, end)


def order_article_actions(markup):
    if 'class="article-growth"' not in markup: return markup
    blocks = Blocks(markup).blocks
    if not all(name in blocks for name in ('article-share', 'article-newsletter', 'article-growth')):
        return re.sub(r'(?m)^[ \t]+$', '', markup)
    share, newsletter, growth = (blocks[name] for name in ('article-share', 'article-newsletter', 'article-growth'))
    related = blocks.get('article-related')
    if share[0] < newsletter[0] and (not related or share[0] < related[0] < newsletter[0]):
        return re.sub(r'(?m)^[ \t]+$', '', markup)
    moved = [share] + ([related] if related else [])
    replacement = '\n'.join(markup[start:end] for start, end in moved) + '\n        '
    edits = [(start, end, '') for start, end in moved] + [(newsletter[0], newsletter[0], replacement)]
    for start, end, text in sorted(edits, reverse=True):
        markup = markup[:start] + text + markup[end:]
    return re.sub(r'(?m)^[ \t]+$', '', markup)
