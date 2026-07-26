import yfinance as yf
import pandas as pd

from daily_calmar_sprint import deploy_today, DEFAULTS

# pull last ~300 hourly bars of whatever the competition asset is 
#SOL-USD, EURUSD=X, BTC_USD, XRP-USD, ETH-USD, GBPUSD=X, JPY=X, CHF=X, AUDUSD=X, USDCAD=X, NZDUSD=X
df = yf.download("XRP-USD", interval="1h", period="20d", progress=False)
df.columns = [str(c[0]).lower() if isinstance(c, tuple) else str(c).lower()
              for c in df.columns]
df = df[["open", "high", "low", "close"]].dropna().tail(300)


assert len(df) >= 50, f"Only {len(df)} bars -- bad ticker or no data"
age_min = (pd.Timestamp.now(tz="UTC") - df.index[-1].tz_convert("UTC")).total_seconds() / 60
assert age_min < 120, f"Last bar is {age_min:.0f} min old -- stale feed, do not trade"
print(f"OK: {len(df)} bars, last bar {age_min:.0f} min ago, last close {df['close'].iloc[-1]}")

# get today's ticket
print(deploy_today(df, DEFAULTS))