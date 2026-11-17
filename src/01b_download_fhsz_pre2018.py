"""Download the pre-Camp-Fire FHSZ files: SRA map adopted 7 Nov 2007, plus the LRA draft (2007) and recommended (2008) maps.

CAL FIRE's own site blocks scripts and no longer hosts these old files, so they come from the Internet Archive
copies of frap.fire.ca.gov captured on 23 Dec 2016. That capture date is almost two years before the Camp Fire,
which shows these are the zones as they stood before the fire.
"""
import requests

from common import RAW, log_source

BASE = "http://frap.fire.ca.gov/webdata/data"
FILES = {  # output name: (Wayback timestamp, original path)
    "fhszs.sn_wayback20161223.zip": ("20161223010403", "statewide/fhszs.sn.zip"),
    "butte_fhszl06_1.4sn_wayback20161223.zip": ("20161223010723", "butte/fhszl06_1.4sn.zip"),
    "butte_fhszl06_3.4ns_wayback20161223.zip": ("20161223010719", "butte/fhszl06_3.4ns.zip"),
    "shasta_fhszl06_1.45sn_wayback20161223.zip": ("20161223010622", "shasta/fhszl06_1.45sn.zip"),
    "shasta_fhszl06_3.45ns_wayback20161223.zip": ("20161223010618", "shasta/fhszl06_3.45ns.zip"),
    "tehama_fhszl06_1.52sn_wayback20161223.zip": ("20161223010655", "tehama/fhszl06_1.52sn.zip"),
    "tehama_fhszl06_3.52ns_wayback20161223.zip": ("20161223010650", "tehama/fhszl06_3.52ns.zip"),
}
out_dir = RAW / "fhsz_pre2018"
out_dir.mkdir(parents=True, exist_ok=True)
for name, (stamp, path) in FILES.items():
    dest = out_dir / name
    if not dest.exists():
        r = requests.get(f"http://web.archive.org/web/{stamp}id_/{BASE}/{path}", timeout=300)  # id_ = original bytes
        r.raise_for_status()
        dest.write_bytes(r.content)
    print(f"{name}: {dest.stat().st_size:,} bytes")
log_source("Pre-2018 FHSZ maps", "http://web.archive.org/web/2016*/frap.fire.ca.gov/webdata/data/*",
           "Internet Archive captures (23 Dec 2016) of CAL FIRE FRAP downloads. "
           "fhszs06_3: SRA zones adopted by CAL FIRE on 7 Nov 2007 (statewide). "
           "fhszl06_3 (Butte, Shasta, Tehama): CAL FIRE final recommended Very High zones in LRA, published 2008; "
           "the file metadata says local adoption must be checked with each city. "
           "fhszl06_1 (same counties): September 2007 DRAFT LRA map with all classes; never adopted. "
           "The 2024 and 2025 maps in data/raw/fhsz are the post-fire robustness layer.")
