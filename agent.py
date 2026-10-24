"""Query -> intent -> data -> metrics -> LLM commentary."""
import os, re, json
from dotenv import load_dotenv
import analysis as A

load_dotenv()
MODEL = "llama-3.3-70b-versatile"
SYSTEM = """You are a senior Indian equity strategist. Use ONLY the data provided; never invent prices or figures.
Factor in Indian context where relevant: RBI policy/liquidity, FII/DII flows, INR/USD, crude, monsoon, earnings season.
Format in Markdown with these sections: ## Verdict (2 sentences), ## Sector Read, ## Stock Signals
(table: Ticker | Signal | Why, 5-8 rows, signals must be BUY/HOLD/AVOID), ## Risks, ## Outlook (one of: Bullish / Cautiously Bullish / Neutral / Cautious / Bearish).
Answer the user's actual question first. Be concise. End with: 'Not investment advice.'"""

_SECT_PAT = {"Banking & Finance": "bank|financ|nbfc", "IT": r"\bit\b|tech|software", "FMCG": "fmcg|consumer", "Auto": r"\bauto|\bcars?\b",
             "Pharma & Health": "pharma|health", "Energy & Power": "energy|oil|power", "Metals & Mining": "metal|steel|mining"}

def parse_intent(q: str) -> dict:
    ql = q.lower()
    period = next((k for k, pat in {"1 week": r"week|7 day", "3 months": r"quarter|3 month|three month", "6 months": r"6 month|half.year",
                                    "1 year": r"year|annual|12 month", "1 month": r"month|30 day"}.items() if re.search(pat, ql)), "1 month")
    sector = next((k for k, p in _SECT_PAT.items() if re.search(p, ql)), None)
    return {"period": period, "sector": sector}

def run(query: str, close=None, vol=None) -> dict:
    intent = parse_intent(query)
    window = A.WINDOWS[intent["period"]]
    if close is None: close, vol = A.fetch_universe()
    m = A.compute_metrics(close, vol, window)
    sec = A.sector_table(m)
    idx = A.fetch_indices(window)
    payload = {"query": query, "period": intent["period"], "focus_sector": intent["sector"],
               "indices": idx.round(2).to_dict("records"), "sectors": sec.to_dict("records"),
               "top_gainers": m.nlargest(5, "Return %")[["Ticker", "Return %", "RSI", "Signal"]].to_dict("records"),
               "top_losers": m.nsmallest(5, "Return %")[["Ticker", "Return %", "RSI", "Signal"]].to_dict("records"),
               "oversold": m[m.RSI < 35][["Ticker", "RSI"]].to_dict("records"),
               "overbought": m[m.RSI > 65][["Ticker", "RSI"]].to_dict("records")}
    if intent["sector"]:
        payload["focus_stocks"] = m[m.Sector == intent["sector"]].drop(columns=["Sector"]).to_dict("records")
    return {"intent": intent, "metrics": m, "sectors": sec, "indices": idx, "commentary": explain(payload)}

_PREF = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
_SKIP = ("whisper", "guard", "tts", "embed", "playai", "orpheus", "safeguard")
_model = None

def pick_model(client) -> str:
    """GROQ_MODEL from .env wins; otherwise choose the best model your key can actually use."""
    global _model
    if os.getenv("GROQ_MODEL"): return os.getenv("GROQ_MODEL")
    if _model: return _model
    ids = [m.id for m in client.models.list().data]
    _model = next((m for m in _PREF if m in ids), None) or next(m for m in ids if not any(k in m for k in _SKIP))
    return _model

def explain(payload: dict) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key or "your-groq-key" in key:
        return "⚠️ Set `GROQ_API_KEY` in `.env` to enable AI commentary. Data tabs still work."
    try:
        from groq import Groq
        c = Groq(api_key=key)
        r = c.chat.completions.create(
            model=pick_model(c), temperature=0.3, max_tokens=1400,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps(payload, default=str)}])
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ LLM call failed: {e}"