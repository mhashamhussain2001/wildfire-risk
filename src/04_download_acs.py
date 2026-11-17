"""Get ACS 2014-2018 5-year tract data for Butte (007), Shasta (089), Tehama (103). No API key needed.

The Census API now requires a key, so this reads the ACS Summary File instead: the same published estimates,
as plain files on www2.census.gov. Each "sequence" file holds a block of tables, one row per geography, with no
header. The lookup file gives each table's sequence number and starting column. The geography file maps each
row number (LOGRECNO) to a GEOID.
"""
import io
import zipfile

import pandas as pd
import requests

from common import RAW, log_source

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2018"
SEQ_DIR = f"{BASE}/data/5_year_seq_by_state/California/Tracts_Block_Groups_Only"
TABLES = {"B19013": "median_hh_income", "B01003": "total_pop"}  # both are one-cell tables; density is computed later
COUNTIES = {"007": "Butte", "089": "Shasta", "103": "Tehama"}


def get(url):
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    return r.content


lookup = pd.read_csv(io.BytesIO(get(f"{BASE}/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt")),
                     dtype=str, encoding="latin-1")
geo = pd.read_csv(io.BytesIO(get(f"{SEQ_DIR}/g20185ca.csv")), header=None, dtype=str, encoding="latin-1")
geo = geo[[4, 48]].set_axis(["LOGRECNO", "geo_id"], axis=1)       # geo_id looks like 14000US06007000101
geo = geo[geo["geo_id"].str.startswith("14000US06")]              # summary level 140 = census tract
geo["GEOID"] = geo["geo_id"].str[7:]
geo = geo[geo["GEOID"].str[2:5].isin(COUNTIES)]

df = geo[["GEOID", "LOGRECNO"]]
for table, name in TABLES.items():
    row = lookup[(lookup["Table ID"] == table) & lookup["Start Position"].notna()].iloc[0]
    seq, start = int(row["Sequence Number"]), int(row["Start Position"])  # Start Position counts columns from 1
    z = zipfile.ZipFile(io.BytesIO(get(f"{SEQ_DIR}/20185ca{seq:04d}000.zip")))
    est = pd.read_csv(z.open(f"e20185ca{seq:04d}000.txt"), header=None, dtype=str)  # "e" file = estimates
    est = est[[5, start - 1]].set_axis(["LOGRECNO", name], axis=1)
    df = df.merge(est, on="LOGRECNO", how="left")
    df[name] = pd.to_numeric(df[name], errors="coerce")  # "." means no estimate (too few households)

df["county"] = df["GEOID"].str[2:5].map(COUNTIES)
out = RAW / "census" / "acs5_2018_tracts.csv"
df.drop(columns="LOGRECNO").to_csv(out, index=False)
print(df.groupby("county").agg(tracts=("GEOID", "size"), pop=("total_pop", "sum"),
                               median_of_tract_income=("median_hh_income", "median")))
print(f"{out.name}: {len(df)} tracts, {df.median_hh_income.isna().sum()} with no income estimate")
assert len(df) == 110, "expected 110 study-area tracts (2010 tract grid)"
log_source("ACS 5-year 2018 (2014-2018) tract data", SEQ_DIR,
           "ACS Summary File, sequence files for California tracts. Tables B19013 (median household income, "
           "2018 dollars) and B01003 (total population) for FIPS 06007, 06089, 06103. Empty income = no estimate published.")
