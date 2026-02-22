# Source Materials

Place your raw source materials in this directory. The KB Builder agent ingests these to populate `candidate_profile.yaml` and `candidate_narrative.md`.

## Supported Formats

- **PDF** — resumes, published papers, certificates
- **Markdown / Text** — transcripts, notes, project write-ups
- **Word (.docx)** — existing resumes, cover letters
- **Images** — certificates, awards, screenshots of recommendations

## Suggested Organization

You can organize files into subdirectories:

```
sources/
├── resumes/           # Existing resume versions
├── transcripts/       # Interview transcripts, voice memo transcripts
├── articles/          # Published articles, blog posts
├── certificates/      # Certification documents
└── references/        # Recommendation letters, performance reviews
```

## Usage

After adding files, run the KB Builder agent:

```bash
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."
```

The agent will:
1. Read each source document
2. Extract structured data (skills, achievements, experience)
3. Write to `candidate_profile.yaml` and `candidate_narrative.md`
4. Log provenance in `source_index.md`
