"""Download FHFA's annual house price index for census tracts (fallback outcome if no sale-level data arrives).

Free, public, no login. Built by FHFA from repeat sales of the same homes. FHFA labels the tract
series "developmental". It is an index of price change per tract and year, not individual sale prices.
"""
import io

import pandas as pd
import requests

from common import RAW, log_source

URL = "https://www.fhfa.gov/hpi/download/annual/hpi_at_tract.csv"
r = requests.get(URL, timeout=300)
r.raise_for_status()
df = pd.read_csv(io.BytesIO(r.content), dtype={"tract": str})
df = df[df["tract"].str[:5].isin(["06007", "06089", "06103"])]
out = RAW / "fhfa" / "hpi_at_tract_study_area.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)
span = df[df.year.between(2014, 2023)]
print(f"{out.name}: {df.tract.nunique()} tracts, years {df.year.min()}-{df.year.max()}. "
      f"Tracts with an index value in every year 2014-2023: {(span.dropna(subset=['hpi']).groupby('tract').size() == 10).sum()}")
log_source("FHFA annual house price index, census tracts", URL,
           "Developmental annual repeat-sales index by 2010 census tract, filtered to Butte, Shasta, Tehama. "
           "Columns: hpi (base = first year), hpi1990, hpi2000, annual_change (percent). Fallback outcome only.")
