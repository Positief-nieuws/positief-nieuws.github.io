import unittest
from related_content import select

class RelatedTests(unittest.TestCase):
    def record(self, path, title, kind='article'):
        return {'path':path,'type':kind,'item':{'title':title,'summary':'Drinkwater kraan watersysteem gezinnen'}}
    def test_exclusion_dedup_and_special_priority(self):
        item={'title':'Drinkwater kraan voor gezinnen','summary':'Drinkwater kraan watersysteem gezinnen'}
        records=[self.record('/self/',item['title']), self.record('/a/',item['title']),self.record('/a/',item['title']),self.record('/s/',item['title'],'special'),self.record('/s2/',item['title'],'special')]
        # A realistic background corpus makes the shared subject distinctive.
        records += [{'path':f'/other-{i}/','type':'article','item':{'title':f'Ruimtesonde Jupiter {i}'}} for i in range(30)]
        result=select(item,'/self/',records)
        self.assertEqual([r['path'] for r in result],['/s/','/a/'])
    def test_category_is_not_enough(self):
        self.assertEqual(select({'title':'Juice reist naar Jupiter','category':'Wetenschap'},'/self/',[self.record('/x/','DNA in een muizenembryo')]),[])

    def test_fallback_fills_links_from_same_topic(self):
        from build_editions import select_related_articles
        item = {'title': 'Vrijwilligers helpen in de wijk', 'category': 'Mens',
                'article_slug': 'wijk', 'article_body': ['Een verhaal.']}
        rows = [
            {'date': '2026-10-22', 'slug': 'samen', 'category': 'Mens',
             'item': {'title': 'Samen in de buurt', 'category': 'Mens'}},
            {'date': '2026-10-19', 'slug': 'leer', 'category': 'Mens',
             'item': {'title': 'Ouders helpen met leren', 'category': 'Mens'}},
            {'date': '2026-10-15', 'slug': 'zorg', 'category': 'Mens',
             'item': {'title': 'Nieuwe zorg voor ouderen', 'category': 'Mens'}},
            {'date': '2026-10-29', 'slug': 'technologie', 'category': 'Wetenschap',
             'item': {'title': 'Ruimtesonde bekijkt sterren', 'category': 'Wetenschap'}},
        ]
        result = select_related_articles(item, '2026-10-29', rows)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(r['category'] == 'Mens' for r in result))
        self.assertEqual(len({r['path'] for r in result}), 3)

    def test_suggestions_follow_sharing_and_newsletter(self):
        from build_editions import render_article_page
        from article_layout import order_article_actions
        item = {'title': 'Samen in de buurt', 'category': 'Mens',
                'article_slug': 'samen', 'article_body': ['Een verhaal.'],
                'url': 'https://example.org/bron'}
        suggested = [{'path': '/artikelen/2026-10-22/leer/', 'type': 'article',
                      'item': {'title': 'Ander menselijk verhaal'}}]
        page = order_article_actions(render_article_page(item, '2026-10-29', suggested))
        self.assertLess(page.index('class="article-share"'),
                        page.index('class="article-newsletter"'))
        self.assertLess(page.index('class="article-newsletter"'),
                        page.index('class="article-related"'))

    def test_existing_article_body_is_not_regenerated(self):
        from scripts.refresh_related_articles import update_article_markup
        page = ('<article>Originele artikeltekst</article>'
                '<section class="article-related"><h2>Lees ook</h2></section>'
                '<section class="article-growth"><div class="article-share"></div>'
                '<section class="article-newsletter"></section></section>'
                '<p class="article-back">Terug</p>')
        related = '<section class="article-related">Nieuw</section>'
        updated = update_article_markup(page, related)
        self.assertIn('<article>Originele artikeltekst</article>', updated)
        self.assertEqual(updated.count('class="article-related"'), 1)
        self.assertLess(updated.index('class="article-newsletter"'),
                        updated.index('class="article-related"'))
        self.assertEqual(updated, update_article_markup(updated, related))
