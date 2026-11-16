"""Homepage headlines have titles and short intros, without numeric prefixes."""
import json
import re
import unittest
from pathlib import Path
from build_editions import homepage_story_html, _headline_html

class HeadlinesLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(Path("nieuws.json").read_text(encoding="utf-8"))
        cls.date = cls.data["meta"]["edition_date"]

    def test_homepage_card(self):
        for index, story in enumerate(self.data["headlines"]):
            html = homepage_story_html(story, self.date, "headlines", index)
            self.assertIn("<h3", html)
            self.assertIn(story["summary"], html)
            self.assertIn('class="teaser"', html)
            self.assertNotIn(' / 03', html)
            self.assertNotIn('class="count"', html)

    def test_edition_card(self):
        for index, story in enumerate(self.data["headlines"], start=1):
            html = _headline_html(story, index, self.date)
            self.assertIn(story["summary"], html)
            self.assertIn('class="teaser"', html)
            self.assertNotIn('class="num"', html)
            self.assertNotRegex(html, r">0[123]</div>")

    def test_homepage_fallback_and_dynamic_renderer(self):
        html = Path("index.html").read_text(encoding="utf-8")
        block = html.split("<!-- homepage-headlines:start -->", 1)[1].split("<!-- homepage-headlines:end -->", 1)[0]
        self.assertEqual(block.count('class="short"'), 3)
        self.assertEqual(block.count('class="teaser"'), 3)
        self.assertNotIn("01 / 03", html)
        self.assertNotIn("02 / 03", html)
        self.assertNotIn("03 / 03", html)
        self.assertIn("safeText(article.teaser)", html)

if __name__ == "__main__":
    unittest.main()
