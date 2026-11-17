# Data sources

## CAL FIRE FHSZ: fhsz_sra_2023map.geojson
- URL: https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA_23_3/FeatureServer/0
- Downloaded: 2026-10-13
- Notes: FHSZ State Responsibility Area. Map dated 2023-09-29, adopted 2024-01-31, effective 2024-04-01. Zones: 1 Moderate, 2 High, 3 Very High. SRA only; cities and other Local Responsibility Areas are not in this layer. Clipped to a bounding box around Butte/Shasta/Tehama only (not yet to county lines). Both maps were produced AFTER the 2018 Camp Fire.
## CAL FIRE FHSZ: fhsz_lra_2025map.geojson
- URL: https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0
- Downloaded: 2026-10-13
- Notes: FHSZ Local Responsibility Area. Map dated 2025-03-24, all phases of the LRA rollout. LRA only. Clipped to a bounding box around Butte/Shasta/Tehama only (not yet to county lines). Both maps were produced AFTER the 2018 Camp Fire.
## Camp Fire 2018 perimeter
- URL: https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/2018_California_Fire_Perimeters_View/FeatureServer/0
- Downloaded: 2026-10-13
- Notes: CAL FIRE FRAP 2018 fire perimeters, FIRE_NAME='CAMP', UNIT_ID='BTU'. About 153,336 acres, alarm date 2018-11-08. Cross-check source: NIFC Interagency Fire Perimeter History (same fire, INCIDENT='Camp', FIRE_YEAR=2018).

## TIGER/Line 2018 California census tracts
- URL: https://www2.census.gov/geo/tiger/TIGER2018/TRACT/tl_2018_06_tract.zip
- Downloaded: 2026-10-13
- Notes: Statewide shapefile (all CA tracts). Filter to COUNTYFP 007 (Butte), 089 (Shasta), 103 (Tehama) later. ALAND column (square meters) gives land area for population density.

## Home sales (NOT DOWNLOADED)
- Not yet acquired. Planned source: Zillow ZTRAX (ICPSR 39652), restricted access by application.
- Redfin was not used: its Terms of Use (section 2.3.5) prohibit automated collection, and its export is capped at 350 homes.

## Pre-2018 FHSZ maps
- URL: http://web.archive.org/web/2016*/frap.fire.ca.gov/webdata/data/*
- Downloaded: 2026-11-09
- Notes: Internet Archive captures (23 Dec 2016) of CAL FIRE FRAP downloads. fhszs06_3: SRA zones adopted by CAL FIRE on 7 Nov 2007 (statewide). fhszl06_3 (Butte, Shasta, Tehama): CAL FIRE final recommended Very High zones in LRA, published 2008; the file metadata says local adoption must be checked with each city. fhszl06_1 (same counties): September 2007 DRAFT LRA map with all classes; never adopted. The 2024 and 2025 maps in data/raw/fhsz are the post-fire robustness layer.

## Census Gazetteer 2018, California places
- URL: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2018_Gazetteer/2018_gaz_place_06.txt
- Downloaded: 2026-11-09
- Notes: Tab-separated. INTPTLAT and INTPTLONG are the internal point of each place. FUNCSTAT 'A' marks active incorporated cities; 'S' marks census designated places.

## TIGER/Line 2018 unified school districts, California
- URL: https://www2.census.gov/geo/tiger/TIGER2018/UNSD/tl_2018_06_unsd.zip
- Downloaded: 2026-11-09
- Notes: Statewide shapefile, read straight from the zip.

## TIGER/Line 2018 elementary school districts, California
- URL: https://www2.census.gov/geo/tiger/TIGER2018/ELSD/tl_2018_06_elsd.zip
- Downloaded: 2026-11-09
- Notes: Statewide shapefile, read straight from the zip.

## TIGER/Line 2018 secondary school districts, California
- URL: https://www2.census.gov/geo/tiger/TIGER2018/SCSD/tl_2018_06_scsd.zip
- Downloaded: 2026-11-09
- Notes: Statewide shapefile, read straight from the zip.

## CAASPP 2017-18 Smarter Balanced research file (all entities)
- URL: https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca2018_all_csv_v3.zip
- Downloaded: 2026-11-09
- Notes: Statewide test results. District rows have School Code 0000000. Subgroup ID 1 = all students, Grade 13 = all grades, Test Id 1 = English language arts, 2 = mathematics.

## CAASPP 2017-18 entities file
- URL: https://caaspp-elpac.ets.org/caaspp/researchfiles/sb_ca2018entities_csv.zip
- Downloaded: 2026-11-09
- Notes: Names for the county, district and school codes in the research file.

## ACS 5-year 2018 (2014-2018) tract data
- URL: https://www2.census.gov/programs-surveys/acs/summary_file/2018/data/5_year_seq_by_state/California/Tracts_Block_Groups_Only
- Downloaded: 2026-11-09
- Notes: ACS Summary File, sequence files for California tracts. Tables B19013 (median household income, 2018 dollars) and B01003 (total population) for FIPS 06007, 06089, 06103. Empty income = no estimate published.

## FHFA annual house price index, census tracts
- URL: https://www.fhfa.gov/hpi/download/annual/hpi_at_tract.csv
- Downloaded: 2026-11-17
- Notes: Developmental annual repeat-sales index by 2010 census tract, filtered to Butte, Shasta, Tehama. Columns: hpi (base = first year), hpi1990, hpi2000, annual_change (percent). Fallback outcome only.

## Parcels, Butte County
- URL: https://services.arcgis.com/3t3QfTXFRFX44zo8/arcgis/rest/services/Butte_County_Parcel_Public_Data/FeatureServer/0
- Downloaded: 2026-11-17
- Notes: Public county parcel layer, fields APN,SITUS only (no owner names). Current parcels, not historical: parcels split or merged since a sale will not match by APN.
## Parcels, Shasta County
- URL: https://gis.shastacounty.gov/arcgis/rest/services/OpenData/ParcelAssesseeSitus/MapServer/0
- Downloaded: 2026-11-17
- Notes: Public county parcel layer, fields APN,Situs_Address only (no owner names). Current parcels, not historical: parcels split or merged since a sale will not match by APN.
## Parcels, Tehama County
- URL: https://services2.arcgis.com/3iNbxbY9zhyxPvde/arcgis/rest/services/PublicParcelsAGOL/FeatureServer/0
- Downloaded: 2026-11-17
- Notes: Public county parcel layer, fields PARCELID,Situs1_1 only (no owner names). Current parcels, not historical: parcels split or merged since a sale will not match by APN.