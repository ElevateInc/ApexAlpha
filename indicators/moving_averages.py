from __future__ import annotations

import pandas as pd


def add_moving_averages(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add the moving averages required by ApexAlpha.

    Indicators added:
    - SMA20
    - SMA50
    - SMA200
    - EMA20
    - EMA50

    Parameters
    ----------
    data:
        Market price DataFrame containing a Close column.

    Returns
    -------
    pd.DataFrame
        A copy of the original DataFrame with moving-average columns added.
    """

    if data is None or data.empty:
        raise ValueError("Market data is empty.")

    if "Close" not in data.columns:
        raise KeyError("Market data must contain a 'Close' column.")

    result = data.copy()

    close_prices = result["Close"]

    # Handle yfinance MultiIndex columns where Close may return a DataFrame.
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    close_prices = pd.to_numeric(close_prices, errors="coerce")

    result["SMA20"] = close_prices.rolling(
        window=20,
        min_periods=20,
    ).mean()

    result["SMA50"] = close_prices.rolling(
        window=50,
        min_periods=50,
    ).mean()

    result["SMA200"] = close_prices.rolling(
        window=200,
        min_periods=200,
    ).mean()

    result["EMA20"] = close_prices.ewm(
        span=20,
        adjust=False,
        min_periods=20,
    ).mean()

    result["EMA50"] = close_prices.ewm(
        span=50,
        adjust=False,
        min_periods=50,
    ).mean()

    return result


def calculate_sma(
    data: pd.DataFrame,
    period: int,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate a Simple Moving Average for any chosen period.
    """

    if period <= 0:
        raise ValueError("SMA period must be greater than zero.")

    if column not in data.columns:
        raise KeyError(f"Column '{column}' was not found.")

    values = data[column]

    if isinstance(values, pd.DataFrame):
        values = values.iloc[:, 0]

    values = pd.to_numeric(values, errors="coerce")

    return values.rolling(
        window=period,
        min_periods=period,
    ).mean()


def calculate_ema(
    data: pd.DataFrame,
    period: int,
    column: str = "Close",
) -> pd.Series:
    """
    Calculate an Exponential Moving Average for any chosen period.
    """

    if period <= 0:
        raise ValueError("EMA period must be greater than zero.")

    if column not in data.columns:
        raise KeyError(f"Column '{column}' was not found.")

    values = data[column]

    if isinstance(values, pd.DataFrame):
        values = values.iloc[:, 0]

    values = pd.to_numeric(values, errors="coerce")

    return values.ewm(
        span=period,
        adjust=False,
        min_periods=period,
    ).mean()


def has_sufficient_history(
    data: pd.DataFrame,
    minimum_rows: int = 200,
) -> bool:
    """
    Confirm that enough market history exists for long-term indicators.
    """

    return data is not None and len(data) >= minimum_rows