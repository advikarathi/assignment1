import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from stock import Stock


@st.cache_data(show_spinner=False)
def load_stock(symbol, start, end, ma_window, ma_long_window=None):
    """Create (and therefore download) a Stock. Cached per argument combination."""
    return Stock(symbol, start=start, end=end, ma_window=ma_window,
                 ma_long_window=ma_long_window)


def plot_price_ma(stock):
    """Line chart of Close and its moving average, built from stock.data."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock.data.index, y=stock.data['Close'],
                             mode='lines', name='Close'))
    # The first ma_window - 1 rows of MA are NaN; Plotly simply leaves them out.
    fig.add_trace(go.Scatter(x=stock.data.index, y=stock.data['MA'],
                             mode='lines', name=f'{stock.ma_window}-day MA'))
    if 'MA_long' in stock.data:
        fig.add_trace(go.Scatter(x=stock.data.index, y=stock.data['MA_long'],
                                 mode='lines', name=f'{stock.ma_long_window}-day MA'))
    fig.update_layout(title=f'{stock.symbol} Close Price and Moving Averages',
                      xaxis_title='Date', yaxis_title='Price ($)')
    return fig


def zero_based_performance(stock):
    """Cumulative log return shifted so the first day of the range is exactly 0.0."""
    cum = stock.data['return'].cumsum()
    return cum - cum.iloc[0]


st.set_page_config(page_title='Stock Analysis', layout='wide')
st.title('Stock Analysis')

# --- Shared sidebar ---
st.sidebar.header('Settings')
symbol = st.sidebar.text_input('Ticker symbol', value='AAPL').strip().upper()
today = dt.date.today()
start = st.sidebar.date_input('Start date', value=today - dt.timedelta(days=365))
end = st.sidebar.date_input('End date', value=today)
ma_window = st.sidebar.slider('Short moving average window (days)',
                              min_value=5, max_value=200, value=20)
ma_long_window = st.sidebar.slider('Long moving average window (days)',
                                   min_value=5, max_value=200, value=50)
if ma_window >= ma_long_window:
    st.sidebar.warning('Short window should be smaller than the long window.')

if start >= end:
    st.sidebar.error('Start date must be before end date.')
    st.stop()

fetch = st.sidebar.button('Fetch data', type='primary')

tab_single, tab_portfolio = st.tabs(['Single Stock Analysis', 'Portfolio Comparison'])

# --- Tab 1: Single Stock Analysis ---
with tab_single:
    if fetch:
        # Remember the settings at click time so later widget changes don't refetch.
        st.session_state['single_args'] = (symbol, start, end, ma_window, ma_long_window)

    if 'single_args' not in st.session_state:
        st.info('Choose a ticker and settings in the sidebar, then click **Fetch data**.')
    elif not st.session_state['single_args'][0]:
        st.error('Enter a ticker symbol in the sidebar.')
    else:
        with st.spinner('Fetching data...'):
            stock = load_stock(*st.session_state['single_args'])

        if stock.data is None:
            st.error(stock.message)
        else:
            st.success(stock.message)

            col1, col2, col3 = st.columns(3)
            col1.metric('Last close', f"${stock.data['Close'].iloc[-1]:,.2f}",
                        f"{stock.data['change'].iloc[-1]:+.2f}")
            col2.metric('Cumulative log return', f"{stock.data['return'].sum():.2%}")
            col3.metric('Trading days', len(stock.data))

            st.plotly_chart(plot_price_ma(stock))
            st.plotly_chart(stock.plot_performance())
            st.plotly_chart(stock.plot_return_dist())

            st.subheader('Daily return statistics')
            st.dataframe(stock.data['return'].describe().to_frame())

# --- Tab 2: Portfolio Comparison ---
with tab_portfolio:
    tickers_text = st.text_input('Ticker symbols (comma-separated)',
                                 value='AAPL, MSFT, GOOG')
    # dict.fromkeys drops repeated tickers while keeping their order.
    tickers = list(dict.fromkeys(t.strip().upper() for t in tickers_text.split(',') if t.strip()))

    if st.button('Compare'):
        st.session_state['portfolio_args'] = (tuple(tickers), start, end, ma_window)

    if 'portfolio_args' not in st.session_state:
        st.info('Enter tickers and click **Compare**.')
    else:
        p_tickers, p_start, p_end, p_ma = st.session_state['portfolio_args']
        fig = go.Figure()
        with st.spinner('Fetching portfolio data...'):
            for ticker in p_tickers:
                stock = load_stock(ticker, p_start, p_end, p_ma)
                if stock.data is None:
                    st.error(f'{ticker}: {stock.message}')
                    continue
                perf = zero_based_performance(stock)
                fig.add_trace(go.Scatter(x=perf.index, y=perf, mode='lines', name=ticker))

        if fig.data:
            fig.update_layout(title='Zero-based Cumulative Performance',
                              xaxis_title='Date', yaxis_title='Cumulative log return',
                              legend_title='Ticker')
            st.plotly_chart(fig)
        else:
            st.warning('No tickers downloaded successfully.')
