# Software Specification: Automated Subsurface Data Ingestion Pipeline

**Objective:** Develop a modular, extensible system capable of programmatically identifying and downloading Routine Core Analysis (RCA) reports from global geological repositories for the purpose of creating a high-diversity training dataset.

## 1. System Overview

The system consists of a **Core Controller** that orchestrates the workflow and independent **Source Modules** for each repository. This modular design allows for site-specific navigation logic, credential management, and error handling without affecting the rest of the pipeline.

### Core Requirements

| Requirement | Description |
|-------------|-------------|
| **Local Storage** | Files stored using convention: `/data/raw/{source}/{region}/{well_name}_{API}.pdf` |
| **Metadata Manifest** | JSON entry for each download: source URL, timestamp, API number, well name, formation |
| **Integrity Verification** | Verify file size against server-reported size to ensure complete transmission |

## 2. Source-Specific Fetching Modules

### Module A: USGS Core Research Center (CRC)

| Aspect | Details |
|--------|---------|
| **Search** | Filter for wells where "Analysis" = "YES" |
| **Navigation** | Extract Library Number (e.g., A569, CZ08825) from results table |
| **Fetch** | Identify links under "Analysis" category; use "download all" for zipped packages |

### Module B: North Dakota Industrial Commission (NDIC)

| Aspect | Details |
|--------|---------|
| **Authentication** | Requires Premium/Basic subscription login session management |
| **Search** | Query Well Index by File Number or API for "Scout Ticket" |
| **Fetch** | Download "Well File PDF" (monolithic docs - RCA often in appendix) |

### Module C: University Lands (UL) - Texas

| Aspect | Details |
|--------|---------|
| **Search** | Input 10-14 digit API number into Well Detail Portal |
| **Filter** | Access "Documents" tab, filter for type "Cores - Core Analysis" |
| **Fetch** | Download `.pdf` or `.tif` files from document table |

### Module D: UK National Data Repository (NDR)

| Aspect | Details |
|--------|---------|
| **Bulk** | Target CGG Core Analysis Database (2,000+ wells, 43GB package) |
| **Granular** | Look for "Available" icon next to "Core data (LAS/ASCII/SCAL reports)" |

### Module E: DISKOS (Norway)

| Aspect | Details |
|--------|---------|
| **Navigation** | Use DISKOS Public Portal "Wells" interface |
| **Search** | Filter "Well Data Set" by "Rock & Core" → "Conventional Core Analysis" |
| **Priority** | Target open datasets (e.g., Volve field) for peer-reviewed reports |

### Module F: WAPIMS (Western Australia)

| Aspect | Details |
|--------|---------|
| **Search** | Wells Search Page with "Report types" filter = "CORE ANALYSIS" |
| **Batch** | Use "Basket" feature to aggregate multiple reports |

### Module G: Alberta Energy Regulator (AER)

| Aspect | Details |
|--------|---------|
| **Search** | Query Product Catalogue for "Core Analysis File" or "IGDS Well File" |
| **Filter** | Non-confidential wells only (confidentiality expires after 1-2 years) |

## 3. Data Sources Summary

| Source | Region | Access | Volume |
|--------|--------|--------|--------|
| USGS CRC | USA | Public | Individual wells |
| NDIC | North Dakota | Subscription | Well files |
| University Lands | Texas | Public | Individual wells |
| UK NDR | UK Continental Shelf | Public | 2,000+ wells (43GB bulk) |
| DISKOS | Norway | Public | Volve field + others |
| WAPIMS | Western Australia | Public | Batch download |
| AER | Alberta, Canada | Public | Non-confidential wells |

## 4. Source References

| Source | Reference |
|--------|-----------|
| USGS CRC | "To see and download any available reports... click on the Library Number... choose 'download all' to get a zipped file." |
| NDIC | "Well files are scanned into Adobe PDF documents that include... core analysis reports." |
| University Lands | "Documents... Type: Cores - Core Analysis." |
| UK NDR | "CGG Core Analysis Database provides core analysis data for cores from over 2000 wells in the UKCS. (43GB)" |
| DISKOS | "Well Data Set. Data types... Rock & Core. Conventional Core Analysis." |
| WAPIMS | "To find core analysis reports specifically, use the Report types filter." |
| AER | "Services... Core Analysis File... IGDS Well File." |
