import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import kit_draft as kit


class KitReleaseTests(unittest.TestCase):
    def setUp(self):
        self.repo = "test/repo"
        self.edition = "2026-11-26"
        self.data = {"meta": {"edition_date": self.edition}}
        self.current = (self.data, [], [], [])
        self.event = {
            "action": "completed",
            "workflow_run": {
                "conclusion": "success", "event": "dynamic", "head_branch": "main",
                "head_repository": {"full_name": self.repo},
            },
        }

    def test_only_successful_regular_production_deployment_creates_a_draft(self):
        previous_dir = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                Path("redactie").mkdir()
                Path("redactie", self.edition + ".json").write_text("{}")
                Path("edities").mkdir()
                edition = json.dumps(self.data)
                Path("nieuws.json").write_text(edition)
                Path("edities", self.edition + ".json").write_text(edition)
                with (
                    patch("editorial_check.check", return_value={"ready": True}),
                    patch.object(kit, "check_live") as live,
                    patch.object(kit, "build_body", return_value="Newsletter"),
                    patch.object(kit, "build_preheader", return_value="Preview"),
                    patch.object(kit, "create_draft") as create,
                    patch.dict(os.environ, KIT_API_KEY="test"),
                ):
                    for updates in (
                        {"conclusion": "failure"}, {"head_branch": "preview"},
                        {"event": "pull_request"}, {"event": "workflow_dispatch"},
                    ):
                        event = {"action": "completed", "workflow_run": {**self.event["workflow_run"], **updates}}
                        self.assertIsNone(kit.run_release(event, self.current, "2026-11-23", self.repo))
                    self.assertIsNone(kit.run_release(self.event, self.current, self.edition, self.repo))
                    create.assert_not_called()
                    live.assert_not_called()
                    kit.run_release(self.event, self.current, "2026-11-23", self.repo)
                    live.assert_called_once()
                    create.assert_called_once()
            finally:
                os.chdir(previous_dir)

    def test_rerun_and_uncertain_response_reuse_broadcast(self):
        draft = {"id": 12, "status": "draft", "send_at": None, "public": False}
        args = ("test", "Subject", '<a href="{{ unsubscribe_url }}">Afmelden</a>', self.data, "Preview")
        with (
            patch.dict(os.environ, KIT_SENDER_EMAIL="test@positief-nieuws.nl"),
            patch.object(kit, "claim_edition") as claim,
            patch.object(kit, "find_broadcast", side_effect=[None, draft, draft]),
            patch.object(kit, "request_json", side_effect=TimeoutError) as request,
        ):
            self.assertEqual(kit.create_draft(*args), draft)
            self.assertEqual(kit.create_draft(*args), draft)
            claim.assert_called_once()
            request.assert_called_once()
            payload = request.call_args.args[-1]
            self.assertIsNone(payload["send_at"])
            self.assertIs(payload["public"], False)
            self.assertEqual(payload["description"], "pn-2026-11-26")

    def test_existing_claim_without_visible_draft_prevents_second_post(self):
        with (
            patch.dict(os.environ, KIT_SENDER_EMAIL="test@positief-nieuws.nl"),
            patch.object(kit, "find_broadcast", return_value=None),
            patch.object(kit, "claim_edition", side_effect=RuntimeError("Claim exists")),
            patch.object(kit, "request_json") as request,
        ):
            with self.assertRaisesRegex(RuntimeError, "Claim exists"):
                kit.create_draft("test", "Subject", "{{ unsubscribe_url }}", self.data, "Preview")
            request.assert_not_called()
