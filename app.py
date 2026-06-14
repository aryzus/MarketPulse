import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
from agent import run_agent, gather_market_data
from analysis import get_stock_summary, fetch_stock_data, calculate_returns
from stocks import NIFTY50_STOCKS, SECTORS, INDICES

load_dotenv()

st.set_page_config(
    page_title="India Stock Market AI Agent",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0a0e1a; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #1f2937; }
    
    /* Cards/metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px;
    }
    
    /* Metric value color */
    [data-testid="stMetricValue"] { color: #00d4aa; font-size: 1.4rem; font-weight: 700; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #0d1117; border-bottom: 1px solid #1f2937; }
    .stTabs [data-baseweb="tab"] { color: #6b7280; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #00d4aa; border-bottom-color: #00d4aa; }
    
    /* Buttons */
    .stButton > button {
        background: #1a1f35;
        color: #00d4aa;
        border: 1px solid #00d4aa;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #00d4aa;
        color: #0a0e1a;
    }
    
    /* Chat input */
    [data-testid="stChatInput"] { background: #1a1f35; border: 1px solid #1f2937; border-radius: 12px; }
    
    /* Title */
    h1 { color: #00d4aa !important; font-weight: 800 !important; }
    h2, h3 { color: #e2e8f0 !important; }
    
    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid #1f2937; border-radius: 8px; }
    
    /* Divider */
    hr { border-color: #1f2937; }

    /* Selectbox */
    [data-testid="stSelectbox"] > div { background: #1a1f35; border: 1px solid #1f2937; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🇮🇳 India Stock Market AI Agent")
st.caption("Powered by live NSE/BSE data + Llama 3.3 via Groq")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "market_data" not in st.session_state:
    st.session_state.market_data = None

with st.sidebar:
    st.subheader("⚙️ Settings")
    period = st.selectbox(
        "Analysis period",
        ["1wk", "1mo", "3mo", "6mo", "1y"],
        index=1
    )

    st.divider()
    st.subheader("💡 Try these queries")
    example_queries = [
        "Which sector performed best this month?",
        "Compare IT vs Banking sector performance",
        "Which Nifty 50 stocks have RSI below 40?",
        "What is the market outlook for next month?",
        "Top 5 stocks by returns this period",
        "Which stocks are oversold right now?",
    ]
    for q in example_queries:
        if st.button(q, use_container_width=True, key=q):
            st.session_state.pending_query = q

    st.divider()
    if st.button("🔄 Refresh market data", use_container_width=True):
        st.session_state.market_data = None
        st.rerun()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

tab1, tab2, tab3 = st.tabs([
    "🤖 AI Agent", "📊 Market Overview", "🔍 Stock Analyzer"
])

with tab1:
    st.subheader("Ask the AI Agent")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    query = st.chat_input("Ask anything about Indian stock markets...")

    if "pending_query" in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Agent analyzing live NSE/BSE data..."):
                try:
                    insight, market_data = run_agent(query, period)
                    st.session_state.market_data = market_data
                    st.markdown(insight)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": insight
                    })
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.subheader("Live Market Overview")

    if st.button("Load market data", use_container_width=True):
        with st.spinner("Fetching live NSE/BSE data..."):
            st.session_state.market_data = gather_market_data(period)

    if st.session_state.market_data:
        data = st.session_state.market_data

        st.markdown("#### Market indices")
        cols = st.columns(len(data['indices']))
        for i, (name, ret) in enumerate(data['indices'].items()):
            cols[i].metric(name, f"{ret:+.2f}%", delta=f"{ret:+.2f}%")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Sector performance")
            sectors = data.get('sectors', {})
            sector_df = pd.DataFrame(
                list(sectors.items()),
                columns=['Sector', 'Return (%)']
            ).sort_values('Return (%)', ascending=True)
            fig1 = px.bar(
                sector_df,
                x='Return (%)',
                y='Sector',
                orientation='h',
                color='Return (%)',
                color_continuous_scale=['#e74c3c', '#95a5a6', '#2ecc71'],
                color_continuous_midpoint=0,
                text='Return (%)'
            )
            fig1.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=20, b=20),
                showlegend=False,
                coloraxis_showscale=False,
                height=350
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            st.markdown("#### Top stocks performance")
            stocks = data.get('stocks', {})
            if stocks:
                stock_df = pd.DataFrame([
                    {
                        'Stock': name,
                        'Price (₹)': info['current_price'],
                        'Return (%)': info['total_return'],
                        'RSI': info.get('rsi', 'N/A')
                    }
                    for name, info in stocks.items()
                ]).sort_values('Return (%)', ascending=False)
                st.dataframe(stock_df, use_container_width=True, hide_index=True)
                fig2 = px.bar(
                    stock_df,
                    x='Stock',
                    y='Return (%)',
                    color='Return (%)',
                    color_continuous_scale=['#e74c3c', '#95a5a6', '#2ecc71'],
                    color_continuous_midpoint=0,
                    text='Return (%)'
                )
                fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=20),
                    showlegend=False,
                    coloraxis_showscale=False,
                    xaxis_tickangle=45,
                    height=350
                )
                st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.markdown("#### Export report")
        if st.button("📄 Generate PDF report", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                try:
                    from report import generate_report
                    last_insight = ""
                    if st.session_state.messages:
                        for msg in reversed(st.session_state.messages):
                            if msg["role"] == "assistant":
                                last_insight = msg["content"]
                                break
                    filename = generate_report(
                        st.session_state.market_data,
                        last_insight,
                        period
                    )
                    with open(filename, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF report",
                            data=f,
                            file_name=f"india_market_report_{period}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    st.success("Report generated!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Click 'Load market data' to fetch live NSE/BSE data")

with tab3:
    st.subheader("Individual Stock Analyzer")

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_stock = st.selectbox(
            "Select stock",
            list(NIFTY50_STOCKS.keys())
        )
    with col2:
        stock_period = st.selectbox(
            "Period",
            ["1wk", "1mo", "3mo", "6mo", "1y"],
            index=1,
            key="stock_period"
        )

    if st.button("Analyze stock", use_container_width=True):
        ticker = NIFTY50_STOCKS[selected_stock]
        with st.spinner(f"Fetching {selected_stock} data..."):
            summary = get_stock_summary(selected_stock, ticker, stock_period)

            if summary:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current price", f"₹{summary['current_price']}")
                col2.metric(
                    "Return",
                    f"{summary['total_return']:+.2f}%",
                    delta=f"{summary['total_return']:+.2f}%"
                )
                col3.metric("RSI", summary.get('rsi', 'N/A'))
                col4.metric("Volatility", f"{summary['volatility']:.2f}%")

                df = summary['data']

                fig3 = go.Figure()
                fig3.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=selected_stock,
                    increasing_line_color='#2ecc71',
                    decreasing_line_color='#e74c3c'
                ))
                fig3.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'].rolling(20).mean(),
                    name='20-day MA',
                    line=dict(color='#3498db', width=1.5)
                ))
                fig3.update_layout(
                    title=f"{selected_stock} — Candlestick Chart",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_rangeslider_visible=False,
                    height=450,
                    margin=dict(t=40, b=20)
                )
                st.plotly_chart(fig3, use_container_width=True)

                col_c, col_d = st.columns(2)
                with col_c:
                    fig4 = px.bar(
                        df.reset_index(),
                        x='Date',
                        y='daily_return',
                        color='daily_return',
                        color_continuous_scale=['#e74c3c', '#95a5a6', '#2ecc71'],
                        color_continuous_midpoint=0,
                        title="Daily returns (%)"
                    )
                    fig4.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        coloraxis_showscale=False,
                        height=300,
                        margin=dict(t=40, b=20)
                    )
                    st.plotly_chart(fig4, use_container_width=True)

                with col_d:
                    fig5 = px.line(
                        df.reset_index(),
                        x='Date',
                        y='cumulative_return',
                        title="Cumulative return (%)",
                        color_discrete_sequence=['#3498db']
                    )
                    fig5.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=300,
                        margin=dict(t=40, b=20)
                    )
                    st.plotly_chart(fig5, use_container_width=True)

                st.markdown("#### Volume analysis")
                fig6 = px.bar(
                    df.reset_index(),
                    x='Date',
                    y='Volume',
                    color_discrete_sequence=['#9b59b6'],
                    title="Trading volume"
                )
                fig6.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=250,
                    margin=dict(t=40, b=20)
                )
                st.plotly_chart(fig6, use_container_width=True)
            else:
                st.error("Could not fetch stock data. Try another stock.")

