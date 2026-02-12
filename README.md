# PRIME Tools

Shared tooling for the PRIME AI ecosystem — Gemini API helpers, Jules integration, and session automation scripts.

## Setup

1. Copy `gemini_config.template.json` to `gemini_config.json`
2. Add your API keys (Gemini from aistudio.google.com, Jules from jules.google Settings)
3. Install dependencies: `pip install -U google-genai`
4. Test: `python gemini_setup_test.py`

## Tools

### gemini_helper.py
Multi-purpose Gemini API CLI for all PRIME sessions.

```bash
# Simple Q&A
python gemini_helper.py --task ask --prompt "Your question"

# Summarize a file
python gemini_helper.py --task summarize --input "path/to/file.txt"

# OCR an image
python gemini_helper.py --task ocr --input "path/to/image.png"

# Batch summarize a folder
python gemini_helper.py --task batch-summarize --input "path/to/folder" --pattern "*.txt"

# Extract structured JSON
python gemini_helper.py --task json-extract --input "file.txt" --prompt "Extract as JSON"
```

### gemini_setup_test.py
Verifies API connectivity, lists available models, runs test calls.

## Architecture

```
Claude (brain)  →  designs, reasons, coordinates
Gemini (reader) →  OCR, summarize, classify, extract
Jules (coder)   →  writes code, opens PRs, runs tests
```

## Security

- `gemini_config.json` contains real API keys — **never commit it**
- Use `gemini_config.template.json` as the safe template
- `credentials/` directory is gitignored
