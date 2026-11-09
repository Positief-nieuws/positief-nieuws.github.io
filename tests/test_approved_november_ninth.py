"""Owner approval binds one edition and never waives evidence or known dates."""
import json
import unittest
from datetime import date
from pathlib import Path
import editorial_check as gate

ROOT = Path(__file__).resolve().parents[1]


class ApprovedNovemberNinthTests(unittest.TestCase):
    def setUp(self):
        self.news = json.loads((ROOT / 'edities/2026-11-09.json').read_text())
        self.dossier = json.loads((ROOT / 'redactie/2026-11-09.json').read_text())

    def review(self):
        return gate.check(self.news, self.dossier, history=[], as_of=date(2026, 11, 9))

    def test_reviewed_edition_passes(self):
        self.assertTrue(self.review()['ready'])

    def test_new_copy_cannot_reuse_approval_with_rebound_hash(self):
        self.news['int'][3]['title'] = 'A different claim'
        digest = gate.news_digest(self.news)
        self.dossier['news_sha256'] = digest
        self.dossier['owner_approved_selection']['news_sha256'] = digest
        self.assertFalse(self.review()['ready'])

    def test_unverified_claim_still_blocks(self):
        self.dossier['articles']['int:pip-glimlach-reist-wereld']['evidence']['verified'] = False
        self.assertFalse(self.review()['ready'])

    def test_unknown_date_needs_explicit_reason(self):
        self.dossier['articles']['int:pip-glimlach-reist-wereld'].pop('publication_date_unknown_reason')
        self.assertFalse(self.review()['ready'])

    def test_owner_record_is_required(self):
        self.dossier.pop('owner_approved_selection')
        self.assertFalse(self.review()['ready'])
