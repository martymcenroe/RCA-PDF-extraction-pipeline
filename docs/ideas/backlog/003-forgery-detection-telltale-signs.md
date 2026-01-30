# Idea: Forgery Detection - Telltale Signs

**Status:** Brief / Research Required
**Effort:** Medium (rule-based) to High (ML-based)
**Value:** High - catch amateur forgeries before human review

---

## Problem

Forged documents often contain telltale signs that a trained eye catches but automated systems miss. These include:
- Unusual or non-existent addresses
- Names of known bad actors (debarred, sanctioned)
- Grammatical/spelling errors (classic "Nigerian prince" tells)
- Anachronisms (wrong date formats, future dates)
- Metadata inconsistencies

---

## Detection Categories

### 1. Address Verification

**Red flags:**
- Address doesn't exist (USPS API returns invalid)
- Address is a vacant lot or demolished building
- Address is a known mail drop / virtual office
- State/ZIP mismatch
- International address for domestic company

**Implementation:**

```python
def verify_address(address: str) -> dict:
    """
    Check address against USPS, Google Maps, known mail drops.
    Returns confidence score and flags.
    """
    result = {
        "valid_usps": check_usps(address),
        "valid_google": check_google_places(address),
        "is_mail_drop": check_mail_drop_database(address),
        "is_virtual_office": check_virtual_office_list(address),
    }
    return result
```

**Data sources:**
- USPS Address Validation API (free for basic)
- Google Places API (~$5/1000 requests)
- Virtual office provider lists (scraped/compiled)
- SEC filings for known shell company addresses

### 2. Debarred / Sanctioned Parties

**Red flags:**
- Name matches OFAC SDN list (sanctions)
- Company on EPA debarment list
- Individual on state professional license revocation
- Company in SEC enforcement actions

**Public databases:**

| Database | Source | Access |
|----------|--------|--------|
| OFAC SDN List | US Treasury | Free API |
| SAM.gov Exclusions | GSA | Free API |
| EPA Debarment | EPA | Downloadable |
| SEC Enforcement | SEC EDGAR | Free API |
| State Bar Discipline | State bars | Varies |
| State PE Revocations | Licensing boards | Varies |

**Implementation:**

```python
def check_sanctions(name: str, company: str) -> list:
    """
    Check name/company against sanctions and debarment lists.
    Returns list of matches with source.
    """
    matches = []

    # OFAC Specially Designated Nationals
    if ofac_match := search_ofac_sdn(name, company):
        matches.append({"source": "OFAC SDN", "match": ofac_match})

    # SAM.gov (federal contractors)
    if sam_match := search_sam_exclusions(name, company):
        matches.append({"source": "SAM.gov", "match": sam_match})

    # State-specific
    if state_match := search_state_debarments(name, company):
        matches.append({"source": state_match["state"], "match": state_match})

    return matches
```

### 3. Linguistic Red Flags

**Classic "Nigerian scam" tells:**

| Pattern | Example | Detection |
|---------|---------|-----------|
| Unusual capitalization | "URGENT Business PROPOSAL" | Regex + frequency analysis |
| Formal + informal mix | "Dear Sir, pls respond ASAP" | Style consistency check |
| Money emphasis | "USD $10,000,000.00" | Currency pattern detection |
| Urgency language | "respond within 24 hours" | Keyword list |
| Title inflation | "Dr. Barrister Chief Engr." | Title density check |
| Awkward phrasing | "I am writing to inform you that..." | N-gram analysis |
| Missing articles | "Please send document" vs "the document" | Grammar check |
| Wrong prepositions | "reply me" vs "reply to me" | Grammar check |

**Implementation:**

```python
URGENCY_KEYWORDS = [
    "urgent", "immediate", "asap", "act now", "limited time",
    "expire", "deadline", "within 24 hours", "respond immediately"
]

SCAM_PATTERNS = [
    r"USD?\s*\$[\d,]+\.00",  # Round dollar amounts
    r"(?:Dr\.?\s*)?(?:Chief|Barrister|Prince|Minister)",  # Title stacking
    r"(?:URGENT|CONFIDENTIAL|PRIVATE).*(?:URGENT|CONFIDENTIAL|PRIVATE)",  # Multiple emphatics
    r"\d{1,3}(?:,\d{3})*\s*(?:million|billion)",  # Large round numbers
]

def check_linguistic_flags(text: str) -> list:
    flags = []

    # Urgency keywords
    urgency_count = sum(1 for kw in URGENCY_KEYWORDS if kw.lower() in text.lower())
    if urgency_count > 2:
        flags.append({"type": "urgency", "count": urgency_count})

    # Scam patterns
    for pattern in SCAM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({"type": "scam_pattern", "pattern": pattern})

    # Grammar check (using language_tool_python or similar)
    grammar_errors = check_grammar(text)
    if grammar_errors > threshold:
        flags.append({"type": "grammar", "errors": grammar_errors})

    return flags
```

### 4. Metadata Inconsistencies

**Red flags:**
- PDF created date after document date
- Creator software inconsistent with era (e.g., 1995 doc made in Acrobat 2020)
- Modified date before created date
- Author name doesn't match signatory
- Timezone inconsistencies

**Implementation:**

```python
def check_metadata_consistency(pdf_path: str, document_date: str) -> list:
    flags = []
    doc = fitz.open(pdf_path)
    metadata = doc.metadata

    # Check creation date vs document date
    if metadata.get("creationDate"):
        created = parse_pdf_date(metadata["creationDate"])
        doc_date = parse_date(document_date)
        if created < doc_date:
            flags.append({
                "type": "anachronism",
                "detail": f"PDF created {created} but document dated {doc_date}"
            })

    # Check producer software
    producer = metadata.get("producer", "")
    if "2020" in producer and "1995" in document_date:
        flags.append({
            "type": "software_anachronism",
            "detail": f"Modern software ({producer}) for old document"
        })

    return flags
```

### 5. Domain-Specific Red Flags (Oil & Gas)

For RCA reports specifically:

| Red Flag | Detection |
|----------|-----------|
| Well API number invalid | Check against state database |
| Operator not registered | State RRC lookup |
| Lab not accredited | Check lab certification databases |
| Impossible values | Porosity > 40%, density < 1.0 |
| Non-existent county | State boundary check |
| Wrong formation name | Geological database lookup |

---

## Architecture

```
┌─────────────────┐
│  Input Document │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Text Extraction│────▶│  Entity Extraction│
└────────┬────────┘     │  (names, addresses│
         │              │   companies, dates)│
         │              └──────────┬─────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐     ┌──────────────────┐
│  Metadata Check │     │  Database Checks  │
│  (dates, author)│     │  (OFAC, SAM, etc) │
└────────┬────────┘     └──────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐     ┌──────────────────┐
│ Linguistic Check│     │  Address Verify   │
│ (grammar, style)│     │  (USPS, Google)   │
└────────┬────────┘     └──────────┬────────┘
         │                         │
         └──────────┬──────────────┘
                    ▼
         ┌──────────────────┐
         │  Risk Score      │
         │  + Flag Summary  │
         └──────────────────┘
```

---

## Risk Scoring

| Flag Type | Weight | Example |
|-----------|--------|---------|
| OFAC match | CRITICAL | Auto-reject |
| SAM exclusion | CRITICAL | Auto-reject |
| Invalid address | HIGH | +30 points |
| Grammar errors > 10 | MEDIUM | +15 points |
| Urgency language | LOW | +5 points |
| Metadata anachronism | MEDIUM | +20 points |

**Score interpretation:**
- 0-20: Low risk, process normally
- 21-50: Medium risk, flag for review
- 51-80: High risk, senior review required
- 81+: Critical, do not process

---

## Data Sources Summary

| Check | Data Source | Cost | Update Frequency |
|-------|-------------|------|------------------|
| OFAC sanctions | Treasury API | Free | Daily |
| SAM exclusions | SAM.gov API | Free | Daily |
| Address validation | USPS API | Free (limited) | Real-time |
| Grammar check | LanguageTool | Free (limited) | N/A |
| State debarments | State APIs | Free | Varies |
| Well API validation | State RRC | Free | Daily |

---

## Next Steps

1. [ ] Build entity extraction for names, addresses, companies
2. [ ] Integrate OFAC SDN API
3. [ ] Integrate SAM.gov exclusions API
4. [ ] Build linguistic analysis module
5. [ ] Create risk scoring framework
6. [ ] Test against known-good and known-bad documents
7. [ ] Define human review workflow for flagged documents

---

## References

- OFAC SDN List: https://sanctionssearch.ofac.treas.gov/
- SAM.gov: https://sam.gov/content/exclusions
- USPS Address API: https://www.usps.com/business/web-tools-apis/
- Texas RRC: https://www.rrc.texas.gov/
- LanguageTool: https://languagetool.org/
