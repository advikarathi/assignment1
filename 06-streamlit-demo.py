import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Stock Explorer", page_icon="📊", layout="wide")
st.title("📊 Stock Explorer")


@st.cache_data
def get_stock_data(symbol, start, end):
    """Download daily price history for one ticker."""
    return yf.Ticker(symbol).history(start=start, end=end)


# ---------------- Sidebar ----------------
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker", value="AAPL").upper()
comparison_ticker = st.sidebar.text_input("Comparison Ticker", value="SPY").upper()
start_date = st.sidebar.date_input("Start date", dt.date.today() - dt.timedelta(days=365))
end_date = st.sidebar.date_input("End date", dt.date.today())
run_button = st.sidebar.button("Run")

# ---------------- Main ----------------
if run_button:
    with st.spinner("Loading data..."):
        df = get_stock_data(ticker, start_date, end_date)
        comparison_df = get_stock_data(comparison_ticker, start_date, end_date)

    if df.empty or comparison_df.empty:
        st.error("No data returned. Check the ticker symbols and dates.")
        st.stop()

    st.success("Done!")

    df["normalized_close"] = (df["Close"] / df["Close"].iloc[0]) * 100
    comparison_df["normalized_close"] = (
        comparison_df["Close"] / comparison_df["Close"].iloc[0]
    ) * 100

    # ---------------- Tabs ----------------
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📉 Price Chart", "🗂️ Data", "📋 Statistics", "📈 Comparison"]
    )

    with tab1:
        st.header(f"{ticker} Closing Price")
        fig = px.line(df, x=df.index, y="Close", labels={"x": "Date", "Close": "Price ($)"})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header(f"{ticker} Raw Data")
        st.dataframe(df)

    with tab3:
        st.header(f"{ticker} Summary Statistics")
        st.dataframe(df[["Open", "High", "Low", "Close", "Volume"]].describe())

    with tab4:
        st.header("📈 Comparison")

        combined = pd.concat(
            [df["normalized_close"].rename(ticker),
             comparison_df["normalized_close"].rename(comparison_ticker)],
            axis=1,
        ).dropna()

        comp_fig = px.line(
            combined,
            x=combined.index,
            y=[ticker, comparison_ticker],
            title=f"{ticker} vs {comparison_ticker} Performance (Base 100)",
            labels={"x": "Date", "value": "Normalized Close", "variable": "Ticker"},
        )
        st.plotly_chart(comp_fig, use_container_width=True)

        summary = pd.DataFrame(
            {
                "Min": combined.min(),
                "Max": combined.max(),
                "Final Normalized Value": combined.iloc[-1],
                "Total Return (%)": combined.iloc[-1] - 100,
            }
        ).round(2)
        st.dataframe(summary)
else:
    st.info("Enter tickers in the sidebar and press **Run**.")