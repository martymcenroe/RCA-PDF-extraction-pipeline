# Forgery Detection: Seals and Signatures

## User Story
As a **claims processor**,
I want **automated detection of potentially forged seals and signatures on submitted documents**,
So that **fraudulent claims can be flagged for manual review before processing, reducing financial losses and legal exposure**.

## Objective
Add a forgery detection layer to the document validation pipeline that identifies suspicious seals, signatures, and manipulation artifacts, flagging documents that require human review.

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
2. Verify seal clarity meets minimum threshold (not blurry, fully visible)
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

## Technical Approach
- **Seal Detection:** OpenCV for contour detection and shape analysis; pre-trained model for seal classification; template matching against reference seals
- **Signature Detection:** CNN-based signature detection model; stroke analysis using image processing; Siamese network for signature comparison
- **Manipulation Detection:** ELA (Error Level Analysis) for compression artifacts; frequency domain analysis for splicing; metadata parser for editing history
- **Confidence Scoring:** Ensemble scoring combining multiple detection signals; calibrated probabilities for actionable thresholds
- **Pipeline Integration:** New `ForgeryDetector` class implementing existing validator interface; async processing to minimize latency impact

## Security Considerations
- Reference seal/signature databases must be encrypted at rest and access-logged
- Detection results may contain sensitive information; follow existing PII handling
- Audit logs must be tamper-evident (append-only, checksummed)
- Model weights should be protected to prevent adversarial attacks
- False positive rates must be monitored to prevent legitimate claim denial

## Files to Create/Modify
- `src/extraction/forgery/__init__.py` — Module initialization
- `src/extraction/forgery/seal_detector.py` — Seal detection and analysis
- `src/extraction/forgery/signature_detector.py` — Signature detection and comparison
- `src/extraction/forgery/manipulation_detector.py` — Artifact and tampering detection
- `src/extraction/forgery/confidence_scorer.py` — Ensemble confidence scoring
- `src/extraction/validators/authenticity_validator.py` — Pipeline integration validator
- `src/extraction/models/forgery_result.py` — Data models for detection results
- `tests/extraction/forgery/` — Test suite for all forgery detection components
- `config/forgery_thresholds.yaml` — Configurable detection thresholds

## Dependencies
- OpenCV (`opencv-python`) for image processing
- PyTorch or TensorFlow for pre-trained models
- `python-magic` for file type validation
- `Pillow` for image manipulation
- Existing validation pipeline must support async validators

## Out of Scope (Future)
- **Real-time video verification** — Live notarization verification deferred
- **Blockchain seal verification** — Digital notary integration for future
- **Multi-language seal OCR** — Focus on English seals initially
- **Signature biometric analysis** — Pressure/timing analysis requires specialized hardware
- **Automatic reference database building** — Manual curation for MVP

## Acceptance Criteria
- [ ] Seal detector identifies seal presence with ≥90% accuracy on test dataset
- [ ] Seal detector flags known forgery artifacts (perfect geometry, digital fonts) with ≥85% recall
- [ ] Signature detector identifies signature presence on designated lines with ≥95% accuracy
- [ ] Signature detector flags typed/stamped signatures as non-handwritten
- [ ] Manipulation detector identifies copy/paste artifacts in synthetic test images
- [ ] Manipulation detector flags compression inconsistencies with configurable sensitivity
- [ ] Confidence scores are calibrated (80% confidence = 80% actual accuracy)
- [ ] Flagged documents include detailed reasoning for human reviewers
- [ ] Audit trail records all detection runs with inputs, outputs, and timestamps
- [ ] Pipeline latency increase ≤500ms per document for standard analysis
- [ ] False positive rate ≤5% on legitimate document test set
- [ ] Integration tests pass with existing validation pipeline

## Definition of Done

### Implementation
- [ ] Core forgery detection module implemented
- [ ] All three detectors (seal, signature, manipulation) functional
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
- [ ] Document threshold configuration options
- [ ] Add API documentation for new modules
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created
- [ ] `docs/reports/{IssueID}/model-evaluation-report.md` created (detection accuracy metrics)

### Verification
- [ ] Run 0809 Security Audit - PASS (reference database access controls)
- [ ] Run 0810 Privacy Audit - PASS (signature data handling)
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Unit Testing
- Test each detector independently with synthetic and real document samples
- Include known forgeries in test dataset (create synthetic forgeries for testing)
- Test edge cases: low-resolution scans, rotated documents, partial seals

### Integration Testing
- Test full pipeline flow with flagged documents
- Verify audit trail completeness
- Test threshold configuration changes

### Forcing Error States
- Provide documents with intentionally corrupted metadata to test manipulation detector
- Use generated "perfect circle" seals to trigger forgery artifacts
- Submit typed signatures to verify handwritten detection

### Performance Testing
- Measure latency impact with batch of 100 documents
- Profile memory usage during image analysis
- Test concurrent processing limits