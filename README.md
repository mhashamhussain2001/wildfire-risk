# Is Wildfire Risk Priced into Northern California Home Values?

Capstone project, MS Data Science and Analytics, California State University, Chico. Study area: Butte, Shasta and Tehama counties, California. Home sales 2014 to 2023.

**Status:** the data pipeline and models are built and tested on sample data. Home sales data is not yet acquired.

## Research questions
1. Do homes in High or Very High CAL FIRE Fire Hazard Severity Zones (FHSZ) sell for less than comparable homes outside those zones?
2. Did that price gap change after the November 2018 Camp Fire? This is tested with a difference-in-differences design.

## Data sources
Full URLs and download dates are logged in `data/raw/SOURCES.md` (written by the download scripts).

| Data | Source | Script |
|---|---|---|
| Fire Hazard Severity Zones (State and Local Responsibility Areas) | CAL FIRE ArcGIS services | `src/01_download_fhsz.py` |
| 2018 Camp Fire perimeter | CAL FIRE FRAP 2018 fire perimeters (NIFC as cross-check) | `src/02_download_camp_fire.py` |
| Census tract boundaries (2010 grid) | Census TIGER/Line 2018 | `src/03_download_tiger_tracts.py` |
| Tract income and population | Census ACS 2014-2018 5-year Summary File (no key needed) | `src/04_download_acs.py` |
| Pre-2018 FHSZ maps (2007 SRA, 2007 draft LRA, 2008 recommended LRA) | CAL FIRE FRAP files, Internet Archive capture of 23 Dec 2016 | `src/01b_download_fhsz_pre2018.py` |
| City points, school district boundaries, 2017-18 test scores | Census Gazetteer and TIGER/Line 2018, CAASPP research file | `src/03b_download_controls.py` |
| County parcel points (APN and location) | Butte, Shasta and Tehama county GIS parcel layers | `src/03c_download_parcels.py` |
| Tract house price index (fallback outcome) | FHFA annual HPI, census tracts | `src/04b_download_fhfa_tract_hpi.py` |
| Home sales, 2014 to 2023 | Not yet acquired. Planned source: Zillow ZTRAX (ICPSR 39652, restricted access) | none |

## Hazard zone layers
The 2024 and 2025 maps were drawn after the Camp Fire, so the main analysis uses zones as they stood before it.
`05_combine_fhsz.py` builds three layers in `data/clean/`:
1. `pre2018`: SRA zones adopted 7 Nov 2007, plus CAL FIRE's 2008 recommended Very High zones in LRA. Inside cities this layer only knows "Very High" or "not Very High".
2. `pre2018draft`: the same SRA zones, plus the September 2007 draft LRA map, which gives city land a full class. The draft was never adopted.
3. `current`: the 2024 SRA and 2025 LRA maps. Robustness check only.

## Folder layout
```
data/raw/      downloaded source files, one subfolder per source (not tracked by git, except SOURCES.md)
data/clean/    cleaned and merged data (not tracked by git)
notebooks/     Jupyter notebooks (01_data_inventory.ipynb)
src/           download and processing scripts
outputs/       figures and tables
```

## Reproduce the environment
Requires Python 3.12 or newer. From the project root, in PowerShell:
```
py -3.14 -m venv .venv          # or any Python 3.12+ you have
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Download the data (run from the `src` folder):
```
cd src
python 01_download_fhsz.py
python 01b_download_fhsz_pre2018.py
python 02_download_camp_fire.py
python 03_download_tiger_tracts.py
python 03b_download_controls.py
python 03c_download_parcels.py
python 04_download_acs.py
python 04b_download_fhfa_tract_hpi.py
python 05_combine_fhsz.py pre2018        # combines SRA + LRA, prints area by class per county
python 05_combine_fhsz.py pre2018draft
python 05_combine_fhsz.py current
python 06_geocode_and_join_sample.py     # tests geocoding + hazard join on src/sample_addresses.csv
python 07_build_analysis_dataset.py      # full merge on src/sample_sales_FAKE.csv (made-up prices, test only)
python 07_build_analysis_dataset.py path\to\real_sales.csv   # once sales data exists
python 08_models.py --selftest           # checks the regression code on simulated sales
python 08_models.py                      # RQ1 and RQ2 models on the real dataset
```
Then open `notebooks/01_data_inventory.ipynb` with `jupyter notebook`.
