import os
from groq import Groq
from dotenv import load_dotenv
import json
from analysis import (
    get_stock_summary, get_sector_performance,
    get_index_data, fetch_stock_data, calculate_returns
)
from stocks import NIFTY50_STOCKS, SECTORS

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert Indian stock market analyst AI agent.
You analyze NSE/BSE data and provide clear, actionable business insights.

You have access to real-time Nifty 50 data including:
- Stock prices, returns, RSI, volatility, moving averages
- Sector performance (IT, Banking, FMCG, Auto, Pharma, Energy, Metals, Finance)
- Market indices (Nifty 50, Sensex, Nifty Bank, Nifty IT)

When given market data, you:
1. Identify the key trends and patterns
2. Highlight top performers and underperformers
3. Provide sector-level insights
4. Give specific, actionable recommendations
5. Use Indian market context (RBI policy, FII/DII flows, rupee impact)
6. Format your response with clear sections and bullet points
7. Always mention risk factors

Keep responses concise, data-driven and professional.
Use INR (₹) for prices. Reference Indian market terminology.
"""

def run_agent(query, period="1mo"):
    print(f"Agent running: {query}")
    print("Fetching market data...")

    market_data = gather_market_data(period)
    data_summary = format_data_for_agent(market_data)

    messages = [
        {
            "role": "user",
            "content": f"""
User Query: {query}

Current Market Data ({period}):
{data_summary}

Please analyze this data and answer the query with specific insights,
numbers, and actionable recommendations for Indian investors.
"""
        }
    ]

    print("Generating AI insights...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    insight = response.choices[0].message.content
    return insight, market_data

def gather_market_data(period="1mo"):
    data = {}

    print("Fetching index data...")
    data['indices'] = {}
    from stocks import INDICES
    for name, ticker in INDICES.items():
        df = fetch_stock_data(ticker, period)
        if df is not None and not df.empty:
            df = calculate_returns(df)
            ret = df['cumulative_return'].iloc[-1]
            data['indices'][name] = round(ret, 2)

    print("Fetching sector performance...")
    data['sectors'] = get_sector_performance(period)

    print("Fetching top stocks...")
    data['stocks'] = {}
    priority_stocks = [
        "Reliance Industries", "TCS", "HDFC Bank",
        "Infosys", "ICICI Bank", "State Bank of India",
        "Bharti Airtel", "ITC", "Sun Pharma", "Maruti Suzuki"
    ]
    for name in priority_stocks:
        ticker = NIFTY50_STOCKS.get(name)
        if ticker:
            summary = get_stock_summary(name, ticker, period)
            if summary:
                data['stocks'][name] = {
                    k: v for k, v in summary.items() if k != 'data'
                }

    return data

def format_data_for_agent(data):
    lines = []

    lines.append("=== MARKET INDICES ===")
    for name, ret in data.get('indices', {}).items():
        emoji = "📈" if ret > 0 else "📉"
        lines.append(f"{emoji} {name}: {ret:+.2f}%")

    lines.append("\n=== SECTOR PERFORMANCE ===")
    sectors = data.get('sectors', {})
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    for sector, ret in sorted_sectors:
        emoji = "📈" if ret > 0 else "📉"
        lines.append(f"{emoji} {sector}: {ret:+.2f}%")

    lines.append("\n=== KEY STOCKS ===")
    for name, stock in data.get('stocks', {}).items():
        ret = stock.get('total_return', 0)
        rsi = stock.get('rsi', 'N/A')
        price = stock.get('current_price', 'N/A')
        emoji = "📈" if ret > 0 else "📉"
        lines.append(
            f"{emoji} {name}: ₹{price} | Return: {ret:+.2f}% | RSI: {rsi}"
        )

    return "\n".join(lines)

if __name__ == "__main__":
    query = "Which sectors are performing best this month and what should investors focus on?"
    insight, data = run_agent(query, "1mo")
    print("\n" + "="*50)
    print("AI AGENT RESPONSE:")
    print("="*50)
    print(insight)