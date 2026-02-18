# Gemini Offload Strategy — PRIME Ecosystem
## 2026-02-12 | From: Google Session

**Goal:** Reduce Claude token burn across all sessions by offloading bulk work to Gemini API ($110/mo in unused Cloud credits).

---

## Current Token Burn Analysis

| Session | Directory | Transcript Size | Conversations | Root Cause |
|---------|-----------|----------------|---------------|------------|
| G:\My Drive (PRIME root) | G--My-Drive | 113 MB | 1 massive | Single conversation never compacted |
| Athena (CSCBSP) | CSCBSP | 85 MB | 1 massive | Re-reads 2,800 lines every restart |
| Google (this session) | Desktop | 55 MB | 5 convos | Bulk API responses (Drive map, Gmail) |
| Atlas | Atlas v11.1 | 56 MB | 1 massive | Reads across 498 files |
| JADO | JADO-Project | 33 MB | 1 | Capsule builds, source verification |
| PRIME Central | 00-CLAUDE-PRIME | 18 MB | 1 | Coordination overhead |
| **TOTAL** | | **428 MB** | **945 files** | |

---

## Session-by-Session Offload Plan

### 1. ATLAS — Biographical Research & Document Processing

**Current Claude burn:** 56 MB transcript, reads 498 files, heavy OMPF analysis

**Offload to Gemini:**
- **OCR all OMPF pages** — 47 pages, Gemini does it for $0.02 total. Already proven.
- **Batch OCR any scanned documents** on Drive (medical records, tax docs, certificates)
- **Document summarization** — Instead of Claude reading 17-page PDFs, Gemini pre-summarizes them into 1-page digests
- **Biographical data extraction** — Gemini extracts dates, names, locations from emails/docs into structured JSON
- **Photo tagging** — 45,000 Google Photos: Gemini vision can tag people, places, events for Daedalus timeline

**Command examples:**
```bash
# OCR all OMPF pages at once
python gemini_helper.py --task batch-summarize --input "C:\Users\lacro\OneDrive\Desktop\ompf_pages" --pattern "*.png"

# Extract biographical data from a document
python gemini_helper.py --task json-extract --input "document.txt" --prompt "Extract: names, dates, locations, relationships as JSON"
```

**Estimated savings:** 60-70% of Atlas's document reading can go through Gemini.

---

### 2. ATHENA — Academic Research & Course Material

**Current Claude burn:** 85 MB transcript, re-reads 2,800 lines of JSON every restart

**Offload to Gemini:**
- **Pre-session state summary** — Gemini reads the 2,800-line JSON and produces a 200-line summary. Claude reads the summary instead.
- **Source document summarization** — COI research has 363 URLs in Athena_Eos.json. Gemini can pre-summarize sources so Claude doesn't have to read full articles.
- **Essay draft generation** — For exam prep (8901 Boyd vs Warden essay), Gemini can generate rough drafts that Claude refines.
- **Citation extraction** — Gemini extracts quotes and page numbers from PDFs for academic writing.

**Concrete implementation:**
```bash
# Generate lean session summary
python gemini_helper.py --task summarize --input "G:\My Drive\...\Athena_Eos.json" --output "ATHENA_STATE_SUMMARY.md"

# Pre-summarize a research source
python gemini_helper.py --task summarize --input "source_article.pdf" --output "source_digest.md"
```

**Estimated savings:** 50-60% reduction if state summaries replace raw JSON reads.

---

### 3. SKETCHI — Product Design & E-Commerce

**Current status:** Active Shopify+Printify+social media automation

**Offload to Gemini:**
- **Product description generation** — Gemini writes SEO-optimized product descriptions from design images
- **Design mockup analysis** — Upload mockup PNGs, Gemini describes them for catalog entries
- **Social media caption writing** — Batch generate captions for Instagram/TikTok/Pinterest
- **Competitor analysis** — Gemini with Google Search grounding can research trending designs
- **Image generation** — Gemini 2.0 Flash Image Gen can create product concept art
- **Hashtag research** — Gemini analyzes trending hashtags per platform

**Command examples:**
```bash
# Generate product description from design image
python gemini_helper.py --task ask --prompt "Write an SEO-optimized product description for this t-shirt design" --model gemini-2.5-flash

# Batch analyze mockup images
python gemini_helper.py --task ocr --input "mockup.png"
```

**Estimated savings:** Moderate — Sketchi's main burn is API orchestration, not text processing. But content generation is a natural Gemini fit.

---

### 4. SEMPER / FSMAO — Marine Corps Professional

**Offload to Gemini:**
- **Order/publication summarization** — MCO, NAVMC, and reference documents are long. Gemini summarizes them.
- **Checklist generation** — Given an order reference, Gemini extracts requirements into checklist format
- **LPC testing prep** — Gemini can generate practice questions from FSMAO functional area playbooks
- **Award write-up drafts** — Gemini generates NAVMC 11533 narrative drafts from bullet points

**Command examples:**
```bash
# Summarize a Marine Corps Order
python gemini_helper.py --task summarize --input "MCO_5000.pdf" --output "MCO_5000_digest.md"

# Generate checklist from an order
python gemini_helper.py --task extract --input "order.pdf" --prompt "Extract all requirements as a numbered checklist"
```

---

### 5. JADO — Space Force Brief & Course Capsules

**Current Claude burn:** 33 MB transcript, capsule builds with source verification

**Offload to Gemini:**
- **Source verification** — Instead of Claude fetching and reading web sources, Gemini with Search grounding does it
- **Capsule draft generation** — Gemini generates initial capsule text from source material, Claude refines
- **PowerPoint content** — Gemini extracts key points from research for slide content

---

### 6. PRIME — System Coordination

**Offload to Gemini:**
- **Lean Session Start summaries** — Gemini generates per-session state summaries nightly
- **Inbox summarization** — When inbox files get long (680+ lines), Gemini summarizes pending items
- **Transcript analysis** — Gemini analyzes conversation logs to identify token burn patterns

---

## Cross-Session Infrastructure to Build

### Priority 1: Gemini Pre-Processor Script
A script that runs before any session starts:
1. Reads the session's key files
2. Sends them through Gemini for summarization
3. Writes `SESSION_STATE_SUMMARY.md`
4. Session reads the 200-line summary instead of 2,800 lines of raw data

**Impact:** Could save 50-80% of session-start token burn across all sessions.

### Priority 2: Gemini OCR Pipeline
Batch process ALL scanned documents on Drive:
- OMPF pages (done)
- Medical records
- Tax documents
- Military orders
- Certificates
- Any PDF that's a scanned image

Store the OCR text alongside the originals. One-time cost: probably < $1.

### Priority 3: Gemini Embedding Search
Index all 136,718 Drive files using Gemini Embeddings:
- Natural language search across entire Drive
- "Find Steve's tax returns from 2022" → instant results
- Replace slow Drive API search with semantic search

### Priority 4: Cloud Function Automation
Use the Cloud credits for scheduled tasks:
- Weekly health report (Gmail + Drive + Calendar summary)
- Nightly session state summaries
- Auto-labeling for new emails that bypass filters
- Drive auto-organization rules

---

## Budget Projection

**Monthly Cloud credits available:** $110

| Item | Monthly Cost | Frequency |
|------|-------------|-----------|
| Session state summaries (6 sessions) | ~$0.50 | Daily |
| OCR pipeline (new documents) | ~$0.10 | As needed |
| Weekly health report | ~$0.05 | Weekly |
| Ad-hoc Gemini calls from sessions | ~$5.00 | Ongoing |
| Embedding index maintenance | ~$1.00 | Monthly |
| **Total estimated usage** | **~$7/mo** | |
| **Unused credits** | **~$103/mo** | |

**You're barely going to touch these credits.** Even aggressive usage would struggle to spend $20/month. The capacity is massive relative to the need.

---

## Implementation Priority

| # | Task | Effort | Impact | Build Now? |
|---|------|--------|--------|-----------|
| 1 | Session State Summaries (Gemini pre-processor) | 2 hours | HIGH — saves tokens across ALL sessions | YES |
| 2 | Batch OCR pipeline for Drive documents | 1 hour | HIGH — one-time, unlocks text search | YES |
| 3 | Subscription audit via Gmail | 30 min | MEDIUM — saves real money | YES |
| 4 | Weekly health report | 2 hours | MEDIUM — prevents inbox drift | Next session |
| 5 | Embedding search index | 4 hours | MEDIUM — replaces slow Drive search | Next session |
| 6 | Cloud Function automation | 4 hours | LOW urgency — nice to have | Future |

---

## Immediate Next Steps

1. **Steve activates Developer Program** at developers.google.com/profile (claims $100/mo credits)
2. **Steve activates $300 GCP free trial** at console.cloud.google.com (if not already)
3. **Google session builds** the Pre-Processor Script (Priority 1)
4. **Google session runs** subscription audit (Priority 3)
5. **PRIME routes** this strategy doc to all sessions for awareness
