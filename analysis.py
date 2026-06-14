import yfinance as yf
import pandas as pd
from stocks import NIFTY50_STOCKS, SECTORS, INDICES

def fetch_stock_data(ticker, period="1mo"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        return df
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def fetch_multiple_stocks(period="1mo"):
    results = {}
    for name, ticker in NIFTY50_STOCKS.items():
        df = fetch_stock_data(ticker, period)
        if df is not None and not df.empty:
            results[name] = df
    return results

def calculate_returns(df):
    if df is None or df.empty:
        return None
    df = df.copy()
    df['daily_return'] = df['Close'].pct_change() * 100
    df['cumulative_return'] = ((df['Close'] / df['Close'].iloc[0]) - 1) * 100
    return df

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_stock_summary(name, ticker, period="1mo"):
    df = fetch_stock_data(ticker, period)
    if df is None or df.empty:
        return None

    df = calculate_returns(df)
    current_price = df['Close'].iloc[-1]
    start_price = df['Close'].iloc[0]
    total_return = df['cumulative_return'].iloc[-1]
    volatility = df['daily_return'].std()
    avg_volume = df['Volume'].mean()
    rsi = calculate_rsi(df)
    ma20 = df['Close'].rolling(20).mean().iloc[-1]

    return {
        "name": name,
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "start_price": round(start_price, 2),
        "total_return": round(total_return, 2),
        "volatility": round(volatility, 2),
        "avg_volume": int(avg_volume),
        "rsi": round(rsi, 2) if not pd.isna(rsi) else None,
        "ma20": round(ma20, 2) if not pd.isna(ma20) else None,
        "data": df
    }

def get_sector_performance(period="1mo"):
    sector_returns = {}
    for sector, stocks in SECTORS.items():
        returns = []
        for stock_name in stocks:
            ticker = NIFTY50_STOCKS.get(stock_name)
            if ticker:
                df = fetch_stock_data(ticker, period)
                if df is not None and not df.empty:
                    ret = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                    returns.append(ret)
        if returns:
            sector_returns[sector] = round(sum(returns) / len(returns), 2)
    return sector_returns

def get_index_data(period="1mo"):
    results = {}
    for name, ticker in INDICES.items():
        df = fetch_stock_data(ticker, period)
        if df is not None and not df.empty:
            df = calculate_returns(df)
            results[name] = df
    return results

if __name__ == "__main__":
    print("Testing data pipeline...")
    print("\nFetching Nifty 50 index...")
    nifty = fetch_stock_data("^NSEI", "1mo")
    if nifty is not None:
        print(f"Nifty 50 — {len(nifty)} days of data")
        print(f"Latest close: {nifty['Close'].iloc[-1]:.2f}")

    print("\nFetching TCS...")
    tcs = get_stock_summary("TCS", "TCS.NS", "1mo")
    if tcs:
        print(f"TCS Price: ₹{tcs['current_price']}")
        print(f"TCS Return: {tcs['total_return']}%")
        print(f"TCS RSI: {tcs['rsi']}")

    print("\nFetching sector performance...")
    sectors = get_sector_performance("1mo")
    for sector, ret in sectors.items():
        print(f"{sector}: {ret}%")

    print("\nPipeline test complete!")