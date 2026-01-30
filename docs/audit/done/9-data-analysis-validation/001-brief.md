# Idea: Data Analysis & Validation

**Status:** Enhancement
**Effort:** Medium (4-6 hours)
**Value:** High - validates extraction accuracy, provides insights

---

## Problem

We have extracted 138 samples but haven't validated the data quality or performed any analysis to verify the extraction is correct.

---

## Proposal

Create a data analysis script that:

1. **Validates data integrity** - catches extraction errors
2. **Generates summary statistics** - sanity check
3. **Identifies anomalies** - outliers, unexpected patterns
4. **Produces visualizations** - for manual review

---

## Validation Checks

### 1. Structural Validation

```python
def validate_structure(df):
    """Verify expected structure."""
    checks = {
        'row_count': len(df) == 138,
        'column_count': len(df.columns) >= 11,
        'no_duplicate_samples': df['sample_number'].is_unique,
        'cores_present': set(df['core_number'].unique()) == {4, 5},
    }
    return checks
```

### 2. Range Validation

| Column | Expected Range | Rationale |
|--------|---------------|-----------|
| core_number | 4-5 | Only 2 cores in this dataset |
| depth_feet | 9,500 - 10,000 | Well depth range |
| permeability_air_md | 0 - 1,000 | Typical range |
| porosity_ambient_pct | 0 - 30 | Physical limit |
| porosity_ncs_pct | 0 - 30 | Physical limit |
| grain_density_gcc | 2.0 - 3.0 | Rock density range |
| saturation_*_pct | 0 - 100 | Percentage |

```python
def validate_ranges(df):
    """Check values are within expected ranges."""
    issues = []

    if df['depth_feet'].min() < 9500 or df['depth_feet'].max() > 10000:
        issues.append(f"Depth out of range: {df['depth_feet'].min()} - {df['depth_feet'].max()}")

    if df['porosity_ambient_pct'].max() > 30:
        issues.append(f"Porosity too high: {df['porosity_ambient_pct'].max()}")

    # ... more checks
    return issues
```

### 3. Consistency Validation

```python
def validate_consistency(df):
    """Check internal consistency."""
    issues = []

    # Depth should increase within each core
    for core in df['core_number'].unique():
        core_df = df[df['core_number'] == core].sort_values('sample_number')
        if not core_df['depth_feet'].is_monotonic_increasing:
            issues.append(f"Core {core}: depth not monotonically increasing")

    # NCS porosity should be <= ambient porosity
    mask = df['porosity_ncs_pct'] > df['porosity_ambient_pct']
    if mask.any():
        issues.append(f"NCS porosity > ambient for {mask.sum()} samples")

    # Saturation total should ≈ water + oil
    df['sat_calc'] = df['saturation_water_pct'] + df['saturation_oil_pct']
    diff = abs(df['saturation_total_pct'] - df['sat_calc'])
    if (diff > 1).any():
        issues.append(f"Saturation mismatch for {(diff > 1).sum()} samples")

    return issues
```

---

## Summary Statistics

```python
def generate_summary(df):
    """Generate summary statistics."""
    return {
        'total_samples': len(df),
        'cores': df['core_number'].unique().tolist(),
        'depth_range': (df['depth_feet'].min(), df['depth_feet'].max()),
        'fracture_samples': df['is_fracture'].sum() if 'is_fracture' in df else 'N/A',
        'below_detection': (df['permeability_air_md'] == '+').sum(),
        'no_saturation': (df['saturation_water_pct'] == '**').sum(),

        'porosity_mean': df['porosity_ambient_pct'].mean(),
        'porosity_std': df['porosity_ambient_pct'].std(),
        'grain_density_mean': df['grain_density_gcc'].mean(),
    }
```

---

## Visualizations

### 1. Depth vs Property Plots

```python
import matplotlib.pyplot as plt

def plot_depth_profiles(df):
    """Plot properties vs depth."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 8))

    # Porosity vs depth
    axes[0].scatter(df['porosity_ambient_pct'], df['depth_feet'])
    axes[0].set_xlabel('Porosity (%)')
    axes[0].set_ylabel('Depth (ft)')
    axes[0].invert_yaxis()

    # Permeability vs depth (log scale)
    axes[1].scatter(df['permeability_air_md'], df['depth_feet'])
    axes[1].set_xscale('log')
    axes[1].set_xlabel('Permeability (md)')
    axes[1].invert_yaxis()

    # Grain density vs depth
    axes[2].scatter(df['grain_density_gcc'], df['depth_feet'])
    axes[2].set_xlabel('Grain Density (g/cc)')
    axes[2].invert_yaxis()

    # Saturation vs depth
    axes[3].scatter(df['saturation_water_pct'], df['depth_feet'], label='Water')
    axes[3].scatter(df['saturation_oil_pct'], df['depth_feet'], label='Oil')
    axes[3].set_xlabel('Saturation (%)')
    axes[3].invert_yaxis()
    axes[3].legend()

    plt.tight_layout()
    plt.savefig('data/output/analysis/depth_profiles.png')
```

### 2. Correlation Matrix

```python
def plot_correlations(df):
    """Plot correlation matrix of numeric columns."""
    numeric_cols = ['depth_feet', 'porosity_ambient_pct', 'porosity_ncs_pct',
                    'grain_density_gcc', 'saturation_water_pct']
    corr = df[numeric_cols].corr()

    plt.figure(figsize=(10, 8))
    plt.imshow(corr, cmap='coolwarm', aspect='auto')
    plt.colorbar()
    plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=45)
    plt.yticks(range(len(numeric_cols)), numeric_cols)
    plt.title('Property Correlations')
    plt.savefig('data/output/analysis/correlations.png')
```

### 3. Distribution Histograms

```python
def plot_distributions(df):
    """Plot histograms of key properties."""
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))

    df['porosity_ambient_pct'].hist(ax=axes[0, 0], bins=20)
    axes[0, 0].set_title('Porosity Distribution')

    # ... more histograms

    plt.tight_layout()
    plt.savefig('data/output/analysis/distributions.png')
```

---

## Output

```
=== RCA Data Analysis Report ===

STRUCTURE VALIDATION
✓ Row count: 138 samples
✓ Column count: 12 columns
✓ No duplicate samples
✓ Cores present: [4, 5]

RANGE VALIDATION
✓ Depth range: 9,580.5 - 9,727.5 ft
✓ Porosity range: 0.3 - 8.5 %
✓ Grain density range: 2.13 - 2.76 g/cc
⚠ 3 samples with permeability > 100 md (check if valid)

CONSISTENCY VALIDATION
✓ Depth monotonically increasing within cores
✓ NCS porosity ≤ ambient porosity
✓ Saturation totals match (within 0.5%)

SUMMARY STATISTICS
- Fracture samples: 42 (30.4%)
- Below detection: 8 (5.8%)
- No saturation data: 45 (32.6%)
- Mean porosity: 4.2%
- Mean grain density: 2.65 g/cc

PLOTS GENERATED
- data/output/analysis/depth_profiles.png
- data/output/analysis/correlations.png
- data/output/analysis/distributions.png

VALIDATION: PASSED (1 warning)
```

---

## Deliverable

```bash
python scripts/analyze_output.py data/output/spec/core_analysis.csv

# Outputs:
# - Console report
# - data/output/analysis/validation_report.txt
# - data/output/analysis/depth_profiles.png
# - data/output/analysis/correlations.png
# - data/output/analysis/distributions.png
```

---

## Next Steps

1. [ ] Create `scripts/analyze_output.py`
2. [ ] Implement validation checks
3. [ ] Add matplotlib visualizations
4. [ ] Generate sample report
5. [ ] Add to CI/CD pipeline
