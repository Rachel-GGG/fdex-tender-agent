import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("review_worker", TOOLS / "review_worker.py")
worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)


class FakeGitHub:
    def __init__(self):
        self.writes = []
        self.head = "abc"
    def get(self, path):
        return {"number": 1, "state": "closed" if getattr(self, "merged", False) else "open", "head": {"sha": self.head}, "base": {"sha": "base", "ref": "main"}}
    def write(self, *args):
        self.writes.append(args)


class ModelPublicationTests(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd(); self.temp = tempfile.TemporaryDirectory(); os.chdir(self.temp.name)
        self.api = FakeGitHub()
        Path("review-metadata.json").write_text(json.dumps({"pr_number": 1, "head_sha": "abc", "base_sha": "base", "workflow_run_id": 123}))
        self.result = {"verdict": "APPROVE", "summary": "已核对任务与补丁", "findings": []}
    def tearDown(self):
        os.chdir(self.old); self.temp.cleanup()
    def publish(self):
        Path("review-result.json").write_text(json.dumps(self.result))
        with patch.object(worker, "GitHub", return_value=self.api), patch.object(worker, "contribution", return_value=(True, "ok")), patch.object(worker, "auto_merge", side_effect=lambda api, number: setattr(api, "merged", True)):
            worker.publish()
    def test_current_result_publishes_bound_review(self):
        self.publish()
        self.assertEqual(self.api.writes[0][2]["commit_id"], "abc")
        self.assertEqual(self.api.writes[0][2]["event"], "APPROVE")
    def test_changed_head_never_publishes_old_approval(self):
        self.api.head = "new"; self.publish()
        self.assertEqual(self.api.writes, [])
    def test_findings_cannot_be_silently_approved(self):
        self.result["findings"] = [{"priority": "P1", "file": "module.py", "explanation": "缺陷"}]
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual(self.api.writes, [])
    def test_need_human_is_comment_not_approval(self):
        self.result["verdict"] = "NEEDS_HUMAN"; self.publish()
        self.assertEqual(self.api.writes[0][2]["event"], "COMMENT")


if __name__ == "__main__":
    unittest.main()
