import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="FinPulse", page_icon="📈", layout="wide")

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

# Header
st.title("📈 FinPulse — Indian Stock Market Dashboard")
st.markdown("Tracking 20 listed Indian companies across key sectors")

# Load data
df = get_all_stocks()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Market Overview", "Stock Analysis", "Sector Comparison"])

if page == "Market Overview":
    st.header("Market Overview")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Companies", len(df))
    with col2:
        st.metric("Avg P/E Ratio", f"{df['pe_ratio'].mean():.2f}")
    with col3:
        st.metric("Highest Price", f"₹{df['price'].max():,.2f}")
    with col4:
        st.metric("Lowest Price", f"₹{df['price'].min():,.2f}")
    
    st.subheader("All Stocks")
    display_df = df[["name", "ticker", "price", "market_cap", "pe_ratio", "eps", "sector"]].copy()
    display_df["market_cap"] = (display_df["market_cap"] / 1e7).round(2)
    display_df.columns = ["Company", "Ticker", "Price (₹)", "Market Cap (Cr)", "P/E Ratio", "EPS", "Sector"]
    st.dataframe(display_df, use_container_width=True)
    
    # Market Cap Bar Chart
    st.subheader("Market Cap Comparison")
    fig = px.bar(display_df.sort_values("Market Cap (Cr)", ascending=False),
                 x="Company", y="Market Cap (Cr)",
                 color="Sector", title="Market Capitalization by Company")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Stock Analysis":
    st.header("Stock Analysis")
    
    selected = st.selectbox("Select a Company", df["name"].tolist())
    stock_data = df[df["name"] == selected].iloc[0]
    ticker = stock_data["ticker"]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Price", f"₹{stock_data['price']:,.2f}")
    with col2:
        st.metric("P/E Ratio", f"{stock_data['pe_ratio']:.2f}")
    with col3:
        st.metric("EPS", f"₹{stock_data['eps']:.2f}")
    with col4:
        market_cap_cr = stock_data['market_cap'] / 1e7
        st.metric("Market Cap", f"₹{market_cap_cr:,.0f} Cr")
    
    col5, col6 = st.columns(2)
    with col5:
        st.metric("52 Week High", f"₹{stock_data['week_52_high']:,.2f}")
    with col6:
        st.metric("52 Week Low", f"₹{stock_data['week_52_low']:,.2f}")
    
    # Historical Price Chart
    st.subheader(f"{selected} — 1 Year Price History")
    hist = get_history(ticker)
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist["date"], y=hist["close"],
                                  mode="lines", name="Close Price",
                                  line=dict(color="#00ff88", width=2)))
        fig.update_layout(template="plotly_dark",
                          xaxis_title="Date", yaxis_title="Price (₹)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No historical data available")

elif page == "Sector Comparison":
    st.header("Sector Comparison")
    
    sector_df = df.groupby("sector").agg(
        avg_pe=("pe_ratio", "mean"),
        avg_eps=("eps", "mean"),
        count=("name", "count")
    ).reset_index()
    
    st.subheader("Average P/E by Sector")
    fig = px.bar(sector_df, x="sector", y="avg_pe",
                 color="sector", title="Average P/E Ratio by Sector")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("P/E vs EPS Scatter")
    fig2 = px.scatter(df, x="eps", y="pe_ratio",
                      color="sector", hover_name="name",
                      title="P/E Ratio vs EPS by Company")
    st.plotly_chart(fig2, use_container_width=True)