#!/usr/bin/env python3
"""Trusted-base GitHub task coordinator. Never checks out or runs PR code."""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MARKER = "<!-- tender-task-state:v1 -->"
META = re.compile(r"<!-- tender-task-meta:(.*?) -->", re.S)
TRUSTED_STATE_AUTHORS = {"github-actions[bot]", "iurp"}


def now():
    return datetime.now(timezone.utc)


def state_from(comments):
    states = []
    for comment in comments:
        if comment.get("user", {}).get("login") not in TRUSTED_STATE_AUTHORS or not comment.get("body", "").startswith(MARKER):
            continue
        try:
            body = comment["body"].split("```json\n", 1)[1].split("\n```", 1)[0]
            states.append((comment, json.loads(body)))
        except (IndexError, ValueError):
            continue
    return states[-1] if states else (None, {"owner": None, "collaborators": [], "assist_requests": [], "events": [], "history": []})


def task_meta(issue):
    match = META.search(issue.get("body") or "")
    return json.loads(match.group(1)) if match else None


def transition(state, actor, command, text="", *, manager=False, active_count=0, ready=True, difficulty="beginner", at=None):
    state = json.loads(json.dumps(state))
    at = at or now()
    owner = state.get("owner")
    update = at.isoformat()
    if command == "/claim":
        if owner:
            return state, f"当前负责人是 @{owner}。可以 /assist 请求协作，或选择其他任务。"
        if not ready:
            return state, "本任务尚未开放，先完成依赖或等待维护者开放。"
        if active_count >= 1:
            return state, "你已有一个主要任务。请先推进、求助或完成交接释放，再领取新任务。"
        if state.get("requested_by") and state["requested_by"] != actor:
            return state, "已有待确认的复杂任务认领，请选择其他任务或请求协作。"
        if difficulty == "advanced" and not manager:
            state.update(requested_by=actor, plan=text, requested_at=update)
            return state, "已登记认领申请，尚未占为成功。请补充实施计划，等待维护者 /approve-claim @你的账号。"
        state.update(owner=actor, collaborators=[], claimed_at=update, last_progress_at=update, blocked=False, requested_by=None)
        return state, f"认领成功：@{actor} 为唯一主要负责人。24小时内说明计划，48小时内更新一次有效进展。"
    if command == "/approve-claim":
        target = text.strip().lstrip("@")
        if not manager or target != state.get("requested_by") or active_count >= 1:
            return state, "只有维护者可确认已登记的申请，且申请人不能已有主要任务。"
        state.update(owner=target, claimed_at=update, last_progress_at=update, blocked=False, requested_by=None)
        return state, f"认领成功：@{target} 的计划已由维护者确认。"
    if command == "/assist":
        if not owner:
            return state, "尚无负责人，先认领任务。"
        if actor == owner or actor in state["collaborators"]:
            return state, "你已经参与本任务。"
        if actor not in state["assist_requests"]:
            state["assist_requests"].append(actor)
        return state, f"协作申请已登记，请 @{owner} 明确分工后 /approve-assist @{actor}。"
    if command == "/approve-assist":
        target = text.strip().lstrip("@")
        if (actor != owner and not manager) or target not in state["assist_requests"]:
            return state, "负责人或维护者可批准已经登记的协作者。"
        state["assist_requests"].remove(target)
        state["collaborators"].append(target)
        return state, f"已登记协作者 @{target}；主要负责人仍是 @{owner}，请在 Issue 写清双方分工。"
    if actor != owner and not manager and not (command == "/release" and actor == state.get("requested_by")):
        return state, "该操作由主要负责人或维护者完成。"
    if command in ("/progress", "/help"):
        if len(text.strip()) < 10:
            return state, "请说明实际进展或阻塞，以及对应分支、PR、验证或下一步。"
        state.update(last_progress_at=update, progress=text, blocked=command == "/help")
        state.pop("reminded_at", None)
        return state, "已记录求助并暂停无进展回收，请维护者处理阻塞。" if command == "/help" else "进展已记录，保留负责人和已有成果。"
    if command == "/release":
        if len(text.strip()) < 10:
            return state, "请附交接说明：已做内容、成果位置、阻塞原因和下一步。"
        state["history"].append({"owner": owner, "released_by": actor, "at": update, "handoff": text})
        state.update(owner=None, collaborators=[], assist_requests=[], blocked=False, requested_by=None)
        return state, "交接已保存，任务重新开放；既有代码和贡献不删除。"
    return state, "支持 /claim /progress /help /assist /approve-assist /release；复杂任务由维护者 /approve-claim。"


class GitHub:
    def __init__(self):
        self.repo = os.environ.get("GITHUB_REPOSITORY", "iurp/fdex-tender-agent")
        if self.repo != "iurp/fdex-tender-agent":
            raise ValueError("Coordinator is scoped to iurp/fdex-tender-agent")
        self.token = os.environ["GITHUB_TOKEN"]

    def request(self, method, path, value=None):
        data = json.dumps(value).encode() if value is not None else None
        req = Request("https://api.github.com/" + path, data=data, method=method,
                      headers={"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json", "Content-Type": "application/json", "User-Agent": "fdex-tender-coordinator"})
        with urlopen(req, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else None

    def get(self, path):
        return self.request("GET", "repos/" + self.repo + "/" + path)

    def write(self, method, path, value):
        return self.request(method, "repos/" + self.repo + "/" + path, value)

    def pages(self, path):
        rows = []
        for page in range(1, 101):
            sep = "&" if "?" in path else "?"
            batch = self.get(f"{path}{sep}per_page=100&page={page}")
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise ValueError("Pagination limit reached, refusing incomplete state")

    def manager(self, actor):
        try:
            response = self.get(f"collaborators/{actor}/permission")
            return response["permission"] == "admin" or response.get("role_name") in ("admin", "maintain")
        except HTTPError as exc:
            if exc.code == 404:
                return False
            raise


def synchronize(api, number, comment, state):
    body = MARKER + "\n```json\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n```\n\n此记录由协调工作流维护；主要负责人唯一，协作者独立登记。"
    if comment:
        api.write("PATCH", f"issues/comments/{comment['id']}", {"body": body})
    else:
        api.write("POST", f"issues/{number}/comments", {"body": body})
    labels = [x["name"] for x in api.get(f"issues/{number}")["labels"] if not x["name"].startswith("task:")]
    labels.append("task:blocked" if state.get("blocked") else "task:claimed" if state.get("owner") else "task:ready")
    api.write("PATCH", f"issues/{number}", {"assignees": [state["owner"]] if state.get("owner") else [], "labels": labels})


def issue_event(api, event):
    item = event["issue"]
    comment_event = event["comment"]
    if "pull_request" in item or comment_event["user"].get("type") == "Bot":
        return
    number = item["number"]
    current = api.get(f"issues/{number}")
    meta = task_meta(current)
    if not meta or current["state"] != "open":
        return
    body = comment_event["body"].strip()
    match = re.match(r"^(/[-a-z]+)(?:\s+([\s\S]*))?$", body)
    if not match:
        return
    actor, command, text = comment_event["user"]["login"], match[1], match[2] or ""
    replies = api.pages(f"issues/{number}/comments")
    record, state = state_from(replies)
    eid = str(comment_event["id"])
    if eid in state.get("events", []):
        synchronize(api, number, record, state)
        return
    target = text.strip().lstrip("@") if command == "/approve-claim" else actor
    active = api.pages(f"issues?state=open&assignee={target}")
    count = sum(1 for i in active if i["number"] != number and "pull_request" not in i and any(l["name"] == "task:claimed" for l in i["labels"]))
    ready = any(l["name"] in ("task:ready", "task:claimed", "task:blocked") for l in current["labels"])
    state, message = transition(state, actor, command, text, manager=api.manager(actor), active_count=count,
                                ready=ready, difficulty=meta["difficulty"])
    state.setdefault("events", []).append(eid)
    # A backlog claim rejection must not accidentally open the task.
    if ready or state.get("owner"):
        synchronize(api, number, record, state)
    elif record:
        api.write("PATCH", f"issues/comments/{record['id']}", {"body": MARKER + "\n```json\n" + json.dumps(state) + "\n```"})
    api.write("POST", f"issues/{number}/comments", {"body": f"{message}\n\n<!-- tender-command:{eid} -->"})


def linked_issue(body):
    match = re.search(r"(?im)^\s*(?:closes|fixes|resolves)\s+#([1-9]\d*)\b", body or "")
    return int(match[1]) if match else None


def contribution(api, pr):
    number = linked_issue(pr.get("body"))
    if not number:
        return False, "PR正文必须独立一行写 Closes #任务号。"
    item = api.get(f"issues/{number}")
    if not task_meta(item):
        return False, "关联Issue不是本项目的任务。"
    _, state = state_from(api.pages(f"issues/{number}/comments"))
    actor = pr["user"]["login"]
    if actor not in [state.get("owner")] + state.get("collaborators", []) and not api.manager(actor):
        return False, "提交者未认领，也未被登记为协作者。"
    if len((pr.get("body") or "").strip()) < 80:
        return False, "请补充变更、实际验证、接口影响和未实现范围。"
    return True, "任务绑定与负责人验证通过；内容与测试仍需审查。"


def pr_check(api, number):
    pr = api.get(f"pulls/{number}")
    valid, reason = contribution(api, pr)
    api.write("POST", f"statuses/{pr['head']['sha']}", {"state": "success" if valid else "failure", "context": "contribution", "description": reason[:130]})
    if valid:
        api.write("POST", f"issues/{number}/labels", {"labels": ["needs-maintainer-review"]})
    else:
        api.write("POST", f"issues/{number}/comments", {"body": reason})


def current_review(api, pr):
    latest = {}
    for review in api.pages(f"pulls/{pr['number']}/reviews"):
        who = review["user"]["login"]
        if who == pr["user"]["login"] or who not in ("iurp", "xiao8-agent"):
            continue
        if review.get("commit_id") == pr["head"]["sha"] and review["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[who] = review["state"]
    return "APPROVED" in latest.values() and "CHANGES_REQUESTED" not in latest.values()


def auto_merge(api, number):
    pr = api.get(f"pulls/{number}")
    if pr["state"] != "open" or pr["draft"] or pr["base"]["ref"] != "main":
        return
    valid, _ = contribution(api, pr)
    if not valid or not current_review(api, pr):
        return
    sha = pr["head"]["sha"]
    status = api.get(f"commits/{sha}/status")
    named = {s["context"]: s["state"] for s in reversed(status["statuses"])}
    checks = api.get(f"commits/{sha}/check-runs")["check_runs"]
    tests = [c for c in checks if c["name"] == "test"]
    if named.get("contribution") != "success" or not tests or tests[0].get("conclusion") != "success":
        return
    if pr.get("mergeable_state") in ("dirty", "behind") or pr.get("mergeable") is not True:
        return
    fresh = api.get(f"pulls/{number}")
    if fresh["head"]["sha"] != sha or not current_review(api, fresh):
        return
    api.write("POST", f"statuses/{sha}", {"state": "success", "context": "maintainer-review", "description": "当前提交由独立维护者批准，待分支保护与合并验证"})
    result = api.write("PUT", f"pulls/{number}/merge", {"sha": sha, "merge_method": "squash"})
    if result.get("merged"):
        task = linked_issue(pr["body"])
        api.write("POST", f"issues/{number}/comments", {"body": f"已合并当前审核版本 `{sha}`；merge `{result['sha']}`。工程合并不代表业务审批或正式递交。"})
        item = api.get(f"issues/{task}")
        labels = [l["name"] for l in item["labels"] if not l["name"].startswith("task:")] + ["task:done"]
        api.write("PATCH", f"issues/{task}", {"state": "closed", "labels": labels})


def sweep(api):
    for item in api.pages("issues?state=open"):
        if "pull_request" in item or not task_meta(item):
            continue
        comments = api.pages(f"issues/{item['number']}/comments")
        record, state = state_from(comments)
        if state.get("requested_by") and not state.get("owner") and state.get("requested_at"):
            if now() - datetime.fromisoformat(state["requested_at"]) > timedelta(hours=48):
                state.update(requested_by=None, plan="")
                synchronize(api, item["number"], record, state)
            continue
        if not state.get("owner") or state.get("blocked") or not state.get("last_progress_at"):
            continue
        # An open PR by the owner pauses stale-task reclamation.
        prs = api.pages("pulls?state=open")
        if any(linked_issue(p.get("body")) == item["number"] for p in prs):
            continue
        age = now() - datetime.fromisoformat(state["last_progress_at"])
        if age > timedelta(hours=48) and not state.get("reminded_at"):
            state["reminded_at"] = now().isoformat()
            synchronize(api, item["number"], record, state)
            api.write("POST", f"issues/{item['number']}/comments", {"body": f"@{state['owner']} 请更新进展或 /help。提醒后24小时仍无回应且无PR时，任务将重新开放。"})
        elif state.get("reminded_at") and now() - datetime.fromisoformat(state["reminded_at"]) > timedelta(hours=24):
            state["history"].append({"owner": state["owner"], "at": now().isoformat(), "handoff": "提醒后无回应自动释放；已有成果仍保留"})
            state.update(owner=None, collaborators=[], blocked=False)
            synchronize(api, item["number"], record, state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("issue", "pr", "merge", "sweep"))
    parser.add_argument("--number", type=int)
    args = parser.parse_args()
    api = GitHub()
    if args.mode == "issue":
        issue_event(api, json.loads(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8").read()))
    elif args.mode == "pr":
        pr_check(api, args.number)
    elif args.mode == "merge":
        auto_merge(api, args.number)
    else:
        sweep(api)


if __name__ == "__main__":
    main()
