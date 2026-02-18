"""Read key Daedalus biographical files from Drive to get operator-verified data."""
import requests, json, sys, io, base64
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load stephen@bender23.com credentials (has Drive access)
creds_path = r'C:\Users\lacro\.google_workspace_mcp\credentials\stephen@bender23.com.json'
with open(creds_path) as f:
    creds = json.load(f)

# Refresh token
resp = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'refresh_token': creds['refresh_token'],
    'grant_type': 'refresh_token'
})
token_data = resp.json()
if 'error' in token_data:
    print(f"TOKEN ERROR: {token_data}")
    sys.exit(1)
headers = {'Authorization': f'Bearer {token_data["access_token"]}'}

DRIVE_BASE = 'https://www.googleapis.com/drive/v3'

def read_file(file_id, name=""):
    """Read a Drive file's content."""
    # Try export as text first (for Google Docs)
    try:
        resp = requests.get(f'{DRIVE_BASE}/files/{file_id}/export',
                          headers=headers,
                          params={'mimeType': 'text/plain'}, timeout=15)
        if resp.status_code == 200:
            return resp.text[:5000]
    except:
        pass
    # Try direct download (for non-Google files)
    try:
        resp = requests.get(f'{DRIVE_BASE}/files/{file_id}',
                          headers=headers,
                          params={'alt': 'media'}, timeout=15)
        if resp.status_code == 200:
            return resp.text[:5000]
    except:
        pass
    return "(could not read)"

# Search for key biographical files
files_to_find = [
    'living_profile.json',
    'adjutant_service.json',
    'psyche_identity.json',
    'daedalus_master_profile.json',
    'hearth_family.json',
    'odyssey_experiences.json',
]

for fname in files_to_find:
    print(f"\n{'='*60}")
    print(f"  Searching for: {fname}")
    print(f"{'='*60}")
    resp = requests.get(f'{DRIVE_BASE}/files', headers=headers,
                       params={'q': f"name='{fname}' and trashed=false",
                              'fields': 'files(id,name,mimeType,modifiedTime)'},
                       timeout=15)
    files = resp.json().get('files', [])
    if not files:
        print("  Not found")
        continue
    for f in files:
        print(f"  Found: {f['name']} (modified: {f.get('modifiedTime', '?')})")
        content = read_file(f['id'], f['name'])
        print(content[:5000])
