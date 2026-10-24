"""Nifty 50 universe + sector map. Review periodically: index constituents change."""
SECTORS = {
    "Banking & Finance": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "BAJFINANCE", "BAJAJFINSV", "SHRIRAMFIN", "HDFCLIFE", "SBILIFE"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "Auto": ["MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "Pharma & Health": ["SUNPHARMA", "DRREDDY", "CIPLA", "APOLLOHOSP", "DIVISLAB"],
    "Energy & Power": ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "COALINDIA", "BPCL"],
    "Metals & Mining": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "ADANIENT"],
    "Infra & Others": ["LT", "ULTRACEMCO", "GRASIM", "ASIANPAINT", "TITAN", "BHARTIARTL", "ADANIPORTS"],
}
TICKER_TO_SECTOR = {t: s for s, ts in SECTORS.items() for t in ts}
TICKERS = list(TICKER_TO_SECTOR)
def yf_symbol(t: str) -> str: return f"{t}.NS"
INDICES = {"Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT"}
