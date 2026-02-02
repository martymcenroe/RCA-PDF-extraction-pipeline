# LLD Review: 1019 - Feature: Forgery Detection: Seals and Signatures

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD is exceptionally well-structured, showing deep consideration for security (sandboxing, input sanitization) and privacy (hashing). The detailed breakdown of the microservice architecture and the rigorous test plan are commendable. However, there are critical gaps regarding secrets management for the reference database encryption and bounded processing for computer vision operations that must be addressed before implementation.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Secrets Management (Encryption Keys):** The design specifies "AES-256 encryption at rest" for the reference database (Section 7.1) but does not define how the decryption keys are injected into the `forgery-sandbox-service`.
    - **Recommendation:** Explicitly define the mechanism (e.g., Environment Variable `REF_DB_KEY`, Docker secret) in the `Proposed Changes` -> `Data Structures` or `Dependencies` section. Ensure `config/` files do NOT store the key.

### Safety
- [ ] **Unbounded Loops in CV Operations:** The logic flow implies iterating over detected regions ("FOR each page/image... Find contours"). Noisy images (e.g., scanned paper textures) can generate thousands of false-positive contours. Processing all of them can cause DoS or timeouts.
    - **Recommendation:** Define a `MAX_REGIONS_TO_PROCESS` constant (e.g., 50) in `SealDetectorConfig` and `SignatureDetectorConfig`. Abort or truncate processing if this limit is exceeded.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Dependency Weight:** The LLD adds `torch` (PyTorch) for a CPU-only implementation involving basic image processing (ELA, Hashing, Template Matching). PyTorch is extremely heavy (>700MB).
    - **Recommendation:** Verify if `torch` is strictly necessary. If detection logic uses standard CV (SIFT/ORB, Laplacian, ELA via pixel math), `opencv-python` + `numpy` + `scikit-image` is sufficient and drastically lighter. If a specific NN model is used, document which one in "Data Structures".

### Quality
- [ ] **Test Plan - Network Isolation (Test 280):** The test "Sandbox network isolation" is marked as "Auto". Implementing a test that *truly* verifies network isolation requires the test runner to inspect container capabilities or network namespaces, which is complex to automate reliably in a standard `pytest` suite running on a host.
    - **Recommendation:** Clarify the implementation of Test 280. Will it run *inside* the container trying to `curl google.com`, or inspect the `docker inspect` output? The former is preferred.

### Observability
- [ ] **Missing Metric - Detection Counts:** While `processing_time_ms` is logged, the *number* of candidate regions analyzed is not. This is crucial for debugging performance regressions on specific document types.
    - **Recommendation:** Add `candidate_region_count` to `ForgeryDetectionResult`.

## Tier 3: SUGGESTIONS
- **Reference DB Management:** The LLD mentions a reference database but no tooling to *add* seals to it. A simple CLI tool (`tools/manage_ref_db.py`) would be valuable for the MVP.
- **Microservice Communication:** The LLD asks "What queue system...?" and answers "Redis Streams" in architecture decisions. Ensure the `services/forgery-sandbox-service/main.py` implementation explicitly handles the Redis consumer group logic to prevent race conditions if scaled horizontally.

## Questions for Orchestrator
1. **Reference Database Initialization:** How will the initial "100-500 reference seals" be populated? Does this require a separate task/issue for data collection before this feature can go live?

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision