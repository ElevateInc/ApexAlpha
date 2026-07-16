import pandas as pd


def add_simple_moving_average(
    data: pd.DataFrame,
    period: int = 20,
) -> pd.DataFrame:
    """Add a simple moving-average column to market data."""

    result = data.copy()
    result[f"SMA_{period}"] = result["Close"].rolling(window=period).mean()

    return result