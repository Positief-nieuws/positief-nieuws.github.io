import unittest
from pathlib import Path
import re
from analytics_policy import protect_markup, TAG
from build_editions import analytics_html

class AnalyticsPolicyTests(unittest.TestCase):
    def test_every_tracking_page_has_policy_first(self):
        count = 0
        for path in Path('.').rglob('*.html'):
            if '.git' in path.parts:
                continue
            html = path.read_text()
            self.assertNotIn('simpleanalyticscdn.com/latest.js', html, str(path))
            self.assertNotIn('noscript.gif', html, str(path))
            if 'pnLoadAnalytics()' in html:
                count += 1
                self.assertEqual(html.count(TAG), 1, str(path))
                self.assertLess(html.index(TAG), html.index('pnLoadAnalytics()'), str(path))
                self.assertRegex(html, r'<head[^>]*>' + re.escape(TAG))
                self.assertEqual(protect_markup(html), html)
        self.assertGreaterEqual(count, 112)

    def test_future_generated_pages(self):
        html = '<html><head></head><body>' + analytics_html({'page_type': 'article'}) + '</body></html>'
        normalized = protect_markup(html)
        self.assertEqual(normalized.count(TAG), 1)
        self.assertIn('window.pnLoadAnalytics();', normalized)
        self.assertIn('article_click', normalized)
        self.assertIn('source_click', normalized)
        self.assertNotIn('simpleanalyticscdn.com/latest.js', normalized)
