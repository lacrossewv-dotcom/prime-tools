"""
OAuth2 Authorization Flow for lacrossewv@gmail.com — v2
Forces re-consent to ensure gmail.readonly scope is actually granted.

IMPORTANT: When the Google consent screen appears, make sure you see
"View your email messages and settings" in the permissions list.
If you only see "See your email address" — the Gmail scope wasn't registered.
"""
import json, os, sys, io
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import webbrowser
import requests
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load credentials from gemini_config.json or environment
_config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'gemini_config.json')
if os.path.exists(_config_path):
    with open(_config_path) as _f:
        _cfg = json.load(_f)
    CLIENT_ID = _cfg.get('oauth_client_id', os.environ.get('GOOGLE_OAUTH_CLIENT_ID', ''))
    CLIENT_SECRET = _cfg.get('oauth_client_secret', os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', ''))
else:
    CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.readonly',
]
REDIRECT_URI = 'http://localhost:8090/callback'
CREDS_PATH = os.path.expanduser(r'~\.google_workspace_mcp\credentials\lacrossewv@gmail.com.json')

os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this tab.</p></body></html>')
        elif 'error' in params:
            self.send_response(400)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            error_msg = params.get('error', ['unknown'])[0]
            self.wfile.write(f'<html><body><h1>Failed: {error_msg}</h1></body></html>'.encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

# Build auth URL with explicit scope string
scope_string = 'openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.readonly'

auth_params = {
    'client_id': CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'scope': scope_string,
    'access_type': 'offline',
    'prompt': 'consent',
    'login_hint': 'lacrossewv@gmail.com',
    'include_granted_scopes': 'true',
}
auth_url = f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}'

print("=" * 60)
print("  OAuth2 Setup for lacrossewv@gmail.com (v2)")
print("=" * 60)
print()
print("Opening browser for authorization...")
print()
print("IMPORTANT: On the consent screen, verify you see:")
print('  - "See your email address"')
print('  - "View your email messages and settings"')
print()
print("If you only see the first one, Gmail scope was NOT registered.")
print("In that case, go to GCP console > APIs & Services > OAuth consent screen")
print("and add gmail.readonly to the scopes list.")
print()

webbrowser.open(auth_url)

print("Waiting for callback on port 8090...")
server = HTTPServer(('localhost', 8090), CallbackHandler)
server.handle_request()

if not auth_code:
    print("\nERROR: No authorization code received.")
    sys.exit(1)

print("\nAuth code received! Exchanging for tokens...")

token_resp = requests.post('https://oauth2.googleapis.com/token', data={
    'code': auth_code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'authorization_code',
})
token_data = token_resp.json()

if 'error' in token_data:
    print(f"\nERROR: {token_data['error']}")
    print(f"Details: {token_data.get('error_description', 'none')}")
    sys.exit(1)

# Verify scopes on the new token
print("\nVerifying granted scopes...")
verify = requests.get('https://www.googleapis.com/oauth2/v1/tokeninfo',
                      params={'access_token': token_data['access_token']})
token_info = verify.json()
granted_scopes = token_info.get('scope', '')
print(f"  Granted scopes: {granted_scopes}")

if 'gmail.readonly' in granted_scopes:
    print("  >>> gmail.readonly: GRANTED")
else:
    print("  >>> gmail.readonly: NOT GRANTED!")
    print("  You need to add gmail.readonly to the OAuth consent screen scopes.")
    print("  Go to: console.cloud.google.com > APIs & Services > OAuth consent screen > Scopes")
    print("  Add: https://www.googleapis.com/auth/gmail.readonly")
    print("  Then re-run this script.")

# Save credentials regardless
creds = {
    'token': token_data['access_token'],
    'refresh_token': token_data.get('refresh_token', ''),
    'token_uri': 'https://oauth2.googleapis.com/token',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scopes': SCOPES,
    'expiry': (datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat()
}
with open(CREDS_PATH, 'w') as f:
    json.dump(creds, f, indent=2)

print(f"\nCredentials saved to: {CREDS_PATH}")

# Test Gmail access
print("\nTesting Gmail API access...")
gmail_headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
test = requests.get('https://www.googleapis.com/gmail/v1/users/me/profile', headers=gmail_headers)
if test.status_code == 200:
    profile = test.json()
    print(f"  Email: {profile.get('emailAddress')}")
    print(f"  Messages: {profile.get('messagesTotal')}")
    print(f"  Threads: {profile.get('threadsTotal')}")
    print("\n  SUCCESS! Gmail API access working!")
else:
    print(f"  Gmail test FAILED: {test.status_code}")
    print(f"  {test.text[:300]}")
