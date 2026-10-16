import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import build_editions as build
import buttondown_draft as email
import social_sharing as sharing


class SharingTests(unittest.TestCase):
    def fixture(self, title='Een concreet verhaal'):
        return ('<html><head><title>'+title+'</title><meta name="description" content="Context &amp; nuance">'
                '<link rel="canonical" href="https://positief-nieuws.nl/artikelen/voorbeeld/">'
                '<script type="application/ld+json">{"@type":"NewsArticle"}</script></head>'
                '<body><header class="site-header"></header><main><h1>'+title+'</h1>'
                '<form method="post" action="https://buttondown.com/api/emails/embed-subscribe/positiefnieuws">'
                '<input name="metadata__signup_source" value="article_end"></form></main></body></html>')

    def test_metadata_fallback_and_idempotence(self):
        original = self.fixture()
        updated = sharing.enhance(original, Path('artikelen/voorbeeld/index.html'))
        head = sharing.Head(updated)
        self.assertEqual(head.meta['og:image'], sharing.DEFAULT_IMAGE)
        self.assertEqual(head.meta['twitter:title'], 'Een concreet verhaal')
        self.assertEqual(head.meta['twitter:description'], 'Context & nuance')
        self.assertEqual(head.meta['twitter:card'], 'summary_large_image')
        self.assertEqual(head.canonical, sharing.Head(original).canonical)
        for pattern in [r'<form.*?</form>', r'<script type="application/ld\+json">.*?</script>']:
            self.assertEqual(re.search(pattern,original)[0],re.search(pattern,updated)[0])
        self.assertEqual(sharing.enhance(updated,Path('artikelen/voorbeeld/index.html')),updated)
        self.assertEqual(updated.count('src="/social-sharing.js?v=1"'),1)

    def test_existing_editorial_image_is_selected(self):
        img = '/images/artikelen/test.jpg'
        markup = self.fixture().replace('</main>', '<img src="'+img+'" alt="Een illustratief beeld"></main>')
        with patch.object(sharing,'dimensions',return_value=(1280,853)):
            updated = sharing.enhance(markup,Path('artikelen/test/index.html'))
        head=sharing.Head(updated)
        self.assertEqual(head.meta['og:image'],sharing.SITE+img)
        self.assertEqual(head.meta['og:image:width'],'1280')
        self.assertEqual(head.meta['og:image:alt'],'Een illustratief beeld')

    def test_tiny_or_external_image_uses_fallback(self):
        for src in ['/images/artikelen/tiny.jpg','https://example.org/unknown.jpg']:
            with patch.object(sharing,'dimensions',return_value=(100,100)):
                m=sharing.enhance(self.fixture().replace('</main>','<img src="'+src+'"></main>'),Path('artikelen/test/index.html'))
            self.assertEqual(sharing.Head(m).meta['og:image'],sharing.DEFAULT_IMAGE)

    def test_share_link_encoding_and_general_component(self):
        block=sharing.share_block('newsletter','https://positief-nieuws.nl/nieuwsbrief/','Nieuws & nuance')
        self.assertIn('Nieuws%20%26%20nuance',block)
        self.assertIn('role="status"',block)
        self.assertIn('data-share-action="copy"',block)
        self.assertIn('data-share-action="native" hidden',block)

    def test_future_article_migrates_share_handlers_only(self):
        item={'title':'Vooruitgang','article_slug':'vooruitgang','article_body':['Context.'],'category':'Mens','url':'https://example.org/bron'}
        markup=sharing.enhance(build.render_article_page(item,'2026-10-15'),Path('artikelen/2026-10-15/vooruitgang/index.html'))
        self.assertNotIn("block.querySelectorAll('[data-share-channel]')",markup)
        self.assertIn('article_newsletter_view',markup)
        self.assertEqual(markup.count('src="/social-sharing.js?v=1"'),1)
        self.assertIn('id="article-copy-link"',markup)

    def test_future_email_is_forwardable_without_changing_sent_files(self):
        data={'meta':{'edition_date':'2026-10-15'}}
        block=email.build_share_block(data)
        self.assertIn('Stuur deze nieuwsbrief gerust door.',block)
        self.assertIn('href="https://positief-nieuws.nl/nieuwsbrief/"',block)
        self.assertIn('https://wa.me/?text=',block)
        self.assertNotIn('<script',block)

    def test_generated_edition_has_component_after_enhancement(self):
        markup=sharing.enhance(build.render_edition({'nl':[],'int':[],'headlines':[]},'2026-10-15'),Path('edities/2026-10-15/index.html'))
        self.assertIn('data-share-type="edition"',markup)
        self.assertEqual(sharing.Head(markup).meta['og:type'],'article')


if __name__=='__main__': unittest.main()
