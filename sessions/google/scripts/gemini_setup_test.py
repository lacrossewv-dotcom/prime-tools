"""
Gemini API Setup & Test Script
================================
Run this after pasting your API key into gemini_config.json.
Tests connectivity, lists available models, and runs a quick benchmark.
"""

import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "gemini_config.json"

def main():
    print("=" * 60)
    print("  GEMINI API SETUP TEST")
    print("=" * 60)

    # 1. Check config
    print("\n[1/5] Checking config file...")
    if not CONFIG_PATH.exists():
        print(f"  FAIL: Config not found at {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    api_key = config.get("api_key", "")
    if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
        print("  FAIL: API key not set in config")
        print(f"  Edit: {CONFIG_PATH}")
        print("  Get key from: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    print(f"  OK: API key found ({api_key[:8]}...{api_key[-4:]})")

    # 2. Import library
    print("\n[2/5] Importing google-genai...")
    try:
        from google import genai
        print(f"  OK: google-genai v{genai.__version__}")
    except ImportError:
        print("  FAIL: google-genai not installed")
        print("  Run: pip install -U google-genai")
        sys.exit(1)

    # 3. Initialize client
    print("\n[3/5] Connecting to Gemini API...")
    try:
        client = genai.Client(api_key=api_key)
        print("  OK: Client initialized")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 4. List available models
    print("\n[4/5] Listing available models...")
    try:
        models = list(client.models.list())
        gemini_models = [m for m in models if "gemini" in m.name.lower()]
        print(f"  Found {len(gemini_models)} Gemini models:")
        for m in sorted(gemini_models, key=lambda x: x.name):
            display_name = getattr(m, 'display_name', m.name)
            print(f"    - {m.name}: {display_name}")
    except Exception as e:
        print(f"  WARNING: Could not list models: {e}")
        print("  (This may be normal — continuing with test call)")

    # 5. Test API call
    print("\n[5/5] Testing API call (gemini-2.5-flash)...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Respond with exactly: GEMINI_API_TEST_OK"
        )
        result = response.text.strip()
        print(f"  Response: {result}")
        if "OK" in result.upper():
            print("  STATUS: PASS")
        else:
            print("  STATUS: PASS (unexpected response but API is working)")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE")
    print("=" * 60)
    print(f"\nConfig: {CONFIG_PATH}")
    print(f"Helper: {CONFIG_PATH.parent / 'gemini_helper.py'}")
    print("\nQuick test commands:")
    print(f'  python "{CONFIG_PATH.parent / "gemini_helper.py"}" --task ask --prompt "Hello"')
    print(f'  python "{CONFIG_PATH.parent / "gemini_helper.py"}" --task summarize --input "path/to/file.txt"')
    print(f'  python "{CONFIG_PATH.parent / "gemini_helper.py"}" --task ocr --input "path/to/image.png"')

    # Cost estimate
    print("\n--- MONTHLY BUDGET ESTIMATE ---")
    print("Ultra plan ($249.99/mo) includes $100/mo Google Cloud credits")
    print("Pro plan ($19.99/mo) includes $10/mo Google Cloud credits")
    print("\nWith $110/mo in credits you can run approximately:")
    print("  - Gemini 2.5 Flash: ~367M input tokens + 44M output tokens/mo")
    print("  - Gemini 2.0 Flash: ~1.1B input tokens + 275M output tokens/mo")
    print("  - Gemini 2.5 Pro:   ~88M input tokens + 11M output tokens/mo")
    print("\nThat's MASSIVE capacity for offloading Claude tasks.")


if __name__ == "__main__":
    main()
