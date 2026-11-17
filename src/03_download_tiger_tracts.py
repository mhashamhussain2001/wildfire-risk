"""Download Census TIGER/Line 2018 census tract boundaries for California.

The 2018 files use the 2010 tract grid, which matches ACS 2014-2018 5-year data.
"""
import zipfile

import requests

from common import RAW, log_source

url = "https://www2.census.gov/geo/tiger/TIGER2018/TRACT/tl_2018_06_tract.zip"
out = RAW / "census" / "tiger_2018_ca_tracts"
out.mkdir(parents=True, exist_ok=True)
zpath = out / "tracts.zip"
zpath.write_bytes(requests.get(url, timeout=300).content)
zipfile.ZipFile(zpath).extractall(out)
zpath.unlink()
print(f"extracted to {out}")
log_source("TIGER/Line 2018 California census tracts", url,
           "Statewide shapefile (all CA tracts, 2010 tract grid). Filter to COUNTYFP 007 (Butte), 089 (Shasta), 103 (Tehama) later. "
           "ALAND column (square meters) gives land area for population density.")
