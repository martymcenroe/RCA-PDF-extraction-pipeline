# Automated Data Validation for PDF Extraction Pipeline

## User Story
As a claims processor,
I want extracted PDF data to be automatically validated for format and consistency,
So that I can catch data quality issues immediately rather than discovering them downstream.

## Objective
Add an automated validation layer after PDF extraction that validates field formats, cross-field consistency, and flags suspicious values for review.

## UX Flow

### Scenario 1: Successful Validation (Happy Path)
1. PDF extraction completes with structured data output
2. Validation layer receives extracted data and document type
3. System runs field-level validations (date formats, VIN checksum, amount ranges)
4. System runs cross-field validations (date ordering, amount sums)
5. All validations pass with high confidence
6. Result: Data proceeds to next pipeline stage with validation report attached

### Scenario 2: Validation Warnings (Suspicious Values)
1. PDF extraction completes with structured data
2. Validation layer detects mileage value outside typical range (e.g., 500,000 miles)
3. System flags value as suspicious but not definitively invalid
4. Result: Data proceeds with warning flag; validation report includes confidence score and recommendation for manual review

### Scenario 3: Validation Failure (Invalid Data)
1. PDF extraction completes with structured data
2. Validation layer detects invalid VIN checksum
3. System blocks extraction from proceeding
4. Result: Pipeline halts; validation report details the failure; data queued for re-extraction or manual correction

### Scenario 4: Missing Required Fields
1. PDF extraction completes with partial data
2. Validation layer checks required fields based on document type (e.g., auto claim requires VIN)
3. System detects missing VIN field
4. Result: Validation fails with clear error indicating which required fields are missing

## Requirements

### Field-Level Validation
1. Date validation supporting MM/DD/YYYY and ISO8601 formats
2. Currency amount validation (positive values, configurable reasonable range)
3. VIN validation (17 characters, valid checksum algorithm)
4. Mileage validation (numeric, configurable reasonable range 0-500,000)
5. Policy number format validation (configurable regex per carrier)

### Cross-Field Validation
1. Date of loss must be on or after policy effective date
2. Date of loss must be on or before policy expiration date
3. Mileage must be reasonable given vehicle age (calculated from VIN year)
4. Line item amounts must sum to total amount (within tolerance)
5. Required fields must be present based on claim type configuration

### Validation Output
1. Generate structured validation report for each extraction
2. Include confidence scores (0-100) for each validated field
3. Categorize issues as ERROR (blocks pipeline) or WARNING (flags for review)
4. Provide human-readable error messages with field paths

### Configuration
1. Support document-type-specific validation rule sets
2. Allow per-field override of validation rules
3. Configurable thresholds for "reasonable" ranges
4. Enable/disable specific validations via configuration

## Technical Approach
- **Pydantic Models:** Define validation schemas using Pydantic v2 with custom validators for complex rules (VIN checksum, cross-field logic)
- **Rule Engine:** Implement configurable validation rules as composable functions that can be enabled/disabled per document type
- **Validation Report:** Structured JSON output with field-level results, confidence scores, and aggregate pass/fail status
- **Pipeline Integration:** Add validation as a discrete stage between extraction and downstream processing, using existing pipeline patterns
- **Configuration Loading:** Use `yaml.safe_load` exclusively for parsing YAML configuration files to prevent deserialization attacks
- **Infrastructure Impact:** Negligible compute impact expected; Pydantic validation is highly efficient and adds minimal processing time per document, well within existing operational budget

## Security Considerations
- Validation logic runs on already-extracted data; no additional PII access required
- **PII Handling in Validation Reports:** Validation reports containing PII must not be transmitted externally and must be stored in the secure document storage database (same location as extraction outputs), avoiding general application logs (e.g., stdout/CloudWatch) to prevent PII leakage
- Validation reports inherit the same data retention policies as extraction output
- Configuration files should be read-only in production to prevent rule tampering

## Files to Create/Modify
- `src/validation/validators.py` — Core validation functions (date, VIN, currency, etc.)
- `src/validation/schemas.py` — Pydantic models for each document type
- `src/validation/rules.py` — Cross-field validation rule engine
- `src/validation/report.py` — Validation report generation
- `src/pipeline/stages/validate.py` — Pipeline stage integration
- `config/validation_rules.yaml` — Document-type-specific validation configuration with default values
- `tests/validation/` — Unit and integration tests for validation layer
- `tests/validation/fixtures/` — Static JSON fixtures library (valid, invalid, warning-state samples)

## Dependencies
- None — can be implemented independently of other pipeline work

## Out of Scope (Future)
- ML-based anomaly detection for edge cases — defer to follow-up issue once baseline rules are established
- Historical data analysis to auto-tune thresholds — nice-to-have, not MVP
- UI for configuring validation rules — configuration via YAML files for MVP
- Auto-correction of invalid values — flag only, no automatic fixes

## Acceptance Criteria
- [ ] Date fields validated for MM/DD/YYYY and ISO8601 formats
- [ ] Currency amounts validated as positive numbers within configured range (default: $0.01 - $10,000,000)
- [ ] VIN validated for 17-character length and valid checksum
- [ ] Mileage validated as numeric within configured range (default: 0 - 500,000)
- [ ] Cross-field date ordering enforced (loss date within policy period)
- [ ] Line item sum validation with configurable tolerance (default: $0.01)
- [ ] Required field presence checked based on document type configuration
- [ ] Validation report generated in structured JSON format with confidence scores
- [ ] Issues categorized as ERROR or WARNING based on severity
- [ ] Validation rules configurable per document type via YAML
- [ ] Default validation values defined in `config/validation_rules.yaml`
- [ ] Pipeline blocks on ERROR-level validation failures
- [ ] Pipeline proceeds with WARNING-level issues flagged for review

## Definition of Done

### Implementation
- [ ] Core validation functions implemented with comprehensive edge case handling
- [ ] Pydantic schemas defined for supported document types
- [ ] Cross-field validation rule engine implemented
- [ ] Pipeline stage integration complete
- [ ] Unit tests written and passing (>90% coverage for validation logic)

### Test Fixtures
- [ ] Static JSON fixture library created in `tests/validation/fixtures/`
- [ ] Fixtures include: valid documents, invalid documents (various error types), warning-state documents
- [ ] Fixtures documented to enable testing validation layer without running full PDF extraction pipeline

### Tools
- [ ] CLI tool for running validation on extracted JSON files (`tools/validate_extraction.py`)
- [ ] CLI tool for validating configuration files (`tools/validate_config.py`)
- [ ] Document tool usage in tool headers

### Documentation
- [ ] Update pipeline architecture wiki page with validation stage
- [ ] Create validation rules reference documentation
- [ ] Document configuration options and examples
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes
- Test VIN validation with known valid/invalid checksums (use NHTSA test VINs)
- Test date validation with ambiguous formats (01/02/2024 could be Jan 2 or Feb 1)
- Test cross-field validation by providing dates where loss date equals boundary dates
- Test sum tolerance by providing amounts that differ by exactly the tolerance threshold
- Force validation failures by omitting required fields from test fixtures
- Test WARNING vs ERROR categorization with values at threshold boundaries
- Use static fixtures from `tests/validation/fixtures/` for isolated validation layer testing

## Labels
`feature`, `pipeline`, `quality-assurance`

## Effort Estimate
Size: **M** (3-5 days)

## Original Brief
# Automated Data Validation

## Problem

Extracted PDF data lacks automated validation:
- Field formats are not checked (dates, amounts, VINs)
- Cross-field consistency is not verified
- Missing required fields are not flagged
- Data quality issues are discovered late in the pipeline

## Proposed Solution

Add automated validation layer after PDF extraction:

### Field-Level Validation
- Date formats (MM/DD/YYYY, ISO8601)
- Currency amounts (positive, reasonable range)
- VIN format (17 characters, valid checksum)
- Mileage (numeric, reasonable range)

### Cross-Field Validation
- Date of loss after effective date
- Mileage consistent with date range
- Amounts sum correctly
- Required fields present based on claim type

### Output
- Validation report with confidence scores
- Flag suspicious values for manual review
- Block clearly invalid extractions

## Acceptance Criteria

- [ ] All required fields validated for format
- [ ] Cross-field consistency checks implemented
- [ ] Validation report generated for each extraction
- [ ] Configurable validation rules per document type
- [ ] Integration with existing pipeline stages

## Technical Considerations

- Could use Pydantic for field validation
- May need document-type-specific validation rules
- Consider ML-based anomaly detection for edge cases