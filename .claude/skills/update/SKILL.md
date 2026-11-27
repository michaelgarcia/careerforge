---
name: update
description: >
  Update CareerForge to the latest version from GitHub without risking personal data: back up
  user_data/ outside the repo, show what's new, then fast-forward safely. Use for "update
  CareerForge", "get the latest version", "pull from GitHub", "is there a new version?".
---

# Update CareerForge

The repo is the product. Everything personal is in `user_data/`, which git never tracks, so an update has nothing there to change. This skill keeps it that way: a backup first, then a fast-forward that refuses to overwrite any ignored file. **Never** use `git pull`, `git reset`, `git clean`, `git stash --all` or `git checkout -- <path>` here.

## 1. Preflight

- `git rev-parse --is-inside-work-tree`. If this isn't a git repo (a ZIP download), explain that updates need a git clone, point to the install steps in `README.md`, and stop.
- `git rev-parse --abbrev-ref HEAD`. If it isn't `main`, say which branch they're on and ask before continuing.
- `git status --porcelain --untracked-files=no`. If tracked files are modified, list them in plain words (e.g. "you edited `.claude/agents/scorer.md`") and ask:
  1. Keep my changes and update around them (uses `--autostash`; any overlap gets shown to you)
  2. Stop here

## 2. Back up

Run `python scripts/backup_workspace.py --note "before update from $(git rev-parse --short HEAD)"`. If it prints `BACKUP FAILED` or exits non-zero, stop: never update without a good backup. Tell the user the backup path.

## 3. What's new

1. Run `git fetch origin`. If `git rev-list --count HEAD..origin/main` is 0, say "You're on the latest version" and stop.
2. Show `git log --oneline --no-merges HEAD..origin/main` as a short plain-language summary, not raw hashes.
3. Run `git diff HEAD..origin/main -- CHANGELOG.md` and list every **Action needed** line in the range.
4. Run `git diff --name-status HEAD..origin/main` and check it. Stop and explain if any path starts with `user_data/`, since that should never happen. Mention any change to `.gitignore`. Mention `requirements.txt` changes, since packages will be installed.
5. Ask: "Update now?"

## 4. Update

```bash
git merge --ff-only --no-overwrite-ignore origin/main
```

Add `--autostash` if the user chose option 1 in preflight. If the merge fails, explain the reason in plain words and stop. Change nothing else; the backup is there.
- *Not possible to fast-forward*: local commits diverge from GitHub.
- *Would overwrite ignored file*: an update tried to write over one of your files, so it was blocked.
- *Autostash conflict*: your edit and the update touch the same lines. Show the file.

## 5. After

- If `requirements.txt` changed, run `python -m pip install --quiet -r requirements.txt`.
- Carry out each **Action needed** entry, asking the user before each one.
- Check that `user_data/knowledge_base/candidate_profile.yaml` (if it existed before) and `user_data/postings/applications.csv` are still there. If either is missing, restore it from the backup zip and tell the user.
- Close with what changed, the backup path, and: "Start a new session so the updated skills and rules load."
