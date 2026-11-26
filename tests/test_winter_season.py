"""Guard the explicitly approved December theme during future site builds."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WinterSeasonTests(unittest.TestCase):
    def test_season_is_imported_before_base_rules(self):
        theme = (ROOT / "site-theme.css").read_text(encoding="utf-8")
        self.assertRegex(theme.lstrip(), r'^@import\s+url\("/winter-season\.css\?v=[^"]+"\);')
        self.assertNotIn("/* PN winter season:", theme)

    def test_winter_gutters_and_reduced_motion(self):
        season = (ROOT / "winter-season.css").read_text(encoding="utf-8")
        self.assertIn("html body.pn-home,", season)
        self.assertIn("html body:not(.pn-home) {", season)
        self.assertIn("@media (min-width: 1400px)", season)
        self.assertIn("background-repeat: repeat-y", season)
        self.assertEqual(season.count("data:image/svg+xml,"), 2)
        self.assertIn("pointer-events: none", season)
        self.assertIn("pn-winter-drift", season)
        self.assertIn("prefers-reduced-motion: reduce", season)
        self.assertIn("animation: none", season)

    def test_refresh_repairs_missing_and_duplicate_links(self):
        from build_editions import ensure_site_theme, SITE_THEME_HREF
        tag = f'<link rel="stylesheet" href="{SITE_THEME_HREF}">'
        source = '<html><head><style>body{color:black}</style></head><body><header class="site-header"></header></body></html>'
        result = ensure_site_theme(source)
        self.assertEqual(result, source.replace('</head>', tag + '</head>'))
        self.assertEqual(ensure_site_theme(result), result)
        outdated = source.replace('</head>', '<link rel="stylesheet" href="/site-theme.css?v=old"><link rel="stylesheet" href="/site-theme.css"></head>')
        self.assertEqual(ensure_site_theme(outdated), result)
        redirect = '<html><head><meta http-equiv="refresh" content="0;url=/"></head></html>'
        self.assertEqual(ensure_site_theme(redirect), redirect)

    def test_shared_theme_on_content_pages(self):
        for page in ROOT.rglob("*.html"):
            html = page.read_text(encoding="utf-8")
            if not re.search(r'<header\b[^>]*class="site-header"', html):
                continue
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertRegex(html, r'<link\b[^>]*href=["\']/site-theme\.css(?:\?[^"\']*)?["\']')


if __name__ == "__main__":
    unittest.main()
