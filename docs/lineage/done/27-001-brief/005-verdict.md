# Issue Review: Orchestrator Clarification Request

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate: FAILED

The submitted text does not meet the structural requirements for a GitHub Issue Review. It appears to be a request for clarification rather than a structured issue draft.

### Missing Required Sections:
- [ ] User Story
- [ ] Acceptance Criteria
- [ ] Definition of Done

**Verdict: REJECTED - Issue must include all required sections before review can proceed.**

***

**TPM Note on Clarification Request:**
While I cannot process this as an issue review, I can provide the necessary governance guidance for your next draft:

1.  **License Compliance:** Assume **G-FIAT is MIT licensed**.
    *   *Guidance:* **PyMuPDF (AGPL)** is strictly **FORBIDDEN** in MIT projects unless we isolate it in a separate service (too complex for MVP).
    *   *Action:* Switch Technical Approach to **`pypdf`** (BSD-3-Clause) or **`pdfminer.six`** (MIT). Do not use AGPL libraries.

2.  **Inline Images:**
    *   *Guidance:* Keep MVP scope tight.
    *   *Action:* **Out of Scope** for MVP. Create a separate "Follow-up" issue for "Extract Inline Images from PDF" and link it. Focus MVP strictly on text extraction.

**Please resubmit the Issue Draft with these decisions incorporated.**