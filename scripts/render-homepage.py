#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def render(sections_dir: Path, output: Path) -> None:
    files = sorted(p for p in sections_dir.glob("*.yaml") if p.is_file())
    if not files:
        raise SystemExit(f"no section files found in {sections_dir}")
    content = ""
    for idx, path in enumerate(files):
        text = path.read_text().rstrip()
        if not text:
            continue
        if content:
            content += "\n"
        content += text + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    print(f"wrote {output} from {len(files)} fragments")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Homepage services.yaml from per-section fragments.")
    parser.add_argument("--sections", default="services/homepage/sections", help="Directory containing section YAML fragments")
    parser.add_argument("--output", default="services/homepage/services.yaml", help="Rendered Homepage services file")
    args = parser.parse_args()
    render(Path(args.sections).expanduser(), Path(args.output).expanduser())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
