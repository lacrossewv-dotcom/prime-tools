#!/usr/bin/env python3
"""
Groq Helper CLI — Ultra-fast LLM inference via Groq Cloud (free tier).

Usage:
    py -3.13 groq_helper.py --task ask --prompt "What is the Suez Crisis?"
    py -3.13 groq_helper.py --task ask --prompt "Explain friction in war" --model llama-3.3-70b-versatile
    py -3.13 groq_helper.py --task summarize --input "path/to/file.txt"
    py -3.13 groq_helper.py --task summarize --input "path/to/file.txt" --prompt "Focus on key arguments"
    py -3.13 groq_helper.py --task extract --input "path/to/file.txt" --prompt "Extract all dates and events"
    py -3.13 groq_helper.py --task models
    py -3.13 groq_helper.py --task test

Config: ~/.google_workspace_mcp/gemini_config.json (groq_api_key field)
Requires: py -3.13 -m pip install groq
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Usage logging
sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_logger import log_usage

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".google_workspace_mcp", "gemini_config.json")

# Groq model catalog (free tier)
MODELS = {
    "llama-3.3-70b-versatile": {
        "description": "Llama 3.3 70B — best quality on free tier, versatile",
        "context": 131072,
        "speed": "~275 tok/s",
    },
    "llama-3.1-8b-instant": {
        "description": "Llama 3.1 8B — fastest, good for simple tasks",
        "context": 131072,
        "speed": "~750 tok/s",
    },
    "llama-3-70b-8192": {
        "description": "Llama 3 70B — strong reasoning, 8K context",
        "context": 8192,
        "speed": "~330 tok/s",
    },
    "mixtral-8x7b-32768": {
        "description": "Mixtral 8x7B — good balance of speed and quality",
        "context": 32768,
        "speed": "~480 tok/s",
    },
    "gemma2-9b-it": {
        "description": "Gemma 2 9B — Google's open model, good for short tasks",
        "context": 8192,
        "speed": "~500 tok/s",
    },
}

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_api_key() -> str:
    """Load Groq API key from config."""
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    key = config.get("groq_api_key")
    if not key:
        print("ERROR: 'groq_api_key' not found in config file.")
        print(f"Add it to: {CONFIG_PATH}")
        sys.exit(1)
    return key


def get_client():
    """Get Groq client."""
    from groq import Groq
    return Groq(api_key=get_api_key())


def read_file(filepath: str) -> str:
    """Read a file with encoding fallback."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    print(f"ERROR: Could not decode {filepath}")
    sys.exit(1)


def _log_groq(model, task_name, response):
    """Extract usage from Groq response and log it."""
    input_tokens = 0
    output_tokens = 0
    try:
        usage = response.usage
        if usage:
            input_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            output_tokens = getattr(usage, 'completion_tokens', 0) or 0
    except Exception:
        pass
    log_usage("groq", model, task_name,
              input_tokens=input_tokens, output_tokens=output_tokens,
              cost_estimate=0.0)
    return input_tokens, output_tokens


def task_ask(args):
    """Ask a question — simple chat completion."""
    client = get_client()
    model = args.model or DEFAULT_MODEL

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise and accurate."},
            {"role": "user", "content": args.prompt},
        ],
        temperature=0.3,
        max_tokens=args.max_tokens,
    )

    result = response.choices[0].message.content
    print(result)

    in_tok, out_tok = _log_groq(model, "ask", response)
    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Model: {model}", file=sys.stderr)
        print(f"Input tokens: {in_tok}", file=sys.stderr)
        print(f"Output tokens: {out_tok}", file=sys.stderr)
        print(f"Total tokens: {in_tok + out_tok}", file=sys.stderr)


def task_summarize(args):
    """Summarize a file."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    content = read_file(args.input)
    filename = os.path.basename(args.input)

    extra = ""
    if args.prompt:
        extra = f"\n\nAdditional instruction: {args.prompt}"

    prompt = f"""Summarize the following document concisely. Include the key points, main arguments, and important details.{extra}

Document: {filename}

---
{content[:30000]}
---

Summary:"""

    client = get_client()
    model = args.model or DEFAULT_MODEL

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise document summarizer. Focus on the most important content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=args.max_tokens,
    )

    print(f"Summary of '{filename}':\n")
    print(response.choices[0].message.content)

    in_tok, out_tok = _log_groq(model, "summarize", response)
    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Model: {model}", file=sys.stderr)
        print(f"Tokens: {in_tok} in / {out_tok} out", file=sys.stderr)


def task_extract(args):
    """Extract specific data from a file."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)
    if not args.prompt:
        print("ERROR: --prompt is required for extract task (what to extract)")
        sys.exit(1)

    content = read_file(args.input)
    filename = os.path.basename(args.input)

    prompt = f"""From the following document, extract: {args.prompt}

Document: {filename}

---
{content[:30000]}
---

Extracted data:"""

    client = get_client()
    model = args.model or DEFAULT_MODEL

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise data extractor. Output structured, clean results."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=args.max_tokens,
    )

    print(response.choices[0].message.content)

    in_tok, out_tok = _log_groq(model, "extract", response)
    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Model: {model}", file=sys.stderr)
        print(f"Tokens: {in_tok} in / {out_tok} out", file=sys.stderr)


def task_models(args):
    """List available models."""
    print("Groq Cloud Models (free tier):\n")
    for model_id, info in MODELS.items():
        default = " (DEFAULT)" if model_id == DEFAULT_MODEL else ""
        print(f"  {model_id}{default}")
        print(f"    {info['description']}")
        print(f"    Context: {info['context']:,} tokens | Speed: {info['speed']}")
        print()

    print("Free tier limits: 14,400 tokens/min, 30 requests/min")
    print("Use --model <id> to select a specific model")


def task_test(args):
    """Test connectivity."""
    print("Testing Groq API connection...")
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Groq is connected' and nothing else."}],
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        _log_groq("llama-3.1-8b-instant", "test", response)
        print(f"Response: {result}")
        print(f"Model: llama-3.1-8b-instant")
        print(f"Tokens: {response.usage.total_tokens}")
        print("STATUS: OPERATIONAL")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Groq Cloud Helper for PRIME ecosystem")
    parser.add_argument("--task", required=True,
                        choices=["ask", "summarize", "extract", "models", "test"],
                        help="Task to perform")
    parser.add_argument("--prompt", "-p", help="Prompt or question")
    parser.add_argument("--input", "-i", help="Input file path")
    parser.add_argument("--model", "-m", help=f"Model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Max output tokens (default: 2048)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show token usage stats")

    args = parser.parse_args()

    if args.task == "ask" and not args.prompt:
        parser.error("--prompt is required for ask task")

    tasks = {
        "ask": task_ask,
        "summarize": task_summarize,
        "extract": task_extract,
        "models": task_models,
        "test": task_test,
    }
    tasks[args.task](args)


if __name__ == "__main__":
    main()
