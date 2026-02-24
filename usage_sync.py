#!/usr/bin/env python3
"""
Usage Sync — Push local JSONL usage logs to the PRIME Data Catalog Google Sheet.

Reads usage_log_YYYY-MM.jsonl files, tracks the last-synced position via a
bookmark file, and appends new rows to _USAGE / _USAGE_DAILY tabs.

Usage:
    python usage_sync.py               # Sync new entries since last run
    python usage_sync.py --full        # Re-sync everything (ignores bookmark)
    python usage_sync.py --status      # Show sync status without syncing

Requires: google-auth, google-auth-oauthlib, google-api-python-client
Credentials: ~/.google_workspace_mcp/credentials/stephen@bender23.com.json
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Paths
BASE_DIR = Path(os.path.expanduser("~")) / ".google_workspace_mcp"
CRED_PATH = BASE_DIR / "credentials" / "stephen@bender23.com.json"
BOOKMARK_PATH = BASE_DIR / "usage_sync_bookmark.json"

# Google Sheet — PRIME Data Catalog
SPREADSHEET_ID = "1Vijb9kxxRUUaKJ9ZUD6CR6RyB0uFSG-t_ZxNC1F5rmc"
USAGE_TAB = "_USAGE"
DAILY_TAB = "_USAGE_DAILY"


def get_sheets_service():
    """Build authenticated Google Sheets API service."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if not CRED_PATH.exists():
        print(f"ERROR: Credentials not found: {CRED_PATH}")
        sys.exit(1)

    with open(CRED_PATH) as f:
        cred_data = json.load(f)

    creds = Credentials(
        token=cred_data.get("token"),
        refresh_token=cred_data.get("refresh_token"),
        token_uri=cred_data.get("token_uri"),
        client_id=cred_data.get("client_id"),
        client_secret=cred_data.get("client_secret"),
        scopes=cred_data.get("scopes"),
    )

    return build("sheets", "v4", credentials=creds)


def load_bookmark() -> dict:
    """Load sync bookmark (tracks last-synced position per log file)."""
    if BOOKMARK_PATH.exists():
        with open(BOOKMARK_PATH) as f:
            return json.load(f)
    return {}


def save_bookmark(bookmark: dict) -> None:
    """Save sync bookmark."""
    with open(BOOKMARK_PATH, "w") as f:
        json.dump(bookmark, f, indent=2)


def find_log_files() -> list[Path]:
    """Find all usage_log_*.jsonl files."""
    return sorted(BASE_DIR.glob("usage_log_*.jsonl"))


def read_new_entries(log_path: Path, offset: int) -> tuple[list[dict], int]:
    """Read entries from a log file starting at byte offset."""
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        f.seek(offset)
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        new_offset = f.tell()
    return entries, new_offset


def entries_to_rows(entries: list[dict]) -> list[list]:
    """Convert JSONL entries to Sheet rows.

    Columns: Timestamp | Provider | Model | Task | Input Tokens | Output Tokens | Cost ($) | Session | Source
    """
    rows = []
    for e in entries:
        rows.append([
            e.get("timestamp", ""),
            e.get("provider", ""),
            e.get("model", ""),
            e.get("task", ""),
            e.get("input_tokens", 0),
            e.get("output_tokens", 0),
            e.get("cost_estimate", 0),
            e.get("session", "unknown"),
            e.get("source", "cli"),
        ])
    return rows


def compute_daily_rollups(entries: list[dict]) -> dict:
    """Compute daily rollups keyed by (date, provider, model).

    Returns dict of key -> {input_tokens, output_tokens, cost, call_count}
    """
    rollups = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "call_count": 0})
    for e in entries:
        ts = e.get("timestamp", "")
        date = ts[:10] if len(ts) >= 10 else "unknown"
        provider = e.get("provider", "unknown")
        model = e.get("model", "unknown")
        key = (date, provider, model)
        rollups[key]["input_tokens"] += e.get("input_tokens", 0)
        rollups[key]["output_tokens"] += e.get("output_tokens", 0)
        rollups[key]["cost"] += e.get("cost_estimate", 0)
        rollups[key]["call_count"] += 1
    return rollups


def ensure_tabs_exist(service) -> None:
    """Create _USAGE and _USAGE_DAILY tabs if they don't exist."""
    sheet_meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    existing_tabs = {s["properties"]["title"] for s in sheet_meta.get("sheets", [])}

    requests = []
    for tab_name in [USAGE_TAB, DAILY_TAB]:
        if tab_name not in existing_tabs:
            requests.append({
                "addSheet": {
                    "properties": {"title": tab_name}
                }
            })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        print(f"Created tabs: {[r['addSheet']['properties']['title'] for r in requests]}")

    # Write headers if tabs were just created
    for tab_name in [USAGE_TAB, DAILY_TAB]:
        if tab_name not in existing_tabs:
            if tab_name == USAGE_TAB:
                headers = [["Timestamp", "Provider", "Model", "Task", "Input Tokens",
                            "Output Tokens", "Cost ($)", "Session", "Source"]]
            else:
                headers = [["Date", "Provider", "Model", "Input Tokens", "Output Tokens",
                            "Cost ($)", "Call Count"]]
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{tab_name}!A1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()


def append_usage_rows(service, rows: list[list]) -> int:
    """Append rows to _USAGE tab."""
    if not rows:
        return 0
    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{USAGE_TAB}!A:I",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows}
    ).execute()
    return result.get("updates", {}).get("updatedRows", len(rows))


def sync_daily_rollups(service, rollups: dict) -> int:
    """Read existing _USAGE_DAILY rows, merge with new rollups, write back."""
    # Read existing daily data
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{DAILY_TAB}!A:G"
    ).execute()
    existing_rows = result.get("values", [])

    # Parse existing into same rollup structure (skip header)
    merged = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "call_count": 0})
    for row in existing_rows[1:]:
        if len(row) >= 7:
            key = (row[0], row[1], row[2])
            merged[key]["input_tokens"] = int(row[3]) if row[3] else 0
            merged[key]["output_tokens"] = int(row[4]) if row[4] else 0
            merged[key]["cost"] = float(row[5]) if row[5] else 0.0
            merged[key]["call_count"] = int(row[6]) if row[6] else 0

    # Merge new rollups
    for key, data in rollups.items():
        merged[key]["input_tokens"] += data["input_tokens"]
        merged[key]["output_tokens"] += data["output_tokens"]
        merged[key]["cost"] += data["cost"]
        merged[key]["call_count"] += data["call_count"]

    # Convert back to rows, sorted by date desc
    new_rows = []
    for (date, provider, model), data in sorted(merged.items(), reverse=True):
        new_rows.append([
            date, provider, model,
            data["input_tokens"], data["output_tokens"],
            round(data["cost"], 6), data["call_count"]
        ])

    # Clear and rewrite (header + data)
    header = [["Date", "Provider", "Model", "Input Tokens", "Output Tokens", "Cost ($)", "Call Count"]]
    all_rows = header + new_rows

    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{DAILY_TAB}!A:G"
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{DAILY_TAB}!A1",
        valueInputOption="RAW",
        body={"values": all_rows}
    ).execute()

    return len(new_rows)


def cmd_sync(full: bool = False) -> None:
    """Main sync: read JSONL → push to Sheet."""
    log_files = find_log_files()
    if not log_files:
        print("No usage log files found.")
        return

    bookmark = {} if full else load_bookmark()
    all_entries = []

    for log_path in log_files:
        fname = log_path.name
        offset = bookmark.get(fname, 0)
        entries, new_offset = read_new_entries(log_path, offset)
        if entries:
            all_entries.extend(entries)
            print(f"  {fname}: {len(entries)} new entries")
        bookmark[fname] = new_offset

    if not all_entries:
        print("No new entries to sync.")
        save_bookmark(bookmark)
        return

    print(f"\nSyncing {len(all_entries)} entries to Google Sheet...")
    service = get_sheets_service()
    ensure_tabs_exist(service)

    # Append raw entries to _USAGE
    rows = entries_to_rows(all_entries)
    appended = append_usage_rows(service, rows)
    print(f"  _USAGE: {appended} rows appended")

    # Compute and merge daily rollups
    rollups = compute_daily_rollups(all_entries)
    daily_count = sync_daily_rollups(service, rollups)
    print(f"  _USAGE_DAILY: {daily_count} rollup rows")

    save_bookmark(bookmark)
    print("Sync complete.")


def cmd_status() -> None:
    """Show sync status."""
    log_files = find_log_files()
    bookmark = load_bookmark()

    print("Usage Sync Status")
    print("=" * 50)
    total_entries = 0
    unsynced = 0

    for log_path in log_files:
        fname = log_path.name
        file_size = log_path.stat().st_size
        synced_offset = bookmark.get(fname, 0)

        with open(log_path, "r", encoding="utf-8") as f:
            count = sum(1 for line in f if line.strip())

        # Count unsynced
        f_entries, _ = read_new_entries(log_path, synced_offset)
        unsync = len(f_entries)

        total_entries += count
        unsynced += unsync
        status = "synced" if unsync == 0 else f"{unsync} pending"
        print(f"  {fname}: {count} entries ({status})")

    print(f"\nTotal: {total_entries} entries, {unsynced} unsynced")
    print(f"Sheet: {SPREADSHEET_ID}")
    print(f"Bookmark: {BOOKMARK_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Sync usage logs to Google Sheet")
    parser.add_argument("--full", action="store_true",
                        help="Full re-sync (ignore bookmark)")
    parser.add_argument("--status", action="store_true",
                        help="Show sync status without syncing")

    args = parser.parse_args()

    if args.status:
        cmd_status()
    else:
        cmd_sync(full=args.full)


if __name__ == "__main__":
    main()
