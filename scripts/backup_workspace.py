"""Back up user_data/ to a zip outside the repository.

Run before every update (the update skill does this). Backups go to
~/CareerForge-backups/careerforge_<timestamp>.zip, so no git command and no
re-clone of the repo can touch them. The scratch folder user_data/output/.work/
is skipped. Only the newest --keep backups are kept (default 3).

    python scripts/backup_workspace.py
    python scripts/backup_workspace.py --keep 5 --note "before update to abc1234"
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, USER_DATA  # noqa: E402

BACKUP_DIR = Path.home() / "CareerForge-backups"
EXTRA_FILES = [ROOT / ".claude" / "settings.local.json"]
SKIP_DIRS = {USER_DATA / "output" / ".work"}


def files_to_back_up() -> list[Path]:
    files = [
        p for p in sorted(USER_DATA.rglob("*"))
        if p.is_file() and not any(skip in p.parents for skip in SKIP_DIRS)
    ]
    return files + [p for p in EXTRA_FILES if p.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keep", type=int, default=3, help="number of backups to keep (default 3)")
    parser.add_argument("--note", default="", help="free text recorded in the backup log")
    args = parser.parse_args()

    if not USER_DATA.is_dir():
        print(f"No {USER_DATA} folder: nothing to back up.")
        return 1

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = BACKUP_DIR / f"careerforge_{stamp}.zip"
    files = files_to_back_up()
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(dest) as z:
        bad = z.testzip()
        count = len(z.namelist())
    if bad or count != len(files):
        print(f"BACKUP FAILED: {dest} (bad entry: {bad}, {count} of {len(files)} files)")
        return 1

    old = sorted(BACKUP_DIR.glob("careerforge_*.zip"))[: -args.keep or None] if args.keep > 0 else []
    for p in old:
        p.unlink()

    size_mb = dest.stat().st_size / 1e6
    with (BACKUP_DIR / "update_log.txt").open("a", encoding="utf-8") as log:
        log.write(f"{stamp}\t{dest.name}\t{count} files\t{size_mb:.1f} MB\t{args.note}\n")
    print(f"Backed up {count} files ({size_mb:.1f} MB) to {dest}")
    if old:
        print(f"Removed {len(old)} older backup(s); keeping the newest {args.keep}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
