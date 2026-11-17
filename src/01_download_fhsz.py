"""Download CAL FIRE Fire Hazard Severity Zones (SRA and LRA) for the study-area bounding box."""
from common import RAW, STUDY_BBOX, arcgis_geojson, log_source

HOST = "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services"
LAYERS = {
    "fhsz_sra_2023map.geojson": (f"{HOST}/FHSZSRA_23_3/FeatureServer/0",
        "FHSZ State Responsibility Area. Map dated 2023-09-29, adopted 2024-01-31, effective 2024-04-01. "
        "Zones: 1 Moderate, 2 High, 3 Very High. SRA only; cities and other Local Responsibility Areas are not in this layer."),
    "fhsz_lra_2025map.geojson": (f"{HOST}/FHSALRA25_v1_All/FeatureServer/0",
        "FHSZ Local Responsibility Area. Map dated 2025-03-24, all phases of the LRA rollout. LRA only."),
}

for name, (url, notes) in LAYERS.items():
    arcgis_geojson(url, RAW / "fhsz" / name, bbox=STUDY_BBOX)
    log_source(f"CAL FIRE FHSZ: {name}", url,
               notes + " Clipped to a bounding box around Butte/Shasta/Tehama only (not yet to county lines). "
               "Both maps were produced AFTER the 2018 Camp Fire.")
