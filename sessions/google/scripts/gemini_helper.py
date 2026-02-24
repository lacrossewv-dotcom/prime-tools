"""
Gemini API Helper for PRIME Ecosystem
======================================
Central interface for all Claude Code sessions to call Gemini models.
Reduces Claude token burn by offloading bulk tasks to Google's API.

Usage from any session:
    python gemini_helper.py --task summarize --input "path/to/file.txt"
    python gemini_helper.py --task classify --input "text to classify" --categories "cat1,cat2,cat3"
    python gemini_helper.py --task extract --input "path/to/file.txt" --prompt "Extract all dates"
    python gemini_helper.py --task ask --prompt "What is the capital of France?"
    python gemini_helper.py --task ocr --input "path/to/image.png"
    python gemini_helper.py --task batch-summarize --input "path/to/folder" --pattern "*.txt"

Environment: Set GEMINI_API_KEY or store in gemini_config.json
"""

import argparse
import json
import os
import sys
import time
import glob as globmod
from pathlib import Path

# Usage logging — add parent dirs so usage_logger.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # ~/.google_workspace_mcp
from usage_logger import log_usage

# Fix Windows Unicode output crash (arrows, superscripts, etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Config file location
CONFIG_PATH = Path(__file__).parent / "gemini_config.json"


def get_api_key():
    """Get API key from env var or config file."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        key = config.get("api_key", "")
        if key and key != "PASTE_YOUR_KEY_HERE":
            return key

    print("ERROR: No API key found.")
    print("Set GEMINI_API_KEY environment variable or update gemini_config.json")
    print(f"Config file: {CONFIG_PATH}")
    sys.exit(1)


def get_default_model():
    """Get default model from config."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config.get("default_model", "gemini-2.5-flash")
    return "gemini-2.5-flash"


def get_client():
    """Initialize Gemini client."""
    from google import genai
    return genai.Client(api_key=get_api_key())


def read_input(input_arg):
    """Read input from file path or treat as literal text."""
    path = Path(input_arg)
    if path.exists() and path.is_file():
        # Handle images
        if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']:
            return {"type": "image", "path": str(path)}
        # Handle PDFs
        if path.suffix.lower() == '.pdf':
            return {"type": "pdf", "path": str(path)}
        # Handle DOCX (binary document — route through multimodal upload)
        if path.suffix.lower() == '.docx':
            return {"type": "docx", "path": str(path)}
        # Handle audio files
        if path.suffix.lower() in ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma']:
            return {"type": "audio", "path": str(path)}
        # Handle text files
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return {"type": "text", "content": f.read(), "source": str(path)}
    return {"type": "text", "content": input_arg, "source": "literal"}


def retry_on_rate_limit(func, *args, max_retries=3, **kwargs):
    """Retry API calls with exponential backoff on 429 rate limit errors."""
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if '429' in str(e) and attempt < max_retries:
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"Rate limited. Retrying in {wait}s (attempt {attempt + 1}/{max_retries})...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise


# Global flag — set by --quiet CLI arg
_quiet = False


def generate_and_log(client, model, contents, task_name, **gen_kwargs):
    """Wrapper: call generate_content, extract usage, log it, return response."""
    response = retry_on_rate_limit(
        client.models.generate_content, model=model, contents=contents, **gen_kwargs
    )

    # Extract usage metadata (available on most Gemini responses)
    input_tokens = 0
    output_tokens = 0
    try:
        usage = response.usage_metadata
        if usage:
            input_tokens = getattr(usage, 'prompt_token_count', 0) or 0
            output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
    except Exception:
        pass

    log_usage("gemini", model, task_name,
              input_tokens=input_tokens, output_tokens=output_tokens)

    if not _quiet and (input_tokens or output_tokens):
        print(f"[usage] gemini/{model} {task_name}: {input_tokens} in / {output_tokens} out",
              file=sys.stderr)

    return response


def task_ask(client, model, prompt, **kwargs):
    """Simple question/answer."""
    response = generate_and_log(client, model, prompt, "ask")
    return response.text


def task_summarize(client, model, input_data, **kwargs):
    """Summarize text or document content."""
    if input_data["type"] in ["docx", "pdf", "image"]:
        # Route binary files through OCR first, then summarize
        text = task_ocr(client, model, input_data)
        input_data = {"type": "text", "content": text}
    if input_data["type"] != "text":
        return "ERROR: Summarize only works with text input"

    prompt = f"""Summarize the following text concisely. Focus on key facts, decisions, and actionable items.

TEXT:
{input_data['content']}

SUMMARY:"""

    response = generate_and_log(client, model, prompt, "summarize")
    return response.text


def task_classify(client, model, input_data, categories="", **kwargs):
    """Classify text into categories."""
    if not categories:
        return "ERROR: --categories required for classify task"

    text = input_data["content"] if input_data["type"] == "text" else str(input_data)

    prompt = f"""Classify the following text into exactly ONE of these categories: {categories}

Respond with ONLY the category name, nothing else.

TEXT:
{text}

CATEGORY:"""

    response = generate_and_log(client, model, prompt, "classify")
    return response.text.strip()


def task_extract(client, model, input_data, prompt="", **kwargs):
    """Extract specific information from text."""
    if not prompt:
        return "ERROR: --prompt required for extract task"

    text = input_data["content"] if input_data["type"] == "text" else str(input_data)

    full_prompt = f"""{prompt}

SOURCE TEXT:
{text}

EXTRACTED:"""

    response = generate_and_log(client, model, full_prompt, "extract")
    return response.text


def task_ocr(client, model, input_data, **kwargs):
    """OCR an image, PDF, or DOCX using Gemini's multimodal capability."""
    if input_data["type"] not in ["image", "pdf", "docx"]:
        return "ERROR: OCR requires an image, PDF, or DOCX file"

    from google.genai import types

    file_path = input_data["path"]

    # Upload the file
    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    # Determine mime type
    ext = Path(file_path).suffix.lower()
    mime_map = {
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
        '.tiff': 'image/tiff', '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    mime_type = mime_map.get(ext, 'application/octet-stream')

    prompt = "Extract ALL text from this document. Preserve formatting, tables, and structure as much as possible. If there are handwritten elements, transcribe them too."

    response = generate_and_log(client, model, [
        prompt,
        types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    ], "ocr")
    return response.text


def task_batch_summarize(client, model, input_arg, pattern="*.txt", **kwargs):
    """Summarize all matching files in a directory."""
    path = Path(input_arg)
    if not path.is_dir():
        return f"ERROR: {input_arg} is not a directory"

    files = sorted(globmod.glob(str(path / pattern)))
    if not files:
        return f"No files matching {pattern} in {path}"

    results = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if len(content.strip()) < 10:
                results.append(f"### {Path(filepath).name}\n*Empty or too short*\n")
                continue

            # Truncate very large files
            if len(content) > 100000:
                content = content[:100000] + "\n[...truncated...]"

            summary = task_summarize(client, model, {"type": "text", "content": content})
            results.append(f"### {Path(filepath).name}\n{summary}\n")
        except Exception as e:
            results.append(f"### {Path(filepath).name}\nERROR: {e}\n")

    return "\n".join(results)


def task_json_extract(client, model, input_data, prompt="", **kwargs):
    """Extract structured JSON from text."""
    text = input_data["content"] if input_data["type"] == "text" else str(input_data)

    if not prompt:
        prompt = "Extract all structured data from this text as JSON"

    full_prompt = f"""{prompt}

Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object.

SOURCE TEXT:
{text}"""

    response = generate_and_log(client, model, full_prompt, "json-extract")
    # Try to clean response
    result = response.text.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1])
    return result


TASKS = {
    "ask": task_ask,
    "summarize": task_summarize,
    "classify": task_classify,
    "extract": task_extract,
    "ocr": task_ocr,
    "batch-summarize": task_batch_summarize,
    "json-extract": task_json_extract,
}


def main():
    parser = argparse.ArgumentParser(description="Gemini API Helper for PRIME Ecosystem")
    parser.add_argument("--task", required=True, choices=list(TASKS.keys()),
                        help="Task to perform")
    parser.add_argument("--input", help="Input text or file path")
    parser.add_argument("--prompt", help="Custom prompt (for ask/extract tasks)")
    parser.add_argument("--model", help="Model override (default from config)")
    parser.add_argument("--categories", help="Comma-separated categories (for classify)")
    parser.add_argument("--pattern", default="*.txt", help="File pattern (for batch tasks)")
    parser.add_argument("--output", help="Output file path (optional, otherwise stdout)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress usage stats on stderr (still logs to JSONL)")

    args = parser.parse_args()

    global _quiet
    _quiet = args.quiet

    model = args.model or get_default_model()
    client = get_client()

    # Read input if provided
    input_data = None
    if args.input:
        input_data = read_input(args.input)

    # For 'ask' task, use prompt as the main input
    if args.task == "ask":
        if not args.prompt:
            print("ERROR: --prompt required for ask task")
            sys.exit(1)
        result = task_ask(client, model, args.prompt)
    elif args.task == "batch-summarize":
        result = task_batch_summarize(client, model, args.input, pattern=args.pattern)
    else:
        if not input_data:
            print("ERROR: --input required for this task")
            sys.exit(1)
        result = TASKS[args.task](client, model, input_data,
                                   prompt=args.prompt or "",
                                   categories=args.categories or "")

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Output written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
