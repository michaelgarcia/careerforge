---
name: build-kb
description: >
  Build or update the candidate's career profile (the knowledge base) from the documents in
  user_data/knowledge_base/sources/. Use when the user adds career documents, says "build my profile",
  "update my profile", "I added my resume", "rebuild my KB", or when the profile is missing or stale.
argument-hint: "[quick] [a URL or file to ingest]"
context: fork
agent: kb-builder
background: false
---
Ingest the source materials in user_data/knowledge_base/sources/ and build or update the candidate profile.

Scan for new or modified files, process them in priority order, merge into candidate_profile.yaml, update source_index.md and ingestion_progress.yaml, and write candidate_narrative.md after all files are processed.

If the arguments include "quick", process only the `Resumes and mind maps/` folder (the first priority group), write the narrative, and stop, reporting how many files remain for a full build. Otherwise process everything pending.

Arguments: $ARGUMENTS
