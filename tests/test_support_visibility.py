import unittest
from support_visibility import hide


class SupportVisibilityTests(unittest.TestCase):
    def test_roundtrip_preserves_other_content_and_spacing(self):
        original = ('<section class="support"><div>Steun Positief nieuws</div>'
                    '<a href="/steun/">Steun</a></section>'
                    '<p>Redactioneel verhaal over steun aan gezinnen.</p>'
                    '<footer>Contact · <a href="/steun/">Steun</a> · Over</footer>'
                    '<h2>Vrijwillige bijdragen</h2><p>Betalen bij RegioBank.</p>')
        fragments = {}
        hidden = hide(original, fragments)
        self.assertNotIn('/steun/', hidden)
        self.assertNotIn('RegioBank', hidden)
        self.assertIn('steun aan gezinnen', hidden)
        self.assertEqual(hide(hidden, fragments), hidden)
        for key, value in fragments.items():
            hidden = hidden.replace('<!-- support-offline:' + key + ' -->', value)
        self.assertEqual(hidden, original)
