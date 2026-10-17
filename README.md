MarketPulse

> Autonomous market intelligence — fetch live NSE/BSE data, run technical analysis on Nifty 50 stocks, and generate a professional PDF report from a single plain English query.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red)
![Groq](https://img.shields.io/badge/LLM-Groq%20%2B%20Llama3.3-orange)
![yfinance](https://img.shields.io/badge/Data-NSE%2FBSE%20Live-green)
![ReportLab](https://img.shields.io/badge/Export-PDF%20Report-purple)

---

<!-- Add a demo GIF here: screenshots/demo.gif -->
<!-- Tip: record a 30-second screen capture and convert with ezgif.com -->

---

## What It Does

Ask a question like *"Which sectors are leading the market this week?"* and MarketPulse:

1. Fetches live price data for all 43 Nifty 50 stocks via yfinance
2. Computes RSI, 20-day MA, volatility and cumulative returns
3. Groups stocks by sector — IT, Banking, FMCG, Auto, Pharma, Energy, Metals
4. Sends the full analysis to Llama 3.3 70B with Indian market context (RBI, FII/DII, rupee)
5. Returns institutional-grade commentary with buy/hold/avoid signals
6. Exports a formatted PDF report in one click

---

## Sample Output (June 2026)

| Insight | Finding |
|---------|---------|
| Best performing sector | Banking +5.82% (ICICI +8.10%, SBI +6.25%) |
| Worst performing sector | Energy -6.21% |
| Nifty 50 return | +1.04% (1 month) |
| Nifty Bank return | +6.09% |
| Oversold signal | Reliance Industries — RSI 27.11 |
| Market outlook | Cautiously bullish — banking-led rally |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit + custom CSS |
| LLM | Llama 3.3 70B via Groq API |
| Market data | yfinance — live NSE/BSE |
| Technical analysis | Pandas, NumPy |
| Visualization | Plotly (candlestick, bar, line) |
| PDF export | ReportLab |

---

## Dashboard

**Tab 1 — AI Chat**
Plain English queries → autonomous data fetch → LLM analysis → buy/hold/avoid signals with reasoning

**Tab 2 — Market Overview**
Live Nifty 50, Sensex, Nifty Bank, Nifty IT indices · Sector performance chart · Top 10 stocks by return · One-click PDF export

**Tab 3 — Stock Analyzer**
Candlestick chart with 20-day MA overlay · Daily returns · Cumulative return · Volume analysis

---

## Screenshots

![AI Agent Response](screenshots/01_ai_agent_response.png)
![Market Overview](screenshots/02_market_overview.png)
![Candlestick Chart](screenshots/03_candlestick_chart.png)
![Stock Metrics](screenshots/04_stock_metrics.png)
![Sector Performance](screenshots/05_sector_performance.png)

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/aryzus/stock-market-agent-ai.git
cd stock-market-agent-ai

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
echo "GROQ_API_KEY=your-groq-key-here" > .env
# Free key at console.groq.com

# 5. Run
python -m streamlit run app.py
```

---

## Project Structure

```
marketpulse/
├── app.py          # Streamlit dashboard + UI
├── agent.py        # Data fetching + LLM analysis
├── analysis.py     # RSI, returns, volatility
├── report.py       # PDF report generator
├── stocks.py       # Nifty 50 tickers + sector mapping
├── data/           # Generated reports
├── screenshots/    # Dashboard screenshots
├── requirements.txt
└── .env            # API key (not pushed)
```
