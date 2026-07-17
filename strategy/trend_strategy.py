def analyse_trend(latest_close: float, sma_20: float) -> str:
    """Simple trend strategy based on the 20-day SMA."""

    if latest_close > sma_20:
        return "BUY"

    elif latest_close < sma_20:
        return "SELL"

    else:
        return "HOLD"