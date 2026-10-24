"""Technical indicators and rule-based signals (pure pandas/numpy, no I/O besides yfinance)."""
import numpy as np, pandas as pd, yfinance as yf
from stocks import TICKERS, TICKER_TO_SECTOR, INDICES, yf_symbol

WINDOWS = {"1 week": 5, "1 month": 21, "3 months": 63, "6 months": 126, "1 year": 250}

def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's RSI."""
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))

def fetch_universe(period: str = "1y", chunk: int = 10):
    """Chunked, non-threaded download with timeout + retry. Bad/delisted tickers are skipped, never hang the app."""
    import time
    closes, vols = [], []
    for i in range(0, len(TICKERS), chunk):
        syms = [yf_symbol(t) for t in TICKERS[i:i + chunk]]
        for attempt in range(2):
            try:
                raw = yf.download(syms, period=period, interval="1d", auto_adjust=True,
                                  progress=False, threads=False, timeout=15)
                if raw is not None and not raw.empty:
                    c, v = raw["Close"], raw["Volume"]
                    if isinstance(c, pd.Series): c, v = c.to_frame(syms[0]), v.to_frame(syms[0])
                    closes.append(c); vols.append(v); break
            except Exception:
                pass
            time.sleep(1.5)
    if not closes:
        raise RuntimeError("Could not fetch any data from Yahoo Finance (network, rate limit, or outdated yfinance). "
                           "Try: pip install -U yfinance")
    ren = lambda d: d.rename(columns=lambda c: c.replace(".NS", "")).dropna(axis=1, how="all")
    close, vol = ren(pd.concat(closes, axis=1)), ren(pd.concat(vols, axis=1))
    return close, vol[[c for c in close.columns if c in vol.columns]]

def fetch_indices(window: int = 21) -> pd.DataFrame:
    rows = []
    for name, sym in INDICES.items():
        try:
            c = yf.Ticker(sym).history(period="1y", timeout=10)["Close"].dropna()
            rows.append({"Index": name, "Level": c.iloc[-1], "Day %": (c.iloc[-1] / c.iloc[-2] - 1) * 100,
                         "Period %": (c.iloc[-1] / c.iloc[-window - 1] - 1) * 100})
        except Exception:
            rows.append({"Index": name, "Level": np.nan, "Day %": np.nan, "Period %": np.nan})
    return pd.DataFrame(rows)

def signal(row) -> tuple[str, int]:
    s = 0
    s += 2 if row["RSI"] < 30 else -2 if row["RSI"] > 70 else 0
    s += 1 if row["Price"] > row["MA20"] else -1
    s += 1 if row["MA20"] > row["MA50"] else -1
    s += 1 if row["Return %"] > 0 else -1
    return ("BUY" if s >= 2 else "AVOID" if s <= -2 else "HOLD"), s

def compute_metrics(close: pd.DataFrame, vol: pd.DataFrame, window: int) -> pd.DataFrame:
    rows = []
    for t in close.columns:
        c = close[t].dropna()
        if len(c) < window + 2: continue
        r = c.pct_change().dropna()
        dd = (c / c.cummax() - 1).min() * 100
        rows.append({"Ticker": t, "Sector": TICKER_TO_SECTOR[t], "Price": c.iloc[-1],
                     "Return %": (c.iloc[-1] / c.iloc[-window - 1] - 1) * 100,
                     "RSI": rsi(c).iloc[-1], "MA20": c.tail(20).mean(), "MA50": c.tail(50).mean(),
                     "Volatility %": r.tail(window).std() * np.sqrt(252) * 100, "Max DD %": dd,
                     "Vol Ratio": vol[t].tail(5).mean() / vol[t].tail(50).mean()})
    df = pd.DataFrame(rows)
    df[["Signal", "Score"]] = df.apply(lambda x: pd.Series(signal(x)), axis=1)
    return df.round(2)

def sector_table(m: pd.DataFrame) -> pd.DataFrame:
    g = m.groupby("Sector").agg(**{"Return %": ("Return %", "mean"), "RSI": ("RSI", "mean"),
                                    "Volatility %": ("Volatility %", "mean"), "Stocks": ("Ticker", "count")})
    return g.sort_values("Return %", ascending=False).round(2).reset_index()
