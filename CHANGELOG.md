# Changelog

Newest first. An entry with **Action needed** asks for a one-time step; the `update` skill shows these and carries them out with your OK.

## 2026-11-25: Personal data moves to `user_data/`; plugin install removed

- Everything personal now lives in one gitignored folder, `user_data/` (`knowledge_base/`, `config/`, `postings/`, `output/`, `data/` inside it, same names as before). The repo has no files there, so updates can never change your data.
- New `update` skill: say "update CareerForge". It backs up `user_data/` to `~/CareerForge-backups/`, shows what's new, and fast-forwards with `git merge --ff-only --no-overwrite-ignore`.
- New `setup` skill (replaces `/cf-init`): creates `user_data/` and installs the Python packages.
- The resume style default moved from `config/resume_style.yaml` to `templates/resume_style.yaml`. Your own overrides go in `user_data/config/resume_style.yaml`.
- The email-alert config (`config.ini`) now lives at `user_data/config/config.ini`.
- Removed: the Claude Code plugin (`.claude-plugin/`, `marketplace.json`, `/cf-init`), the plugin ZIP builder, and the setup and launch scripts. Install by cloning the repo and opening it in the Claude desktop app (see README).

**Action needed (installs from before this date):** copy your data into `user_data/`. Start a new session and say yes when CareerForge offers it, or run `python scripts/migrate_to_user_data.py`. It copies and verifies every file and never moves or deletes anything. If you had edited `config/resume_style.yaml`, it is copied to `user_data/config/resume_style.yaml`. Once `user_data/` looks right, delete the old top-level `knowledge_base/`, `config/`, `postings/`, `output/` and `data/` folders yourself.
