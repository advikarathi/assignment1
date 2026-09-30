import numpy as np
import plotly.express as px
import yfinance as yf


class Stock:
    def __init__(self, symbol, start=None, end=None, ma_window=10,
                 ma_long_window=None):
        self.symbol = symbol
        self.start = start
        self.end = end
        self.ma_window = ma_window
        self.ma_long_window = ma_long_window
        self.data, self.message = self.get_data()

    def get_data(self):
        try:
            data = yf.download(self.symbol,
                               start=self.start,
                               end=self.end,
                               progress=False,
                               multi_level_index=False)
            if data.empty:
                return None, f"No data found for {self.symbol}"
            data = self._calc_returns(data)
            if data.empty:
                return None, f"Not enough data for {self.symbol}; choose a longer date range"
            data = self._calc_ma(data, self.ma_window)
            if self.ma_long_window is not None:
                data = self._calc_ma(data, self.ma_long_window, column='MA_long')
            return data, f"Successfully downloaded for {self.symbol}"
        except Exception as e:
            return None, f"Failed due to {e}"

    def _calc_returns(self, df):
        df['change'] = df['Close'] - df['Close'].shift(1)
        df['return'] = np.log(df['Close']).diff().round(4)
        # First trading day has no prior close; keep later MA NaNs in place.
        return df.dropna(subset=['change', 'return'])

    def _calc_ma(self, df, window, column='MA'):
        df[column] = df['Close'].rolling(window=window).mean()
        return df

    def plot_performance(self):
        """Return a Plotly line chart of cumulative (log) return."""
        performance = self.data['return'].cumsum()
        fig = px.line(x=performance.index,
                      y=performance.values,
                      title=f'Cumulative Return for {self.symbol}',
                      labels={'x': 'Date', 'y': 'Cumulative Return'})
        fig.update_traces(line=dict(color='#2ca02c', width=2))
        fig.add_hline(y=0, line_dash='dash', line_color='black', opacity=0.7)
        fig.update_layout(yaxis_tickformat='.1%', hovermode='x unified',
                          showlegend=False)
        return fig

    def plot_return_dist(self):
        """Return a Plotly histogram of daily log returns."""
        mean_return = self.data['return'].mean()
        fig = px.histogram(self.data['return'],
                           nbins=35,
                           title=f'Distribution of Daily Returns for {self.symbol}',
                           labels={'value': 'Return', 'count': 'Frequency'},
                           opacity=0.85,
                           color_discrete_sequence=['#1f77b4'])
        fig.update_traces(marker_line_color='rgb(255,255,255)',
                          marker_line_width=0.5)
        fig.add_vline(x=mean_return,
                      line_dash='dash',
                      line_color='red',
                      annotation_text=f'Mean: {mean_return:.4f}',
                      annotation_position='top right')
        return fig


# --- For development testing only ---
def main():
    test = Stock(symbol='AAPL', start="2025-09-24", end="2026-09-23")
    print(test.data)
    #print(test.message)
    fig = test.plot_return_dist()
    fig.show()


if __name__ == '__main__':
    main()