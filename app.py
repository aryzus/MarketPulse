import streamlit as st, plotly.graph_objects as go, plotly.express as px, yfinance as yf
from plotly.subplots import make_subplots
import analysis as A, agent, report
from stocks import TICKERS, SECTORS

st.set_page_config("MarketPulse", "📈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1300px}
.hero{background:linear-gradient(120deg,#0B1F3A,#1E3A8A);color:#fff;padding:1.2rem 1.6rem;border-radius:14px;margin-bottom:1rem}
.hero h1{margin:0;font-size:1.7rem}.hero p{margin:.2rem 0 0;opacity:.8}
[data-testid=stMetric]{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:.7rem 1rem}
@media(prefers-color-scheme:dark){[data-testid=stMetric]{background:#111827;border-color:#1F2937}}
</style><div class="hero"><h1>📈 MarketPulse</h1><p>Autonomous NSE/BSE intelligence — ask in plain English, get data-backed signals and a PDF.</p></div>""", unsafe_allow_html=True)

@st.cache_data(ttl=900, show_spinner="Fetching live NSE data…")
def universe(): return A.fetch_universe()
@st.cache_data(ttl=900, show_spinner=False)
def history(t, period): return yf.Ticker(f"{t}.NS").history(period=period)
@st.cache_data(ttl=900, show_spinner=False)
def indices(w): return A.fetch_indices(w)

with st.sidebar:
    st.header("Settings")
    period = st.selectbox("Analysis window", list(A.WINDOWS), index=1)
    if st.button("🔄 Refresh data", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.caption("Data: yfinance (delayed). Educational use only.")
window = A.WINDOWS[period]
try:
    close, vol = universe()
except Exception as e:
    st.error(f"Data fetch failed: {e}"); st.info("Run `pip install -U yfinance`, check your internet/VPN, then press Rerun."); st.stop()
metrics = A.compute_metrics(close, vol, window); sectors = A.sector_table(metrics)
tab1, tab2, tab3 = st.tabs(["🤖 AI Analyst", "🌐 Market Overview", "🔍 Stock Analyzer"])

with tab1:
    st.session_state.setdefault("chat", [])
    ex = st.columns(3)
    for col, q in zip(ex, ["Which sectors are leading this week?", "Is banking overbought right now?", "Find oversold Nifty stocks this month"]):
        if col.button(q, use_container_width=True): st.session_state.pending = q
    for m_ in st.session_state.chat:
        with st.chat_message(m_["role"]): st.markdown(m_["content"])
    hist = st.container()
    q = st.chat_input("Ask about sectors, stocks, momentum, risk…") or st.session_state.pop("pending", None)
    if q:
        with st.spinner("Analysing market data…"):
            res = agent.run(q, close, vol)
        st.session_state.chat += [{"role": "user", "content": q},
            {"role": "assistant", "content": res["commentary"], "pdf": report.build_pdf(res, q),
             "meta": f"Window: {res['intent']['period']} · Focus: {res['intent']['sector'] or 'whole market'}"}]
    with hist:
        for i, m_ in enumerate(st.session_state.chat):
            with st.chat_message(m_["role"]):
                st.markdown(m_["content"])
                if m_.get("pdf"):
                    st.caption(m_["meta"]); st.download_button("⬇️ PDF report", m_["pdf"], "marketpulse_report.pdf", "application/pdf", key=f"pdf{i}")

with tab2:
    idx = indices(window); cols = st.columns(4)
    for c, r in zip(cols, idx.to_dict("records")):
        c.metric(r["Index"], f"{r['Level']:,.0f}" if r["Level"] == r["Level"] else "n/a", f"{r['Day %']:+.2f}% today" if r["Day %"] == r["Day %"] else None)
    l, r_ = st.columns(2)
    fig = px.bar(sectors.sort_values("Return %"), x="Return %", y="Sector", orientation="h", color="Return %", color_continuous_scale="RdYlGn", color_continuous_midpoint=0, title=f"Sector return ({period})")
    l.plotly_chart(fig.update_layout(coloraxis_showscale=False, height=380), use_container_width=True)
    top = metrics.nlargest(10, "Return %")
    r_.plotly_chart(px.bar(top, x="Ticker", y="Return %", color="Signal", color_discrete_map={"BUY": "#16A34A", "HOLD": "#64748B", "AVOID": "#DC2626"}, title="Top 10 by return").update_layout(height=380), use_container_width=True)
    st.subheader("Signal board"); st.dataframe(metrics.sort_values("Score", ascending=False), use_container_width=True, hide_index=True, height=320)
    if st.button("📄 Generate PDF report", type="primary"):
        with st.spinner("Building report…"):
            res = {"intent": {"period": period, "sector": None}, "metrics": metrics, "sectors": sectors, "indices": idx,
                   "commentary": agent.explain({"period": period, "sectors": sectors.to_dict("records"), "indices": idx.to_dict("records"),
                                                "top_gainers": top[["Ticker", "Return %", "RSI", "Signal"]].to_dict("records"),
                                                "top_losers": metrics.nsmallest(5, "Return %")[["Ticker", "Return %", "RSI", "Signal"]].to_dict("records"), "query": "Weekly market overview"})}
            st.download_button("⬇️ Download PDF", report.build_pdf(res, "Market overview"), "marketpulse_overview.pdf", "application/pdf")

with tab3:
    c1, c2 = st.columns([2, 1]); t = c1.selectbox("Stock", sorted(TICKERS)); p = c2.selectbox("History", ["3mo", "6mo", "1y", "2y"], index=1)
    h = history(t, p)
    if h.empty: st.warning("No data returned.")
    else:
        h["MA20"] = h.Close.rolling(20).mean(); h["MA50"] = h.Close.rolling(50).mean(); h["RSI"] = A.rsi(h.Close)
        row = metrics[metrics.Ticker == t]
        if not row.empty:
            row = row.iloc[0]; k = st.columns(5)
            for kc, (lab, v) in zip(k, [("Price", f"₹{row.Price:,.1f}"), (f"Return ({period})", f"{row['Return %']:+.2f}%"), ("RSI", f"{row.RSI:.1f}"), ("Volatility", f"{row['Volatility %']:.1f}%"), ("Signal", row.Signal)]): kc.metric(lab, v)
        f = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.6, .2, .2], vertical_spacing=.03)
        f.add_trace(go.Candlestick(x=h.index, open=h.Open, high=h.High, low=h.Low, close=h.Close, name="Price"), 1, 1)
        for ma, col in [("MA20", "#F59E0B"), ("MA50", "#6366F1")]: f.add_trace(go.Scatter(x=h.index, y=h[ma], name=ma, line=dict(color=col, width=1.5)), 1, 1)
        f.add_trace(go.Bar(x=h.index, y=h.Volume, name="Volume", marker_color="#94A3B8"), 2, 1)
        f.add_trace(go.Scatter(x=h.index, y=h.RSI, name="RSI", line=dict(color="#0EA5E9")), 3, 1)
        for y in (30, 70): f.add_hline(y=y, line_dash="dot", line_color="#94A3B8", row=3, col=1)
        st.plotly_chart(f.update_layout(height=700, xaxis_rangeslider_visible=False, margin=dict(t=20)), use_container_width=True)