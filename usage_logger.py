#!/usr/bin/env python3
"""
Usage Logger — Shared JSONL logger for PRIME API usage tracking.

All helper scripts (gemini_helper, groq_helper, chroma_helper) import this
module to log every API call to a local JSONL file. The usage_sync.py script
then pushes these logs to the PRIME Data Catalog Google Sheet for dashboarding.

Usage:
    from usage_logger import log_usage
    log_usage("gemini", "gemini-2.5-flash", "summarize",
              input_tokens=1200, output_tokens=350)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Log directory — same as all other PRIME tools
LOG_DIR = Path(os.path.expanduser("~")) / ".google_workspace_mcp"

# Price table: model_id -> (input_cost_per_1M_tokens, output_cost_per_1M_tokens)
# Updated from gemini_config.json + provider docs
PRICE_TABLE = {
    # Gemini models
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-3-pro-preview": (2.00, 12.00),
    # Claude models (approximate)
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    # OpenAI models
    "gpt-5.2": (1.75, 14.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "dall-e-3": (0.0, 0.0),  # priced per image, not per token
    # Groq — free tier
    "llama-3.3-70b-versatile": (0.0, 0.0),
    "llama-3.1-8b-instant": (0.0, 0.0),
    "llama-3-70b-8192": (0.0, 0.0),
    "mixtral-8x7b-32768": (0.0, 0.0),
    "gemma2-9b-it": (0.0, 0.0),
    # Ollama — local, free
    "llama3.1:8b": (0.0, 0.0),
    "llama3.1:70b": (0.0, 0.0),
    "llava:7b": (0.0, 0.0),
    # Chroma — local, free
    "local": (0.0, 0.0),
}


def _get_log_path() -> Path:
    """Get the log file path for the current month."""
    month_suffix = datetime.now(timezone.utc).strftime("%Y-%m")
    return LOG_DIR / f"usage_log_{month_suffix}.jsonl"


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD from the price table."""
    prices = PRICE_TABLE.get(model)
    if not prices:
        return 0.0
    input_cost, output_cost = prices
    return (input_tokens * input_cost / 1_000_000) + (output_tokens * output_cost / 1_000_000)


def log_usage(
    provider: str,
    model: str,
    task: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_estimate: float | None = None,
    metadata: dict = None,
    source: str = "cli",
) -> None:
    """
    Append one usage record to the monthly JSONL log.

    Args:
        provider: API provider (gemini, groq, claude, chroma)
        model: Model ID string
        task: Task name (ask, summarize, ocr, search, etc.)
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        cost_estimate: Explicit cost override; auto-calculated if None
        metadata: Optional dict of extra fields (duration_ms, filename, etc.)
        source: Where the call originated (cli, prime-mobile-chat, etc.)
    """
    if cost_estimate is None:
        cost_estimate = estimate_cost(model, input_tokens, output_tokens)

    session = os.environ.get("PRIME_SESSION", "unknown")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "task": task,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_estimate": round(cost_estimate, 6),
        "session": session,
        "source": source,
    }
    if metadata:
        record["metadata"] = metadata

    log_path = _get_log_path()
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        # Never crash the caller — log failures are non-fatal
        print(f"[usage_logger] WARNING: Failed to write log: {e}", file=sys.stderr)


def read_log(month: str = None) -> list[dict]:
    """
    Read all records from a monthly log file.

    Args:
        month: YYYY-MM string; defaults to current month.

    Returns:
        List of record dicts.
    """
    if month is None:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    log_path = LOG_DIR / f"usage_log_{month}.jsonl"
    if not log_path.exists():
        return []

    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


if __name__ == "__main__":
    # Quick test: log a dummy entry and print it
    log_usage("test", "test-model", "self-test", input_tokens=100, output_tokens=50)
    records = read_log()
    print(f"Log file: {_get_log_path()}")
    print(f"Total records this month: {len(records)}")
    if records:
        print(f"Latest: {json.dumps(records[-1], indent=2)}")
