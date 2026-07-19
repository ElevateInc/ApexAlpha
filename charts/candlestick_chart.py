import mplfinance as mpf
import pandas as pd


def display_market_chart(
    dataframe,
    symbol,
    fair_value_gaps=None,
    candle_limit=80,
):
    """
    Display professional candlestick chart.
    """

    if dataframe is None or dataframe.empty:
        print("No market data available.")
        return

    df = dataframe.copy()

    # ------------------------------
    # Handle Yahoo Finance MultiIndex
    # ------------------------------
    if isinstance(df.columns, pd.MultiIndex):

        cleaned = {}

        for column in ["Open", "High", "Low", "Close", "Volume"]:

            if column in df.columns.get_level_values(0):

                cleaned[column] = df[column].iloc[:, 0]

        df = pd.DataFrame(cleaned)

    # ------------------------------
    # Keep recent candles
    # ------------------------------

    df = df.tail(candle_limit)

    # ------------------------------
    # Ensure datetime index
    # ------------------------------

    df.index = pd.to_datetime(df.index)

    # ------------------------------
    # Create Moving Average
    # ------------------------------

    df["SMA20"] = df["Close"].rolling(20).mean()

    # ------------------------------
    # Build chart
    # ------------------------------

    mpf.plot(
        df,
        type="candle",
        style="yahoo",
        mav=(20,),
        volume=True,
        title=f"{symbol} Market Analysis",
        ylabel="Price",
        ylabel_lower="Volume",
        figsize=(14, 8),
        tight_layout=True,
    )