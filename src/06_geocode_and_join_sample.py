"""Pipeline test: geocode a small CSV of addresses and tag each with its FHSZ hazard class.

Usage (from the src folder, after 05_combine_fhsz.py has run):
    python 06_geocode_and_join_sample.py [vintage] [addresses.csv]
Defaults: vintage "current", file src/sample_addresses.csv. The input needs columns id, street, city, state, zip.

Geocoder: the free US Census batch geocoder (no key, up to 10,000 addresses per call, public service).
Only the sample addresses (public buildings) are sent. Real sales data would go through the same function.
"""
import csv
import io
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

from common import RAW
from fhsz import CLASS_ORDER, CRS_AREA

GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH = 5000  # stay well under the 10,000 per file limit


def geocode(df):
    """Add lon, lat and geocode_status columns to a DataFrame with id, street, city, state, zip."""
    results = []
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        buf = io.StringIO()
        chunk[["id", "street", "city", "state", "zip"]].to_csv(buf, header=False, index=False)
        r = requests.post(GEOCODER, data={"benchmark": "Public_AR_Current"}, timeout=300,
                          files={"addressFile": ("addresses.csv", buf.getvalue())})
        r.raise_for_status()
        for row in csv.reader(io.StringIO(r.text)):
            # columns: id, input address, Match/No_Match/Tie, Exact/Non_Exact, matched address, "lon,lat", tiger id, side
            lon, lat = (row[5].split(",") if len(row) > 5 and row[5] else (None, None))
            results.append({"id": row[0], "geocode_status": row[2], "lon": lon, "lat": lat})
    res = pd.DataFrame(results)
    res["id"] = res["id"].astype(df["id"].dtype)
    res[["lon", "lat"]] = res[["lon", "lat"]].astype(float)
    return df.merge(res, on="id", how="left")


def tag_hazard(df, fhsz):
    """Point-in-polygon join. Adds haz_class, hazard_source, n_polygons.

    Rows that did not geocode get haz_class NaN. Points inside no study-area county get OutsideStudyArea.
    If a point falls in several polygons (SRA/LRA overlap), the first class in CLASS_ORDER wins, and n_polygons shows it.
    """
    ok = df.dropna(subset=["lon", "lat"])
    pts = gpd.GeoDataFrame(ok, geometry=gpd.points_from_xy(ok["lon"], ok["lat"]), crs=4326).to_crs(CRS_AREA)
    joined = gpd.sjoin(pts, fhsz[["haz_class", "source", "geometry"]], how="left", predicate="within")
    joined["n_polygons"] = joined.groupby("id")["haz_class"].transform("count")
    joined["haz_class"] = joined["haz_class"].fillna("OutsideStudyArea")
    joined["rank"] = joined["haz_class"].map({c: i for i, c in enumerate(CLASS_ORDER + ["OutsideStudyArea"])})
    best = joined.sort_values("rank").drop_duplicates("id")[["id", "haz_class", "source", "n_polygons"]]
    return df.merge(best.rename(columns={"source": "hazard_source"}), on="id", how="left")


if __name__ == "__main__":
    vintage = sys.argv[1] if len(sys.argv) > 1 else "current"
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("sample_addresses.csv")
    layer = RAW.parent / "clean" / f"fhsz_combined_{vintage}.gpkg"
    if not layer.exists():
        sys.exit(f"{layer.name} not found. Run: python 05_combine_fhsz.py {vintage}")
    out = tag_hazard(geocode(pd.read_csv(src, dtype={"zip": str})), gpd.read_file(layer))
    dest = RAW.parent / "clean" / f"sample_with_hazard_{vintage}.csv"
    out.to_csv(dest, index=False)
    print(out[["id", "street", "city", "geocode_status", "lon", "lat", "haz_class", "hazard_source", "n_polygons"]].to_string(index=False))
    print(f"\ngeocode match rate: {(out.geocode_status == 'Match').mean():.0%}. Saved {dest}")
    # Self-check for the sample file: the fake address must fail, and every geocoded row must get a class.
    if src.name == "sample_addresses.csv":
        assert out.loc[out.id == 8, "geocode_status"].iloc[0] != "Match", "fake address should not geocode"
        assert out.loc[out.geocode_status == "Match", "haz_class"].notna().all(), "geocoded rows must get a hazard class"
        assert (out.loc[out.id == 9, "haz_class"] == "OutsideStudyArea").all(), "Sacramento should be outside the study area"
        print("pipeline self-check passed")
