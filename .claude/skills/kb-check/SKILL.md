---
name: kb-check
description: >
  Check whether the career knowledge base is current and complete, without changing anything:
  unprocessed source files, broken provenance, achievements missing metrics, and stale
  narrative or north star. Use for "is my profile up to date?", "what's missing from my KB?",
  "check my knowledge base", or before an important application.
---

# Knowledge base health check (read-only)

Never write or edit any file in this skill. Report, then recommend one next action.

All of these paths are gitignored: use Read, Glob, or `rg --no-ignore` via Bash, never the Grep tool (see `.claude/reference/kb-context.md`).

## Checks

1. **Ready?** `user_data/knowledge_base/candidate_profile.yaml` exists and `personal.name` is not `"Your Name"`. If not, stop and report the state (no sources, or sources but no profile).
2. **Valid YAML:** `python -c "import sys,yaml; yaml.safe_load(sys.stdin); print('Valid YAML')" < user_data/knowledge_base/candidate_profile.yaml`
3. **Sources vs. ingestion state:** list every file under `user_data/knowledge_base/sources/` (excluding `.gitkeep`) and compare it with the entries in `user_data/knowledge_base/ingestion_progress.yaml`. Entries may be `files[].path` (the documented format) or an older layout such as `sources_processed[].file`. Match on the file name with only lowercase letters and digits kept, because older entries may have altered punctuation. If the file isn't in the documented format, say so; `/build-kb` converts it.
   - On disk but not listed: **new, not ingested**.
   - Listed with status `pending`, `modified`, `in_progress` or `error`: **unfinished**. (`ingested`, `complete`, `skipped`, `acknowledged` and `removed` are finished states.)
   - Listed but not on disk: **removed**; its facts are still in the KB.
   - Modified since `last_run`: `find user_data/knowledge_base/sources -type f ! -name .gitkeep -newer user_data/knowledge_base/ingestion_progress.yaml`. A file copied with its old timestamp can slip past this; `/build-kb` re-checks hashes.
4. **Provenance:** collect every `source:` value in the profile. Report values that are `"unverified"` (count) and values that look like a path but don't exist under `user_data/knowledge_base/sources/`. Values starting with `story-capture-session-` are legacy story captures with no file; count them separately.
5. **XYZ gaps:** achievements whose `metrics` is empty or contains `(unquantified)`. List up to 10 by company and the first words of the description.
6. **Freshness:** compare modification times. Flag `candidate_narrative.md`, `north_star.md`, `resume_variants.md` or `candidate_summary_compact.md` when older than `candidate_profile.yaml`.

## Report

```
KB health — <date>
Profile: ready | template | missing      YAML: valid | INVALID
Sources: N files · X new · Y unfinished · Z removed · W modified since last build
Provenance: U unverified · B broken paths · L legacy story captures
XYZ gaps: G achievements without metrics
Stale: <files older than the profile, or "none">

Next step: <one recommendation>
```

Choose the next step in this order, phrased as something the user can just say (shortcut in parentheses): invalid YAML → fix it first. New, unfinished or modified sources → "update my profile" (`/build-kb`). Stale `north_star.md` → "refresh my north star" (`/north-star refresh`). XYZ gaps → "let's add metrics to my stories" (`/capture-story`) for the top ones. Stale compact summary → it regenerates on the next company scan. Otherwise → "Your knowledge base is current."
