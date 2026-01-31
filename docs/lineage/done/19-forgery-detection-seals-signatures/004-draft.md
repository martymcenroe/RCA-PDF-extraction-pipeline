# Forgery Detection: Seals and Signatures

## User Story
As a **claims processor**,
I want **automated detection of potentially forged seals and signatures on submitted documents**,
So that **fraudulent claims can be flagged for manual review before processing, reducing financial losses and legal exposure**.

## Objective
Add a forgery detection layer to the document validation pipeline that identifies suspicious seals, signatures, and manipulation artifacts, flagging documents that require human review.

## Labels
`machine-learning`, `security`, `feature`

## Effort Estimate
**XL** — Requires model tuning, image processing pipeline, and extensive validation testing.

## UX Flow

### Scenario 1: Document Passes Authenticity Check
1. User uploads insurance claim document with notary seal and signature
2. System extracts document and runs forgery detection analysis
3. Seal detection confirms presence, clarity, and positioning within normal parameters
4. Signature detection verifies presence on required lines with consistent characteristics
5. No manipulation artifacts detected
6. Result: Document proceeds through normal validation pipeline with "authenticity: verified" status

### Scenario 2: Suspicious Seal Detected
1. User uploads document with notarized form
2. System analyzes seal and detects anomalies (perfect geometric circle, digital font artifacts)
3. Confidence score falls below threshold (e.g., 0.65)
4. Result: Document flagged with "seal_anomaly" warning, routed to manual review queue with detection details

### Scenario 3: Missing Required Signature
1. User uploads multi-page contract requiring signatures on pages 3 and 7
2. System detects signature on page 3 but signature line on page 7 is empty
3. Result: Document flagged with "missing_signature" error, validation halted pending correction

### Scenario 4: Manipulation Artifacts Detected
1. User uploads document that has been digitally altered
2. System detects inconsistent compression levels and copy/paste boundary artifacts
3. Metadata shows multiple editing applications
4. Result: Document flagged with "manipulation_detected" warning, high-priority manual review triggered

### Scenario 5: Signature Inconsistency Across Documents
1. User uploads multiple documents from same signatory (reference signatures available)
2. System compares signature characteristics against reference
3. Significant deviation detected in stroke patterns
4. Result: Document flagged with "signature_mismatch" warning, comparison report generated for reviewer

## Requirements

### Seal Detection
1. Detect presence/absence of seals in expected document regions
2. Verify seal clarity meets minimum threshold (Laplacian variance > 100)
3. Check seal positioning relative to signature lines and document edges
4. Identify common forgery artifacts: perfect circles, digital/system fonts, uniform color distribution
5. Compare against known authentic seal patterns when reference database available
6. Return confidence score (0.0-1.0) for each detected seal

### Signature Detection
1. Detect signature presence on designated signature lines
2. Verify signature is handwritten (not typed or stamped)
3. Extract signature bounding box and basic characteristics (size, position, ink coverage)
4. Flag unusual characteristics: perfectly horizontal baseline, uniform stroke width, digital artifacts
5. Compare against reference signatures when available (optional feature)
6. Return confidence score for signature authenticity

### Manipulation Detection
1. Detect copy/paste artifacts (boundary discontinuities, inconsistent backgrounds)
2. Identify resolution/compression inconsistencies within document
3. Analyze metadata for suspicious editing history
4. Detect font inconsistencies suggesting text replacement
5. Identify splicing artifacts between document sections

### Pipeline Integration
1. Run forgery detection after document extraction, before data validation
2. Add detection results to document metadata
3. Route flagged documents to appropriate review queues based on severity
4. Maintain audit trail of all detection results and decisions

### Flagging System
1. Define severity levels: `info`, `warning`, `critical`
2. `info`: Minor anomalies, proceed with caution note
3. `warning`: Moderate concerns, recommend manual review
4. `critical`: High likelihood of forgery, block automatic processing
5. Configurable thresholds per document type

### Input Security
1. All uploaded images/PDFs MUST be processed in ephemeral containers with no network access
2. Sanitize image headers before passing to OpenCV/Pillow to prevent buffer overflow exploits
3. Validate file magic bytes before processing (reject mismatched extensions)
4. Enforce maximum file size limits (50MB) and dimension limits (10000x10000px)
5. Strip EXIF and metadata before processing to prevent injection attacks

### Data Residency & Privacy
1. **Local-Only Execution:** All signature and seal processing MUST occur on local infrastructure; NO external API transmission of signature/biometric data is permitted
2. Reference signatures MUST be stored as one-way perceptual hashes, NOT raw images, to reduce liability
3. All processing infrastructure MUST reside within configured data residency region (default: same region as primary database)

## Technical Approach
- **Seal Detection:** OpenCV for contour detection and shape analysis; pre-trained model for seal classification; template matching against reference seals
- **Signature Detection:** CNN-based signature detection model; stroke analysis using image processing; Siamese network for signature comparison
- **Manipulation Detection:** ELA (Error Level Analysis) for compression artifacts; frequency domain analysis for splicing; metadata parser for editing history
- **Confidence Scoring:** Ensemble scoring combining multiple detection signals; calibrated probabilities for actionable thresholds
- **Pipeline Integration:** New `ForgeryDetector` class implementing existing validator interface; async processing to minimize latency impact
- **Input Sandboxing:** Process all images in ephemeral Docker containers with seccomp profiles; use `libseccomp` to restrict syscalls

## Infrastructure & Cost
- **Compute Requirements:** CPU inference only for MVP (no GPU required); estimated 200-400ms per document on 4-core instance
- **Infrastructure Cost:** Estimated $800-1200/month increase for dedicated processing instances (2x c5.xlarge or equivalent)
- **Scaling:** Horizontal scaling via container orchestration; auto-scale based on queue depth
- **Model Storage:** ~500MB for all model weights; served from local filesystem, not fetched at runtime

## Security Considerations
- Reference seal/signature databases must be encrypted at rest (AES-256) and access-logged
- Reference signatures stored as perceptual hashes only, not raw images
- Detection results may contain sensitive information; follow existing PII handling
- Audit logs must be tamper-evident (append-only, checksummed)
- Model weights should be protected to prevent adversarial attacks
- False positive rates must be monitored to prevent legitimate claim denial
- All image processing occurs in sandboxed ephemeral containers

## Files to Create/Modify
- `src/extraction/forgery/__init__.py` — Module initialization
- `src/extraction/forgery/seal_detector.py` — Seal detection and analysis
- `src/extraction/forgery/signature_detector.py` — Signature detection and comparison
- `src/extraction/forgery/manipulation_detector.py` — Artifact and tampering detection
- `src/extraction/forgery/confidence_scorer.py` — Ensemble confidence scoring
- `src/extraction/forgery/input_sanitizer.py` — Image/PDF input validation and sandboxing
- `src/extraction/validators/authenticity_validator.py` — Pipeline integration validator
- `src/extraction/models/forgery_result.py` — Data models for detection results
- `tests/extraction/forgery/` — Test suite for all forgery detection components
- `config/forgery_thresholds.yaml` — Configurable detection thresholds
- `docker/forgery-sandbox/Dockerfile` — Ephemeral container for sandboxed processing

## Dependencies
- OpenCV (`opencv-python`) for image processing
- PyTorch for pre-trained models (CPU inference)
- `python-magic` for file type validation
- `Pillow` for image manipulation
- `imagehash` for perceptual signature hashing
- Docker for sandboxed processing containers
- **Issue #0087** — Existing validation pipeline must support async validators (Status: Complete)

## Out of Scope (Future)
- **Real-time video verification** — Live notarization verification deferred
- **Blockchain seal verification** — Digital notary integration for future
- **Multi-language seal OCR** — Focus on English seals initially
- **Signature biometric analysis** — Pressure/timing analysis requires specialized hardware
- **Automatic reference database building** — Manual curation for MVP
- **GPU acceleration** — CPU inference sufficient for MVP throughput

## Acceptance Criteria
- [ ] Seal detector identifies seal presence with ≥90% accuracy on test dataset
- [ ] Seal detector flags known forgery artifacts (perfect geometry, digital fonts) with ≥85% recall
- [ ] Seal clarity verification uses Laplacian variance threshold > 100
- [ ] Signature detector identifies signature presence on designated lines with ≥95% accuracy
- [ ] Signature detector flags typed/stamped signatures as non-handwritten
- [ ] Manipulation detector identifies copy/paste artifacts in synthetic test images
- [ ] Manipulation detector detects ≥90% of Error Level Analysis discrepancies on test set 4
- [ ] Confidence scores are calibrated (80% confidence = 80% actual accuracy)
- [ ] Flagged documents include detailed reasoning for human reviewers
- [ ] Audit trail records all detection runs with inputs, outputs, and timestamps
- [ ] Pipeline latency increase ≤500ms per document for standard analysis (on c5.xlarge or equivalent)
- [ ] False positive rate ≤5% on legitimate document test set
- [ ] Integration tests pass with existing validation pipeline
- [ ] All image processing occurs in sandboxed containers with no network access
- [ ] No signature/biometric data transmitted to external APIs
- [ ] Reference signatures stored as perceptual hashes only

## Definition of Done

### Implementation
- [ ] Core forgery detection module implemented
- [ ] All three detectors (seal, signature, manipulation) functional
- [ ] Input sanitization and sandboxing implemented
- [ ] Pipeline integration complete with async support
- [ ] Unit tests written and passing (≥80% coverage)
- [ ] Integration tests with validation pipeline passing

### Tools
- [ ] Create `tools/forgery_analyze.py` for standalone document analysis
- [ ] Create `tools/forgery_threshold_tuner.py` for threshold optimization
- [ ] Document tool usage in tool headers

### Documentation
- [ ] Update wiki pages for validation pipeline
- [ ] Create ADR for forgery detection architecture decisions
- [ ] Create ADR for signature storage decision (hashes vs. raw)
- [ ] Document threshold configuration options
- [ ] Add API documentation for new modules
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created
- [ ] `docs/reports/{IssueID}/model-evaluation-report.md` created (detection accuracy metrics)

### Verification
- [ ] Run 0809 Security Audit - PASS (reference database access controls, input sanitization)
- [ ] Run 0810 Privacy Audit - PASS (signature data handling, local-only processing)
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Unit Testing
- Test each detector independently with synthetic and real document samples
- Include known forgeries in test dataset (create synthetic forgeries for testing)
- Test edge cases: low-resolution scans, rotated documents, partial seals
- Test input sanitizer with malformed headers and malicious payloads

### Integration Testing
- Test full pipeline flow with flagged documents
- Verify audit trail completeness
- Test threshold configuration changes
- Verify sandboxed processing container isolation

### Forcing Error States
- Provide documents with intentionally corrupted metadata to test manipulation detector
- Use generated "perfect circle" seals to trigger forgery artifacts
- Submit typed signatures to verify handwritten detection
- Submit malformed images to verify input sanitization rejects them
- Attempt to inject payloads via image headers to verify sandboxing

### Performance Testing
- Measure latency impact with batch of 100 documents
- Profile memory usage during image analysis
- Test concurrent processing limits
- Verify 500ms latency budget on c5.xlarge instances

## Original Brief
# Forgery Detection: Seals and Signatures

## Problem

Document forgery is a significant risk in insurance claims:
- Fake notary seals
- Forged signatures
- Altered document content
- Photocopied or digitally manipulated originals

Current pipeline extracts data without validating document authenticity.

## Proposed Solution

Add forgery detection layer for seals and signatures:

### Seal Detection
- Detect presence/absence of expected seals
- Verify seal clarity and positioning
- Check for common forgery artifacts (perfect circles, digital fonts)
- Compare against known authentic seal patterns

### Signature Detection
- Detect signature presence on required lines
- Check signature consistency across documents
- Flag unusual signature characteristics
- Compare against reference signatures when available

### Manipulation Detection
- Check for copy/paste artifacts
- Detect inconsistent resolution/compression
- Identify suspicious metadata
- Flag documents needing manual review

## Acceptance Criteria

- [ ] Seal detection with confidence scoring
- [ ] Signature presence verification
- [ ] Basic manipulation artifact detection
- [ ] Integration with validation pipeline
- [ ] Flagging system for suspicious documents
- [ ] Audit trail of detection results

## Technical Considerations

- May require OpenCV or similar image processing
- Consider pre-trained models for seal/signature detection
- Balance false positive rate vs. security
- Document types vary in seal/signature requirements