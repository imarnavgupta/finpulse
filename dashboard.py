import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from fetch_data import create_database, fetch_and_store

st.set_page_config(page_title="FinPulse", page_icon="📈", layout="wide")

# Auto-fetch data if database is empty
if not os.path.exists("finpulse.db"):
    create_database()
    fetch_and_store()

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .metric-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        border: 1px solid #2d3250;
    }
    .stock-header {
        color: #00ff88;
        font-size: 24px;
        font-weight: bold;
    }
    .positive { color: #00ff88; }
    .negative { color: #ff4444; }
    </style>
""", unsafe_allow_html=True)

def get_db():
    conn = sqlite3.connect("finpulse.db")
    return conn

def get_all_stocks():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM stocks WHERE price > 0", conn)
    conn.close()
    return df

def get_history(ticker):
    conn = get_db()
    df = pd.read_sql(f"SELECT * FROM historical_prices WHERE ticker = '{ticker}' ORDER BY date ASC", conn)
    conn.close()
    return df

# Sidebar
st.sidebar.title("📈 FinPulse")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Market Overview", "Stock Analysis", "Sector Comparison"])

# Refresh button
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    with st.spinner("Fetching latest market data..."):
        create_database()
        fetch_and_store()
    st.success("Data updated successfully!")

st.sidebar.markdown("---")
st.sidebar.markdown("**Last Updated**")
st.sidebar.markdown("Live NSE/BSE Data via yFinance")

# Header
st.title("📈 FinPulse — Indian Stock Market Dashboard")
st.markdown("Tracking **20 listed Indian companies** across key sectors")
st.markdown("---")

# Load data
df = get_all_stocks()

if page == "Market Overview":
    st.header("🏦 Market Overview")

    # Search bar
    search = st.text_input("🔍 Search for a company", "")
    if search:
        df = df[df["name"].str.contains(search, case=False)]

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Companies", len(df))
    with col2:
        st.metric("📉 Avg P/E Ratio", f"{df['pe_ratio'].mean():.2f}")
    with col3:
        st.metric("🔺 Highest Price", f"₹{df['price'].max():,.2f}")
    with col4:
        st.metric("🔻 Lowest Price", f"₹{df['price'].min():,.2f}")

    st.markdown("---")

    # Stocks table
    st.subheader("All Stocks")
    display_df = df[["name", "ticker", "price", "market_cap", 
                      "pe_ratio", "eps", "week_52_high", "week_52_low", "sector"]].copy()
    display_df["market_cap"] = (display_df["market_cap"] / 1e7).round(2)
    display_df["52W Range"] = display_df.apply(
        lambda x: f"₹{x['week_52_low']:,.0f} - ₹{x['week_52_high']:,.0f}", axis=1)
    display_df = display_df.drop(columns=["week_52_high", "week_52_low"])
    display_df.columns = ["Company", "Ticker", "Price (₹)", "Market Cap (Cr)", 
                           "P/E Ratio", "EPS", "Sector", "52W Range"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

        # Sector comparison chart
    if search and not df.empty:
        sector = df.iloc[0]["sector"]
        sector_stocks = get_all_stocks()
        sector_stocks = sector_stocks[sector_stocks["sector"] == sector]
        sector_stocks["market_cap"] = (sector_stocks["market_cap"] / 1e7).round(2)
        st.subheader(f"📊 {sector} Sector — Market Cap Comparison")
        fig = px.bar(sector_stocks.sort_values("market_cap", ascending=False),
                    x="name", y="market_cap",
                    color="name",
                    title=f"Market Cap Comparison within {sector} Sector (₹ Crore)")
        fig.update_layout(template="plotly_dark", xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader("📊 Market Cap Comparison")
        full_df = get_all_stocks()
        full_df["market_cap"] = (full_df["market_cap"] / 1e7).round(2)
        chart_df = full_df.sort_values("market_cap", ascending=False)
        fig = px.bar(chart_df, x="name", y="market_cap",
                    color="sector",
                    title="Market Capitalization by Company (₹ Crore)")
        fig.update_layout(template="plotly_dark", xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

elif page == "Stock Analysis":
    st.header("🔍 Stock Analysis")

    # Stock selector
    selected = st.selectbox("Select a Company", df["name"].tolist())
    stock_data = df[df["name"] == selected].iloc[0]
    ticker = stock_data["ticker"]

    st.markdown(f"### {selected} ({ticker})")
    st.markdown("---")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Current Price", f"₹{stock_data['price']:,.2f}")
    with col2:
        st.metric("📊 P/E Ratio", f"{stock_data['pe_ratio']:.2f}")
    with col3:
        st.metric("💵 EPS", f"₹{stock_data['eps']:.2f}")
    with col4:
        market_cap_cr = stock_data['market_cap'] / 1e7
        st.metric("🏦 Market Cap", f"₹{market_cap_cr:,.0f} Cr")

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("📈 52W High", f"₹{stock_data['week_52_high']:,.2f}")
    with col6:
        st.metric("📉 52W Low", f"₹{stock_data['week_52_low']:,.2f}")
    with col7:
        price_position = ((stock_data['price'] - stock_data['week_52_low']) /
                         (stock_data['week_52_high'] - stock_data['week_52_low']) * 100
                         if stock_data['week_52_high'] != stock_data['week_52_low'] else 0)
        st.metric("📍 52W Position", f"{price_position:.1f}%")

    st.markdown("---")

    # Chart type selector
    chart_type = st.radio("Chart Type", ["Line Chart", "Candlestick"], horizontal=True)

    hist = get_history(ticker)

    if not hist.empty:
        if chart_type == "Candlestick":
            st.subheader(f"{selected} — Candlestick Chart (1 Year)")
            fig = go.Figure(data=[go.Candlestick(
                x=hist["date"],
                open=hist["open"],
                high=hist["high"],
                low=hist["low"],
                close=hist["close"],
                increasing_line_color="#00ff88",
                decreasing_line_color="#ff4444"
            )])
            fig.update_layout(template="plotly_dark",
                              xaxis_title="Date",
                              yaxis_title="Price (₹)",
                              xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader(f"{selected} — Price History (1 Year)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["date"], y=hist["close"],
                mode="lines", name="Close Price",
                line=dict(color="#00ff88", width=2),
                fill="tozeroy",
                fillcolor="rgba(0, 255, 136, 0.1)"
            ))
            fig.update_layout(template="plotly_dark",
                              xaxis_title="Date",
                              yaxis_title="Price (₹)")
            st.plotly_chart(fig, use_container_width=True)

        # Volume chart
        st.subheader("📊 Trading Volume")
        fig_vol = px.bar(hist, x="date", y="volume",
                         title=f"{selected} — Daily Volume")
        fig_vol.update_layout(template="plotly_dark")
        fig_vol.update_traces(marker_color="#4488ff")
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.warning("No historical data available for this stock")

elif page == "Sector Comparison":
    st.header("🏭 Sector Comparison")

    sector_df = df.groupby("sector").agg(
        avg_pe=("pe_ratio", "mean"),
        avg_eps=("eps", "mean"),
        total_market_cap=("market_cap", "sum"),
        count=("name", "count")
    ).reset_index()
    sector_df["total_market_cap"] = (sector_df["total_market_cap"] / 1e7).round(2)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average P/E by Sector")
        fig = px.bar(sector_df, x="sector", y="avg_pe",
                     color="sector",
                     title="Average P/E Ratio by Sector")
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Total Market Cap by Sector")
        fig2 = px.pie(sector_df, values="total_market_cap", names="sector",
                      title="Market Cap Distribution by Sector")
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("P/E vs EPS — All Companies")
    fig3 = px.scatter(df, x="eps", y="pe_ratio",
                      color="sector", hover_name="name",
                      size="market_cap",
                      title="P/E Ratio vs EPS (bubble size = Market Cap)")
    fig3.update_layout(template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)