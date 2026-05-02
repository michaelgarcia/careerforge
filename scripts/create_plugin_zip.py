#!/usr/bin/env python3
"""
Creates a distributable CareerForge plugin zip for users who cannot use
the marketplace (e.g. the ZIP upload fallback path in Claude Desktop).

Usage:
    python scripts/create_plugin_zip.py

Output:
    careerforge-{version}.zip in the repo root
"""

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INCLUDE_PATHS = [
    ".claude",
    "config",
    "templates",
    "tools",
    "scripts",
    "docs",
    "plugin.json",
    "marketplace.json",
    "README.md",
    "SOUL.md",
    "LICENSE",
    "pyproject.toml",
    "requirements.txt",
]

# Files/dirs to skip even if inside an included path
EXCLUDE_NAMES = {
    "__pycache__",
    "node_modules",
    "worktrees",
    ".git",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

# Files to exclude by relative path (relative to repo root)
EXCLUDE_FILES = {
    ".claude/settings.local.json",
    "config/preferences.yaml",
    "config/search_scopes.yaml",
}


def should_exclude(rel_path: Path) -> bool:
    if str(rel_path).replace("\\", "/") in EXCLUDE_FILES:
        return True
    for part in rel_path.parts:
        if part in EXCLUDE_NAMES:
            return True
    if rel_path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def collect_files() -> list[tuple[Path, Path]]:
    """Returns list of (absolute_path, archive_path) tuples."""
    files = []
    for include in INCLUDE_PATHS:
        abs_path = ROOT / include
        if not abs_path.exists():
            print(f"  [SKIP] {include} (not found)")
            continue
        if abs_path.is_file():
            rel = abs_path.relative_to(ROOT)
            if not should_exclude(rel):
                files.append((abs_path, rel))
        else:
            for f in abs_path.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(ROOT)
                    if not should_exclude(rel):
                        files.append((f, rel))
    return files


def main():
    plugin_json = ROOT / "plugin.json"
    if not plugin_json.exists():
        print("ERROR: plugin.json not found at repo root.")
        raise SystemExit(1)

    with plugin_json.open() as f:
        meta = json.load(f)
    version = meta.get("version", "0.1.0")

    out_path = ROOT / f"careerforge-{version}.zip"
    files = collect_files()

    print(f"\nCreating {out_path.name} ...")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arc_path in sorted(files, key=lambda x: str(x[1])):
            zf.write(abs_path, arc_path)
            print(f"  + {arc_path}")

    size_kb = out_path.stat().st_size // 1024
    print(f"\nDone — {out_path.name} ({size_kb} KB, {len(files)} files)")
    print(f"\nDistribute this zip to users who cannot access the marketplace.")
    print("They upload it in Claude Desktop: /plugin add /path/to/careerforge-{}.zip".format(version))


if __name__ == "__main__":
    main()
