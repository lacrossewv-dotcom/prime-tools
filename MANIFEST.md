# MANIFEST — Source of Truth Mapping

This file maps every tracked resource to its **source of truth** — where the canonical version lives. Files may exist in GitHub, Google Drive, or both.

## Legend

| Source of Truth | Meaning |
|----------------|---------|
| **GitHub** | Repo is canonical. Edit here, push to origin. |
| **Google Drive** | Drive (Google Docs) is canonical. Repo copy is a snapshot/reference. |
| **Both** | Maintained in both places. Sync manually when updated. |
| **Local only** | Gitignored. Lives on disk but never committed. |

---

## Shared Resources

| File | Source of Truth | Drive Location | Repo Path |
|------|----------------|----------------|-----------|
| TOOL_CHEATSHEET.md | Both | `00_CLAUDE_PRIME/TOOL_CHEATSHEET.md` | `shared/TOOL_CHEATSHEET.md` |
| PRIME Mobile (PWA + API) | GitHub | N/A (deployed to Cloud Run) | `shared/prime-mobile/` |

## Sessions — Google

| File | Source of Truth | Drive Location | Repo Path |
|------|----------------|----------------|-----------|
| gemini_helper.py | GitHub | N/A | `sessions/google/scripts/gemini_helper.py` |
| jules_helper.py | GitHub | N/A | `sessions/google/scripts/jules_helper.py` |
| gemini_setup_test.py | GitHub | N/A | `sessions/google/scripts/gemini_setup_test.py` |
| auth_lacrossewv.py | GitHub | N/A | `sessions/google/scripts/auth_lacrossewv.py` |
| daedalus_personal_gmail.py | GitHub | N/A | `sessions/google/scripts/daedalus_personal_gmail.py` |
| read_bio_files.py | GitHub | N/A | `sessions/google/scripts/read_bio_files.py` |
| GEMINI_OFFLOAD_STRATEGY.md | GitHub | N/A | `sessions/google/docs/GEMINI_OFFLOAD_STRATEGY.md` |
| Git Bash Commands for Sessions.txt | GitHub | N/A | `sessions/google/docs/Git Bash Commands for Sessions.txt` |
| gemini_config.template.json | GitHub | N/A | `sessions/google/config/gemini_config.template.json` |
| AGENTS.md (Codex config) | GitHub | N/A | `sessions/google/config/AGENTS.md` |
| gemini_config.json (real keys) | Local only | N/A | Gitignored — `gemini_config.json` at repo root |
| OAuth credentials | Local only | N/A | Gitignored — `credentials/` |

## Cross-Session Deliverables

| File | Source of Truth | Produced By | Consumed By | Repo Path |
|------|----------------|-------------|-------------|-----------|
| ATLAS_DAEDALUS_RESEARCH_RESULTS.md | GitHub | Google session | Atlas session | `cross-session/daedalus/` |
| daedalus_personal_findings.md | GitHub | Google session | Atlas session | `cross-session/daedalus/` |

## Drive-Sync (Google Drive canonical, repo snapshots)

_No files synced yet. As sessions are migrated, files whose source of truth is Google Drive will be tracked here._

| File | Drive Location | Repo Path | Last Synced |
|------|----------------|-----------|-------------|
| _(placeholder)_ | | | |

## Not Yet Migrated

These files remain on the Desktop and belong to other sessions. They will be organized when those sessions are cleaned up.

| File/Folder | Belongs To | Desktop Location |
|-------------|-----------|-----------------|
| Atlas/ | Atlas session | `Desktop/Atlas/` |
| Backup/ | Athena session | `Desktop/Backup/` |
| DocToMarkdown/ | Athena/General | `Desktop/DocToMarkdown/` |
| New Designs/ | Sketchi session | `Desktop/New Designs/` |
| Old Athena Files Probably not needed/ | Athena session | `Desktop/Old Athena Files...` |
| TO_DELETE_old_athena_files/ | Athena session | `Desktop/TO_DELETE_old_athena_files/` |
| ompf_pages/ | Atlas (Google assisted) | `Desktop/ompf_pages/` |
| prompt-builder/ | General | `Desktop/prompt-builder/` |
| Desktop to be organized/ | Personal (Steve) | `Desktop/Desktop to be organized/` |
| ATLAS_ORIGIN_STORY.md | Atlas session | `Desktop/` |
| JADO_Team_Input_Prompt.md | JADO session | `Desktop/` |
| JADO_Brief_Team_Input_Steve_Bender.md | JADO session | `Desktop/` |
| CSCBSP_8902_Master_Extraction.md | Athena session | `Desktop/` |
