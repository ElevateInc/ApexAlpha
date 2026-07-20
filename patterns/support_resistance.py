import pandas as pd


def get_price_series(df, column_name):
    """
    Returns a price series even if the dataframe
    uses MultiIndex columns.
    """

    if column_name in df.columns:
        return df[column_name]

    if isinstance(df.columns, pd.MultiIndex):
        for col in df.columns:
            if column_name in col:
                return df[col]

    raise KeyError(f"Column '{column_name}' not found.")


def detect_support_resistance(df, window=5):
    supports = []
    resistances = []

    lows = get_price_series(df, "Low")
    highs = get_price_series(df, "High")

    for i in range(window, len(df) - window):

        low_window = lows.iloc[i - window : i + window + 1]
        high_window = highs.iloc[i - window : i + window + 1]

        if lows.iloc[i] == low_window.min():
            supports.append(float(lows.iloc[i]))

        if highs.iloc[i] == high_window.max():
            resistances.append(float(highs.iloc[i]))

    return supports, resistances


def nearest_support(current_price, supports):
    below = [x for x in supports if x <= current_price]

    if not below:
        return None

    return max(below)


def nearest_resistance(current_price, resistances):
    above = [x for x in resistances if x >= current_price]

    if not above:
        return None

    return min(above)


def percent_distance(current_price, level):

    if level is None:
        return None

    return abs(current_price - level) / current_price * 100