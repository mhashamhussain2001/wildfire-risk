"""Combine SRA and LRA hazard zones into one layer with a single haz_class column and report area by class and county.

Usage (from the src folder):
    python 05_combine_fhsz.py current     # 2024 SRA + 2025 LRA maps (post Camp Fire, robustness layer)
    python 05_combine_fhsz.py pre2018       # 2007 adopted SRA + 2008 recommended Very High in LRA (in place before the fire)
    python 05_combine_fhsz.py pre2018draft  # 2007 adopted SRA + 2007 DRAFT LRA map with all classes (never adopted)

This only labels land. It does not choose which classes are "treated" or which are the comparison group.
"""
import sys

import pandas as pd

from common import RAW
from fhsz import CLASS_ORDER, combine

vintage = sys.argv[1] if len(sys.argv) > 1 else "current"
combined, overlap = combine(vintage)

out = RAW.parent / "clean" / f"fhsz_combined_{vintage}.gpkg"
combined.to_file(out, driver="GPKG")

area = combined.pivot_table(index="county", columns="haz_class", values="area_km2", aggfunc="sum", fill_value=0)
area = area.reindex(columns=[c for c in CLASS_ORDER if c in area.columns])
pd.options.display.float_format = "{:,.1f}".format
print(f"\nFHSZ vintage: {vintage}. Area in square km by county and hazard class")
print(area.assign(total=area.sum(axis=1)).to_string())
print("\nShare of each county (percent)")
print((area.div(area.sum(axis=1), axis=0) * 100).to_string())
print("\nBy responsibility area (square km)")
print(combined.pivot_table(index="source", columns="haz_class", values="area_km2", aggfunc="sum", fill_value=0).to_string())
print(f"\nSRA/LRA overlap (double counted above): {overlap:,.2f} sq km")

print("""
How special classes are handled
- NonWildland: kept as its own class. CAL FIRE uses it for built-up land with no wildland fuel (LRA map only).
  It is NOT folded into Moderate or Unzoned.
- Unzoned: any part of a county covered by no SRA or LRA polygon. This mixes federal land (not zoned by CAL FIRE)
  with LRA land that has no zone. The two cannot be told apart with these files alone.
- Comparison group: not chosen here. Pick it in your analysis (for example High and Very High vs Moderate and below).""")
if vintage == "pre2018":
    print("- Pre-2018 LRA files contain Very High zones ONLY, so 'Unzoned' inside cities means 'not Very High',"
          " not 'low hazard'. Treat city homes accordingly.")
if vintage == "pre2018draft":
    print("- LRA classes here come from the September 2007 DRAFT map. It was never adopted and had no legal"
          " or disclosure effect. 'Urban Unzoned' is CAL FIRE's draft label for built-up land it did not rate.")
print(f"\nSaved {out}")
