import argparse
import json
from pathlib import Path
from .core import InputError, read_json, validate_envelope
from .pipeline import run, rerun_module, release


def main():
    parser = argparse.ArgumentParser(description="FDEX 招投标 DEMO 制作核心线")
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("run")
    cmd.add_argument("--input", default="samples/e2e/core-normal")
    cmd.add_argument("--output", required=True)
    cmd = sub.add_parser("module")
    cmd.add_argument("module")
    cmd.add_argument("--from-run", required=True)
    cmd.add_argument("--output", required=True)
    cmd = sub.add_parser("release")
    cmd.add_argument("--run", required=True)
    cmd.add_argument("--approver", required=True)
    cmd = sub.add_parser("validate")
    cmd.add_argument("file")
    args = parser.parse_args()
    try:
        if args.command == "run":
            result = run(args.input, args.output)
            print(json.dumps({"output": str(Path(args.output).resolve()), "modules": {k: v["processing_status"] for k, v in result.items()}, "scope": "人员资质章节", "full_bid": False}, ensure_ascii=False))
            return 0 if result["M14"]["processing_status"] == "COMPLETE" else 2
        if args.command == "module":
            result = rerun_module(args.module, args.from_run, args.output)
            print(json.dumps({"module": args.module, "processing_status": result[args.module]["processing_status"], "downstream": "STALE"}, ensure_ascii=False))
            return 0 if result[args.module]["processing_status"] == "COMPLETE" else 2
        if args.command == "release":
            print(json.dumps(release(args.run, args.approver), ensure_ascii=False))
        else:
            validate_envelope(read_json(args.file))
            print("Schema validation passed; semantics and visual layout are separate checks.")
        return 0
    except (InputError, OSError, KeyError, ValueError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
