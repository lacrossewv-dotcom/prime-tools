# PRIME Tools — Monorepo

Central repository for the PRIME AI ecosystem. Organized by session, with shared resources and cross-session deliverables tracked in a single repo.

## Structure

```
prime-tools/
├── shared/                     Resources used across all sessions
│   ├── TOOL_CHEATSHEET.md      10-tool ecosystem reference
│   └── prime-mobile/           PRIME Mobile PWA + API (Cloud Run)
├── sessions/
│   └── google/                 Google session (IT/GCP/Workspace)
│       ├── scripts/            API helpers, OAuth utilities
│       ├── docs/               Strategy docs, references
│       └── config/             Templates, Codex AGENTS.md
├── cross-session/              Deliverables spanning multiple sessions
│   └── daedalus/               Biographical research (Google → Atlas)
├── drive-sync/                 Snapshots of Google Drive canonical files
├── MANIFEST.md                 Source-of-truth mapping for all files
└── .github/workflows/          Claude Code GitHub Action
```

## Quick Start

1. Copy `sessions/google/config/gemini_config.template.json` to `gemini_config.json` (repo root)
2. Add your API keys (Gemini from aistudio.google.com, Jules from jules.google)
3. Install dependencies: `pip install -U google-genai`
4. Test: `python sessions/google/scripts/gemini_setup_test.py`

## Key Tools

### Gemini Helper (`sessions/google/scripts/gemini_helper.py`)
Multi-purpose Gemini API CLI — Q&A, summarize, OCR, classify, extract, batch process.

```bash
python sessions/google/scripts/gemini_helper.py --task ask --prompt "Your question"
python sessions/google/scripts/gemini_helper.py --task ocr --input "image.png"
python sessions/google/scripts/gemini_helper.py --task batch-summarize --input "folder/" --pattern "*.txt"
```

### Jules Helper (`sessions/google/scripts/jules_helper.py`)
Google Jules coding agent CLI — submit tasks, monitor sessions, approve plans.

### PRIME Mobile (`shared/prime-mobile/`)
Dashboard PWA serving all 12 PRIME sessions. Deployed to Cloud Run.

## Architecture

```
Claude (brain)  →  designs, reasons, coordinates
Codex  (hands)  →  overflow coding, bulk file ops
Gemini (reader) →  OCR, summarize, classify, extract
Jules  (coder)  →  autonomous PRs, repo tasks
```

## Adding a Session

When cleaning up another session's files:
1. Create `sessions/<session-name>/` with `scripts/`, `docs/`, `config/` as needed
2. Move files from Desktop into the appropriate subfolders
3. Update `MANIFEST.md` with the new entries and source-of-truth mapping
4. Cross-session deliverables go in `cross-session/<project-name>/`
5. Files whose source of truth is Google Drive go in `drive-sync/`

## Security

- `gemini_config.json` — real API keys, **never committed** (gitignored)
- `credentials/` — OAuth tokens, **never committed** (gitignored)
- Use `gemini_config.template.json` as the safe template
