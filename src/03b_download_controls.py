"""Download the inputs for two control variables: distance to nearest city center, and school district quality.

1. Census Gazetteer 2018 place file: one latitude/longitude point per city (the Census "internal point").
2. TIGER/Line 2018 school district boundaries for California (unified, elementary, secondary).
3. CAASPP 2017-18 Smarter Balanced test results (California Department of Education), all districts.
   The 2017-18 tests were taken in spring 2018, before the November 2018 Camp Fire.
"""
import requests

from common import RAW, log_source

FILES = {
    "census/2018_gaz_place_06.txt": (
        "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2018_Gazetteer/2018_gaz_place_06.txt",
        "Census Gazetteer 2018, California places",
        "Tab-separated. INTPTLAT and INTPTLONG are the internal point of each place. FUNCSTAT 'A' marks active "
        "incorporated cities; 'S' marks census designated places."),
    "census/tl_2018_06_unsd.zip": (
        "https://www2.census.gov/geo/tiger/TIGER2018/UNSD/tl_2018_06_unsd.zip",
        "TIGER/Line 2018 unified school districts, California", "Statewide shapefile, read straight from the zip."),
    "census/tl_2018_06_elsd.zip": (
        "https://www2.census.gov/geo/tiger/TIGER2018/ELSD/tl_2018_06_elsd.zip",
        "TIGER/Line 2018 elementary school districts, California", "Statewide shapefile, read straight from the zip."),
    "census/tl_2018_06_scsd.zip": (
        "https://www2.census.gov/geo/tiger/TIGER2018/SCSD/tl_2018_06_scsd.zip",
        "TIGER/Line 2018 secondary school districts, California", "Statewide shapefile, read straight from the zip."),
    "caaspp/sb_ca2018_all_csv_v3.zip": (
        "https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca2018_all_csv_v3.zip",
        "CAASPP 2017-18 Smarter Balanced research file (all entities)",
        "Statewide test results. District rows have School Code 0000000. Subgroup ID 1 = all students, Grade 13 = all "
        "grades, Test Id 1 = English language arts, 2 = mathematics."),
    "caaspp/sb_ca2018entities_csv.zip": (
        "https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca2018entities_csv.zip",
        "CAASPP 2017-18 entities file", "Names for the county, district and school codes in the research file."),
}
for rel, (url, title, notes) in FILES.items():
    dest = RAW / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        dest.write_bytes(r.content)
    print(f"{rel}: {dest.stat().st_size:,} bytes")
    log_source(title, url, notes)
