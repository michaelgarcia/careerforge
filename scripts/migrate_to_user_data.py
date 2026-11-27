"""Copy personal data from the pre-2026-11 layout into user_data/.

Before November 2026, personal data lived in five top-level folders
(knowledge_base/, config/, postings/, output/, data/). It now lives in one
gitignored folder, user_data/, with the same subfolder names.

This script COPIES and never moves or deletes. It refuses to overwrite a
destination file that differs from its source, verifies every copied file by
size and sha256, and prints a per-folder report. Re-running it is safe: files
already copied identically are skipped. Once the report looks right, delete the
old folders yourself.

    python scripts/migrate_to_user_data.py            # copy and verify
    python scripts/migrate_to_user_data.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, TEMPLATES_DIR, USER_DATA  # noqa: E402

FOLDERS = ["knowledge_base", "postings", "output", "data"]
CONFIG_FILES = ["preferences.yaml", "search_scopes.yaml", "company_targets.yaml", "config.ini"]
SKIP_NAMES = {".gitkeep"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def legacy_pairs() -> dict[str, list[tuple[Path, Path]]]:
    """Map each old root to its (source, destination) file pairs."""
    groups: dict[str, list[tuple[Path, Path]]] = {}
    for name in FOLDERS:
        src_root = ROOT / name
        if src_root.is_dir():
            groups[name] = [
                (p, USER_DATA / name / p.relative_to(src_root))
                for p in sorted(src_root.rglob("*"))
                if p.is_file() and p.name not in SKIP_NAMES
            ]
    config = []
    for name in CONFIG_FILES:
        p = ROOT / "config" / name
        if p.is_file():
            config.append((p, USER_DATA / "config" / name))
    style = ROOT / "config" / "resume_style.yaml"
    default_style = TEMPLATES_DIR / "resume_style.yaml"
    if style.is_file() and not (default_style.is_file() and sha256(style) == sha256(default_style)):
        config.append((style, USER_DATA / "config" / "resume_style.yaml"))
    if config:
        groups["config"] = config
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report what would be copied; change nothing")
    args = parser.parse_args()

    groups = legacy_pairs()
    if not groups:
        print("No pre-2026-11 data folders found. Nothing to migrate.")
        return 0

    conflicts: list[Path] = []
    failures: list[Path] = []
    print(f"{'folder':<16}{'files':>7}{'copied':>8}{'already':>9}{'MB':>9}")
    for name, pairs in groups.items():
        copied = already = 0
        size = 0
        for src, dst in pairs:
            size += src.stat().st_size
            if dst.exists():
                if sha256(src) == sha256(dst):
                    already += 1
                else:
                    conflicts.append(dst)
                continue
            if args.dry_run:
                copied += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if dst.stat().st_size != src.stat().st_size or sha256(dst) != sha256(src):
                failures.append(dst)
            else:
                copied += 1
        print(f"{name:<16}{len(pairs):>7}{copied:>8}{already:>9}{size / 1e6:>9.1f}")

    if args.dry_run:
        print("\nDry run: nothing was copied.")
    for dst in conflicts:
        print(f"CONFLICT (kept existing, not overwritten): {dst.relative_to(ROOT)}")
    for dst in failures:
        print(f"VERIFY FAILED: {dst.relative_to(ROOT)}")
    if conflicts or failures:
        return 1
    if not args.dry_run:
        print(
            "\nAll files copied and verified (size + sha256) into user_data/.\n"
            "Your old folders were left untouched. Once you have checked user_data/, "
            "delete knowledge_base/, postings/, output/, data/ and config/ yourself."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
