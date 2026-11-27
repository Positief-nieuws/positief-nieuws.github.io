"""Regression checks for classic Outlook layout and private test broadcasts."""
import os
import re
import unittest
from unittest.mock import patch
from html.parser import HTMLParser

import kit_draft as kit


class Images(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.images = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


class NewsletterLayoutTests(unittest.TestCase):
    def test_fitted_images_never_stretch_portrait(self):
        with patch("social_sharing.dimensions", return_value=(800, 1200)):
            self.assertEqual(kit.fitted_image_size("https://positief-nieuws.nl/images/photo.jpg", 286, 161), (107, 161))
        with patch("social_sharing.dimensions", return_value=(1600, 900)):
            self.assertEqual(kit.fitted_image_size("https://positief-nieuws.nl/images/photo.jpg", 286, 161), (286, 161))

    def test_fixed_table_widths_and_mobile_stacking(self):
        data, nl, world, headlines = kit.load_news()
        body = kit.build_body(data, nl, world, headlines)
        self.assertIn('class="pn-email-shell" width="640" align="center"', body)
        self.assertIn('<!--[if mso]>', body)
        self.assertIn('class="email-column" width="300"', body)
        self.assertIn('.email-column {display:block!important;width:100%!important;', body)
        self.assertNotIn('object-fit:', body)
        self.assertNotIn('width="660"', body)
        self.assertNotIn('class="story-intro"', body)
        self.assertEqual(body.count('class="story-card"'), 15)
        self.assertEqual(body.count('{{ unsubscribe_url }}'), 1)
        self.assertEqual(body.count('{{ address }}'), 1)
        self.assertIn('utm_source=kit', body)
        for image in Images(body).images:
            self.assertLessEqual(int(image["width"]), 598)
        for item in nl + world:
            self.assertIn(kit.esc(item.get("email_title") or item["title"]), body)

    def test_half_column_has_small_image_and_no_teaser(self):
        article = {"title": "Voorbeeld", "teaser": "TEKST NIET OPNEMEN", "url": "https://example.org"}
        with patch.object(kit, "article_thumbnail_url", return_value="https://positief-nieuws.nl/images/example.jpg"), patch("social_sharing.dimensions", return_value=(1600, 900)):
            markup = kit.article_html(article, {"meta": {"edition_date": "2026-11-26"}}, True, column=True)
        self.assertNotIn("TEKST NIET OPNEMEN", markup)
        image = Images(markup).images[0]
        self.assertEqual(int(image["width"]), 286)
        self.assertEqual(int(image["height"]), 161)

    def test_outlook_preview_stays_private_and_unscheduled(self):
        data = {"meta": {"edition_date": "2026-11-26"}}
        draft = {"id": 99, "status": "draft", "public": False, "send_at": None}
        with (
            patch.dict(os.environ, KIT_SENDER_EMAIL="test@positief-nieuws.nl"),
            patch.object(kit, "find_broadcast", return_value=None),
            patch.object(kit, "claim_edition") as claim,
            patch.object(kit, "request_json", return_value={"broadcast": draft}) as request,
        ):
            result = kit.create_draft("test", "TEST Outlook", "{{ unsubscribe_url }}", data, "Preview", trial=True, trial_label="outlook-v1")
            self.assertEqual(result, draft)
            claim.assert_not_called()
            payload = request.call_args.args[-1]
            self.assertEqual(payload["description"], "pn-2026-11-26-proef-outlook-v1")
            self.assertIsNone(payload["send_at"])
            self.assertIs(payload["public"], False)


if __name__ == "__main__":
    unittest.main()
