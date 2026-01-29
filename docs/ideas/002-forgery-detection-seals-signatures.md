# Idea: Forgery Detection - Seals & Signatures

**Status:** Brief / Research Required
**Effort:** Medium-High (investigation) + High (implementation)
**Value:** High - document authenticity verification

---

## Problem

Legacy subsurface documents (RCA reports, well logs, title documents) may be forged. Verification of authenticity requires detecting and validating:
- Official seals (state, company, notary)
- Professional signatures (geologist, engineer)
- Certification stamps

The PDF format may degrade or obscure these elements, making detection difficult.

---

## Questions to Investigate

### 1. Can we find seals in this document?

**Unknown.** Need to:
- Convert PDF pages to images
- Use image detection (OpenCV, YOLO) to find circular/oval shapes
- Look for text patterns like "SEAL", "CERTIFIED", state names

**Hypothesis:** Core Labs reports typically have:
- Company logo/seal on cover page
- State certification seals (if required)
- Possibly notary seals on certification pages

### 2. How many seals should there be?

Depends on document type and jurisdiction:

| Document Type | Expected Seals |
|---------------|----------------|
| Core Analysis Report | Company seal, possibly state |
| Well Log | State oil/gas commission seal |
| Title Document | Notary seal, county seal |
| Engineering Report | PE stamp/seal (state-specific) |

### 3. What about signatures?

Signatures are harder because:
- PDF text extraction doesn't capture them (they're images)
- Scanning degrades quality
- No standard format

**Detection approach:**
- Image segmentation to find handwriting-like regions
- ML model trained on signature vs non-signature

### 4. Should we convert PDF to images?

**Yes, for seal/signature detection.**

```python
import fitz  # PyMuPDF

doc = fitz.open("document.pdf")
for page_num, page in enumerate(doc):
    pix = page.get_pixmap(dpi=300)  # High DPI for detail
    pix.save(f"page_{page_num}.png")
```

**Trade-offs:**

| Approach | Pros | Cons |
|----------|------|------|
| PDF extraction | Fast, small files | Loses image detail |
| Image conversion | Preserves visual elements | Large files, slower |
| Hybrid | Best of both | Complexity |

### 5. Public database of seals?

**Research needed.** Potential sources:

| Source | Type | Access |
|--------|------|--------|
| State Secretary of State | Notary seals | Some public APIs |
| State Oil & Gas Commissions | Well permit seals | Varies by state |
| Professional Licensing Boards | PE/PG stamps | Usually searchable |
| NIST? | Forensic standards | Unknown |

**Likely answer:** No comprehensive public database. Each state/agency maintains their own.

### 6. Public database of signatures?

**Almost certainly not.**

- Privacy concerns (signatures are PII)
- Fraud risk (publishing signatures enables forgery)
- No legitimate use case for public access

**What exists:**
- Financial institutions have internal signature cards
- Notary journals (private, subpoena required)
- Court records (case-by-case)

### 7. Could we build a company database?

**Yes, but carefully.**

**For seals:**
- Collect known-good seals from verified documents
- Index by: state, agency, date range, visual hash
- Legal: Generally OK (seals are public instruments)

**For signatures:**
- Collect from verified documents with consent
- Store visual hash, not actual image (privacy)
- Legal: Requires consent, data protection compliance
- Use: Similarity matching, not identity verification

**Architecture:**

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  New Document   │────▶│  Seal Extractor  │────▶│  Seal Database  │
│                 │     │  (image detect)  │     │  (known good)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Match Score    │
                                                 │  (0-100%)       │
                                                 └─────────────────┘
```

---

## Technical Approach

### Phase 1: Image Extraction

```python
def extract_page_images(pdf_path, output_dir, dpi=300):
    """Convert PDF pages to high-resolution images."""
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        pix.save(f"{output_dir}/page_{page_num:03d}.png")
```

### Phase 2: Seal Detection

Options:
1. **Template matching** - Compare against known seal templates
2. **Circle detection** - Hough circles for round seals
3. **Text detection** - OCR for "SEAL", "CERTIFIED", etc.
4. **ML object detection** - Train YOLO/Faster-RCNN on seal dataset

### Phase 3: Signature Detection

Options:
1. **Ink color segmentation** - Signatures often blue/black ink
2. **Handwriting detection** - ML model for cursive regions
3. **Location heuristics** - Signatures near "Signed:", dates

### Phase 4: Verification

- Extract detected seals/signatures
- Compare against known-good database
- Generate confidence score
- Flag anomalies for human review

---

## Risks & Considerations

| Risk | Mitigation |
|------|------------|
| False positives | Human review for low-confidence matches |
| Privacy (signatures) | Hash-based matching, no raw storage |
| Legal (seal forgery) | Consult legal, document chain of custody |
| Image quality | Multiple DPI extractions, enhancement |

---

## Next Steps

1. [ ] Extract W20552.pdf to images, manually inspect for seals
2. [ ] Research Texas RRC seal requirements for core analysis reports
3. [ ] Prototype circle detection with OpenCV
4. [ ] Survey state oil/gas commission APIs for seal verification
5. [ ] Legal review of signature database concept

---

## Open Questions

- Does Core Laboratories use a consistent seal format?
- Are there industry standards for RCA report certification?
- What's the false positive tolerance for production use?
- Integration with existing document workflow?
