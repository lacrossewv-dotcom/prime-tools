# PRIME Ecosystem — Tools, APIs & Capabilities Reference
**Last Updated:** 2026-02-18
**Maintained By:** Google Session
**Location:** `G:\My Drive\00_CLAUDE_PRIME\TOOL_CHEATSHEET.md`
**Desktop Copy:** `C:\Users\lacro\OneDrive\Desktop\TOOL_CHEATSHEET.md`

All sessions should reference this file for available tools, accounts, and usage instructions.

---

## 1. Claude Code (Primary AI Agent)

| Spec | Value |
|------|-------|
| **Version** | 2.1.45 |
| **Model** | Claude Opus 4.6 (`claude-opus-4-6`) |
| **Platform** | MINGW64 (Git Bash on Windows) |
| **Max output tokens** | 64,000 (custom) |
| **Auth** | Anthropic API key |
| **Cost** | Per-token (Anthropic billing) |
| **Best for** | Complex reasoning, PRIME orchestration, code gen, multi-file edits, cross-session coordination |

### Built-in Tools (18)
Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task (subagents), TaskCreate/Update/Get/List, TaskOutput, TaskStop, NotebookEdit, AskUserQuestion, EnterPlanMode/ExitPlanMode, Skill

### Plugins (6 Enabled)

| Plugin | Source | What It Adds |
|--------|--------|-------------|
| **superpowers** | claude-plugins-official | 17 skills: brainstorming, TDD, systematic debugging, code review, planning, git worktrees, parallel agents, verification |
| **prime** | local-desktop-app-uploads | 5 skills: inbox check, route messages, session status, cheatsheet |
| **firecrawl** | claude-plugins-official | Web scraping/search/crawl/browser — replaces WebFetch/WebSearch for advanced use |
| **hookify** | claude-plugins-official | Behavioral hooks, safety rules, conversation analysis |
| **commit-commands** | claude-plugins-official | Git commit, push, PR workflows |
| **claude-md-management** | claude-plugins-official | CLAUDE.md audit and improvement |

### MCP Servers (4 Configured)

| Server | Status | Workaround |
|--------|--------|------------|
| google-workspace | Tools DON'T LOAD (platform bug) | Direct REST API via Python `requests`/`urllib` |
| athena | Tools DON'T LOAD | Direct file access |
| github | Tools DON'T LOAD | `gh` CLI (see GitHub CLI section) |
| tavily | Tools DON'T LOAD | Firecrawl plugin or WebSearch |

> **All 4 MCP servers are configured in `~/.claude/settings.json` but Claude Code's MCP client never loads their tools. This is a known platform-level bug. Use CLI fallbacks.**

### Subagent Types
Bash, general-purpose, Explore (codebase search), Plan (architecture), code-reviewer, statusline-setup, claude-code-guide, hookify:conversation-analyzer

### Session Launch Commands

| Session | Command |
|---------|---------|
| PRIME | `cd "G:/My Drive/00_CLAUDE_PRIME" && claude` |
| Athena | `cd "G:/My Drive/Personal Drive - Stephen Robert/USMC/CSCBSP" && claude` |
| 8901 | `cd "G:/My Drive/Personal Drive - Stephen Robert/USMC/CSCBSP/8901" && claude` |
| 8902 | `cd "G:/My Drive/Personal Drive - Stephen Robert/USMC/CSCBSP/8902" && claude` |
| JADO | `cd "G:/My Drive/Personal Drive - Stephen Robert/USMC/CSCBSP/JADO Project" && claude` |
| Semper | `cd "G:/My Drive/Semper" && claude` |
| FSMAO | `cd "G:/My Drive/Semper/FSMAO" && claude` |
| Atlas | `cd "G:/My Drive/1. Save Atlas/Atlas_Chapter_Work_v11.1" && claude` |
| Google | `cd "C:/Users/lacro/OneDrive/Desktop" && claude` |
| Sketchi | `cd "G:/My Drive/sketchi-studio" && claude` |
| Index | `cd "G:/My Drive/00_CLAUDE_PRIME/Index" && claude` |
| Historian | `cd "G:/My Drive/00_CLAUDE_PRIME/System_Historian" && claude` |

---

## 2. Firecrawl (Web Scraping & Search)

| Spec | Value |
|------|-------|
| **Version** | CLI v1.3.1 |
| **Account** | lacrossewv-dotcom (GitHub login) |
| **Plan** | Free — 500 one-time credits, 2 concurrent jobs |
| **Cost** | Free tier; Hobby $16/mo (3K credits), Standard $83/mo (100K credits) |
| **Best for** | JS-heavy pages, structured extraction, site crawling, browser automation |
| **Status** | AUTHENTICATED (2026-02-18) |

### Credit Costs

| Operation | Cost |
|-----------|------|
| Search (10 results) | 2 credits |
| Scrape (1 page) | 1 credit |
| Map (URL discovery) | 1 credit |
| Crawl (per page) | 1 credit |
| Browser (per minute) | 2 credits |
| Agent | 5 free runs/day, then dynamic |

### Commands
```bash
# Web search
firecrawl search "query" -o .firecrawl/results.json --json

# Search + scrape results
firecrawl search "query" --scrape -o .firecrawl/results.json --json

# Search news/images
firecrawl search "query" --sources news -o .firecrawl/news.json --json
firecrawl search "query" --sources images -o .firecrawl/images.json --json

# Search by time
firecrawl search "query" --tbs qdr:d -o .firecrawl/today.json --json   # past day
firecrawl search "query" --tbs qdr:w -o .firecrawl/week.json --json    # past week

# Scrape a page
firecrawl scrape https://example.com -o .firecrawl/page.md
firecrawl scrape https://example.com --wait-for 3000 -o .firecrawl/spa.md  # JS pages
firecrawl scrape https://example.com --only-main-content -o .firecrawl/clean.md

# Map all URLs on a site
firecrawl map https://example.com --search "docs" -o .firecrawl/urls.txt

# Crawl entire site section
firecrawl crawl https://example.com/docs --limit 50 --wait -o .firecrawl/docs.json

# AI agent extraction
firecrawl agent "Find pricing plans for X" --wait -o .firecrawl/pricing.json

# Browser (interactive pages)
firecrawl browser "open https://example.com"
firecrawl browser "snapshot"                   # get clickable elements
firecrawl browser "click @e5"                  # click element
firecrawl browser "fill @e3 'search text'"     # fill form
firecrawl browser "scrape" -o .firecrawl/page.md

# Check credits
firecrawl --status
firecrawl credit-usage --json --pretty
```

### When to Use Firecrawl vs Built-in Tools

| Scenario | Use |
|----------|-----|
| Quick web search | **WebSearch** (free, unlimited) |
| Read a simple page | **WebFetch** (free, unlimited) |
| JS-rendered SPA content | **Firecrawl scrape** with `--wait-for` |
| Structured data extraction | **Firecrawl agent** |
| Crawl entire docs site | **Firecrawl crawl** |
| Click through pagination/forms | **Firecrawl browser** |
| Find all URLs on a site | **Firecrawl map** |

---

## 3. Gemini API (OCR, Summarization, Classification)

| Spec | Value |
|------|-------|
| **Account** | lacrossewv@gmail.com |
| **Plan** | Google AI Pro ($19.99/mo) — downgraded from Ultra 2026-02-18 |
| **API Key** | Stored in `~/.google_workspace_mcp/gemini_config.json` |
| **Package** | google-genai v1.63.0 |
| **Models available** | 45 |
| **Billing** | Pay-as-you-go via GCP (API is independent of subscription) |
| **Best for** | OCR, bulk file processing, summarization, classification, data extraction, cheap Q&A |
| **Status** | OPERATIONAL (2026-02-18) |

### Models & Pricing

| Model | ID | Cost (input/output per 1M tokens) | Use Case |
|-------|-----|-----------------------------------|----------|
| Flash Lite 2.5 | gemini-2.5-flash-lite | $0.10 / $0.40 | Bulk classification, cheapest |
| Flash 2.0 | gemini-2.0-flash | $0.10 / $0.40 | Fast general tasks |
| Flash 2.5 | gemini-2.5-flash | $0.30 / $2.50 | **Default workhorse** |
| Pro 2.5 | gemini-2.5-pro | $1.25 / $10.00 | Complex reasoning |
| Flash 3 | gemini-3-flash-preview | $0.50 / $3.00 | Latest flash |
| Pro 3 | gemini-3-pro-preview | $2.00 / $12.00 | Frontier reasoning |

### Commands
```bash
# Simple Q&A
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task ask --prompt "Your question"

# Summarize a file
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task summarize --input "path/to/file.txt"

# OCR an image or scanned PDF
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task ocr --input "path/to/scan.pdf"

# Extract specific data
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task extract --input "file.txt" --prompt "Extract all dates"

# Classify text
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task classify --input "text" --categories "cat1,cat2,cat3"

# Batch summarize a folder
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task batch-summarize --input "path/to/folder" --pattern "*.txt"

# Extract structured JSON
python C:/Users/lacro/.google_workspace_mcp/gemini_helper.py --task json-extract --input "file.txt" --prompt "Extract as JSON"
```

### Config & Helper Paths

| File | Path |
|------|------|
| Config (API keys) | `C:\Users\lacro\.google_workspace_mcp\gemini_config.json` |
| Helper CLI | `C:\Users\lacro\.google_workspace_mcp\gemini_helper.py` |
| Test script | `C:\Users\lacro\.google_workspace_mcp\gemini_setup_test.py` |

---

## 4. Jules API (Autonomous Coding Agent)

| Spec | Value |
|------|-------|
| **Account** | lacrossewv@gmail.com |
| **API Key** | In `gemini_config.json` → `jules_api_key` |
| **Base URL** | `https://jules.googleapis.com/v1alpha/` |
| **GitHub Account** | lacrossewv-dotcom |
| **GitHub App** | Installed, full read/write all repos |
| **Best for** | Autonomous PRs, repo maintenance, CI/CD tasks |
| **Status** | 404 on endpoints (2026-02-18) — may be API change or plan-related, investigating |

### Commands
```bash
# List connected repos
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task list-sources

# Submit a coding task
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task submit --repo prime-tools --prompt "Add requirements.txt"

# Submit with auto-PR
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task submit --repo prime-tools --prompt "Fix bug" --auto-pr

# Repoless task (ephemeral)
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task submit-repoless --prompt "Create a CSV parser"

# Monitor progress
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task status --session SESSION_ID
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task activities --session SESSION_ID

# Send follow-up
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task message --session SESSION_ID --prompt "Also add tests"

# Approve a plan
python C:/Users/lacro/.google_workspace_mcp/jules_helper.py --task approve --session SESSION_ID
```

---

## 5. OpenAI Codex CLI (Overflow Coding Agent)

| Spec | Value |
|------|-------|
| **Version** | 0.101.0 |
| **Model** | gpt-5.3-codex |
| **Auth** | ChatGPT login (included with Pro plan — no API cost) |
| **Config** | `~/.codex/config.toml` |
| **Global instructions** | `~/.codex/AGENTS.md` |
| **Project instructions** | `C:\Users\lacro\.google_workspace_mcp\AGENTS.md` |
| **Best for** | Overflow coding, bulk file ops, simple refactors, code review when Claude context is full |
| **Limitations** | No PRIME context, no memory, no Drive integration |
| **Status** | INSTALLED (2026-02-14) |

### Commands
```bash
# Interactive mode
codex "your prompt here"

# Non-interactive (run and return)
codex exec "your prompt here"

# Target specific directory
codex -C /path/to/project "your prompt here"

# Full auto mode (sandboxed)
codex --full-auto "your prompt here"

# Code review
codex review

# With web search
codex --search "research question"

# Resume previous session
codex resume

# Run on OpenAI's cloud
codex cloud exec --env <ENV_ID> "task"
```

### Codex Cloud Environments
- **CSCBSP** — connected at chatgpt.com/codex
- **prime-tools** — connected at chatgpt.com/codex

---

## 6. GitHub CLI & Integration

| Spec | Value |
|------|-------|
| **Account** | lacrossewv-dotcom (lacrossewv@gmail.com) |
| **Protocol** | HTTPS |
| **Token scopes** | gist, read:org, repo, workflow |
| **Executable** | `C:\Program Files\GitHub CLI\gh.exe` |
| **Bash path** | `"/c/Program Files/GitHub CLI/gh.exe"` (full path required) |
| **Repos** | prime-tools (public), CSCBSP (private) |
| **Status** | AUTHENTICATED |

### Commands
```bash
# View repo
"/c/Program Files/GitHub CLI/gh.exe" repo view lacrossewv-dotcom/prime-tools

# Create PR
"/c/Program Files/GitHub CLI/gh.exe" pr create --title "Title" --body "Description"

# List issues
"/c/Program Files/GitHub CLI/gh.exe" issue list

# View PR status
"/c/Program Files/GitHub CLI/gh.exe" pr status

# View PR comments
"/c/Program Files/GitHub CLI/gh.exe" api repos/lacrossewv-dotcom/prime-tools/pulls/1/comments
```

### GitHub Automations

| Feature | Status |
|---------|--------|
| **Claude Code GitHub Action** | ACTIVE — `@claude` in issues/PRs triggers Claude |
| **Auto code review** | Every PR to prime-tools gets automatic review |
| **Jules GitHub App** | Installed, full read/write all repos |
| **Workflow file** | `.github/workflows/claude.yml` |
| **API key** | `ANTHROPIC_API_KEY` in repo secrets |

### GitHub MCP Server
- Binary: `C:/Users/lacro/.local/bin/github-mcp-server.exe` (v0.30.3)
- Status: Binary works, MCP client doesn't load tools — use `gh` CLI instead

---

## 7. Google Workspace APIs (10 APIs, 38 OAuth Scopes)

| Spec | Value |
|------|-------|
| **Account** | stephen@bender23.com (Super Admin) |
| **Domain** | bender23.com (B23Fitness org) |
| **OAuth credentials** | `~/.google_workspace_mcp/credentials/stephen@bender23.com.json` |
| **Mode** | Full read/write (38 scopes) |
| **Access method** | Direct REST API via Python (most reliable) |
| **Backup** | `workspace-mcp` CLI via `uv tool run` (can hang on token refresh) |
| **Status** | OPERATIONAL — all 10 APIs tested and working |

### APIs & Capabilities

| API | What You Can Do |
|-----|----------------|
| **Gmail** | Search, read, label management, filter creation, batch modify (1000 msgs/batch). 745 filters active. |
| **Drive** | Full traversal, file CRUD, storage analysis. 136,718 files mapped. |
| **Calendar** | Read/write events across 4 calendars (635 events/year on primary) |
| **Docs** | Read/write Google Docs |
| **Sheets** | Read/write spreadsheets (PRIME Data Catalog, etc.) |
| **Slides** | Read/write presentations |
| **Forms** | Read/write Google Forms |
| **Tasks** | Read/write task lists and tasks |
| **People** | Read/write contacts and groups |
| **Admin SDK** | User/org management for bender23.com domain |

### API Access Pattern (Recommended)
```python
import requests, json

# Load credentials
with open('C:/Users/lacro/.google_workspace_mcp/credentials/stephen@bender23.com.json', 'r') as f:
    creds = json.load(f)

# Refresh token
resp = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'refresh_token': creds['refresh_token'],
    'grant_type': 'refresh_token'
})
token = resp.json()['access_token']

# Make API calls
headers = {'Authorization': f'Bearer {token}'}
resp = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/messages?q=your_query', headers=headers)
```

### GCP Projects

| Project | Owner | ID | Use |
|---------|-------|-----|-----|
| workspace-admin-cli | stephen@bender23.com | workspace-admin-cli-486706 | Workspace MCP OAuth, PRIME Mobile OAuth |
| gen-lang-client | lacrossewv@gmail.com | gen-lang-client-0317935100 | Gemini API, Jules API, Cloud Run |

---

## 8. ChatGPT Pro (Browser-Based AI Suite)

| Spec | Value |
|------|-------|
| **Account** | Google login (lacrossewv@gmail.com) |
| **Plan** | Pro ($200/mo) |
| **Model** | GPT-5.2 (Auto, Instant, Thinking, Pro modes) |
| **Access** | chatgpt.com (Steve's browser only) |
| **Best for** | Research, image/video gen, data analysis, web automation |
| **Status** | ALL CONFIGURED (2026-02-14) |

### Features

| Feature | How to Access | Limit |
|---------|--------------|-------|
| **Deep Research** | + menu → Deep research | Unlimited |
| **DALL-E / GPT Image** | + menu → Create image | Unlimited |
| **Sora 2 Video** | Sidebar → Sora, or sora.com | Unlimited |
| **Agent Mode** | + menu → Agent mode | 40/mo |
| **Scheduled Tasks** | Ask ChatGPT, then "Schedule" | 40/mo |
| **Data Analysis** | Upload CSV/Excel/PDF to chat | Unlimited |
| **Shopping Research** | + menu → Shopping research | Unlimited |
| **Codex Cloud** | chatgpt.com/codex → pick repo | Unlimited |

### Connectors (Always On)
- **GitHub:** CSCBSP + prime-tools repos synced and indexed
- **Gmail:** Auto-use ON, proactive activity ON

### Personalization
- **Memory:** All ON (saved memories, chat history, Pulse)
- **Custom instructions:** PRIME context injected
- **About you:** Steve's identity, role, preferences configured

### Action Items
- **$50 API credits** need redemption at platform.openai.com (deadline ~March 16)

---

## 9. PRIME Mobile (PWA Dashboard)

| Spec | Value |
|------|-------|
| **URL** | https://prime-mobile-769012743541.us-west1.run.app |
| **Platform** | Google Cloud Run (us-west1) |
| **Auth** | Google OAuth → JWT (24h), stephen@bender23.com only |
| **Features** | Session dashboard, unified inbox, context-aware chat (Claude + Gemini), Drive file browser |
| **Deploy** | `cd C:/Users/lacro/.google_workspace_mcp && bash deploy.sh` |
| **Status** | DEPLOYED (2026-02-14) |
| **Note** | Cloud Run needs pay-as-you-go billing enabled now that Ultra Cloud credits are gone |

---

## 10. Python Environment

| Spec | Value |
|------|-------|
| **Version** | Python 3.14.2 |
| **Key packages** | requests (2.32.5), google-genai (1.63.0) |
| **pip** | User install at `C:\Users\lacro\AppData\Roaming\Python\Python314\` |
| **Note** | Git Bash may not find user-installed packages — use `python -c "import module"` to test |

---

## Accounts Summary

| Service | Account | Auth Method | Cost |
|---------|---------|-------------|------|
| **Anthropic (Claude)** | API key in settings | Terminal | Per-token |
| **Google Workspace** | stephen@bender23.com | OAuth (38 scopes) | ~$12/mo |
| **Google AI / Gemini** | lacrossewv@gmail.com | API key | $19.99/mo (AI Pro) |
| **ChatGPT Pro** | lacrossewv@gmail.com (Google login) | Browser | $200/mo |
| **GitHub** | lacrossewv-dotcom | PAT + gh CLI | Free |
| **Firecrawl** | lacrossewv-dotcom (GitHub login) | Stored credentials | Free (500 credits) |

---

## Architecture — When to Use What

```
Claude Code  (brain)     →  orchestration, PRIME context, complex reasoning, code gen
Codex CLI    (hands)     →  overflow coding, isolated mechanical tasks
ChatGPT Pro  (utility)   →  research, image gen, video, data analysis, web automation
Gemini       (reader)    →  OCR, bulk summarization, classification, extraction
Jules        (coder)     →  autonomous PRs, repo tasks (currently 404 — investigating)
Firecrawl    (scraper)   →  JS pages, site crawls, browser automation, structured extraction
```

| Situation | Use This |
|-----------|----------|
| Complex multi-step reasoning | **Claude Code** |
| PRIME session coordination | **Claude Code** |
| Writing/editing code in a project | **Claude Code** |
| Quick web search | **WebSearch** (free) or **Firecrawl search** (2 credits) |
| Read a webpage | **WebFetch** (free) or **Firecrawl scrape** (1 credit) |
| JS-heavy or interactive pages | **Firecrawl scrape/browser** |
| Crawl entire documentation site | **Firecrawl crawl** |
| Quick isolated code task | **Codex CLI** |
| Bulk rename, grep-replace | **Codex CLI** |
| Code review | **Codex CLI** (`codex review`) |
| OCR scanned documents | **Gemini** (`--task ocr`) |
| Summarize 50+ files cheaply | **Gemini** (`--task batch-summarize`) |
| Classify or extract data | **Gemini** (`--task classify`/`extract`) |
| Autonomous PR creation | **Jules** (when API restored) |
| Deep web research | **ChatGPT Deep Research** |
| Generate images/logos | **ChatGPT DALL-E** |
| Generate marketing videos | **ChatGPT Sora** |
| Analyze spreadsheets/CSVs | **ChatGPT Data Analysis** |
| Browse websites autonomously | **ChatGPT Agent** |
| Automated recurring reports | **ChatGPT Scheduled Tasks** |

---

## Key Paths

| What | Path |
|------|------|
| Desktop (workspace) | `C:\Users\lacro\OneDrive\Desktop` |
| CLAUDE.md (Desktop) | `C:\Users\lacro\OneDrive\Desktop\CLAUDE.md` |
| This cheatsheet | `G:\My Drive\00_CLAUDE_PRIME\TOOL_CHEATSHEET.md` |
| PRIME inboxes | `G:\My Drive\00_CLAUDE_PRIME\messages\TO_*.md` |
| prime-tools repo | `C:\Users\lacro\.google_workspace_mcp\` |
| Gemini config | `C:\Users\lacro\.google_workspace_mcp\gemini_config.json` |
| Gemini helper | `C:\Users\lacro\.google_workspace_mcp\gemini_helper.py` |
| Jules helper | `C:\Users\lacro\.google_workspace_mcp\jules_helper.py` |
| Codex config | `~/.codex/config.toml` |
| Codex instructions | `~/.codex/AGENTS.md` |
| Claude settings | `C:\Users\lacro\.claude\settings.json` |
| Claude memory | `C:\Users\lacro\.claude\projects\...\memory\MEMORY.md` |
| Workspace credentials | `~/.google_workspace_mcp/credentials/stephen@bender23.com.json` |
| Sheets token | `C:\Users\lacro\.claude\sheets-token.json` |
| GitHub MCP binary | `C:/Users/lacro/.local/bin/github-mcp-server.exe` |
| PRIME Data Catalog | Sheet ID `1Vijb9kxxRUUaKJ9ZUD6CR6RyB0uFSG-t_ZxNC1F5rmc` |
