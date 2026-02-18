"""
Daedalus Personal Gmail Search — lacrossewv@gmail.com
Searches for biographical data gaps that stephen@bender23.com couldn't answer.
Focus: pre-military life, WVU, family history, childhood, relationships, hobbies.
"""
import requests, json, sys, io, time
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load and refresh credentials
creds_path = r'C:\Users\lacro\.google_workspace_mcp\credentials\lacrossewv@gmail.com.json'
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
    print(f"TOKEN REFRESH ERROR: {token_data}")
    sys.exit(1)
creds['token'] = token_data['access_token']
creds['expiry'] = (datetime.now(timezone.utc) + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat()
with open(creds_path, 'w') as f:
    json.dump(creds, f, indent=2)

headers = {'Authorization': f'Bearer {creds["token"]}'}
GMAIL_BASE = 'https://www.googleapis.com/gmail/v1/users/me'

def search_gmail(query, label='', max_results=15):
    """Search Gmail and return message snippets + headers."""
    params = {'q': query, 'maxResults': max_results}
    try:
        resp = requests.get(f'{GMAIL_BASE}/messages', headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  API Error: {resp.status_code}")
            return []
        data = resp.json()
        messages = data.get('messages', [])
        if not messages:
            print(f"  No results")
            return []
        print(f"  Found {data.get('resultSizeEstimate', len(messages))} results")
        results = []
        for msg in messages[:max_results]:
            try:
                detail = requests.get(
                    f'{GMAIL_BASE}/messages/{msg["id"]}',
                    headers=headers,
                    params={'format': 'metadata', 'metadataHeaders': ['From', 'To', 'Subject', 'Date']},
                    timeout=15
                ).json()
                hdrs = {h['name']: h['value'] for h in detail.get('payload', {}).get('headers', [])}
                snippet = detail.get('snippet', '')[:200]
                print(f"    [{hdrs.get('Date', '?')[:16]}] {hdrs.get('From', '?')[:40]}")
                print(f"      Subject: {hdrs.get('Subject', '(none)')[:80]}")
                print(f"      Snippet: {snippet[:150]}")
                results.append({
                    'id': msg['id'],
                    'from': hdrs.get('From', ''),
                    'to': hdrs.get('To', ''),
                    'subject': hdrs.get('Subject', ''),
                    'date': hdrs.get('Date', ''),
                    'snippet': snippet
                })
                time.sleep(0.1)
            except Exception as e:
                print(f"    Error reading msg: {e}")
        return results
    except Exception as e:
        print(f"  Error: {e}")
        return []

def get_email_body(msg_id):
    """Get full email body text."""
    try:
        resp = requests.get(
            f'{GMAIL_BASE}/messages/{msg_id}',
            headers=headers,
            params={'format': 'full'},
            timeout=15
        )
        msg = resp.json()
        payload = msg.get('payload', {})

        def extract_text(part):
            text = ''
            if part.get('mimeType', '').startswith('text/plain'):
                import base64
                data = part.get('body', {}).get('data', '')
                if data:
                    text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            for sub in part.get('parts', []):
                text += extract_text(sub)
            return text

        body = extract_text(payload)
        return body[:3000]
    except Exception as e:
        return f"Error: {e}"


# ============================================================
print("=" * 70)
print("  DAEDALUS PERSONAL GMAIL SEARCH — lacrossewv@gmail.com")
print("=" * 70)

# First: Get mailbox stats
print("\n--- MAILBOX OVERVIEW ---")
resp = requests.get(f'{GMAIL_BASE}/profile', headers=headers, timeout=15)
if resp.status_code == 200:
    profile = resp.json()
    print(f"  Email: {profile.get('emailAddress', '?')}")
    print(f"  Total messages: {profile.get('messagesTotal', '?')}")
    print(f"  Total threads: {profile.get('threadsTotal', '?')}")

# Get label list for context
print("\n--- LABELS ---")
resp = requests.get(f'{GMAIL_BASE}/labels', headers=headers, timeout=15)
if resp.status_code == 200:
    labels = resp.json().get('labels', [])
    user_labels = [l for l in labels if l.get('type') == 'user']
    print(f"  System labels: {len(labels) - len(user_labels)}")
    print(f"  User labels: {len(user_labels)}")
    for l in sorted(user_labels, key=lambda x: x.get('name', '')):
        print(f"    {l.get('name')}")

# ============================================================
# PHASE 1: PSYCHE DOMAIN — Early Life, Childhood, Family Origins
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 1: PSYCHE DOMAIN — Early Life & Childhood")
print("=" * 70)

print("\n[1.1] Where was Steve born?")
search_gmail("born OR birthday OR birthplace OR birth certificate")

print("\n[1.2] Childhood in West Virginia — Martinsburg / Eastern Panhandle")
search_gmail("Martinsburg OR 'Eastern Panhandle' OR 'West Virginia' OR WV childhood")

print("\n[1.3] High school — what school did Steve attend?")
search_gmail("high school OR graduation OR alumni OR yearbook OR class of")

print("\n[1.4] Parents — Janice Bender, father info")
search_gmail("from:janice OR from:mom OR 'Janice Bender' OR mother OR dad OR father")

print("\n[1.5] Siblings — brothers, sisters")
search_gmail("brother OR sister OR sibling OR from:bender")

print("\n[1.6] Pre-military life — what was Steve doing before enlisting?")
search_gmail("before:2004/01/01 subject:job OR work OR application OR interview")

print("\n[1.7] Why did Steve enlist in the Marines?")
search_gmail("enlist OR recruit OR recruiter OR 'Marine Corps' OR USMC before:2005/01/01")

# ============================================================
# PHASE 2: WVU / EDUCATION
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 2: EDUCATION — WVU & Early Career")
print("=" * 70)

print("\n[2.1] WVU enrollment and major")
search_gmail("WVU OR 'West Virginia University' OR Morgantown OR college OR university")

print("\n[2.2] WVU years — what years was Steve there?")
search_gmail("WVU OR Morgantown before:2010/01/01")

print("\n[2.3] Lacrosse at WVU")
search_gmail("lacrosse OR 'lax' OR team OR practice OR game")

print("\n[2.4] Major / degree")
search_gmail("degree OR major OR graduation OR diploma OR 'bachelor' OR transcript")

print("\n[2.5] Fraternity / campus life")
search_gmail("fraternity OR greek OR rush OR chapter OR campus OR dorm")

# ============================================================
# PHASE 3: ADJUTANT DOMAIN — Military Career
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 3: ADJUTANT — Military Career Details")
print("=" * 70)

print("\n[3.1] Boot camp — MCRD San Diego or Parris Island?")
search_gmail("boot camp OR 'MCRD' OR 'Parris Island' OR 'San Diego' OR recruit depot OR OCS OR TBS")

print("\n[3.2] OCS / Commissioning")
search_gmail("OCS OR 'Officer Candidates School' OR commission OR 'second lieutenant' OR 2ndLt")

print("\n[3.3] TBS — The Basic School")
search_gmail("TBS OR 'Basic School' OR Quantico OR 'MOS school'")

print("\n[3.4] MOS — Military Occupational Specialty")
search_gmail("MOS OR '0402' OR '3002' OR '0402' OR logistics OR 'ground supply'")

print("\n[3.5] First duty station")
search_gmail("PCS OR 'duty station' OR orders OR 'check in' OR 'report to' before:2010/01/01")

print("\n[3.6] Unit assignments — all units Steve served with")
search_gmail("CLB OR 'Combat Logistics' OR MLG OR '1st MarDiv' OR 'RadBn' OR '3d RadBn' OR MaintBn OR FSMAO")

print("\n[3.7] Deployments")
search_gmail("deploy OR deployment OR OEF OR OIF OR Iraq OR Afghanistan OR Qatar OR Norway OR Bahrain OR CENTCOM")

print("\n[3.8] Promotion history")
search_gmail("promotion OR promote OR 'select' OR captain OR major OR '1stLt' OR 'pin on'")

print("\n[3.9] Awards and decorations")
search_gmail("award OR medal OR NAM OR 'Navy Achievement' OR 'commendation' OR meritorious OR FITREP")

print("\n[3.10] EWS — Expeditionary Warfare School")
search_gmail("EWS OR 'Expeditionary Warfare' OR 'Intermediate Level' OR ILS OR PME")

# ============================================================
# PHASE 4: HEARTH DOMAIN — Family & Relationships
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 4: HEARTH — Family & Relationships")
print("=" * 70)

print("\n[4.1] How did Steve meet Lana?")
search_gmail("Lana before:2012/01/01")

print("\n[4.2] Wedding / Marriage")
search_gmail("wedding OR married OR marriage OR engagement OR ring OR ceremony")

print("\n[4.3] Stephen Murray — son's birth")
search_gmail("Stephen Murray OR baby OR born OR newborn OR son OR nursery")

print("\n[4.4] Aimee — daughter")
search_gmail("Aimee OR daughter OR baby girl")

print("\n[4.5] Divorce / custody")
search_gmail("divorce OR custody OR separation OR attorney OR lawyer OR court")

print("\n[4.6] From Lana specifically")
search_gmail("from:lana", max_results=20)

print("\n[4.7] Family emails — mom, dad, siblings")
search_gmail("from:bender -from:stephen", max_results=15)

# ============================================================
# PHASE 5: ODYSSEY — Life Experiences & Travel
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 5: ODYSSEY — Life Experiences")
print("=" * 70)

print("\n[5.1] 29 Palms life")
search_gmail("'29 Palms' OR 'Twentynine Palms' OR Joshua Tree OR Yucca Valley")

print("\n[5.2] Camp Pendleton / Oceanside")
search_gmail("Pendleton OR Oceanside OR 'Camp Pendleton' OR 'San Clemente'")

print("\n[5.3] Camp Lejeune / Jacksonville NC")
search_gmail("Lejeune OR Jacksonville OR 'North Carolina' OR Onslow")

print("\n[5.4] Travel and trips")
search_gmail("vacation OR trip OR travel OR flight OR hotel OR Banff OR Disney OR cruise")

print("\n[5.5] Moving / PCS moves")
search_gmail("moving OR movers OR 'household goods' OR HHG OR PCS OR TMO")

# ============================================================
# PHASE 6: DOC DOMAIN — Health & Fitness
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 6: DOC — Health & Fitness")
print("=" * 70)

print("\n[6.1] Injuries / medical")
search_gmail("injury OR surgery OR doctor OR hospital OR medical OR physical therapy OR VA")

print("\n[6.2] Fitness — B23Fitness, lifting")
search_gmail("B23 OR workout OR gym OR lifting OR CrossFit OR competition OR Hyrox")

print("\n[6.3] PFT / CFT scores")
search_gmail("PFT OR CFT OR 'physical fitness' OR 'combat fitness' OR run time")

# ============================================================
# PHASE 7: McDUCK — Financial & Property
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 7: McDUCK — Financial & Property")
print("=" * 70)

print("\n[7.1] Home purchases")
search_gmail("mortgage OR house OR home OR 'real estate' OR escrow OR closing OR Zillow OR Redfin")

print("\n[7.2] Vehicles")
search_gmail("truck OR car OR vehicle OR Tacoma OR 4Runner OR auto OR VIN")

print("\n[7.3] TSP / retirement savings")
search_gmail("TSP OR 'Thrift Savings' OR retirement OR 401k OR invest")

# ============================================================
# PHASE 8: TECHNE — Skills & Certifications
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 8: TECHNE — Skills & Education")
print("=" * 70)

print("\n[8.1] Certifications")
search_gmail("certification OR certified OR PMP OR DAWIA OR 'lean six sigma' OR credential")

print("\n[8.2] Online courses / continuing education")
search_gmail("course OR training OR certificate OR Coursera OR Udemy OR MarineNet")

# ============================================================
# PHASE 9: LOGOS — Creative & Digital
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 9: LOGOS — Creative Life")
print("=" * 70)

print("\n[9.1] TikTok activity")
search_gmail("TikTok")

print("\n[9.2] Photography / creative projects")
search_gmail("photo OR GoPro OR camera OR design OR Photoshop OR creative")

print("\n[9.3] Gaming")
search_gmail("Xbox OR PlayStation OR Steam OR game OR gaming OR Nintendo OR Minecraft")

# ============================================================
# PHASE 10: AION — Dreams, Goals, Legacy
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 10: AION — Dreams & Legacy")
print("=" * 70)

print("\n[10.1] Retirement planning")
search_gmail("retire OR retirement OR 'after the military' OR 'get out' OR transition OR TAPS")

print("\n[10.2] Career aspirations")
search_gmail("dream job OR career OR aspiration OR goal OR 'when I grow up' OR future")

print("\n[10.3] AI / tech interest")
search_gmail("AI OR 'artificial intelligence' OR Claude OR ChatGPT OR automation OR coding OR Python")

# ============================================================
# PHASE 11: BONUS — Pets, Hobbies, Music
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 11: BONUS — Personal Details")
print("=" * 70)

print("\n[11.1] Pets")
search_gmail("dog OR cat OR pet OR puppy OR vet OR animal")

print("\n[11.2] Music")
search_gmail("Spotify OR playlist OR concert OR music OR band OR festival")

print("\n[11.3] Woodworking / crafts")
search_gmail("woodworking OR wood OR build OR workbench OR tools OR shop")

print("\n[11.4] Cooking / food")
search_gmail("recipe OR cooking OR grill OR smoker OR BBQ OR meal prep")

# ============================================================
# PHASE 12: DEEP DIVE — Read key emails in full
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 12: DEEP DIVE — Key Early Emails")
print("=" * 70)

# Oldest emails in the account
print("\n[12.1] Oldest emails in the account")
search_gmail("before:2006/01/01", max_results=20)

print("\n[12.2] Earliest WVU emails")
search_gmail("WVU OR Morgantown before:2008/01/01", max_results=10)

print("\n[12.3] Earliest military emails")
search_gmail("Marine OR USMC OR military before:2008/01/01", max_results=10)

print("\n[12.4] Read full body of 3 oldest emails")
print("\n  Searching for oldest messages...")
resp = requests.get(f'{GMAIL_BASE}/messages', headers=headers,
                   params={'q': 'before:2006/01/01', 'maxResults': 3}, timeout=15)
oldest = resp.json().get('messages', [])
for msg in oldest[:3]:
    body = get_email_body(msg['id'])
    print(f"\n  --- EMAIL {msg['id']} ---")
    print(body[:2000])

# ============================================================
# PHASE 13: ACCOUNT HISTORY — Sent mail for Steve's own words
# ============================================================
print("\n\n" + "=" * 70)
print("  PHASE 13: STEVE'S OWN WORDS — Sent Mail")
print("=" * 70)

print("\n[13.1] Earliest sent emails")
search_gmail("in:sent before:2008/01/01", max_results=15)

print("\n[13.2] Sent emails about family")
search_gmail("in:sent (mom OR dad OR brother OR sister OR family OR Janice OR bender)")

print("\n[13.3] Sent emails about military career")
search_gmail("in:sent (Marine OR USMC OR deploy OR PCS OR orders OR promotion)")

print("\n[13.4] Sent emails about life changes")
search_gmail("in:sent (wedding OR baby OR moving OR new house OR divorce OR custody)")

# Read full body of a few key sent emails
print("\n[13.5] Read full body of earliest sent emails")
resp = requests.get(f'{GMAIL_BASE}/messages', headers=headers,
                   params={'q': 'in:sent before:2008/01/01', 'maxResults': 5}, timeout=15)
sent = resp.json().get('messages', [])
for msg in sent[:3]:
    body = get_email_body(msg['id'])
    print(f"\n  --- SENT EMAIL {msg['id']} ---")
    print(body[:2000])


print("\n\n" + "=" * 70)
print("  PERSONAL GMAIL SEARCH COMPLETE")
print("=" * 70)
print(f"\n  Timestamp: {datetime.now().isoformat()}")
print(f"  Account: lacrossewv@gmail.com")
print("  Next: Compile findings into Daedalus biographical update")
