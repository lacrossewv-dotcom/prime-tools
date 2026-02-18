# AGENTS.md - prime-tools Repository

## Project
PRIME Tools — shared tooling for the PRIME AI ecosystem. Contains Gemini API helpers, Jules integration, PRIME Mobile PWA + backend, and session automation scripts.

## Structure
```
.
├── gemini_helper.py        # Gemini API multi-tool CLI
├── jules_helper.py         # Jules API task submission CLI
├── gemini_setup_test.py    # Setup verification script
├── gemini_config.template.json  # Safe config template (commit this)
├── gemini_config.json      # REAL API keys (GITIGNORED - never commit)
├── credentials/            # OAuth tokens (GITIGNORED - never commit)
├── deploy.sh               # Cloud Run deploy script
├── Dockerfile              # Container build
├── backend/                # PRIME Mobile Express API
│   ├── server.js
│   ├── routes/             # auth, chat, files, inbox, sessions
│   ├── services/           # claudeAPI, geminiAPI, googleDrive, primeParser
│   └── middleware/         # auth JWT middleware
├── mobile-pwa/             # PRIME Mobile PWA frontend
│   ├── index.html
│   ├── css/styles.css
│   └── js/                 # app, api, auth, chat, dashboard, files, inbox
└── .github/workflows/      # Claude Code GitHub Action
```

## Security Rules
- NEVER read, modify, or commit `gemini_config.json` — contains real API keys
- NEVER read, modify, or commit anything in `credentials/` — contains OAuth tokens
- NEVER read, modify, or commit `backend/.env` — contains env vars with secrets
- These are all in .gitignore. Keep them there.

## Code Conventions
- Backend: Node.js/Express, CommonJS require, JSDoc comments
- Frontend: Vanilla JS (no framework), dark theme, mobile-first
- Python scripts: PEP 8, argparse CLI, docstrings
- Deployment: Google Cloud Run via deploy.sh

## Testing
- Backend: `node --test backend/tests/`
- Python: `python gemini_setup_test.py`
- Local dev: `node backend/server.js` (port 8080)
