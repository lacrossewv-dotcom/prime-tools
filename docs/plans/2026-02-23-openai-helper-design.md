# OpenAI Helper CLI — Design Document

**Date:** 2026-02-23
**Session:** Google
**Status:** Approved

## Purpose

Add OpenAI API access to the PRIME six-layer architecture via `openai_helper.py`, matching the established pattern of `groq_helper.py` and `gemini_helper.py`. Includes budget guardrails to prevent runaway costs.

## Architecture

- **Location:** `C:\Users\lacro\.google_workspace_mcp\openai_helper.py` (root level, alongside other helpers)
- **Pattern:** Single-file CLI, argparse, reads key from `gemini_config.json`, logs via `usage_logger.py`
- **Python:** `py -3.13` (same as Groq/Chroma)
- **Package:** `openai` (needs `pip install`)

## Tasks (9)

| Task | Default Model | Description |
|------|---------------|-------------|
| ask | gpt-4.1-mini | Simple Q&A chat completion |
| summarize | gpt-4.1-mini | Summarize a file |
| extract | gpt-4.1-mini | Extract specific data from a file |
| search | gpt-4.1-mini | Web search with citations (web_search_preview tool) |
| vision | gpt-4.1-mini | Analyze an image (base64 encoded) |
| json-extract | gpt-4.1-mini | Structured JSON output from a file |
| image | dall-e-3 | Generate an image, save to disk |
| models | — | List available models with pricing |
| budget | — | Show current month spend vs budget cap |
| test | gpt-4.1-nano | Quick connectivity test |

## Model Catalog

| Model | Cost (in/out per 1M) | Use Case |
|-------|----------------------|----------|
| gpt-4.1-mini (DEFAULT) | $0.40 / $1.60 | Default for most tasks |
| gpt-4.1-nano | $0.10 / $0.40 | Bulk/classification |
| gpt-5.2 | $1.75 / $14.00 | Complex reasoning (explicit --model) |
| dall-e-3 | ~$0.04-0.08/image | Image generation |

## Budget Guardrails

1. **Monthly cap:** `gemini_config.json` → `"openai_monthly_budget": 30.00`
2. **Hard block:** If month spend >= budget, refuse to make API calls
3. **Per-call warning:** If estimated cost > $1.00, require `--yes` flag
4. **Running total:** Every call prints `[OpenAI] Cost: $X.XX | Month: $Y.YY / $Z.ZZ (N%)`
5. **Budget task:** `--task budget` shows breakdown

## Config Changes

- `gemini_config.json`: Add `"openai_api_key"` and `"openai_monthly_budget"` fields
- `usage_logger.py`: Add OpenAI models to PRICE_TABLE

## Files Modified

1. `openai_helper.py` — NEW
2. `gemini_config.json` — Add 2 fields
3. `usage_logger.py` — Add OpenAI price entries
