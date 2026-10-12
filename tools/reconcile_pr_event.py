"""Use only base code and API data; never run scripts from a PR."""
import json
import os
from github_coordinator import GitHub, pr_check, auto_merge

event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
numbers = []
if os.environ["EVENT_NAME"] == "workflow_dispatch":
    numbers = [int(os.environ["DISPATCH_PR"])]
elif "pull_request" in event:
    numbers = [event["pull_request"]["number"]]
elif "workflow_run" in event:
    numbers = [p["number"] for p in event["workflow_run"].get("pull_requests", [])]
    if not numbers:
        sha = event["workflow_run"]["head_sha"]
        api = GitHub()
        numbers = [p["number"] for p in api.pages("pulls?state=open") if p["head"]["sha"] == sha]
api = GitHub()
for number in set(numbers):
    pr_check(api, number)
    auto_merge(api, number)
