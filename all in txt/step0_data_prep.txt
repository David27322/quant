"""
Step 0 — NQ Futures Data Prep  (v2 — primary source: 2022-2025 1-min file)
===========================================================================
Primary source : NQ 1-min 2022-2025  (timestamp ET | open,high,low,close,volume,Vwap_RTH,Vwap_ETH)
Old files      : NQ_in_1_minute.csv, NQ_in_5_minute.csv  — left untouched, ignored.

What this produces (in data_clean/):
  NQ_1min_full.csv   — full Globex session, Backtrader-ready
  NQ_5min_full.csv   — resampled from 1-min
  NQ_15min_full.csv
  NQ_30min_full.csv
  NQ_1min_rth.csv    — RTH only (09:30–15:59 ET)
  NQ_5min_rth.csv
  NQ_15min_rth.csv
  NQ_30min_rth.csv

Usage:
  python step0_data_prep.py
  (run from the folder that contains your 1-min CSV)
"""

import os
import pandas as pd

# ── CONFIG ─────────────────────────────────────────────────────────────────────
INPUT_FILE  = "NQ_1min_2022_2025.csv"   # ← change to your exact filename if different
OUTPUT_DIR  = "data_clean"

RTH_START   = "09:30"
RTH_END     = "15:59"    # last 1-min bar whose open is still inside RTH

# ── LOAD & CLEAN ───────────────────────────────────────────────────────────────

def load_and_clean(filepath: str) -> pd.DataFrame:
    print(f"\n{'='*60}")
    print(f"Loading: {filepath}")
    print("(70 MB — may take 10-20 sec) ...")

    df = pd.read_csv(filepath)

    print(f"  Columns found    : {list(df.columns)}")

    # -- Normalise column names to lowercase, strip spaces
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # -- Detect timestamp column (handles 'timestamp et', 'datetime', 'date', etc.)
    ts_col = None
    for candidate in ["timestamp_et", "timestamp", "datetime", "date", "time"]:
        if candidate in df.columns:
            ts_col = candidate
            break
    if ts_col is None:
        raise ValueError(f"Cannot find timestamp column. Columns: {list(df.columns)}")
    print(f"  Timestamp column : '{ts_col}'")

    # -- Parse timestamp
    # Format in sample: 12/26/2022 18:01  →  MM/DD/YYYY HH:MM
    df["datetime"] = pd.to_datetime(df[ts_col], format="mixed")
    if ts_col != "datetime":
        df.drop(columns=[ts_col], inplace=True)

    # -- Keep only the columns we need; drop VWAP cols (not used by Backtrader)
    keep = ["datetime", "open", "high", "low", "close", "volume"]
    for col in keep:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' not found. Columns: {list(df.columns)}")
    df = df[keep].copy()

    # -- Localize to US/Eastern (data is already in ET per filename)
    df["datetime"] = df["datetime"].dt.tz_localize(
        "America/New_York", ambiguous="infer", nonexistent="shift_forward"
    )

    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # -- Duplicate timestamps
    dupes = df.duplicated(subset="datetime")
    print(f"  Rows loaded      : {len(df):,}")
    print(f"  Duplicates       : {dupes.sum():,}  {'→ dropped' if dupes.any() else '(none)'}")
    df = df[~dupes].copy()

    # -- Date range
    print(f"  Date range       : {df['datetime'].iloc[0]}  →  {df['datetime'].iloc[-1]}")

    # -- Gaps > 90 min  (maintenance window ~17:00-18:00 ET is NORMAL — ~750 per year)
    diffs    = df["datetime"].diff().dropna()
    big_gaps = diffs[diffs > pd.Timedelta(minutes=90)]
    normal   = big_gaps[big_gaps <= pd.Timedelta(hours=2)]    # maintenance windows
    abnormal = big_gaps[big_gaps > pd.Timedelta(hours=2)]     # holiday/data holes
    print(f"  Maintenance gaps (90min–2hr) : {len(normal):,}  (expected ~250/yr, normal)")
    print(f"  Abnormal gaps (>2hr)         : {len(abnormal):,}")
    if 0 < len(abnormal) <= 10:
        for idx, gap in abnormal.items():
            print(f"    → {df['datetime'][idx]}  gap={gap}")
    elif len(abnormal) > 10:
        print(f"    (first 5 shown)")
        for idx, gap in list(abnormal.items())[:5]:
            print(f"    → {df['datetime'][idx]}  gap={gap}")

    # -- NaN check
    nulls = df[["open","high","low","close","volume"]].isnull().sum()
    if nulls.any():
        print(f"  NaN rows         : {nulls.to_dict()}  → rows dropped")
        df.dropna(subset=["open","high","low","close"], inplace=True)
    else:
        print(f"  NaN rows         : none")

    # -- OHLC sanity
    bad_hl = (df["high"] < df["low"]).sum()
    bad_c  = ((df["close"] < df["low"]) | (df["close"] > df["high"])).sum()
    print(f"  high < low bars  : {bad_hl:,}")
    print(f"  close OOB bars   : {bad_c:,}")
    if bad_hl > 0 or bad_c > 0:
        print("  ⚠  These are usually tick-data artefacts. Clamping close to [low,high].")
        df["close"] = df["close"].clip(lower=df["low"], upper=df["high"])

    return df


# ── RESAMPLE ───────────────────────────────────────────────────────────────────

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample tz-aware 1-min DataFrame to rule e.g. '5min','15min','30min'."""
    out = (
        df.set_index("datetime")
          .resample(rule, label="left", closed="left")
          .agg(open=("open","first"), high=("high","max"),
               low=("low","min"),   close=("close","last"),
               volume=("volume","sum"))
          .dropna(subset=["open"])
    )
    out.reset_index(inplace=True)
    return out


# ── RTH SLICE ─────────────────────────────────────────────────────────────────

def rth_slice(df: pd.DataFrame) -> pd.DataFrame:
    t    = df["datetime"].dt.time
    mask = (t >= pd.Timestamp(RTH_START).time()) & \
           (t <= pd.Timestamp(RTH_END).time())
    return df[mask].copy()


# ── SAVE (Backtrader GenericCSVData format) ────────────────────────────────────

def save_bt_csv(df: pd.DataFrame, path: str):
    out = df.copy()
    # BT wants naive datetime strings — strip tz
    out["datetime"] = out["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out[["datetime","open","high","low","close","volume"]].to_csv(path, index=False)
    print(f"  ✓  {os.path.basename(path):<28} {len(out):>8,} rows")


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load primary file
    df1 = load_and_clean(INPUT_FILE)

    # 2. Resample
    print(f"\nResampling 1-min → 5 / 15 / 30 min ...")
    df5  = resample_ohlcv(df1, "5min")
    df15 = resample_ohlcv(df1, "15min")
    df30 = resample_ohlcv(df1, "30min")
    print(f"  5-min bars  : {len(df5):,}")
    print(f"  15-min bars : {len(df15):,}")
    print(f"  30-min bars : {len(df30):,}")

    # 3. RTH slices
    df1_rth  = rth_slice(df1)
    df5_rth  = rth_slice(df5)
    df15_rth = rth_slice(df15)
    df30_rth = rth_slice(df30)

    # 4. Save
    print(f"\n{'='*60}")
    print(f"Saving to {OUTPUT_DIR}/")
    save_bt_csv(df1,      os.path.join(OUTPUT_DIR, "NQ_1min_full.csv"))
    save_bt_csv(df5,      os.path.join(OUTPUT_DIR, "NQ_5min_full.csv"))
    save_bt_csv(df15,     os.path.join(OUTPUT_DIR, "NQ_15min_full.csv"))
    save_bt_csv(df30,     os.path.join(OUTPUT_DIR, "NQ_30min_full.csv"))
    save_bt_csv(df1_rth,  os.path.join(OUTPUT_DIR, "NQ_1min_rth.csv"))
    save_bt_csv(df5_rth,  os.path.join(OUTPUT_DIR, "NQ_5min_rth.csv"))
    save_bt_csv(df15_rth, os.path.join(OUTPUT_DIR, "NQ_15min_rth.csv"))
    save_bt_csv(df30_rth, os.path.join(OUTPUT_DIR, "NQ_30min_rth.csv"))

    # 5. Summary table
    print(f"\n{'='*60}")
    print("QUALITY SUMMARY")
    print(f"{'Feed':<22} {'Rows':>8}  {'From':<20} {'To':<20}")
    print("-"*70)
    for name, frame in [
        ("1min  full",  df1),    ("5min  full",  df5),
        ("15min full",  df15),   ("30min full",  df30),
        ("1min  RTH",   df1_rth),("5min  RTH",   df5_rth),
        ("15min RTH",   df15_rth),("30min RTH",  df30_rth),
    ]:
        fr = str(frame["datetime"].iloc[0])
        to = str(frame["datetime"].iloc[-1])
        print(f"  {name:<20} {len(frame):>8,}  {fr:<20} {to:<20}")

    # 6. RTH trade-day count (useful sanity check)
    rth_days = df1_rth["datetime"].dt.date.nunique()
    print(f"\n  RTH trading days in dataset : {rth_days:,}")
    print(f"  Avg 1-min bars / RTH day    : {len(df1_rth)/rth_days:.0f}  (expect ~390)")

    print(f"\n{'='*60}")
    print("Step 0 complete.")
    print(f"Output folder: {os.path.abspath(OUTPUT_DIR)}")
    print("Next → Step 1: harvest 3-5 ORB variant descriptions.")

if __name__ == "__main__":
    main()