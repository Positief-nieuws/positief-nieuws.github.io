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
