def analyse_trend(
    current_price: float,
    moving_average: float,
) -> str:
    """
    Determines the trend using the current price
    and the moving average.
    """

    if current_price > moving_average:
        return "BUY"

    elif current_price < moving_average:
        return "SELL"

    return "HOLD"