"""Download the 2018 Camp Fire perimeter (CAL FIRE FRAP, Butte Unit) as GeoJSON."""
from common import RAW, arcgis_geojson, log_source

URL = "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/2018_California_Fire_Perimeters_View/FeatureServer/0"
# The layer also has a tiny 13 acre "CAMP" fire in San Luis Obispo (unit SLU), so filter by Butte Unit (BTU).
arcgis_geojson(URL, RAW / "camp_fire" / "camp_fire_2018.geojson", where="FIRE_NAME='CAMP' AND UNIT_ID='BTU'")
log_source("Camp Fire 2018 perimeter", URL,
           "CAL FIRE FRAP 2018 fire perimeters, FIRE_NAME='CAMP', UNIT_ID='BTU'. About 153,336 acres, alarm date 2018-11-08. "
           "Cross-check source: NIFC Interagency Fire Perimeter History (same fire, INCIDENT='Camp', FIRE_YEAR=2018).")
