import pandas as pd

from patterns.fair_value_gap import FairValueGap


def get_market_series(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Returns one usable pandas Series from either normal
    or Yahoo Finance MultiIndex market-data columns.
    """

    if dataframe.empty:
        raise ValueError(
            "Cannot track a Fair Value Gap using empty market data."
        )

    if isinstance(dataframe.columns, pd.MultiIndex):
        available_columns = dataframe.columns.get_level_values(0)

        if column_name not in available_columns:
            raise ValueError(
                f"Market data does not contain '{column_name}'."
            )

        values = dataframe.xs(
            column_name,
            axis=1,
            level=0,
        )

    else:
        if column_name not in dataframe.columns:
            raise ValueError(
                f"Market data does not contain '{column_name}'."
            )

        values = dataframe[column_name]

    if isinstance(values, pd.DataFrame):
        if values.empty or values.shape[1] == 0:
            raise ValueError(
                f"The '{column_name}' column contains no usable data."
            )

        values = values.iloc[:, 0]

    return pd.to_numeric(
        values,
        errors="coerce",
    )


def calculate_bullish_fvg_status(
    fair_value_gap: FairValueGap,
    future_data: pd.DataFrame,
) -> FairValueGap:
    """
    Tracks the lifecycle of a bullish Fair Value Gap.

    Price enters a bullish FVG by moving down from above.

    A wick reaching the lower boundary means the gap has been
    fully mitigated.

    A close below the lower boundary invalidates the setup.
    """

    lows = get_market_series(
        dataframe=future_data,
        column_name="Low",
    )

    closes = get_market_series(
        dataframe=future_data,
        column_name="Close",
    )

    deepest_price = fair_value_gap.upper_boundary

    for position in range(len(future_data)):
        candle_low = lows.iloc[position]
        candle_close = closes.iloc[position]

        if pd.isna(candle_low) or pd.isna(candle_close):
            continue

        candle_low = float(candle_low)
        candle_close = float(candle_close)
        candle_time = future_data.index[position]

        if candle_close < fair_value_gap.lower_boundary:
            fair_value_gap.status = "INVALIDATED"
            fair_value_gap.mitigation_percentage = 100.0
            fair_value_gap.invalidation_time = candle_time

            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            return fair_value_gap

        if candle_low <= fair_value_gap.lower_boundary:
            fair_value_gap.status = "FULLY_MITIGATED"
            fair_value_gap.mitigation_percentage = 100.0

            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            return fair_value_gap

        if candle_low < fair_value_gap.upper_boundary:
            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            deepest_price = min(
                deepest_price,
                candle_low,
            )

    if deepest_price < fair_value_gap.upper_boundary:
        penetration = (
            fair_value_gap.upper_boundary
            - deepest_price
        )

        mitigation_percentage = (
            penetration / fair_value_gap.gap_size
        ) * 100

        fair_value_gap.mitigation_percentage = min(
            mitigation_percentage,
            99.99,
        )

        fair_value_gap.status = "PARTIALLY_MITIGATED"

    return fair_value_gap


def calculate_bearish_fvg_status(
    fair_value_gap: FairValueGap,
    future_data: pd.DataFrame,
) -> FairValueGap:
    """
    Tracks the lifecycle of a bearish Fair Value Gap.

    Price enters a bearish FVG by moving up from below.

    A wick reaching the upper boundary means the gap has been
    fully mitigated.

    A close above the upper boundary invalidates the setup.
    """

    highs = get_market_series(
        dataframe=future_data,
        column_name="High",
    )

    closes = get_market_series(
        dataframe=future_data,
        column_name="Close",
    )

    highest_price = fair_value_gap.lower_boundary

    for position in range(len(future_data)):
        candle_high = highs.iloc[position]
        candle_close = closes.iloc[position]

        if pd.isna(candle_high) or pd.isna(candle_close):
            continue

        candle_high = float(candle_high)
        candle_close = float(candle_close)
        candle_time = future_data.index[position]

        if candle_close > fair_value_gap.upper_boundary:
            fair_value_gap.status = "INVALIDATED"
            fair_value_gap.mitigation_percentage = 100.0
            fair_value_gap.invalidation_time = candle_time

            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            return fair_value_gap

        if candle_high >= fair_value_gap.upper_boundary:
            fair_value_gap.status = "FULLY_MITIGATED"
            fair_value_gap.mitigation_percentage = 100.0

            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            return fair_value_gap

        if candle_high > fair_value_gap.lower_boundary:
            if fair_value_gap.entry_time is None:
                fair_value_gap.entry_time = candle_time

            highest_price = max(
                highest_price,
                candle_high,
            )

    if highest_price > fair_value_gap.lower_boundary:
        penetration = (
            highest_price
            - fair_value_gap.lower_boundary
        )

        mitigation_percentage = (
            penetration / fair_value_gap.gap_size
        ) * 100

        fair_value_gap.mitigation_percentage = min(
            mitigation_percentage,
            99.99,
        )

        fair_value_gap.status = "PARTIALLY_MITIGATED"

    return fair_value_gap


def update_fvg_status(
    dataframe: pd.DataFrame,
    fair_value_gap: FairValueGap,
) -> FairValueGap:
    """
    Calculates the lifecycle status, mitigation percentage,
    entry time, invalidation time, and age of one Fair Value Gap.
    """

    if dataframe.empty:
        return fair_value_gap

    final_position = len(dataframe) - 1

    fair_value_gap.age_candles = max(
        final_position - fair_value_gap.candle_position,
        0,
    )

    first_future_position = (
        fair_value_gap.candle_position + 1
    )

    if first_future_position >= len(dataframe):
        return fair_value_gap

    future_data = dataframe.iloc[
        first_future_position:
    ]

    if future_data.empty:
        return fair_value_gap

    if fair_value_gap.direction == "BULLISH":
        return calculate_bullish_fvg_status(
            fair_value_gap=fair_value_gap,
            future_data=future_data,
        )

    if fair_value_gap.direction == "BEARISH":
        return calculate_bearish_fvg_status(
            fair_value_gap=fair_value_gap,
            future_data=future_data,
        )

    raise ValueError(
        "FVG direction must be either BULLISH or BEARISH."
    )


def update_all_fvg_statuses(
    dataframe: pd.DataFrame,
    fair_value_gaps: list[FairValueGap],
) -> list[FairValueGap]:
    """
    Updates the lifecycle status of every detected Fair Value Gap.
    """

    updated_gaps = []

    for fair_value_gap in fair_value_gaps:
        updated_gap = update_fvg_status(
            dataframe=dataframe,
            fair_value_gap=fair_value_gap,
        )

        updated_gaps.append(updated_gap)

    return updated_gaps