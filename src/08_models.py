"""RQ1 baseline regression and RQ2 difference-in-differences on the analysis dataset.

Usage (from the src folder):
    python 08_models.py                      # runs on data/clean/analysis_dataset.csv
    python 08_models.py --selftest           # checks the code recovers effects planted in simulated data
    python 08_models.py --hazard haz_current # use a different hazard column (default haz_pre2018)

Outcome: log sale price, so a coefficient b means roughly 100*b percent (exactly 100*(exp(b)-1)).
Treated: High or Very High. The comparison group is NOT chosen here. Both options are run side by side:
    "Moderate only"            homes in Moderate zones
    "Moderate + unrated"       Moderate plus NonWildland, Urban Unzoned and Unzoned land
Controls: log sqft, beds, age, log lot size, distance to nearest city, school score, log tract median income.
Time: one fixed effect per sale year-month. This covers both year and month effects, and it also absorbs the
post-Camp-Fire indicator, so the DiD model only shows the treated x post interaction.
Standard errors are clustered by census tract, because homes in the same tract share unmeasured traits.

Sample variants (the post-fire housing shortage question) are printed too:
    all sales | drop homes inside the Camp Fire perimeter | drop the acute period Nov 2018 to Dec 2019 |
    Shasta and Tehama only
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

CLEAN = Path(__file__).resolve().parents[1] / "data" / "clean"
TREATED = ["High", "Very High"]
COMPARISONS = {"Moderate only": ["Moderate"],
               "Moderate + unrated": ["Moderate", "NonWildland", "Urban Unzoned", "Unzoned"]}
CONTROLS = "np.log(sqft) + beds + age + np.log(lot_sqft) + dist_city_km + school_pct_met + np.log(median_hh_income)"
NEEDED = ["log_price", "sqft", "beds", "age", "lot_sqft", "dist_city_km", "school_pct_met", "median_hh_income", "tract_geoid"]


def samples(df):
    acute = (df.sale_date >= "2018-11-08") & (df.sale_date < "2020-01-01")
    return {"all sales": df,
            "drop burned area": df[df.in_camp_perimeter == 0],
            "drop Nov 2018-Dec 2019": df[~acute],
            "Shasta + Tehama only": df[df.county.isin(["Shasta", "Tehama"])]}


def fit(df, formula, term):
    m = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["tract_geoid"]})
    b, se, p = m.params[term], m.bse[term], m.pvalues[term]
    return {"coef": b, "pct": 100 * (np.exp(b) - 1), "se": se, "p": p, "n": int(m.nobs)}


def run(df, hazard):
    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["ym"] = df.sale_date.dt.strftime("%Y-%m")
    df = df.dropna(subset=NEEDED + [hazard])
    rows = []
    for comp_name, comp in COMPARISONS.items():
        d = df[df[hazard].isin(TREATED + comp)].copy()
        d["treated"] = d[hazard].isin(TREATED).astype(int)
        for samp_name, s in samples(d).items():
            if s.treated.nunique() < 2 or len(s) < 50:
                continue
            rq1 = fit(s, f"log_price ~ treated + {CONTROLS} + C(ym)", "treated")
            rq2 = fit(s, f"log_price ~ treated + treated:post_camp_fire + {CONTROLS} + C(ym)", "treated:post_camp_fire")
            rows += [{"comparison": comp_name, "sample": samp_name, "model": "RQ1 baseline (treated)", **rq1},
                     {"comparison": comp_name, "sample": samp_name, "model": "RQ2 DiD (treated x post)", **rq2}]
    return pd.DataFrame(rows)


def simulate(n=6000, seed=0, rq1=-0.06, did=-0.04):
    """Fake sales with a known treated effect (rq1) and post-fire change (did). Only for the self-test."""
    rng = np.random.default_rng(seed)
    tract = rng.integers(0, 80, n)
    hz = rng.choice(["Very High", "High", "Moderate", "Unzoned", "NonWildland"], n, p=[.2, .15, .25, .3, .1])
    date = pd.to_datetime("2014-01-01") + pd.to_timedelta(rng.integers(0, 3650, n), "D")
    df = pd.DataFrame({"tract_geoid": tract.astype(str), "haz_pre2018": hz, "sale_date": date,
                       "sqft": rng.uniform(800, 3500, n), "beds": rng.integers(1, 6, n), "age": rng.integers(0, 90, n),
                       "lot_sqft": rng.uniform(3000, 40000, n), "dist_city_km": rng.uniform(0, 40, n),
                       "school_pct_met": rng.uniform(20, 70, n), "median_hh_income": rng.uniform(30000, 90000, n),
                       "in_camp_perimeter": rng.binomial(1, .05, n), "county": rng.choice(["Butte", "Shasta", "Tehama"], n)})
    df["post_camp_fire"] = (df.sale_date >= "2018-11-08").astype(int)
    t = df.haz_pre2018.isin(TREATED).astype(int)
    tract_effect = rng.normal(0, .1, 80)[tract]
    df["log_price"] = (11 + .6 * np.log(df.sqft) - .003 * df.age - .005 * df.dist_city_km + .004 * df.school_pct_met
                       + .03 * (df.sale_date.dt.year - 2014) + rq1 * t + did * t * df.post_camp_fire
                       + tract_effect + rng.normal(0, .15, n))
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hazard", default="haz_pre2018")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    pd.options.display.float_format = "{:,.3f}".format
    if a.selftest:
        res = run(simulate(), "haz_pre2018")
        print(res.to_string(index=False))
        base = res[(res["sample"] == "all sales")].set_index(["comparison", "model"])["coef"]
        for comp in COMPARISONS:
            assert abs(base[(comp, "RQ1 baseline (treated)")] - (-0.06 + -0.04 * 0.5)) < 0.03, "RQ1 should be near the average gap"
            assert abs(base[(comp, "RQ2 DiD (treated x post)")] - (-0.04)) < 0.02, "DiD should recover the planted -0.04"
        print("\nself-test passed: planted effects recovered")
    else:
        src = CLEAN / "analysis_dataset.csv"
        if not src.exists():
            raise SystemExit(f"{src} not found. Build it first: python 07_build_analysis_dataset.py path\\to\\sales.csv")
        res = run(pd.read_csv(src, dtype={"tract_geoid": str}), a.hazard)
        print(f"Hazard column: {a.hazard}\n" + res.to_string(index=False))
        out = Path(__file__).resolve().parents[1] / "outputs" / f"model_results_{a.hazard}.csv"
        res.to_csv(out, index=False)
        print(f"\nSaved {out}")
