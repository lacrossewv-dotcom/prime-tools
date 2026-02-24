#!/usr/bin/env python3
"""
OpenAI Helper CLI — GPT-5.2 / GPT-4.1 access for PRIME ecosystem.

Usage:
    py -3.13 openai_helper.py --task ask --prompt "What is quantum computing?"
    py -3.13 openai_helper.py --task summarize --input "path/to/file.txt"
    py -3.13 openai_helper.py --task extract --input "path/to/file.txt" --prompt "Extract all dates"
    py -3.13 openai_helper.py --task search --prompt "latest AI regulations 2026"
    py -3.13 openai_helper.py --task vision --input "screenshot.png" --prompt "Describe this UI"
    py -3.13 openai_helper.py --task json-extract --input "file.txt" --prompt "Extract as structured JSON"
    py -3.13 openai_helper.py --task image --prompt "A futuristic command center" --output "output.png"
    py -3.13 openai_helper.py --task models
    py -3.13 openai_helper.py --task budget
    py -3.13 openai_helper.py --task test

Config: ~/.google_workspace_mcp/gemini_config.json (openai_api_key field)
Budget: gemini_config.json -> openai_monthly_budget (default $30)
Requires: py -3.13 -m pip install openai
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows Unicode fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Usage logging
sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_logger import log_usage, read_log, estimate_cost

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".google_workspace_mcp", "gemini_config.json")

# --- Model catalog ---

MODELS = {
    "gpt-5.2": {
        "description": "GPT-5.2 -- flagship reasoning, complex tasks",
        "input_cost_per_1m": 1.75,
        "output_cost_per_1m": 14.00,
    },
    "gpt-4.1-mini": {
        "description": "GPT-4.1 Mini -- fast and cheap, good for most tasks (DEFAULT)",
        "input_cost_per_1m": 0.40,
        "output_cost_per_1m": 1.60,
    },
    "gpt-4.1-nano": {
        "description": "GPT-4.1 Nano -- cheapest, bulk classification and simple tasks",
        "input_cost_per_1m": 0.10,
        "output_cost_per_1m": 0.40,
    },
    "dall-e-3": {
        "description": "DALL-E 3 -- image generation (~$0.04-0.08 per image)",
        "input_cost_per_1m": 0.0,
        "output_cost_per_1m": 0.0,
    },
}

DEFAULT_MODEL = "gpt-4.1-mini"
IMAGE_COST_ESTIMATE = 0.04  # conservative per-image estimate for 1024x1024


# --- Config & auth ---

def load_config() -> dict:
    """Load full config from gemini_config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def get_api_key() -> str:
    """Load OpenAI API key from config or env."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    config = load_config()
    key = config.get("openai_api_key", "")
    if not key:
        print("ERROR: 'openai_api_key' not found or empty in config file.")
        print(f"Add your key to: {CONFIG_PATH}")
        print("Get one at: https://platform.openai.com/api-keys")
        sys.exit(1)
    return key


def get_budget() -> float:
    """Get monthly budget cap from config."""
    config = load_config()
    return float(config.get("openai_monthly_budget", 30.00))


def get_client():
    """Get OpenAI client."""
    from openai import OpenAI
    return OpenAI(api_key=get_api_key())


# --- Budget guardrails ---

def get_month_spend() -> float:
    """Calculate total OpenAI spend for the current month from JSONL logs."""
    records = read_log()
    total = 0.0
    for r in records:
        if r.get("provider") == "openai":
            total += r.get("cost_estimate", 0.0)
    return total


def check_budget(estimated_cost: float = 0.0, force: bool = False) -> bool:
    """
    Check budget guardrails. Returns True if OK to proceed.

    Blocks if:
    - Month spend >= budget cap
    - Single call > $1.00 and --yes not passed
    """
    budget = get_budget()
    spent = get_month_spend()

    if spent >= budget:
        print(f"BUDGET EXCEEDED: ${spent:.2f} / ${budget:.2f} this month.", file=sys.stderr)
        print(f"Increase 'openai_monthly_budget' in {CONFIG_PATH} to continue.", file=sys.stderr)
        return False

    if (spent + estimated_cost) > budget:
        print(f"BUDGET WOULD BE EXCEEDED: ${spent:.2f} + ~${estimated_cost:.2f} > ${budget:.2f} cap.", file=sys.stderr)
        print(f"Use --model with a cheaper model or increase budget in config.", file=sys.stderr)
        return False

    if estimated_cost > 1.00 and not force:
        print(f"WARNING: Estimated cost ~${estimated_cost:.2f} exceeds $1.00 threshold.", file=sys.stderr)
        print(f"Re-run with --yes to confirm, or use a cheaper --model.", file=sys.stderr)
        return False

    return True


def print_cost(model: str, input_tokens: int, output_tokens: int, cost: float):
    """Print cost summary line to stderr."""
    budget = get_budget()
    spent = get_month_spend()
    pct = (spent / budget * 100) if budget > 0 else 0
    print(f"[OpenAI] Cost: ${cost:.4f} | Month: ${spent:.2f} / ${budget:.2f} ({pct:.1f}%)", file=sys.stderr)


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


def _log_openai(model: str, task_name: str, response, cost_override: float = None) -> tuple:
    """Extract usage from OpenAI response and log it."""
    input_tokens = 0
    output_tokens = 0
    try:
        usage = response.usage
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0
    except Exception:
        pass

    if cost_override is not None:
        cost = cost_override
    else:
        cost = estimate_cost(model, input_tokens, output_tokens)

    log_usage("openai", model, task_name,
              input_tokens=input_tokens, output_tokens=output_tokens,
              cost_estimate=cost)

    print_cost(model, input_tokens, output_tokens, cost)
    return input_tokens, output_tokens, cost


# --- Tasks ---

def task_ask(args):
    """Ask a question -- simple chat completion."""
    model = args.model or DEFAULT_MODEL
    if not check_budget(force=args.yes):
        sys.exit(1)

    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise and accurate."},
            {"role": "user", "content": args.prompt},
        ],
        temperature=0.3,
        max_tokens=args.max_tokens,
    )

    print(response.choices[0].message.content)
    in_tok, out_tok, cost = _log_openai(model, "ask", response)

    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Model: {model}", file=sys.stderr)
        print(f"Tokens: {in_tok} in / {out_tok} out", file=sys.stderr)


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
{content[:60000]}
---

Summary:"""

    if not check_budget(force=args.yes):
        sys.exit(1)

    client = get_client()
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
    _log_openai(model, "summarize", response)


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
{content[:60000]}
---

Extracted data:"""

    if not check_budget(force=args.yes):
        sys.exit(1)

    client = get_client()
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
    _log_openai(model, "extract", response)


def task_search(args):
    """Web search with citations using OpenAI's web_search_preview tool."""
    if not args.prompt:
        print("ERROR: --prompt is required for search task")
        sys.exit(1)

    model = args.model or DEFAULT_MODEL
    if not check_budget(force=args.yes):
        sys.exit(1)

    client = get_client()
    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search_preview"}],
        input=args.prompt,
    )

    # Extract text output from response
    for item in response.output:
        if item.type == "message":
            for content_block in item.content:
                if content_block.type == "output_text":
                    print(content_block.text)
                    # Print citations if available
                    if hasattr(content_block, "annotations") and content_block.annotations:
                        print("\n--- Sources ---")
                        seen = set()
                        for ann in content_block.annotations:
                            if hasattr(ann, "url") and ann.url not in seen:
                                title = getattr(ann, "title", ann.url)
                                print(f"  - {title}: {ann.url}")
                                seen.add(ann.url)

    # Log usage
    input_tokens = getattr(response.usage, "input_tokens", 0) if response.usage else 0
    output_tokens = getattr(response.usage, "output_tokens", 0) if response.usage else 0
    cost = estimate_cost(model, input_tokens, output_tokens)
    log_usage("openai", model, "search",
              input_tokens=input_tokens, output_tokens=output_tokens,
              cost_estimate=cost)
    print_cost(model, input_tokens, output_tokens, cost)

    if args.verbose:
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Model: {model}", file=sys.stderr)
        print(f"Tokens: {input_tokens} in / {output_tokens} out", file=sys.stderr)


def task_vision(args):
    """Analyze an image using GPT vision."""
    if not args.input or not os.path.isfile(args.input):
        print(f"ERROR: Image file not found: {args.input}")
        sys.exit(1)

    model = args.model or DEFAULT_MODEL
    prompt_text = args.prompt or "Describe this image in detail."

    if not check_budget(force=args.yes):
        sys.exit(1)

    # Read and encode image
    with open(args.input, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Detect MIME type
    ext = Path(args.input).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}
    mime_type = mime_map.get(ext, "image/png")

    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}"
                }},
            ]},
        ],
        max_tokens=args.max_tokens,
    )

    print(response.choices[0].message.content)
    _log_openai(model, "vision", response)


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
Return ONLY valid JSON, no markdown fences, no explanation.

Document: {filename}

---
{content[:60000]}
---"""

    if not check_budget(force=args.yes):
        sys.exit(1)

    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a structured data extractor. Output valid JSON only. No markdown, no explanation."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=args.max_tokens,
        response_format={"type": "json_object"},
    )

    result = response.choices[0].message.content
    # Validate JSON
    try:
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(result)
        print("\nWARNING: Output was not valid JSON", file=sys.stderr)

    _log_openai(model, "json-extract", response)


def task_image(args):
    """Generate an image using DALL-E 3."""
    if not args.prompt:
        print("ERROR: --prompt is required for image task")
        sys.exit(1)

    if not check_budget(estimated_cost=IMAGE_COST_ESTIMATE, force=args.yes):
        sys.exit(1)

    output_path = args.output or "openai_image.png"
    size = args.size or "1024x1024"

    client = get_client()
    response = client.images.generate(
        model="dall-e-3",
        prompt=args.prompt,
        size=size,
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt

    # Download the image
    import urllib.request
    urllib.request.urlretrieve(image_url, output_path)

    print(f"Image saved to: {output_path}")
    print(f"Revised prompt: {revised_prompt}")

    # Log with fixed cost estimate (DALL-E doesn't use tokens)
    log_usage("openai", "dall-e-3", "image",
              input_tokens=0, output_tokens=0,
              cost_estimate=IMAGE_COST_ESTIMATE,
              metadata={"size": size, "output": output_path})
    print_cost("dall-e-3", 0, 0, IMAGE_COST_ESTIMATE)


def task_models(args):
    """List available models with pricing."""
    print("OpenAI Models:\n")
    for model_id, info in MODELS.items():
        default = " (DEFAULT)" if model_id == DEFAULT_MODEL else ""
        print(f"  {model_id}{default}")
        print(f"    {info['description']}")
        if info["input_cost_per_1m"] > 0:
            print(f"    Cost: ${info['input_cost_per_1m']:.2f} / ${info['output_cost_per_1m']:.2f} per 1M tokens (in/out)")
        elif model_id == "dall-e-3":
            print(f"    Cost: ~${IMAGE_COST_ESTIMATE:.2f} per image (1024x1024 standard)")
        print()

    budget = get_budget()
    spent = get_month_spend()
    print(f"Budget: ${spent:.2f} / ${budget:.2f} this month ({spent/budget*100:.1f}%)" if budget > 0 else "Budget: not set")
    print(f"\nUse --model <id> to select a specific model")
    print(f"Use --task budget for detailed spend breakdown")


def task_budget(args):
    """Show detailed budget and usage breakdown."""
    budget = get_budget()
    records = read_log()

    openai_records = [r for r in records if r.get("provider") == "openai"]
    total_cost = sum(r.get("cost_estimate", 0.0) for r in openai_records)
    total_input = sum(r.get("input_tokens", 0) for r in openai_records)
    total_output = sum(r.get("output_tokens", 0) for r in openai_records)
    total_calls = len(openai_records)

    month = datetime.now(timezone.utc).strftime("%B %Y")
    print(f"OpenAI Budget Report -- {month}\n")
    print(f"  Budget cap:     ${budget:.2f}")
    print(f"  Spent:          ${total_cost:.4f}")
    print(f"  Remaining:      ${budget - total_cost:.2f}")
    print(f"  Usage:          {total_cost/budget*100:.1f}%" if budget > 0 else "  Usage: N/A")
    print(f"\n  Total calls:    {total_calls}")
    print(f"  Input tokens:   {total_input:,}")
    print(f"  Output tokens:  {total_output:,}")

    if openai_records:
        # Breakdown by task
        by_task = {}
        for r in openai_records:
            t = r.get("task", "unknown")
            if t not in by_task:
                by_task[t] = {"calls": 0, "cost": 0.0}
            by_task[t]["calls"] += 1
            by_task[t]["cost"] += r.get("cost_estimate", 0.0)

        print(f"\n  Breakdown by task:")
        for t, info in sorted(by_task.items(), key=lambda x: -x[1]["cost"]):
            print(f"    {t:15s}  {info['calls']:3d} calls  ${info['cost']:.4f}")

        # Breakdown by model
        by_model = {}
        for r in openai_records:
            m = r.get("model", "unknown")
            if m not in by_model:
                by_model[m] = {"calls": 0, "cost": 0.0}
            by_model[m]["calls"] += 1
            by_model[m]["cost"] += r.get("cost_estimate", 0.0)

        print(f"\n  Breakdown by model:")
        for m, info in sorted(by_model.items(), key=lambda x: -x[1]["cost"]):
            print(f"    {m:20s}  {info['calls']:3d} calls  ${info['cost']:.4f}")


def task_test(args):
    """Test API connectivity with cheapest model."""
    print("Testing OpenAI API connection...")
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": "Say 'OpenAI is connected' and nothing else."}],
            max_tokens=20,
        )
        result = response.choices[0].message.content.strip()
        _log_openai("gpt-4.1-nano", "test", response)
        print(f"Response: {result}")
        print(f"Model: gpt-4.1-nano")
        usage = response.usage
        if usage:
            print(f"Tokens: {usage.total_tokens}")
        print("STATUS: OPERATIONAL")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="OpenAI Helper CLI for PRIME ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  py -3.13 openai_helper.py --task ask --prompt "Explain OODA loop"
  py -3.13 openai_helper.py --task ask --prompt "Complex analysis" --model gpt-5.2
  py -3.13 openai_helper.py --task search --prompt "AI policy 2026"
  py -3.13 openai_helper.py --task vision --input screenshot.png
  py -3.13 openai_helper.py --task budget
""",
    )
    parser.add_argument("--task", required=True,
                        choices=["ask", "summarize", "extract", "search", "vision",
                                 "json-extract", "image", "models", "budget", "test"],
                        help="Task to perform")
    parser.add_argument("--prompt", "-p", help="Prompt or question")
    parser.add_argument("--input", "-i", help="Input file path")
    parser.add_argument("--output", "-o", help="Output file path (for image task)")
    parser.add_argument("--model", "-m", help=f"Model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max output tokens (default: 4096)")
    parser.add_argument("--size", help="Image size for image task (default: 1024x1024)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show token usage stats")
    parser.add_argument("--yes", "-y", action="store_true", help="Confirm expensive operations (>$1.00)")

    args = parser.parse_args()

    # Validate required args per task
    if args.task == "ask" and not args.prompt:
        parser.error("--prompt is required for ask task")
    if args.task == "search" and not args.prompt:
        parser.error("--prompt is required for search task")
    if args.task == "image" and not args.prompt:
        parser.error("--prompt is required for image task")

    tasks = {
        "ask": task_ask,
        "summarize": task_summarize,
        "extract": task_extract,
        "search": task_search,
        "vision": task_vision,
        "json-extract": task_json_extract,
        "image": task_image,
        "models": task_models,
        "budget": task_budget,
        "test": task_test,
    }
    tasks[args.task](args)


if __name__ == "__main__":
    main()
