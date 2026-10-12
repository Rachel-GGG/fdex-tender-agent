import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tools/github_coordinator.py"
spec = importlib.util.spec_from_file_location("coordinator", path)
coordinator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordinator)


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.state = {"owner": None, "collaborators": [], "assist_requests": [], "events": [], "history": []}
        self.at = datetime(2026, 10, 13, tzinfo=timezone.utc)

    def move(self, actor, cmd, text="", **kw):
        self.state, reply = coordinator.transition(self.state, actor, cmd, text, at=self.at, **kw)
        return reply

    def test_first_confirmed_claim_wins(self):
        self.move("learner-a", "/claim")
        self.move("learner-b", "/claim")
        self.assertEqual(self.state["owner"], "learner-a")

    def test_one_primary_task(self):
        self.move("learner-a", "/claim", active_count=1)
        self.assertIsNone(self.state["owner"])

    def test_backlog_cannot_be_claimed(self):
        self.move("learner-a", "/claim", ready=False)
        self.assertIsNone(self.state["owner"])

    def test_advanced_requires_maintainer(self):
        self.move("learner-a", "/claim", "先复现再增加测试的计划", difficulty="advanced")
        self.assertIsNone(self.state["owner"])
        self.move("other", "/approve-claim", "@learner-a")
        self.assertIsNone(self.state["owner"])
        self.move("iurp", "/approve-claim", "@learner-a", manager=True)
        self.assertEqual(self.state["owner"], "learner-a")

    def test_pending_request_can_release(self):
        self.move("learner-a", "/claim", "计划需要进一步复现", difficulty="advanced")
        self.move("learner-a", "/release", "先领取更小任务，当前没有代码改动")
        self.assertIsNone(self.state["requested_by"])

    def test_assist_requires_owner_agreement(self):
        self.move("learner-a", "/claim")
        self.move("learner-b", "/assist")
        self.assertNotIn("learner-b", self.state["collaborators"])
        self.move("learner-a", "/approve-assist", "@learner-b")
        self.assertEqual(self.state["collaborators"], ["learner-b"])
        self.assertEqual(self.state["owner"], "learner-a")

    def test_other_student_cannot_release_owner(self):
        self.move("learner-a", "/claim")
        self.move("learner-b", "/release", "我想接手这个任务并继续开发")
        self.assertEqual(self.state["owner"], "learner-a")

    def test_help_pauses_reclamation_and_release_keeps_handoff(self):
        self.move("learner-a", "/claim")
        self.move("learner-a", "/help", "测试在字段校验处失败，已有复现记录和分支")
        self.assertTrue(self.state["blocked"])
        self.move("learner-a", "/release", "交接：分支feature/demo，测试失败需要继续检查字段")
        self.assertIsNone(self.state["owner"])
        self.assertEqual(self.state["history"][0]["owner"], "learner-a")

    def test_untrusted_state_comment_not_accepted(self):
        body = coordinator.MARKER + '\n```json\n{"owner":"attacker"}\n```'
        _, state = coordinator.state_from([{"body": body, "user": {"login": "attacker"}}])
        self.assertIsNone(state["owner"])

    def test_anchored_issue_binding(self):
        self.assertEqual(coordinator.linked_issue("Closes #12\n\n真实验证"), 12)
        self.assertIsNone(coordinator.linked_issue("可能涉及 #12 或其他事项"))


if __name__ == "__main__":
    unittest.main()
