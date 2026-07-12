#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = f"prepper-box-configs-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"


def git_tracked_files(root: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    files = [Path(p.decode()) for p in proc.stdout.split(b"\0") if p]
    return files


def backup(archive: Path, root: Path) -> None:
    files = git_tracked_files(root)
    with tarfile.open(archive, "w:gz") as tf:
        for rel in files:
            abs_path = root / rel
            if abs_path.is_file():
                tf.add(abs_path, arcname=str(rel))
    print(f"created {archive}")


def safe_extract(tf: tarfile.TarFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in tf.getmembers():
        target = (dest / member.name).resolve()
        if dest_resolved not in target.parents and target != dest_resolved:
            raise SystemExit(f"unsafe path in archive: {member.name}")
    tf.extractall(dest)


def restore(archive: Path, dest: Path) -> None:
    with tarfile.open(archive, "r:gz") as tf:
        safe_extract(tf, dest)
    print(f"restored {archive} -> {dest}")


def list_archive(archive: Path) -> None:
    with tarfile.open(archive, "r:gz") as tf:
        for member in tf.getmembers():
            print(member.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup and restore tracked prepper-box config files.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_backup = sub.add_parser("backup", help="Create a tar.gz of tracked files")
    p_backup.add_argument("archive", nargs="?", default=DEFAULT_ARCHIVE)
    p_backup.add_argument("--root", default=str(REPO_ROOT), help="Repo root to back up from")

    p_restore = sub.add_parser("restore", help="Extract an archive into a target directory")
    p_restore.add_argument("archive")
    p_restore.add_argument("--dest", default=str(REPO_ROOT), help="Destination directory")

    p_list = sub.add_parser("list", help="List archive contents")
    p_list.add_argument("archive")

    args = parser.parse_args()

    if args.cmd == "backup":
        backup(Path(args.archive).expanduser(), Path(args.root).expanduser())
    elif args.cmd == "restore":
        restore(Path(args.archive).expanduser(), Path(args.dest).expanduser())
    elif args.cmd == "list":
        list_archive(Path(args.archive).expanduser())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
