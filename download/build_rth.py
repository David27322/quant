import sys, glob, pandas as pd

# Usage: python build_rth.py "ndx_*.csv" usa100_rth_only.csv
pattern = sys.argv[1] if len(sys.argv) > 1 else "ndx_*.csv"
dst     = sys.argv[2] if len(sys.argv) > 2 else "usa100_rth_only.csv"

files = sorted(glob.glob(pattern))
assert files, f"No files matched {pattern}"
print(f"Combining {len(files)} files: {files}")

# 1) read + stack
frames = [pd.read_csv(f) for f in files]
df = pd.concat(frames, ignore_index=True)
ts_col = df.columns[0]                      # 'timestamp'

# 2) parse as UTC (pulled WITHOUT --time-zone), convert to NY
ts_utc = pd.to_datetime(df[ts_col], utc=True)
ts_ny  = ts_utc.dt.tz_convert("America/New_York")

# 3) sort + drop exact-duplicate timestamps (year-boundary safety)
df["_ny"] = ts_ny
df = df.sort_values("_ny").drop_duplicates(subset="_ny", keep="first")
ts_ny = df["_ny"]

# 4) RTH (09:30–16:00 NY) + weekdays only
mins = ts_ny.dt.hour * 60 + ts_ny.dt.minute
mask = (mins >= 9*60+30) & (mins <= 16*60) & (ts_ny.dt.dayofweek < 5)

out = df[mask].copy()
out[ts_col] = out["_ny"].dt.strftime("%Y-%m-%d %H:%M")  # NY-local string
out = out.drop(columns="_ny")
out.to_csv(dst, index=False)
print(f"{len(df)} combined rows -> {len(out)} RTH rows -> {dst}")