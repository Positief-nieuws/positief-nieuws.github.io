"""The owner's 29 October approval covers one exact version and no missing evidence."""
import copy
import json
import unittest
from datetime import date
from pathlib import Path
import editorial_check as gate

ROOT=Path(__file__).resolve().parents[1]

class ApprovedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.news=json.loads((ROOT/'edities/2026-10-29.json').read_text())
        self.dossier=json.loads((ROOT/'redactie/2026-10-29.json').read_text())

    def check(self):
        return gate.check(self.news,self.dossier,history=[],as_of=date(2026,10,29))

    def test_exact_owner_approved_preview_passes(self):
        self.assertTrue(self.check()['ready'])

    def test_missing_source_evidence_still_blocks_publication(self):
        self.dossier['articles']['int:wereldwijd-natuurherstel-vn']['evidence']['verified']=False
        self.assertFalse(self.check()['ready'])

    def test_new_content_cannot_reuse_approval_even_with_updated_bindings(self):
        self.news['nl'][0]['title']='Changed after approval'
        digest=gate.news_digest(self.news)
        self.dossier['news_sha256']=digest
        self.dossier['owner_approved_selection']['news_sha256']=digest
        self.assertFalse(self.check()['ready'])

    def test_missing_owner_record_does_not_waive_selection_review(self):
        self.dossier.pop('owner_approved_selection')
        self.assertFalse(self.check()['ready'])
