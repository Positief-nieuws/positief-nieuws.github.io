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

    def test_wrong_action_and_missing_embed(self):
        broken = self.html.replace(m.ACTION, 'https://example.com').replace('name="embed"', 'name="other"')
        self.assertIn('Buttondown action en POST', self.failures(broken))
        self.assertIn('embed=1', self.failures(broken))

    def test_missing_form_and_email(self):
        self.assertIn('formulier aanwezig (exact één)', self.failures(''))
        self.assertIn('emailveld', self.failures(self.html.replace('name="email"', 'name="other"')))

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

    def test_unexpected_redirect_or_inline_success_fails(self):
        broken = self.html.replace('method="post"', 'method="post" onsubmit="return false"')
        self.assertIn('geen client-side succes of afwijkende redirect', self.failures(broken))
        broken = self.html.replace('name="embed"', 'name="redirect_url"')
        self.assertIn('geen client-side succes of afwijkende redirect', self.failures(broken))

    def test_network_failure_is_recorded(self):
        with patch.object(m, 'get', side_effect=TimeoutError), patch.dict(m.os.environ, {}, clear=True):
            rows = m.run()
        self.assertTrue(any(r['status'] == 'FAIL' and r['location'] == '/' for r in rows))
        self.assertTrue(any(r['status'] == 'MANUAL' for r in rows))

if __name__ == '__main__': unittest.main()
