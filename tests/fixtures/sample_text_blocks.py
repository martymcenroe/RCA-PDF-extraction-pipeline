"""
Sample text blocks mimicking PyMuPDF extraction from W20552.pdf.

PyMuPDF extracts text vertically (one value per line), not horizontally.
These fixtures replicate that format for testing without the actual PDF.
"""

# Page 39 header text (for classification testing)
TABLE_PAGE_TEXT = """SUMMARY OF ROUTINE CORE ANALYSES RESULTS
Vacuum Oven Dried at 180° F     Net Confining Stress:  2,600 psi
G3 Operating, LLC
Williams County, North Dakota
Muller #1-21-16H Well
File No.: CO-51887
Climax Field
Date: 10/14/2011
Sample
Permeability,
Porosity,
Grain
Core
Sample
Depth,
millidarcys
percent
Density,
Number
Number
feet
to Air
Klinkenberg
Ambient
NCS
gm/cc
Water
Oil
Total
1
1-1
9,580.50
0.0011
0.0003
0.9
0.9
2.70
96.5
1.5
98.1
1
1-2(F)
9,581.50
+
1.2
2.70
76.4
0.8
77.2
1
1-3
9,582.10
<0.0001
0.3
0.3
2.69
**
"""

# Plot page text (for classification testing)
PLOT_PAGE_TEXT = """PROFILE PLOT
Core Analysis Results
Depth vs Porosity
G3 Operating, LLC
Williams County, North Dakota
"""

# Cover page text (for classification testing)
COVER_PAGE_TEXT = """TABLE OF CONTENTS
CORE LABORATORIES
Advanced Technology Center
Report for G3 Operating, LLC
"""

# Text page with lots of words (for classification testing)
# Need >100 words to be classified as "text"
TEXT_PAGE_TEXT = """This is a narrative text page with more than one hundred words.
It contains detailed explanations about the core analysis methodology
and procedures used in the laboratory. The samples were collected from
various depths and processed according to standard protocols. Each sample
was carefully labeled and stored in appropriate conditions. The analysis
includes measurements of porosity, permeability, grain density, and fluid
saturations. Results are presented in the accompanying tables and figures.
Additional notes about the sampling process and any anomalies observed
during collection are included in the appendix section of this report.
The laboratory technicians followed strict quality control procedures
throughout the entire analysis process. Calibration was performed daily
and all equipment was maintained according to manufacturer specifications.
The data presented in this report has been reviewed for accuracy and
completeness by senior laboratory staff before final release.
"""

# Minimal text (for "other" classification)
OTHER_PAGE_TEXT = """Page 150
Figure 12
"""

# Complete sample lines for parsing tests (vertical format)
SAMPLE_NORMAL = """1
1-1
9,580.50
0.0011
0.0003
0.9
0.9
2.70
96.5
1.5
98.1"""

SAMPLE_FRACTURE = """1
1-2(F)
9,581.50
+
1.2
2.70
76.4
0.8
77.2"""

SAMPLE_BELOW_DETECTION = """1
1-3
9,582.10
<0.0001
0.3
0.3
2.69
**"""

SAMPLE_NO_SATURATION = """1
1-8
9,587.50
0.0017
0.0005
0.5
0.5
2.70
**"""

# Multiple samples for extraction test
MULTI_SAMPLE_TEXT = """1
1-1
9,580.50
0.0011
0.0003
0.9
0.9
2.70
96.5
1.5
98.1
1
1-2(F)
9,581.50
+
1.2
2.70
76.4
0.8
77.2
1
1-3
9,582.10
<0.0001
0.3
0.3
2.69
**"""
