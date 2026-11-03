"""Reconstruct supplied UTC -> New York pipeline for the original 2023 file."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root = Path("/data")
source = root / "raw/ndx_2023.csv"
raw = pd.read_csv(source)
master = pd.read_csv(root / "raw/usa100_clean.csv")
utc = pd.to_datetime(raw["timestamp"], utc=True, errors="raise")
ny = utc.dt.tz_convert("America/New_York")
assert not utc.duplicated().any()
assert raw[["open", "high", "low", "close"]].notna().all().all()
assert (raw["high"] >= raw[["open", "low", "close"]].max(axis=1)).all()
assert (raw["low"] <= raw[["open", "high", "close"]].min(axis=1)).all()
mins = ny.dt.hour * 60 + ny.dt.minute
mask = mins.between(570, 960) & (ny.dt.dayofweek < 5)
rth = raw.loc[mask].copy()
rth["timestamp"] = ny.loc[mask].dt.strftime("%Y-%m-%d %H:%M")
rth["date"] = rth["timestamp"].str[:10]
span = rth.groupby("date").agg(hi=("high", "max"), lo=("low", "min"))
keep = set(span.index[span.hi != span.lo])
rebuilt = rth[rth.date.isin(keep)].drop(columns="date").sort_values("timestamp")
reference = master[master.timestamp.str.startswith("2023-")].sort_values("timestamp")
joined = rebuilt.merge(reference, on="timestamp", how="outer",
                       suffixes=("_rebuilt", "_master"), indicator=True,
                       validate="one_to_one")
both = joined["_merge"] == "both"
cols = ["open", "high", "low", "close"]
delta = np.column_stack([
    (joined.loc[both, c + "_rebuilt"] - joined.loc[both, c + "_master"]).to_numpy()
    for c in cols
])
mismatch = (delta != 0).any(axis=1)
out = {
    "scope": "2023 only; source UTC interpretation supplied by user",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_rows": len(raw),
    "source_duplicate_timestamps": int(utc.duplicated().sum()),
    "raw_utc_minute_intervals_all_60_seconds": bool(
        (utc.sort_values().diff().dropna().dt.total_seconds() == 60).all()),
    "rebuilt_rows": len(rebuilt),
    "master_2023_rows": len(reference),
    "rebuilt_only_rows": int((joined["_merge"] == "left_only").sum()),
    "master_only_rows": int((joined["_merge"] == "right_only").sum()),
    "different_OHLC_rows": int(mismatch.sum()),
    "max_absolute_price_difference": float(np.max(np.abs(delta))) if delta.size else None,
    "exact_match": bool(len(rebuilt) == len(reference) and both.all() and not mismatch.any()),
    "example_winter": {"utc": "2023-01-03 14:30", "ny": str(pd.Timestamp("2023-01-03 14:30", tz="UTC").tz_convert("America/New_York"))},
    "example_summer": {"utc": "2023-07-05 13:30", "ny": str(pd.Timestamp("2023-07-05 13:30", tz="UTC").tz_convert("America/New_York"))},
    "other_years_independently_verified": False,
}
# Independent match check without the merge, using aligned timestamp indices.
if out["exact_match"]:
    a = rebuilt.set_index("timestamp")[cols].sort_index()
    b = reference.set_index("timestamp")[cols].sort_index()
    pd.testing.assert_frame_equal(a, b)
(root / "analysis/source_timezone_validation.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))