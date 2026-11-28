import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('monitor', Path(__file__).resolve().parents[1] / 'scripts/check_newsletter.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.html = Path('nieuwsbrief/index.html').read_text()

    def failures(self, html):
        return [name for _, name, ok in m.form_checks(html, '/nieuwsbrief/') if not ok]

    def test_current_form(self):
        self.assertEqual(self.failures(self.html), [])

    def test_wrong_action(self):
        broken = self.html.replace(m.ACTION, 'https://example.com')
        self.assertIn('Kit action en POST', self.failures(broken))

    def test_missing_form_and_email(self):
        self.assertIn('formulier aanwezig (exact één)', self.failures(''))
        self.assertIn('emailveld', self.failures(self.html.replace('name="email_address"', 'name="other"')))

    def test_duplicate_form(self):
        self.assertIn('formulier aanwezig (exact één)', self.failures(self.html + self.html))

    def test_removed_article_form_is_not_silently_ignored(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / 'artikelen/2026-10-18/test/index.html'
            article.parent.mkdir(parents=True)
            article.write_text('<html>Removed form</html>')
            expected, _ = m.inventory(root)
            self.assertEqual(expected['/artikelen/2026-10-18/test/'], {'article_end'})
            checks = m.form_checks(article.read_text(), '/artikelen/2026-10-18/test/', {'article_end'})
            self.assertTrue(any(not ok for _, _, ok in checks))

    def test_end_only_flag_cannot_silently_remove_upper_form(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markup = '<html><body data-home-newsletter="end-only"></body></html>'
            (root / 'index.html').write_text(markup)
            expected, _ = m.inventory(root)
            self.assertEqual(expected['/'], {'home_hero', 'home_end'})
            checks = m.form_checks(markup, '/', expected['/'])
            self.assertTrue(any(not ok for placement, _, ok in checks if placement == 'home_hero'))

    def test_home_without_explicit_layout_flag_requires_both_forms(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.html').write_text('<html></html>')
            expected, _ = m.inventory(root)
            self.assertEqual(expected['/'], {'home_hero', 'home_end'})

    def test_unexpected_redirect_or_inline_success_fails(self):
        broken = self.html.replace('method="post"', 'method="post" onsubmit="return false"')
        self.assertIn('geen client-side succes of afwijkende redirect', self.failures(broken))
        broken = self.html.replace('</form>', '<input name="redirect_url"></form>', 1)
        self.assertIn('geen client-side succes of afwijkende redirect', self.failures(broken))

    def test_network_failure_is_recorded(self):
        with patch.object(m, 'get', side_effect=TimeoutError), patch.object(m.time, 'sleep'), patch.dict(m.os.environ, {}, clear=True):
            rows = m.run()
        self.assertTrue(any(r['status'] == 'FAIL' and r['location'] == '/' for r in rows))
        self.assertTrue(any(r['status'] == 'MANUAL' for r in rows))

 
class HostedFormTests(unittest.TestCase):
    def error(self, code):
        return m.urllib.error.HTTPError(m.HOSTED_FORM, code, 'test', {}, None)

    def test_success_requires_email_form(self):
        with patch.object(m, 'get', return_value='<form><input name="email_address"></form>'):
            self.assertEqual(m.check_hosted_form()[0], 'PASS')

    def test_successful_http_without_form_is_unverified(self):
        with patch.object(m, 'get', return_value='<html>not a form</html>'):
            status, detail = m.check_hosted_form()
            self.assertEqual(status, 'MANUAL')
            self.assertIn('geen email_address-formulier', detail)
            self.assertIn('geen bewijs van inschrijving', detail)

    def test_access_denied_is_manual_not_pass(self):
        for code in (401, 403):
            with self.subTest(code=code), patch.object(m, 'get', side_effect=self.error(code)) as get:
                status, detail = m.check_hosted_form()
                self.assertEqual(status, 'MANUAL')
                self.assertIn(f'HTTP {code}', detail)
                self.assertEqual(get.call_count, 1)

    def test_missing_page_is_failure(self):
        for code in (404, 410):
            with self.subTest(code=code), patch.object(m, 'get', side_effect=self.error(code)) as get:
                status, detail = m.check_hosted_form()
                self.assertEqual(status, 'FAIL')
                self.assertIn(f'HTTP {code}', detail)
                self.assertEqual(get.call_count, 1)

    def test_temporary_error_recovers(self):
        with patch.object(m, 'get', side_effect=[self.error(503), '<form><input name="email_address"></form>']) as get, patch.object(m.time, 'sleep') as sleep:
            self.assertEqual(m.check_hosted_form()[0], 'PASS')
            self.assertEqual(get.call_count, 2)
            sleep.assert_called_once_with(1)

    def test_exhausted_retry_distinguishes_rate_limit_and_outage(self):
        for code, expected in ((429, 'MANUAL'), (503, 'FAIL')):
            with self.subTest(code=code), patch.object(m, 'get', side_effect=self.error(code)) as get, patch.object(m.time, 'sleep'):
                status, detail = m.check_hosted_form()
                self.assertEqual(status, expected)
                self.assertIn(f'HTTP {code}', detail)
                self.assertIn('3/3', detail)
                self.assertEqual(get.call_count, 3)

    def test_network_timeout_retries_then_fails(self):
        with patch.object(m, 'get', side_effect=TimeoutError) as get, patch.object(m.time, 'sleep'):
            status, detail = m.check_hosted_form()
            self.assertEqual(status, 'FAIL')
            self.assertIn('TimeoutError', detail)
            self.assertEqual(get.call_count, 3)


class LatestEditionSignupTests(unittest.TestCase):
    def test_published_edition_signup_forms_and_analytics(self):
        import json
        from publish_edition import check_newsletter_forms

        date = json.loads(Path("nieuws.json").read_text(encoding="utf-8"))["meta"]["edition_date"]
        articles = sorted((Path("artikelen") / date).rglob("index.html"))
        self.assertEqual(len(articles), 12, "De nieuwste editie moet 12 artikelen bevatten")
        check_newsletter_forms([Path("index.html"), *articles])


    def test_prepublication_guard_catches_missing_intro_link(self):
        from publish_edition import check_newsletter_forms
        import tempfile
        import os
        import re
        source = Path("artikelen/2026-11-19/harlingen/index.html").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                article = Path("artikelen/2026-11-19/harlingen/index.html")
                article.parent.mkdir(parents=True)
                without_intro = re.sub(
                    r'<!-- newsletter:article_intro:start -->.*?<!-- newsletter:article_intro:end -->',
                    '', source, flags=re.S
                )
                article.write_text(without_intro, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Nieuwsbriefintro ontbreekt"):
                    check_newsletter_forms([article])
                article.write_text(source.replace('href="#nieuwsbrief" data-newsletter-cta="article_intro"',
                                                  'href="/nieuwsbrief/" data-newsletter-cta="article_intro"'),
                                   encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Nieuwsbriefintro ontbreekt"):
                    check_newsletter_forms([article])
            finally:
                os.chdir(previous)

    def test_prepublication_guard_catches_missing_forms(self):
        from publish_edition import check_newsletter_forms
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                Path("index.html").write_text("<html><head></head><body></body></html>")
                with self.assertRaisesRegex(ValueError, "Nieuwsbriefcontrole mislukt"):
                    check_newsletter_forms([Path("index.html")])
            finally:
                os.chdir(previous)

if __name__ == '__main__': unittest.main()
