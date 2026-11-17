"""Load FHSZ layers and combine State and Local Responsibility Area maps into one layer.

Three vintages are supported:
  "current"       the 2024 SRA map and 2025 LRA map in data/raw/fhsz/ (made AFTER the Camp Fire; robustness layer)
  "pre2018"       the SRA map adopted 7 Nov 2007 (fhszs06_3) plus CAL FIRE's 2008 recommended Very High zones in
                  LRA (fhszl06_3). These are the designations in place before the fire. LRA has Very High ONLY.
  "pre2018draft"  the same SRA map plus the September 2007 DRAFT LRA map (fhszl06_1), which gives every LRA
                  parcel a class (Moderate/High/Very High/NonWildland/Urban Unzoned). The draft was never adopted.
                  It is a hazard measure for city homes, not a legal designation.
Pre-2018 files are in data/raw/fhsz_pre2018/ (see 01b_download_fhsz_pre2018.py).

Every layer is returned in one schema: source (SRA/LRA/none), vintage, haz_class, geometry (EPSG:3310, meters).
"""
import geopandas as gpd
import pandas as pd

from common import RAW, STUDY_BBOX

CRS_AREA = "EPSG:3310"  # California Albers: equal-area, so .area is in square meters
COUNTIES = {"007": "Butte", "089": "Shasta", "103": "Tehama"}
# Display order. The tie-break for a point inside two overlapping polygons also uses this order (first wins).
CLASS_ORDER = ["Very High", "High", "Moderate", "NonWildland", "Urban Unzoned", "Unzoned"]
CLASS_MAP = {"1": "Moderate", "2": "High", "3": "Very High", "moderate": "Moderate", "high": "High",
             "very high": "Very High", "nonwildland": "NonWildland", "non-wildland": "NonWildland",
             "non-wildland/non-urban": "NonWildland", "urban unzoned": "Urban Unzoned"}
# Column holding the hazard class differs by file. First one present wins. Old files are expected to use HAZ_CLASS.
CLASS_COLUMNS = ["FHSZ_Description", "HAZ_CLASS", "HAZ_CODE", "FHSZ"]

PRE2018_HELP = "Pre-2018 FHSZ files missing or incomplete in {d}. Run: python 01b_download_fhsz_pre2018.py"


def normalize_class(values):
    """Map raw hazard labels or codes to Moderate/High/Very High/NonWildland. Unknown values raise instead of being dropped."""
    key = values.astype(str).str.strip().str.lower().str.replace(r"\.0$", "", regex=True)
    out = key.map(CLASS_MAP)
    if out.isna().any():
        raise ValueError(f"Unrecognised hazard values: {sorted(key[out.isna()].unique())}")
    return out


def _prepare(gdf, source, vintage):
    col = next((c for c in CLASS_COLUMNS if c in gdf.columns), None)
    if col is None:
        raise ValueError(f"No hazard class column in {source} layer. Columns are {list(gdf.columns)}")
    xmin, ymin, xmax, ymax = STUDY_BBOX
    gdf = gdf.to_crs(4326).cx[xmin:xmax, ymin:ymax]  # statewide files: keep only the study-area bounding box
    out = gpd.GeoDataFrame({"source": source, "vintage": vintage, "haz_class": normalize_class(gdf[col])},
                           geometry=gdf.geometry.values, crs=4326).to_crs(CRS_AREA)
    out["geometry"] = out.geometry.make_valid()  # the raw files contain a few self-intersecting polygons
    out = out.explode(index_parts=False)
    return out[out.geom_type == "Polygon"].reset_index(drop=True)


def load_fhsz(vintage):
    """Return all SRA and LRA hazard polygons for a vintage as one GeoDataFrame."""
    if vintage == "current":
        parts = [(RAW / "fhsz" / "fhsz_sra_2023map.geojson", "SRA"), (RAW / "fhsz" / "fhsz_lra_2025map.geojson", "LRA")]
    elif vintage in ("pre2018", "pre2018draft"):
        folder = RAW / "fhsz_pre2018"
        lra_tag = "fhszl06_3" if vintage == "pre2018" else "fhszl06_1"  # recommended Very High vs full draft map
        parts = [(f, "SRA") for f in sorted(folder.glob("fhszs*.zip"))]
        parts += [(f, "LRA") for f in sorted(folder.glob(f"*{lra_tag}*.zip"))]
        if len(parts) != 4:  # one statewide SRA file + one LRA file per county
            raise FileNotFoundError(PRE2018_HELP.format(d=folder))
    else:
        raise ValueError("vintage must be 'current', 'pre2018' or 'pre2018draft'")
    layers = []
    for path, source in parts:
        gdf = gpd.read_file(f"zip://{path}" if path.suffix == ".zip" else path)
        if vintage == "pre2018draft" and source == "LRA":
            # The draft file also carries SRA and federal (FRA) land as context. Keep LRA rows only,
            # so SRA land is classed by the adopted SRA map and federal land stays Unzoned.
            gdf = gdf[gdf["SRA"] == "LRA"]
        layers.append(_prepare(gdf, source, vintage))
    return pd.concat(layers, ignore_index=True)


def load_counties():
    """County outlines (EPSG:3310) built by dissolving the 2018 TIGER tracts of Butte, Shasta and Tehama."""
    tracts = gpd.read_file(next((RAW / "census" / "tiger_2018_ca_tracts").glob("*.shp")))
    counties = tracts[tracts["COUNTYFP"].isin(COUNTIES)].dissolve(by="COUNTYFP").reset_index()
    counties["county"] = counties["COUNTYFP"].map(COUNTIES)
    return counties[["county", "geometry"]].to_crs(CRS_AREA)


def combine(vintage):
    """Clip SRA and LRA to the three counties, add the unzoned remainder, and return (combined, overlap_km2).

    haz_class is one of Very High, High, Moderate, NonWildland, Urban Unzoned, Unzoned. Nothing is merged or dropped:
    NonWildland (an LRA class for built-up land with no wildland fuel) stays its own class, and Unzoned is
    every part of a county covered by no SRA or LRA polygon at all.
    """
    layers = load_fhsz(vintage)
    counties = load_counties()
    clipped = gpd.overlay(layers, counties, how="intersection", keep_geom_type=True)
    unzoned = counties.copy()
    unzoned["geometry"] = counties.geometry.difference(layers.geometry.union_all())
    unzoned = unzoned.assign(source="none", vintage=vintage, haz_class="Unzoned")
    combined = pd.concat([clipped, unzoned], ignore_index=True)
    combined = combined[~combined.is_empty]
    # SRA and LRA should not overlap. Measure it so double counting is visible, not hidden.
    sra, lra = layers[layers.source == "SRA"], layers[layers.source == "LRA"]
    overlap = gpd.overlay(sra, lra, how="intersection", keep_geom_type=True).area.sum() / 1e6 if len(sra) and len(lra) else 0.0
    combined["area_km2"] = combined.area / 1e6
    return combined, overlap
