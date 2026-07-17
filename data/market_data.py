import yfinance as yf
import pandas as pd


def download_stock_data(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Downloads market data from Yahoo Finance.
    """

    print(f"Downloading {symbol}...")

    data = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise ValueError(
            f"No data returned for {symbol}."
        )

    file_path = f"database/{symbol}.csv"

    data.to_csv(file_path)

    print(f"{symbol} saved to {file_path}")

    return data