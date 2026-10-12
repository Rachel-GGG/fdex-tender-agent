#!/usr/bin/env python3
"""Create reproducible source/Skill distributions without runtime data."""
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def write_zip(path, entries):
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()}
    entries = dict(entries)
    entries["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        for name, data in sorted(entries.items()):
            info = ZipInfo(name, date_time=(2026, 10, 13, 0, 0, 0)); info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)


def main():
    dist = ROOT / "dist"; dist.mkdir(exist_ok=True)
    for skill in sorted((ROOT / "skills").iterdir()):
        if skill.is_dir():
            entries = {p.relative_to(skill).as_posix(): p.read_bytes() for p in skill.rglob("*") if p.is_file()}
            entries["references/interfaces.md"] = (ROOT / "docs/interfaces.md").read_bytes()
            entries["references/implementation-status.md"] = (ROOT / "docs/implementation-status.md").read_bytes()
            write_zip(dist / (skill.name + ".zip"), entries)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    entries = {name: (ROOT / name).read_bytes() for name in tracked if name and (ROOT / name).is_file()}
    if not entries:
        raise ValueError("Stage the intended release files before packaging")
    write_zip(dist / "fdex-tender-agent-starter.zip", entries)
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(dist.glob("*.zip")))
    (dist / "SHA256SUMS").write_text(sums, encoding="utf-8")
    print("Built source and Skill ZIPs with internal manifests:", dist)


if __name__ == "__main__":
    main()
