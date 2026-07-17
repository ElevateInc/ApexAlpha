from typing import List, Optional

import pandas as pd

from patterns.fair_value_gap import FairValueGap


def get_price_series(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Returns one Series from normal or Yahoo Finance
    MultiIndex columns.
    """

    if dataframe.empty:
        raise ValueError(
            "Cannot retrieve prices from empty market data."
        )

    if isinstance(dataframe.columns, pd.MultiIndex):
        first_level_columns = (
            dataframe.columns.get_level_values(0)
        )

        if column_name not in first_level_columns:
            raise ValueError(
                f"Market data does not contain "
                f"'{column_name}'."
            )

        values = dataframe.xs(
            column_name,
            axis=1,
            level=0,
        )

    else:
        if column_name not in dataframe.columns:
            raise ValueError(
                f"Market data does not contain "
                f"'{column_name}'."
            )

        values = dataframe[column_name]

    if isinstance(values, pd.DataFrame):
        values = values.iloc[:, 0]

    return pd.to_numeric(
        values,
        errors="coerce",
    )


def detect_fair_value_gaps(
    dataframe: pd.DataFrame,
    symbol: str,
    minimum_gap_size: float = 0.0,
) -> List[FairValueGap]:
    """
    Detects bullish and bearish three-candle FVGs.

    Bullish:
        Candle 1 High < Candle 3 Low

    Bearish:
        Candle 1 Low > Candle 3 High
    """

    if minimum_gap_size < 0:
        raise ValueError(
            "Minimum gap size cannot be negative."
        )

    if len(dataframe) < 3:
        return []

    highs = get_price_series(
        dataframe=dataframe,
        column_name="High",
    )

    lows = get_price_series(
        dataframe=dataframe,
        column_name="Low",
    )

    fair_value_gaps = []

    for candle_three_position in range(
        2,
        len(dataframe),
    ):
        candle_one_position = candle_three_position - 2

        candle_one_high = highs.iloc[
            candle_one_position
        ]
        candle_one_low = lows.iloc[
            candle_one_position
        ]
        candle_three_high = highs.iloc[
            candle_three_position
        ]
        candle_three_low = lows.iloc[
            candle_three_position
        ]

        required_values = [
            candle_one_high,
            candle_one_low,
            candle_three_high,
            candle_three_low,
        ]

        if any(
            pd.isna(value)
            for value in required_values
        ):
            continue

        candle_one_high = float(candle_one_high)
        candle_one_low = float(candle_one_low)
        candle_three_high = float(candle_three_high)
        candle_three_low = float(candle_three_low)

        formation_time = dataframe.index[
            candle_three_position
        ]

        bullish_gap_size = (
            candle_three_low - candle_one_high
        )

        if bullish_gap_size > minimum_gap_size:
            fair_value_gaps.append(
                FairValueGap(
                    symbol=symbol,
                    direction="BULLISH",
                    lower_boundary=candle_one_high,
                    upper_boundary=candle_three_low,
                    formation_time=formation_time,
                    candle_position=candle_three_position,
                    gap_size=bullish_gap_size,
                )
            )

        bearish_gap_size = (
            candle_one_low - candle_three_high
        )

        if bearish_gap_size > minimum_gap_size:
            fair_value_gaps.append(
                FairValueGap(
                    symbol=symbol,
                    direction="BEARISH",
                    lower_boundary=candle_three_high,
                    upper_boundary=candle_one_low,
                    formation_time=formation_time,
                    candle_position=candle_three_position,
                    gap_size=bearish_gap_size,
                )
            )

    return fair_value_gaps


def get_latest_fair_value_gap(
    fair_value_gaps: List[FairValueGap],
) -> Optional[FairValueGap]:
    """
    Returns the newest detected FVG.
    """

    if not fair_value_gaps:
        return None

    return max(
        fair_value_gaps,
        key=lambda gap: gap.candle_position,
    )


def get_latest_active_fair_value_gap(
    fair_value_gaps: List[FairValueGap],
) -> Optional[FairValueGap]:
    """
    Returns the newest FVG that remains active.
    """

    active_gaps = [
        gap
        for gap in fair_value_gaps
        if gap.is_active()
    ]

    if not active_gaps:
        return None

    return max(
        active_gaps,
        key=lambda gap: gap.candle_position,
    )


def display_latest_fair_value_gap(
    symbol: str,
    fair_value_gap: Optional[FairValueGap],
) -> None:
    """
    Displays an FVG lifecycle report.
    """

    print(f"\n{symbol} Fair Value Gap Analysis")
    print("-" * 45)

    if fair_value_gap is None:
        print("No qualifying active Fair Value Gap.")
        return

    print(
        f"Direction      : "
        f"{fair_value_gap.direction}"
    )
    print(
        f"Formation Time : "
        f"{fair_value_gap.formation_time}"
    )
    print(
        f"Gap Zone       : "
        f"{fair_value_gap.display_zone()}"
    )
    print(
        f"Gap Midpoint   : "
        f"${fair_value_gap.midpoint:.2f}"
    )
    print(
        f"Gap Size       : "
        f"${fair_value_gap.gap_size:.4f}"
    )
    print(
        f"Age            : "
        f"{fair_value_gap.age_candles} candles"
    )
    print(
        f"Status         : "
        f"{fair_value_gap.status}"
    )
    print(
        f"Mitigation     : "
        f"{fair_value_gap.mitigation_percentage:.2f}%"
    )

    if fair_value_gap.entry_time is not None:
        print(
            f"First Entry    : "
            f"{fair_value_gap.entry_time}"
        )

    if fair_value_gap.invalidation_time is not None:
        print(
            f"Invalidated At : "
            f"{fair_value_gap.invalidation_time}"
        )