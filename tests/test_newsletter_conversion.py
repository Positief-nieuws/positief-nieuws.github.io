"""Regression coverage for generation and contextual signup preservation."""
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import build_editions as build
import newsletter_conversion as newsletter


class ContextualNewsletterTests(unittest.TestCase):
    def test_future_generated_pages_keep_context_and_native_post(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                for category in build.CATEGORY_ORDER:
                    slug = build.slugify_category(category)
                    topic_path = Path(slug) / 'index.html'
                    topic_path.parent.mkdir()
                    topic_path.write_text(build.render_topic_page({
                        'label': category, 'slug': slug, 'nl': [], 'int': []}))
                    # Include one archive card: even short topic archives retain a signup.
                    topic_path.write_text(topic_path.read_text().replace(
                        '<div class="topic-archive-heading">',
                        '<article class="article"><h3>Voorbeeld</h3></article><div class="topic-archive-heading">'))
                    article_path = Path('artikelen/2026-10-15') / slug / 'index.html'
                    article_path.parent.mkdir(parents=True)
                    article_path.write_text(build.render_article_page({
                        'title': 'Een concrete ontwikkeling', 'category': category,
                        'article_slug': slug, 'article_body': ['Een bericht met context.'],
                        'url': 'https://example.org/bron', 'source': 'Bron'}, '2026-10-15'))
                Path('index.html').write_text('<html>Homepage blijft staan</html>')
                build.refresh_edition_analytics()
                with patch.object(newsletter, 'render_landing'):
                    newsletter.apply()
                    for category in build.CATEGORY_ORDER:
                        slug = build.slugify_category(category)
                        for path, index in [(Path(slug)/'index.html', 0),
                                            (Path('artikelen/2026-10-15')/slug/'index.html', 1)]:
                            text = path.read_text()
                            self.assertIn(newsletter.escape(newsletter.CONTEXT_COPY[category][index]), text)
                            self.assertIn(newsletter.CONTEXT_INTRO, text)
                            self.assertIn('/edition-analytics.js?v=3', text)
                            self.assertEqual(text.count('action="https://buttondown.com/api/emails/embed-subscribe/positiefnieuws"'), 1)
                            self.assertIn('method="post"', text)
                            self.assertIn('name="embed" value="1"', text)
                            if index:
                                self.assertIn('name="metadata__signup_article"', text)
                                self.assertIn('data-newsletter-cta="article_intro"', text)
                                self.assertIn('id="nieuwsbrief"', text)
                    before = {p: p.read_bytes() for p in Path('.').rglob('index.html')}
                    newsletter.apply()
                    self.assertEqual(before, {p: p.read_bytes() for p in before})
                self.assertEqual(Path('index.html').read_text(), '<html>Homepage blijft staan</html>')
            finally:
                os.chdir(previous)

    def test_unknown_category_has_general_fallback(self):
        text = newsletter.contextual_markup(newsletter.block('article_end'), 'Onbekend', article=True)
        self.assertIn('Er gebeurt nog meer goed nieuws.', text)
        self.assertIn(newsletter.CONTEXT_INTRO, text)

    def test_component_preserves_form_and_hidden_metadata(self):
        original = newsletter.block('article_end').replace('</form>', '<input name="metadata__custom" value="keep"></form>')
        changed = newsletter.contextual_markup(original, 'Natuur & klimaat', article=True)
        self.assertEqual(re.search(r'<form.*?</form>', original)[0], re.search(r'<form.*?</form>', changed)[0])


if __name__ == '__main__':
    unittest.main()
