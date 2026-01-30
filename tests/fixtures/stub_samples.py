"""Stub data for offline testing without W20552.db.

These fixtures allow unit testing of the parsing logic without
requiring a live database or PDF environment.
"""

# Sample with lowercase fracture indicator (f)
STUB_SAMPLE_LINES_F_LOWERCASE = [
    "1",           # core_number
    "1-9(f)",      # sample_number with lowercase fracture
    "9,588.50",    # depth
    "0.0027",      # perm_air
    "0.0009",      # perm_klink
    "0.9",         # porosity_amb
    "0.9",         # porosity_ncs
    "2.71",        # grain_density
    "**",          # saturation (merged)
]

# Sample with UPPERCASE fracture indicator (F)
STUB_SAMPLE_LINES_F_UPPERCASE = [
    "1",
    "1-2(F)",      # sample_number with UPPERCASE fracture
    "9,581.50",
    "+",           # merged permeability indicator
    "1.2",         # porosity_amb (only one value for + samples)
    "2.7",         # grain_density
    "76.4",        # sat_water
    "0.8",         # sat_oil
    "77.2",        # sat_total
]

# Sample with detection limit indicator
STUB_SAMPLE_LINES_DETECTION_LIMIT = [
    "1",
    "1-3",
    "9,582.10",
    "<0.0001",     # below detection limit
    "0.3",         # porosity_amb
    "0.3",         # porosity_ncs
    "2.69",        # grain_density
    "**",          # saturation (merged)
]

# Sample with normal numeric values (no special indicators)
STUB_SAMPLE_LINES_NORMAL = [
    "1",
    "1-8",
    "9,587.50",
    "0.0017",      # perm_air
    "0.0005",      # perm_klink
    "0.5",         # porosity_amb
    "0.5",         # porosity_ncs
    "2.7",         # grain_density
    "**",          # no saturations
]

# Sample with + indicator (below detection for permeability)
STUB_SAMPLE_LINES_PLUS = [
    "1",
    "1-4(F)",
    "9,583.50",
    "+",           # merged permeability
    "0.9",         # porosity_amb
    "2.69",        # grain_density
    "**",          # no saturations
]

# Sample with ** saturation only (normal permeability)
STUB_SAMPLE_LINES_STAR_SATURATION = [
    "1",
    "1-14",
    "9,593.50",
    "0.0005",      # perm_air
    "0.0001",      # perm_klink
    "1.6",         # porosity_amb
    "1.6",         # porosity_ncs
    "2.71",        # grain_density
    "**",          # merged saturation
]

# Sample exceeding MAX_SAMPLE_LINES (for safety test)
STUB_SAMPLE_LINES_TOO_LONG = ["line"] * 25
