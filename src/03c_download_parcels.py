"""Download county parcel maps (parcel number + location) for Butte, Shasta and Tehama.

County sales lists identify homes by Assessor's Parcel Number (APN), not by coordinates. These public parcel
layers let a sale be placed on the map by its APN, with no address geocoding.
Only parcel number, address and shape are requested. Owner names are deliberately left out.
Output: data/clean/parcel_points.gpkg, one point per parcel (a point inside the parcel), columns county, apn, situs.
"""
import geopandas as gpd
import pandas as pd

from common import RAW, arcgis_geojson, log_source
from fhsz import CRS_AREA

LAYERS = {  # county: (layer URL, fields to request, APN field, address field)
    "Butte": ("https://services.arcgis.com/3t3QfTXFRFX44zo8/arcgis/rest/services/Butte_County_Parcel_Public_Data/FeatureServer/0",
              "APN,SITUS", "APN", "SITUS"),
    "Shasta": ("https://gis.shastacounty.gov/arcgis/rest/services/OpenData/ParcelAssesseeSitus/MapServer/0",
               "APN,Situs_Address", "APN", "Situs_Address"),
    "Tehama": ("https://services2.arcgis.com/3iNbxbY9zhyxPvde/arcgis/rest/services/PublicParcelsAGOL/FeatureServer/0",
               "PARCELID,Situs1_1", "PARCELID", "Situs1_1"),
}

parts = []
for county, (url, fields, apn, situs) in LAYERS.items():
    path = RAW / "parcels" / f"parcels_{county.lower()}.geojson"
    if not path.exists():
        arcgis_geojson(url, path, out_fields=fields)
    g = gpd.read_file(path).to_crs(CRS_AREA)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    pts = gpd.GeoDataFrame({"county": county, "apn": g[apn].astype(str).str.strip(), "situs": g[situs]},
                           geometry=g.geometry.representative_point(), crs=CRS_AREA)
    # Butte's layer lists every parcel twice; Shasta and Tehama repeat a parcel once per address on it.
    # Keep one point per APN (same parcel, same point).
    pts = pts.drop_duplicates("apn")
    parts.append(pts)
    log_source(f"Parcels, {county} County", url,
               f"Public county parcel layer, fields {fields} only (no owner names). Current parcels, not historical: "
               "parcels split or merged since a sale will not match by APN.")
    print(f"{county}: {len(g):,} rows, {len(pts):,} unique parcels")

out = RAW.parent / "clean" / "parcel_points.gpkg"
pd.concat(parts, ignore_index=True).to_file(out, driver="GPKG")
print(f"Saved {out}")
