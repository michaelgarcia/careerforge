---
paths:
  - "knowledge_base/**"
---
# Knowledge base rules

- **Provenance:** every fact written to `candidate_profile.yaml` has a `source` (a path relative to `knowledge_base/sources/`), or `"unverified"` when no source exists. Never assume one silently.
- **Schema:** `docs/profile_schema.md` is the only schema. Add optional fields there first; never invent top-level keys.
- **Validate after every write:** `python -c "import sys,yaml; yaml.safe_load(sys.stdin); print('Valid YAML')" < knowledge_base/candidate_profile.yaml`
- **Conflicts are flagged, not resolved:** when a source contradicts existing KB data, report it to the user instead of overwriting.
- **Framing files are hand-authored:** only the `north-star` skill writes `north_star.md`; `resume_variants.md` and `memories/` change only on the user's explicit instruction. Ingestion never edits them.
- **Ingestion state:** a file added to `sources/` outside `/build-kb` (for example by story capture) must also be registered in `ingestion_progress.yaml` with its content hash, or the next build will re-ingest it.
