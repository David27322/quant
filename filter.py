import sys
import pandas as pd

src = sys.argv[1] if len(sys.argv) > 1 else "usa100.csv"
dst = sys.argv[2] if len(sys.argv) > 2 else "usa100_rth_only.csv"

df = pd.read_csv(src)
ts_col = df.columns[0]

ts_utc = pd.to_datetime(df[ts_col], utc=True)
ts_ny  = ts_utc.dt.tz_convert("America/New_York")

df[ts_col] = ts_ny.dt.strftime("%Y-%m-%d %H:%M")   # rewrite as NY time

mins = ts_ny.dt.hour * 60 + ts_ny.dt.minute
START, END = 9*60 + 30, 16*60                      # 09:30–16:00 inclusive

rth = df[(mins >= START) & (mins <= END)].copy()
rth.to_csv(dst, index=False)
print(f"{len(df)} rows -> {len(rth)} RTH rows -> {dst}")