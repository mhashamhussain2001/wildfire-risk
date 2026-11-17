"""Turn a CSV of home sales into the analysis dataset: one row per sale with hazard zone and every control variable.

Usage (from the src folder):
    python 07_build_analysis_dataset.py [sales.csv]
Default input is src/sample_sales_FAKE.csv (real addresses of public buildings with MADE-UP prices, for testing only).

Input columns: id, street, city, state, zip, sale_price, sale_date (YYYY-MM-DD), sqft, beds, lot_sqft, year_built.
Output: data/clean/analysis_dataset.csv (or analysis_dataset_SAMPLE.csv for the fake file).

What is added to each sale:
  lon, lat, geocode_status        Census batch geocoder
  haz_pre2018                     2007 adopted SRA zones + 2008 recommended Very High in LRA (main treatment definition)
  haz_pre2018draft                same, but LRA classed by the never-adopted 2007 draft map (all classes inside cities)
  haz_current                     2024 SRA + 2025 LRA maps (drawn after the fire; robustness check only)
  county, tract_geoid             2018 TIGER tracts (2010 tract grid)
  median_hh_income, pop_density   ACS 2014-2018 tract values (empty until 04_download_acs.py has been run)
  nearest_city, dist_city_km      straight-line distance to the nearest incorporated city's Census internal point
  school_district, school_pct_met district-wide share of students meeting or exceeding standard, spring 2018 (CAASPP)
  in_camp_perimeter, dist_camp_km inside the Camp Fire perimeter, and straight-line distance to it (0 if inside)
  post_camp_fire                  1 if sold on or after 8 Nov 2018
  sale_year, sale_month, age, log_price

This script only builds columns. It does not choose the treated and comparison groups or drop any period.
"""
import importlib
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from common import RAW
from fhsz import COUNTIES, CRS_AREA

gj = importlib.import_module("06_geocode_and_join_sample")  # reuse geocode() and tag_hazard()
CLEAN = RAW.parent / "clean"
CAMP_FIRE_START = pd.Timestamp("2018-11-08")
CAASPP_COUNTY = {"04": "007", "45": "089", "52": "103"}  # CDE county code -> county FIPS
REQUIRED = ["id", "street", "city", "state", "zip", "sale_price", "sale_date", "sqft", "beds", "lot_sqft", "year_built"]


def norm_name(s):
    """Make district names comparable between TIGER and CAASPP ('Chico Unified School District' vs 'Chico Unified')."""
    # "elementary" is dropped too: TIGER and CAASPP disagree on it ('Thermalito Union' vs 'Thermalito Union Elementary')
    return (s.str.lower().str.replace("school district", "").str.replace("elementary", "").str.replace(r"[^a-z ]", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True).str.strip())


def district_scores():
    """Percent of students meeting or exceeding standard per district: mean of English and math, all students, all grades."""
    z = zipfile.ZipFile(RAW / "caaspp" / "sb_ca2018_all_csv_v3.zip")
    cols = ["County Code", "District Code", "School Code", "Subgroup ID", "Grade", "Test Id", "Percentage Standard Met and Above"]
    chunks = pd.read_csv(z.open("sb_ca2018_all_csv_v3.txt"), dtype=str, encoding="latin-1", usecols=cols, chunksize=500_000)
    keep = pd.concat(c[c["County Code"].isin(CAASPP_COUNTY) & (c["School Code"] == "0000000") & (c["District Code"] != "00000")
                       & (c["Subgroup ID"] == "1") & (c["Grade"] == "13")] for c in chunks)
    keep["pct"] = pd.to_numeric(keep["Percentage Standard Met and Above"], errors="coerce")  # '*' = too few students
    score = keep.groupby(["County Code", "District Code"])["pct"].mean().rename("school_pct_met").reset_index()
    ent = pd.read_csv(RAW / "caaspp" / "sb_ca2018entities_csv.zip", dtype=str, encoding="latin-1")
    ent = ent[ent["School Code"] == "0000000"][["County Code", "District Code", "District Name"]]
    score = score.merge(ent, on=["County Code", "District Code"])
    score["key"] = norm_name(score["District Name"])
    return score[["key", "school_pct_met"]].drop_duplicates("key")


def load_districts(counties):
    """Unified and elementary district polygons touching the study area, with their test score attached."""
    parts = []
    for kind in ("unsd", "elsd"):
        d = gpd.read_file(f"zip://{RAW / 'census' / f'tl_2018_06_{kind}.zip'}").to_crs(CRS_AREA)
        parts.append(d[d.intersects(counties.union_all())][["NAME", "geometry"]])
    d = pd.concat(parts, ignore_index=True).rename(columns={"NAME": "school_district"})
    d["key"] = norm_name(d["school_district"])
    d = d.merge(district_scores(), on="key", how="left").drop(columns="key")
    missing = sorted(d.loc[d.school_pct_met.isna(), "school_district"])
    if missing:
        # Expected for districts based in a neighbouring county that only touch the study area, and for very
        # small districts whose scores CAASPP hides for privacy.
        print(f"School districts with no test score matched ({len(missing)}): {missing}")
    return d


def build(sales):
    n0 = len(sales)
    df = gj.geocode(sales)
    for vintage in ("pre2018", "pre2018draft", "current"):
        tagged = gj.tag_hazard(df[["id", "lon", "lat"]], gpd.read_file(CLEAN / f"fhsz_combined_{vintage}.gpkg"))
        df = df.merge(tagged[["id", "haz_class"]].rename(columns={"haz_class": f"haz_{vintage}"}), on="id", how="left")

    ok = df.dropna(subset=["lon", "lat"])
    pts = gpd.GeoDataFrame(ok[["id"]], geometry=gpd.points_from_xy(ok["lon"], ok["lat"]), crs=4326).to_crs(CRS_AREA)

    # Census tract and county
    tracts = gpd.read_file(next((RAW / "census" / "tiger_2018_ca_tracts").glob("*.shp")))
    tracts = tracts[tracts["COUNTYFP"].isin(COUNTIES)].to_crs(CRS_AREA)
    tracts["county"] = tracts["COUNTYFP"].map(COUNTIES)
    tracts["tract_km2"] = tracts["ALAND"].astype(float) / 1e6
    acs_path = RAW / "census" / "acs5_2018_tracts.csv"
    if acs_path.exists():
        acs = pd.read_csv(acs_path, dtype={"GEOID": str})
        acs["median_hh_income"] = acs["median_hh_income"].where(acs["median_hh_income"] > 0)  # -666666666 = not available
        tracts = tracts.merge(acs[["GEOID", "median_hh_income", "total_pop"]], on="GEOID", how="left")
        tracts["pop_density"] = tracts["total_pop"] / tracts["tract_km2"]  # people per square km of land
    else:
        print("ACS file not found: median_hh_income and pop_density left empty. Run 04_download_acs.py (needs CENSUS_API_KEY).")
        tracts["median_hh_income"] = np.nan
        tracts["pop_density"] = np.nan
    j = gpd.sjoin(pts, tracts[["GEOID", "county", "median_hh_income", "pop_density", "geometry"]], how="left", predicate="within")
    out = j[["id", "county", "GEOID", "median_hh_income", "pop_density"]].rename(columns={"GEOID": "tract_geoid"})

    # Nearest incorporated city (Census Gazetteer internal point)
    gaz = pd.read_csv(RAW / "census" / "2018_gaz_place_06.txt", sep="\t")
    gaz.columns = gaz.columns.str.strip()
    gaz = gaz[gaz["FUNCSTAT"] == "A"]
    cities = gpd.GeoDataFrame({"nearest_city": gaz["NAME"].str.replace(r" (city|town)$", "", regex=True)},
                              geometry=gpd.points_from_xy(gaz["INTPTLONG"], gaz["INTPTLAT"]), crs=4326).to_crs(CRS_AREA)
    counties = tracts.dissolve(by="county").reset_index()[["county", "geometry"]]
    cities = cities[cities.within(counties.union_all())]
    j = gpd.sjoin_nearest(pts, cities, distance_col="dist_city_km").drop_duplicates("id")
    j["dist_city_km"] /= 1000
    out = out.merge(j[["id", "nearest_city", "dist_city_km"]], on="id", how="left")

    # School district: unified district, else the elementary district. High school districts are ignored,
    # so homes in elementary-district areas get the elementary score only. Add the scsd layer if both are wanted.
    j = gpd.sjoin(pts, load_districts(counties), how="left", predicate="within").drop_duplicates("id")
    out = out.merge(j[["id", "school_district", "school_pct_met"]], on="id", how="left")

    # Camp Fire perimeter
    camp = gpd.read_file(RAW / "camp_fire" / "camp_fire_2018.geojson").to_crs(CRS_AREA).union_all()
    pts["dist_camp_km"] = pts.distance(camp) / 1000
    pts["in_camp_perimeter"] = (pts["dist_camp_km"] == 0).astype(int)
    out = out.merge(pts[["id", "in_camp_perimeter", "dist_camp_km"]], on="id", how="left")

    df = df.merge(out, on="id", how="left")
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["post_camp_fire"] = (df["sale_date"] >= CAMP_FIRE_START).astype(int)
    df["sale_year"], df["sale_month"] = df["sale_date"].dt.year, df["sale_date"].dt.month
    df["age"] = df["sale_year"] - df["year_built"]
    df["log_price"] = np.log(df["sale_price"])

    assert len(df) == n0 and df["id"].is_unique, "joins must not add or drop sales"
    not_geocoded = df["lon"].isna().sum()
    outside = (df["lon"].notna() & df["county"].isna()).sum()
    print(f"\n{n0} sales in. Not geocoded: {not_geocoded}. Geocoded but outside the three counties: {outside}. "
          f"Usable: {n0 - not_geocoded - outside}.")
    return df


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("sample_sales_FAKE.csv")
    sales = pd.read_csv(src, dtype={"zip": str})
    missing = [c for c in REQUIRED if c not in sales.columns]
    if missing:
        sys.exit(f"{src.name} is missing columns: {missing}")
    result = build(sales)
    dest = CLEAN / ("analysis_dataset_SAMPLE.csv" if "FAKE" in src.name else "analysis_dataset.csv")
    result.to_csv(dest, index=False)
    show = ["id", "city", "haz_pre2018", "haz_pre2018draft", "haz_current", "county", "nearest_city", "dist_city_km",
            "school_district", "school_pct_met", "in_camp_perimeter", "dist_camp_km", "post_camp_fire", "age"]
    pd.options.display.float_format = "{:,.1f}".format
    print(result[show].to_string(index=False))
    print(f"\nSaved {dest}")
    if "FAKE" in src.name:  # self-check on the sample
        r = result.set_index("id")
        assert r.loc[2, "haz_pre2018"] == "Very High" and r.loc[2, "in_camp_perimeter"] == 1, "Paradise Town Hall is Very High and burned"
        assert r.loc[3, "nearest_city"] == "Chico" and r.loc[3, "dist_city_km"] < 10, "Chico address should be near Chico"
        assert pd.isna(r.loc[9, "county"]), "Sacramento is outside the study area"
        assert r.loc[1, "post_camp_fire"] == 0 and r.loc[2, "post_camp_fire"] == 1, "post flag follows the sale date"
        print("self-check passed")
