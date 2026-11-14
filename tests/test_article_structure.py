import unittest

from build_editions import article_body_blocks, article_body_paragraphs, render_article_page


class ArticleStructureTests(unittest.TestCase):
    def test_legacy_paragraphs_remain_unchanged(self):
        item = {"article_body": ["Een alinea.", "Nog een alinea."]}
        self.assertEqual(article_body_blocks(item), [("p", "Een alinea."), ("p", "Nog een alinea.")])
        self.assertEqual(article_body_paragraphs(item), ["Een alinea.", "Nog een alinea."])

    def test_heading_blocks_render_in_sequence_and_are_escaped(self):
        item = {
            "article_slug": "test-artikel",
            "title": "Testartikel",
            "url": "https://example.org/bron",
            "source": "Testbron",
            "teaser": "Een inleiding.",
            "category": "Wetenschap",
            "article_body": [
                "Een inleiding.",
                {"h2": "Wat betekent <dit>?"},
                "Een tweede alinea.",
                {"h2": "De beperking"},
                "Een derde alinea.",
            ],
        }
        markup = render_article_page(item, "2026-11-12")
        self.assertIn('<article class="article-copy"><h2>Wat betekent &lt;dit&gt;?</h2><p>Een tweede alinea.</p><h2>De beperking</h2><p>Een derde alinea.</p></article>', markup)
        self.assertIn('<p class="article-deck">Een inleiding.</p>', markup)

    def test_no_forced_headings_for_short_story(self):
        item = {"article_body": ["Een kort verhaal.", "Een afronding."]}
        self.assertEqual([kind for kind, _ in article_body_blocks(item)], ["p", "p"])

    def test_invalid_blocks_are_not_silently_rendered(self):
        for body in [[{"h2": "Begin"}, "Alinea"], ["Alinea", {"h2": "A"}, {"h2": "B"}, "Tekst"], ["Alinea", {"h3": "Niet ondersteund"}]]:
            with self.subTest(body=body):
                with self.assertRaises(ValueError):
                    article_body_blocks({"article_body": body})


if __name__ == "__main__":
    unittest.main()
