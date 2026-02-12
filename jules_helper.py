"""
Jules API Helper — PRIME Ecosystem
====================================
Submit tasks to Jules (Google's autonomous coding agent) via the REST API.
Jules reads your GitHub repos, writes code, and opens PRs.

Usage:
    python jules_helper.py --task submit --repo prime-tools --prompt "Add a requirements.txt"
    python jules_helper.py --task list-sessions
    python jules_helper.py --task list-sources
    python jules_helper.py --task status --session SESSION_ID
    python jules_helper.py --task activities --session SESSION_ID
    python jules_helper.py --task message --session SESSION_ID --prompt "Also add type hints"
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "gemini_config.json"
BASE_URL = "https://jules.googleapis.com/v1alpha"


def get_api_key() -> str:
    """Load Jules API key from config file."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    key = config.get("jules_api_key", "")
    if not key or "PASTE" in key:
        print("ERROR: Jules API key not set in config")
        print("Get it from: jules.google → Settings → API Keys")
        sys.exit(1)
    return key


def api_call(method: str, endpoint: str, body: dict = None) -> dict:
    """Make an authenticated API call to Jules."""
    url = f"{BASE_URL}/{endpoint}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("x-goog-api-key", get_api_key())
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"API Error {e.code}: {e.reason}")
        try:
            error_data = json.loads(error_body)
            print(f"  Message: {error_data.get('error', {}).get('message', error_body[:200])}")
        except json.JSONDecodeError:
            print(f"  Body: {error_body[:200]}")
        sys.exit(1)


def list_sources():
    """List all connected GitHub repositories."""
    data = api_call("GET", "sources")
    sources = data.get("sources", [])
    if not sources:
        print("No sources connected.")
        print("Install the Jules GitHub app at jules.google → Settings")
        return
    print(f"Connected repositories ({len(sources)}):\n")
    for s in sources:
        gh = s.get("githubRepo", {})
        owner = gh.get("owner", "?")
        repo = gh.get("repo", "?")
        private = "Private" if gh.get("isPrivate") else "Public"
        branch = gh.get("defaultBranch", {}).get("displayName", "main")
        branches = [b.get("displayName", "?") for b in gh.get("branches", [])]
        print(f"  {owner}/{repo} ({private})")
        print(f"    Source ID: {s.get('name', '?')}")
        print(f"    Default branch: {branch}")
        print(f"    Branches: {', '.join(branches)}")
        print()


def list_sessions(page_size: int = 20):
    """List recent Jules sessions."""
    data = api_call("GET", f"sessions?pageSize={page_size}")
    sessions = data.get("sessions", [])
    if not sessions:
        print("No sessions yet. Submit your first task!")
        return
    print(f"Sessions ({len(sessions)}):\n")
    for s in sessions:
        name = s.get("name", "?")
        title = s.get("title", "untitled")
        state = s.get("state", "?")
        source = s.get("sourceContext", {}).get("source", "repoless")
        # Extract session ID from name
        sid = name.split("/")[-1] if "/" in name else name
        print(f"  [{state}] {title}")
        print(f"    ID: {sid}")
        print(f"    Source: {source}")
        print()


def submit_task(repo: str, prompt: str, title: str = None, branch: str = "main",
                auto_pr: bool = False, require_approval: bool = True):
    """Submit a new coding task to Jules."""
    # Build source name
    owner = "lacrossewv-dotcom"
    source_name = f"sources/github/{owner}/{repo}"

    body = {
        "prompt": prompt,
        "title": title or prompt[:80],
        "sourceContext": {
            "source": source_name,
            "githubRepoContext": {
                "startingBranch": branch
            }
        }
    }

    if auto_pr:
        body["automationMode"] = "AUTO_CREATE_PR"

    if require_approval:
        body["requirePlanApproval"] = True

    print(f"Submitting task to Jules...")
    print(f"  Repo: {owner}/{repo}")
    print(f"  Branch: {branch}")
    print(f"  Auto-PR: {auto_pr}")
    print(f"  Require plan approval: {require_approval}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print()

    data = api_call("POST", "sessions", body)

    name = data.get("name", "?")
    sid = name.split("/")[-1] if "/" in name else name
    state = data.get("state", "?")

    print(f"Task submitted!")
    print(f"  Session ID: {sid}")
    print(f"  State: {state}")
    print(f"  Full name: {name}")
    print(f"\nMonitor progress:")
    print(f"  python jules_helper.py --task status --session {sid}")
    print(f"  python jules_helper.py --task activities --session {sid}")
    print(f"\nOr view in browser:")
    print(f"  https://jules.google.com")
    return data


def submit_repoless(prompt: str, title: str = None):
    """Submit a repoless task (ephemeral cloud environment)."""
    body = {
        "prompt": prompt,
        "title": title or prompt[:80],
    }

    print(f"Submitting repoless task to Jules...")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print()

    data = api_call("POST", "sessions", body)

    name = data.get("name", "?")
    sid = name.split("/")[-1] if "/" in name else name
    state = data.get("state", "?")

    print(f"Task submitted!")
    print(f"  Session ID: {sid}")
    print(f"  State: {state}")
    print(f"\nMonitor: python jules_helper.py --task status --session {sid}")
    return data


def get_status(session_id: str):
    """Get the current status of a Jules session."""
    data = api_call("GET", f"sessions/{session_id}")
    print(f"Session: {data.get('title', 'untitled')}")
    print(f"  State: {data.get('state', '?')}")
    print(f"  Name: {data.get('name', '?')}")
    source = data.get("sourceContext", {}).get("source", "repoless")
    print(f"  Source: {source}")
    return data


def get_activities(session_id: str):
    """List all activities in a Jules session."""
    data = api_call("GET", f"sessions/{session_id}/activities")
    activities = data.get("activities", [])
    if not activities:
        print("No activities yet — Jules is still working.")
        return
    print(f"Activities ({len(activities)}):\n")
    for a in activities:
        atype = a.get("type", "?")
        create_time = a.get("createTime", "?")
        content = ""
        if "agentMessage" in a:
            content = a["agentMessage"].get("content", "")[:200]
        elif "userMessage" in a:
            content = a["userMessage"].get("content", "")[:200]
        elif "planStep" in a:
            content = a["planStep"].get("description", "")[:200]
        print(f"  [{create_time}] {atype}")
        if content:
            print(f"    {content}")
        print()


def send_message(session_id: str, prompt: str):
    """Send a follow-up message to an active Jules session."""
    body = {"prompt": prompt}
    print(f"Sending message to session {session_id}...")
    api_call("POST", f"sessions/{session_id}:sendMessage", body)
    print(f"Message sent: {prompt[:100]}")
    print(f"\nCheck response: python jules_helper.py --task activities --session {session_id}")


def approve_plan(session_id: str):
    """Approve the plan for a session awaiting approval."""
    print(f"Approving plan for session {session_id}...")
    api_call("POST", f"sessions/{session_id}:approvePlan", {})
    print("Plan approved! Jules will begin implementation.")


def main():
    parser = argparse.ArgumentParser(
        description="Jules API Helper — Submit coding tasks to Google's AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --task list-sources
  %(prog)s --task list-sessions
  %(prog)s --task submit --repo prime-tools --prompt "Add requirements.txt with google-genai"
  %(prog)s --task submit-repoless --prompt "Create a Python script that converts CSV to JSON"
  %(prog)s --task status --session abc123
  %(prog)s --task activities --session abc123
  %(prog)s --task message --session abc123 --prompt "Also add error handling"
  %(prog)s --task approve --session abc123
        """
    )
    parser.add_argument("--task", required=True,
                        choices=["list-sources", "list-sessions", "submit", "submit-repoless",
                                 "status", "activities", "message", "approve"],
                        help="Action to perform")
    parser.add_argument("--repo", help="Repository name (for submit)")
    parser.add_argument("--prompt", help="Task description or message")
    parser.add_argument("--title", help="Session title (optional, defaults to prompt)")
    parser.add_argument("--branch", default="main", help="Starting branch (default: main)")
    parser.add_argument("--session", help="Session ID (for status/activities/message/approve)")
    parser.add_argument("--auto-pr", action="store_true", help="Auto-create PR when done")
    parser.add_argument("--no-approval", action="store_true",
                        help="Skip plan approval (auto-approve)")

    args = parser.parse_args()

    if args.task == "list-sources":
        list_sources()
    elif args.task == "list-sessions":
        list_sessions()
    elif args.task == "submit":
        if not args.repo:
            parser.error("--repo required for submit")
        if not args.prompt:
            parser.error("--prompt required for submit")
        submit_task(
            repo=args.repo,
            prompt=args.prompt,
            title=args.title,
            branch=args.branch,
            auto_pr=args.auto_pr,
            require_approval=not args.no_approval
        )
    elif args.task == "submit-repoless":
        if not args.prompt:
            parser.error("--prompt required for submit-repoless")
        submit_repoless(prompt=args.prompt, title=args.title)
    elif args.task == "status":
        if not args.session:
            parser.error("--session required for status")
        get_status(args.session)
    elif args.task == "activities":
        if not args.session:
            parser.error("--session required for activities")
        get_activities(args.session)
    elif args.task == "message":
        if not args.session or not args.prompt:
            parser.error("--session and --prompt required for message")
        send_message(args.session, args.prompt)
    elif args.task == "approve":
        if not args.session:
            parser.error("--session required for approve")
        approve_plan(args.session)


if __name__ == "__main__":
    main()
