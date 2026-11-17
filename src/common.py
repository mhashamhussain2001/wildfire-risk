"""Shared helpers: paging through ArcGIS REST layers and logging provenance to SOURCES.md."""
import datetime
import json
import re
from pathlib import Path

import time

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
# Rough bounding box (lon/lat, WGS84) around Butte, Shasta and Tehama counties.
STUDY_BBOX = (-123.2, 39.3, -120.9, 41.2)


def arcgis_geojson(layer_url, out_path, where="1=1", bbox=None, out_fields="*"):
    """Download every feature of an ArcGIS REST layer as GeoJSON (WGS84), paging past the record limit."""
    params = {"where": where, "outFields": out_fields, "outSR": 4326, "f": "geojson",
              "returnGeometry": "true", "resultRecordCount": 500}
    if bbox:
        params.update(geometry=",".join(map(str, bbox)), geometryType="esriGeometryEnvelope",
                      inSR=4326, spatialRel="esriSpatialRelIntersects")
    features, offset = [], 0
    while True:
        for attempt in range(5):  # the server sometimes resets connections, so retry with a growing pause
            try:
                r = requests.get(f"{layer_url}/query", params={**params, "resultOffset": offset}, timeout=120)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        batch = data.get("features", [])
        features += batch
        if not batch:
            break
        offset += len(batch)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"{out_path.name}: {len(features)} features")
    return len(features)


def log_source(title, url, notes):
    """Add (or replace) a section for `title` in data/raw/SOURCES.md with today's download date."""
    path = RAW / "SOURCES.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# Data sources\n"
    section = f"\n## {title}\n- URL: {url}\n- Downloaded: {datetime.date.today()}\n- Notes: {notes}\n"
    pattern = re.compile(rf"\n## {re.escape(title)}\n.*?(?=\n## |\Z)", re.S)
    text = pattern.sub(lambda m: section.rstrip("\n"), text) if pattern.search(text) else text.rstrip("\n") + "\n" + section
    path.write_text(text, encoding="utf-8")
