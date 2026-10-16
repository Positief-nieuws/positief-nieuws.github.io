import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_search


class SearchDestinationTests(unittest.TestCase):
    def test_article_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'edities').mkdir()
            detail = root / 'artikelen/2026-09-17/eigen-verhaal/index.html'
            detail.parent.mkdir(parents=True)
            detail.write_text('<h1>Eigen verhaal</h1>')
            entries = [
                {'title': 'Eigen verhaal', 'article_slug': 'eigen-verhaal', 'url': 'https://example.org/original'},
                {'title': 'Vrouwenvoetbal', 'url': 'https://nos.nl/artikel/2631231-voetbal'},
                {'title': 'Ontbrekende detailpagina', 'article_slug': 'ontbreekt', 'url': 'https://example.org/story'},
                {'title': 'Geen bestemming'},
                {'title': 'Onveilig', 'url': 'javascript:alert(1)'},
                {'title': 'Ongeldig', 'url': 'https://['},
            ]
            (root / 'edities/2026-09-17.json').write_text(json.dumps({'nl': entries}))
            with patch.object(build_search, 'ROOT', root):
                build_search.build_index()
            items = json.loads((root / 'zoeken/index.json').read_text())['items']
            self.assertEqual({item['title']: item['url'] for item in items}, {
                'Eigen verhaal': '/artikelen/2026-09-17/eigen-verhaal/',
                'Vrouwenvoetbal': 'https://nos.nl/artikel/2631231-voetbal',
                'Ontbrekende detailpagina': 'https://example.org/story',
            })


if __name__ == '__main__':
    unittest.main()
