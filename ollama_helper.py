#!/usr/bin/env python3
"""
Ollama Helper CLI — Local Llama inference via Ollama (free, offline, no rate limits).

Usage:
    py -3.13 ollama_helper.py --task ask --prompt "What is the OODA loop?"
    py -3.13 ollama_helper.py --task summarize --input "path/to/file.txt"
    py -3.13 ollama_helper.py --task extract --input "path/to/file.txt" --prompt "Extract all dates"
    py -3.13 ollama_helper.py --task classify --input "text" --categories "cat1,cat2,cat3"
    py -3.13 ollama_helper.py --task json-extract --input "file.txt" --prompt "Extract as JSON"
    py -3.13 ollama_helper.py --task vision --input "image.png" --prompt "Describe this"
    py -3.13 ollama_helper.py --task models
    py -3.13 ollama_helper.py --task test

Requires: Ollama installed (https://ollama.com) with at least one model pulled.
Ollama binary: C:/Users/lacro/AppData/Local/Programs/Ollama/ollama.exe
API: http://localhost:11434 (Ollama runs as a background service)
Cost: FREE — runs entirely on local hardware.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Windows Unicode fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Usage logging
sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_logger import log_usage

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_BIN = "C:/Users/lacro/AppData/Local/Programs/Ollama/ollama.exe"
DEFAULT_MODEL = "llama3.1:8b"


# --- API helpers ---

def ollama_api(endpoint: str, payload: dict, timeout: int = 120) -> dict:
    """Make a request to the Ollama REST API."""
    url = f"{OLLAMA_BASE}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE}", file=sys.stderr)
        print(f"Make sure Ollama is running. Start it with: \"{OLLAMA_BIN}\" serve", file=sys.stderr)
        print(f"Detail: {e}", file=sys.stderr)
        sys.exit(1)


def ollama_generate(model: str, prompt: str, system: str = None, images: list = None,
                    format_json: bool = False, timeout: int = 120) -> dict:
    """Generate a completion via Ollama API (non-streaming)."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system
    if images:
        payload["images"] = images
    if format_json:
        payload["format"] = "json"

    start = time.time()
    result = ollama_api("/api/generate", payload, timeout=timeout)
    elapsed_ms = int((time.time() - start) * 1000)

    # Log usage (free, but track for dashboard)
    eval_count = result.get("eval_count", 0)
    prompt_eval_count = result.get("prompt_eval_count", 0)
    log_usage("ollama", model, "generate",
              input_tokens=prompt_eval_count, output_tokens=eval_count,
              cost_estimate=0.0,
              metadata={"duration_ms": elapsed_ms, "local": True})

    return result


def ollama_chat(model: str, messages: list, format_json: bool = False, timeout: int = 120) -> dict:
    """Chat completion via Ollama API (non-streaming)."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if format_json:
        payload["format"] = "json"

    start = time.time()
    result = ollama_api("/api/chat", payload, timeout=timeout)
    elapsed_ms = int((time.time() - start) * 1000)

    # Log usage
    eval_count = result.get("eval_count", 0)
    prompt_eval_count = result.get("prompt_eval_count", 0)
    log_usage("ollama", model, "chat",
              input_tokens=prompt_eval_count, output_tokens=eval_count,
              cost_estimate=0.0,
              metadata={"duration_ms": elapsed_ms, "local": True})

    return result


# --- Utility ---

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


def print_stats(result: dict):
    """Print performance stats to stderr."""
    total_ns = result.get("total_duration", 0)
    eval_count = result.get("eval_count", 0)
    eval_ns = result.get("eval_duration", 0)
    prompt_count = result.get("prompt_eval_count", 0)

    total_ms = total_ns / 1_000_000
    tok_per_sec = (eval_count / (eval_ns / 1_000_000_000)) if eval_ns > 0 else 0

    print(f"\n--- Stats ---", file=sys.stderr)
    print(f"Model: {result.get('model', 'unknown')}", file=sys.stderr)
    print(f"Prompt tokens: {prompt_count}", file=sys.stderr)
    print(f"Output tokens: {eval_count}", file=sys.stderr)
    print(f"Speed: {tok_per_sec:.1f} tok/s", file=sys.stderr)
    print(f"Total time: {total_ms:.0f}ms", file=sys.stderr)
    print(f"Cost: $0.00 (local)", file=sys.stderr)


# --- Tasks ---

def task_ask(args):
    """Ask a question — simple completion."""
    model = args.model or DEFAULT_MODEL
    result = ollama_chat(model, [
        {"role": "system", "content": "You are a helpful assistant. Be concise and accurate."},
        {"role": "user", "content": args.prompt},
    ])

    print(result["message"]["content"])
    if args.verbose:
        print_stats(result)


def task_summarize(args):
    """Summarize a file."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    content = read_file(args.input)
    filename = os.path.basename(args.input)
    model = args.model or DEFAULT_MODEL

    extra = ""
    if args.prompt:
        extra = f"\n\nAdditional instruction: {args.prompt}"

    prompt = f"""Summarize the following document concisely. Include the key points, main arguments, and important details.{extra}

Document: {filename}

---
{content[:15000]}
---

Summary:"""

    result = ollama_chat(model, [
        {"role": "system", "content": "You are a precise document summarizer. Focus on the most important content."},
        {"role": "user", "content": prompt},
    ])

    print(f"Summary of '{filename}':\n")
    print(result["message"]["content"])
    if args.verbose:
        print_stats(result)


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
    model = args.model or DEFAULT_MODEL

    prompt = f"""From the following document, extract: {args.prompt}

Document: {filename}

---
{content[:15000]}
---

Extracted data:"""

    result = ollama_chat(model, [
        {"role": "system", "content": "You are a precise data extractor. Output structured, clean results."},
        {"role": "user", "content": prompt},
    ])

    print(result["message"]["content"])
    if args.verbose:
        print_stats(result)


def task_classify(args):
    """Classify text into categories."""
    if not args.input:
        print("ERROR: --input is required (text or file path)")
        sys.exit(1)
    if not args.categories:
        print("ERROR: --categories is required (comma-separated list)")
        sys.exit(1)

    # Input can be text or a file
    if os.path.isfile(args.input):
        text = read_file(args.input)[:10000]
    else:
        text = args.input

    model = args.model or DEFAULT_MODEL
    cats = args.categories

    prompt = f"""Classify the following text into exactly one of these categories: {cats}

Text:
{text}

Respond with ONLY the category name, nothing else."""

    result = ollama_chat(model, [
        {"role": "system", "content": "You are a text classifier. Respond with only the category name."},
        {"role": "user", "content": prompt},
    ])

    print(result["message"]["content"].strip())
    if args.verbose:
        print_stats(result)


def task_json_extract(args):
    """Extract structured JSON from a file."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    content = read_file(args.input)
    filename = os.path.basename(args.input)
    model = args.model or DEFAULT_MODEL
    instruction = args.prompt or "Extract all structured data as JSON"

    prompt = f"""From the following document, {instruction}.
Return ONLY valid JSON.

Document: {filename}

---
{content[:15000]}
---"""

    result = ollama_chat(model, [
        {"role": "system", "content": "You are a structured data extractor. Output valid JSON only. No markdown, no explanation."},
        {"role": "user", "content": prompt},
    ], format_json=True)

    raw = result["message"]["content"]
    try:
        parsed = json.loads(raw)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(raw)
        print("\nWARNING: Output was not valid JSON", file=sys.stderr)

    if args.verbose:
        print_stats(result)


def task_vision(args):
    """Analyze an image using a vision-capable model."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: Image file not found: {args.input}")
        sys.exit(1)

    # Vision requires a multimodal model — check if current model supports it
    model = args.model or "llava:7b"
    prompt_text = args.prompt or "Describe this image in detail."

    # Read and encode image
    with open(args.input, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    result = ollama_generate(model, prompt_text, images=[image_b64])
    print(result.get("response", ""))
    if args.verbose:
        print_stats(result)


def task_models(args):
    """List installed Ollama models."""
    try:
        url = f"{OLLAMA_BASE}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE}")
        print(f"Make sure Ollama is running. Detail: {e}")
        sys.exit(1)

    models = data.get("models", [])
    if not models:
        print("No models installed. Pull one with:")
        print(f'  "{OLLAMA_BIN}" pull llama3.1:8b')
        return

    print("Installed Ollama Models:\n")
    for m in models:
        name = m.get("name", "unknown")
        size_gb = m.get("size", 0) / (1024**3)
        default = " (DEFAULT)" if name == DEFAULT_MODEL else ""
        param_size = m.get("details", {}).get("parameter_size", "")
        quant = m.get("details", {}).get("quantization_level", "")
        print(f"  {name}{default}")
        if param_size:
            print(f"    Parameters: {param_size}  Quantization: {quant}")
        print(f"    Size: {size_gb:.1f} GB")
        print(f"    Cost: $0.00 (local)")
        print()

    print("Pull more models with:")
    print(f'  "{OLLAMA_BIN}" pull <model>')
    print(f"  Popular: llama3.1:8b, llama3.1:70b, mistral, codellama, llava:7b (vision)")


def task_test(args):
    """Test Ollama connectivity and model inference."""
    print("Testing Ollama connection...")

    # Check API
    try:
        url = f"{OLLAMA_BASE}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m["name"] for m in data.get("models", [])]
        print(f"Ollama API: OK ({len(models)} models)")
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE}")
        print(f"Start Ollama with: \"{OLLAMA_BIN}\" serve")
        sys.exit(1)

    if not models:
        print("No models installed. Pull one first.")
        sys.exit(1)

    # Test inference
    model = args.model or DEFAULT_MODEL
    if model not in models:
        model = models[0]

    print(f"Testing inference with {model}...")
    start = time.time()
    result = ollama_chat(model, [
        {"role": "user", "content": "Say 'Ollama is connected' and nothing else."},
    ])
    elapsed = time.time() - start

    response_text = result["message"]["content"].strip()
    eval_count = result.get("eval_count", 0)
    eval_ns = result.get("eval_duration", 0)
    tok_per_sec = (eval_count / (eval_ns / 1_000_000_000)) if eval_ns > 0 else 0

    print(f"Response: {response_text}")
    print(f"Model: {model}")
    print(f"Speed: {tok_per_sec:.1f} tok/s")
    print(f"Time: {elapsed:.1f}s")
    print(f"Cost: $0.00 (local)")
    print("STATUS: OPERATIONAL")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Ollama Helper CLI — Local Llama inference for PRIME ecosystem (FREE)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  py -3.13 ollama_helper.py --task ask --prompt "Explain OODA loop"
  py -3.13 ollama_helper.py --task summarize --input document.txt
  py -3.13 ollama_helper.py --task classify --input "some text" --categories "positive,negative,neutral"
  py -3.13 ollama_helper.py --task json-extract --input data.txt --prompt "Extract names and dates"
  py -3.13 ollama_helper.py --task models
  py -3.13 ollama_helper.py --task test
""",
    )
    parser.add_argument("--task", required=True,
                        choices=["ask", "summarize", "extract", "classify",
                                 "json-extract", "vision", "models", "test"],
                        help="Task to perform")
    parser.add_argument("--prompt", "-p", help="Prompt or question")
    parser.add_argument("--input", "-i", help="Input file path or text")
    parser.add_argument("--model", "-m", help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--categories", "-c", help="Comma-separated categories (for classify task)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show performance stats")

    args = parser.parse_args()

    if args.task == "ask" and not args.prompt:
        parser.error("--prompt is required for ask task")

    tasks = {
        "ask": task_ask,
        "summarize": task_summarize,
        "extract": task_extract,
        "classify": task_classify,
        "json-extract": task_json_extract,
        "vision": task_vision,
        "models": task_models,
        "test": task_test,
    }
    tasks[args.task](args)


if __name__ == "__main__":
    main()
