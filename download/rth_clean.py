import pandas as pd
df = pd.read_csv("usa100_rth_only.csv")
df["d"] = df["timestamp"].str[:10]
# keep days that had real intraday movement
good = df.groupby("d").filter(lambda x: x["high"].max() != x["low"].min())
good = good.drop(columns="d")
good.to_csv("usa100_clean.csv", index=False)
print(f"{len(df)} -> {len(good)} rows after dropping flat holiday sessions")