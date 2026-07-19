from __future__ import annotations

from typing import Any

import pandas as pd

from charts import display_market_chart
from data.market_data import download_stock_data
from feedback import (
    RuleResult,
    generate_strategy_feedback,
)
from indicators.moving_averages import calculate_sma
from patterns.fvg_detector import (
    detect_fair_value_gaps,
    display_latest_fair_value_gap,
    get_latest_active_fair_value_gap,
)
from patterns.fvg_tracker import update_all_fvg_statuses
from strategy.opportunity_score import (
    calculate_opportunity_score,
    display_opportunity_report,
)
from strategy.signal_filter import should_notify
from strategy.trend_strategy import analyse_trend
from strategy.watchlist import get_watchlist


def get_single_series(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Extract one numeric Series from either normal columns
    or Yahoo Finance MultiIndex columns.
    """

    if dataframe is None or dataframe.empty:
        raise ValueError(
            "Cannot extract market values from an empty DataFrame."
        )

    if isinstance(dataframe.columns, pd.MultiIndex):
        first_level_columns = dataframe.columns.get_level_values(0)

        if column_name not in first_level_columns:
            raise ValueError(
                f"Market data does not contain '{column_name}'."
            )

        values = dataframe.xs(
            column_name,
            axis=1,
            level=0,
        )

        if isinstance(values, pd.DataFrame):
            if values.empty or values.shape[1] == 0:
                raise ValueError(
                    f"No usable '{column_name}' values were found."
                )

            values = values.iloc[:, 0]

    else:
        if column_name not in dataframe.columns:
            raise ValueError(
                f"Market data does not contain '{column_name}'."
            )

        values = dataframe[column_name]

    return pd.to_numeric(
        values,
        errors="coerce",
    )


def get_fvg_value(
    fair_value_gap: Any,
    possible_names: tuple[str, ...],
) -> Any:
    """
    Extract a value safely from either an FVG dictionary
    or an FVG object.
    """

    if fair_value_gap is None:
        return None

    if isinstance(fair_value_gap, dict):
        for name in possible_names:
            if name in fair_value_gap:
                return fair_value_gap[name]

        return None

    for name in possible_names:
        if hasattr(fair_value_gap, name):
            return getattr(fair_value_gap, name)

    return None


def is_bullish_fvg(
    fair_value_gap: Any,
) -> bool:
    """
    Determine whether the latest active Fair Value Gap
    is bullish.
    """

    if fair_value_gap is None:
        return False

    direction = get_fvg_value(
        fair_value_gap=fair_value_gap,
        possible_names=(
            "direction",
            "type",
            "gap_type",
            "fvg_type",
            "side",
        ),
    )

    if direction is None:
        return False

    direction_text = str(direction).strip().lower()

    bullish_terms = (
        "bullish",
        "bull",
        "buy",
        "long",
        "up",
    )

    return any(
        term in direction_text
        for term in bullish_terms
    )


def create_strategy_rules(
    current_price: float,
    previous_close: float,
    current_sma_20: float,
    previous_sma_20: float,
    current_sma_50: float,
    average_price: float,
    bullish_fvg: bool,
    strong_volume: bool,
) -> list[RuleResult]:
    """
    Create the current ApexAlpha strategy rules.
    """

    price_above_sma_20 = current_price > current_sma_20
    price_above_sma_50 = current_price > current_sma_50
    price_increased = current_price > previous_close
    sma_20_rising = current_sma_20 > previous_sma_20
    price_above_average = current_price > average_price

    return [
        RuleResult(
            name="Price above SMA 20",
            passed=price_above_sma_20,
            explanation=(
                "The current price is above the 20-day moving average."
                if price_above_sma_20
                else
                "The current price is below the 20-day moving average."
            ),
            category="required",
        ),
        RuleResult(
            name="Price above SMA 50",
            passed=price_above_sma_50,
            explanation=(
                "The current price is above the 50-day moving average."
                if price_above_sma_50
                else
                "The current price is below the 50-day moving average."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price increased today",
            passed=price_increased,
            explanation=(
                "The latest closing price is above the previous close."
                if price_increased
                else
                "The latest closing price did not rise above "
                "the previous close."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="SMA 20 is rising",
            passed=sma_20_rising,
            explanation=(
                "The 20-day moving average is rising."
                if sma_20_rising
                else
                "The 20-day moving average is flat or falling."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price above recent average",
            passed=price_above_average,
            explanation=(
                "The current price is above its recent average."
                if price_above_average
                else
                "The current price is below its recent average."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Bullish Fair Value Gap",
            passed=bullish_fvg,
            explanation=(
                "An active bullish Fair Value Gap was detected."
                if bullish_fvg
                else
                "No active bullish Fair Value Gap was detected."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Strong volume",
            passed=strong_volume,
            explanation=(
                "Current volume is above the confirmation threshold."
                if strong_volume
                else
                "Current volume is below the confirmation threshold."
            ),
            category="confirmation",
        ),
    ]


def analyse_stock(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
    show_chart: bool = True,
) -> None:
    """
    Download and analyse one market symbol.
    """

    print("\n")
    print("=" * 70)
    print(f"APEXALPHA MARKET ANALYSIS: {symbol}")
    print("=" * 70)

    try:
        data = download_stock_data(
            symbol=symbol,
            period=period,
            interval=interval,
        )

        if data is None or data.empty:
            print(f"No market data was returned for {symbol}.")
            return

        data = calculate_sma(
            dataframe=data,
            period=20,
        )

        data = calculate_sma(
            dataframe=data,
            period=50,
        )

        close_prices = get_single_series(
            dataframe=data,
            column_name="Close",
        )

        sma_20 = get_single_series(
            dataframe=data,
            column_name="SMA_20",
        )

        sma_50 = get_single_series(
            dataframe=data,
            column_name="SMA_50",
        )

        try:
            volume = get_single_series(
                dataframe=data,
                column_name="Volume",
            )
        except ValueError:
            volume = pd.Series(
                index=data.index,
                dtype="float64",
            )

        market_values = pd.DataFrame(
            {
                "Close": close_prices,
                "SMA_20": sma_20,
                "SMA_50": sma_50,
                "Volume": volume,
            }
        )

        valid_market_data = market_values.dropna(
            subset=[
                "Close",
                "SMA_20",
                "SMA_50",
            ]
        )

        if len(valid_market_data) < 2:
            print(
                f"Not enough valid market data exists for {symbol}."
            )
            return

        current_price = float(
            valid_market_data["Close"].iloc[-1]
        )

        previous_close = float(
            valid_market_data["Close"].iloc[-2]
        )

        current_sma_20 = float(
            valid_market_data["SMA_20"].iloc[-1]
        )

        previous_sma_20 = float(
            valid_market_data["SMA_20"].iloc[-2]
        )

        current_sma_50 = float(
            valid_market_data["SMA_50"].iloc[-1]
        )

        average_price = float(
            valid_market_data["Close"]
            .tail(20)
            .mean()
        )

        volume_values = valid_market_data[
            "Volume"
        ].dropna()

        if volume_values.empty:
            current_volume = None
            average_volume = None
            strong_volume = False
        else:
            current_volume = float(
                volume_values.iloc[-1]
            )

            average_volume = float(
                volume_values.tail(20).mean()
            )

            strong_volume = bool(
                average_volume > 0
                and current_volume >= average_volume * 1.20
            )

        price_change = current_price - previous_close

        if previous_close != 0:
            price_change_percentage = (
                price_change / previous_close
            ) * 100
        else:
            price_change_percentage = 0.0

        trend = analyse_trend(
            current_price=current_price,
            moving_average=current_sma_20,
        )

        trend_text = str(trend)

        trend_confirmed = any(
            word in trend_text.lower()
            for word in (
                "buy",
                "bull",
                "up",
                "long",
            )
        )

        print("\nMarket Summary")
        print("-" * 50)
        print(f"Symbol:              {symbol}")
        print(f"Current price:       {current_price:.2f}")
        print(f"Previous close:      {previous_close:.2f}")
        print(f"Daily change:        {price_change:.2f}")
        print(
            f"Daily change (%):    "
            f"{price_change_percentage:.2f}%"
        )
        print(f"SMA 20:              {current_sma_20:.2f}")
        print(f"SMA 50:              {current_sma_50:.2f}")
        print(f"Recent average:      {average_price:.2f}")
        print(f"Trend:               {trend_text}")

        if current_volume is not None:
            print(f"Current volume:      {current_volume:,.0f}")

        if average_volume is not None:
            print(f"Average volume:      {average_volume:,.0f}")

        print(
            "Volume confirmation: "
            f"{'Strong' if strong_volume else 'Normal'}"
        )

        print("\nFair Value Gap Analysis")
        print("-" * 50)

        fair_value_gaps = detect_fair_value_gaps(
            dataframe=data,
            symbol=symbol,
        )

        updated_fair_value_gaps = update_all_fvg_statuses(
            dataframe=data,
            fair_value_gaps=fair_value_gaps,
        )

        latest_fvg = get_latest_active_fair_value_gap(
            updated_fair_value_gaps
        )

        display_latest_fair_value_gap(
            symbol=symbol,
            fair_value_gap=latest_fvg,
        )

        bullish_fvg = is_bullish_fvg(
            fair_value_gap=latest_fvg
        )

        if current_sma_20 != 0:
            price_distance_from_sma_20 = abs(
                (
                    current_price - current_sma_20
                )
                / current_sma_20
            ) * 100
        else:
            price_distance_from_sma_20 = float("inf")

        low_risk = bool(
            current_price > current_sma_20
            and price_distance_from_sma_20 <= 5
        )

        risk_label = (
            "Controlled"
            if low_risk
            else "Elevated"
        )

        if bullish_fvg:
            fvg_label = "Active Bullish"
        elif latest_fvg is not None:
            fvg_label = "Active Non-Bullish"
        else:
            fvg_label = "None"

        print("\nStrategy Feedback")
        print("-" * 50)

        strategy_rules = create_strategy_rules(
            current_price=current_price,
            previous_close=previous_close,
            current_sma_20=current_sma_20,
            previous_sma_20=previous_sma_20,
            current_sma_50=current_sma_50,
            average_price=average_price,
            bullish_fvg=bullish_fvg,
            strong_volume=strong_volume,
        )

        strategy_feedback = generate_strategy_feedback(
            rules=strategy_rules,
            direction=trend_text,
        )

        strategy_feedback.display()

        score_data = calculate_opportunity_score(
            trend=trend_confirmed,
            sma20=current_price > current_sma_20,
            sma50=current_price > current_sma_50,
            bullish_fvg=bullish_fvg,
            strong_volume=strong_volume,
            low_risk=low_risk,
        )

        display_opportunity_report(
            symbol=symbol,
            score_data=score_data,
            trend=trend_text,
            fvg=fvg_label,
            risk=risk_label,
        )

        notification_required = should_notify(
            score=score_data["score"],
            minimum_score=85,
        )

        if notification_required:
            print("\n" + "!" * 70)
            print(f"APEXALPHA OPPORTUNITY ALERT: {symbol}")
            print(
                "The market has something worth seeing."
            )
            print("!" * 70)
        else:
            print(
                "\nApexAlpha remains silent: "
                "the opportunity has not reached "
                "the notification threshold."
            )

        if show_chart:
            display_market_chart(
                dataframe=data,
                symbol=symbol,
                fair_value_gaps=updated_fair_value_gaps,
                candle_limit=80,
            )

    except Exception as error:
        print(f"\nApexAlpha could not analyse {symbol}.")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")


def main() -> None:
    """
    ApexAlpha application entry point.
    """

    print("\n")
    print("=" * 70)
    print("APEXALPHA")
    print("Market Intelligence and Strategy Analysis Platform")
    print("=" * 70)

    symbols = get_watchlist()

    if not symbols:
        print("\nThe ApexAlpha watchlist is empty.")
        return

    print(
        f"\nScanning {len(symbols)} symbols: "
        f"{', '.join(symbols)}"
    )

    for symbol in symbols:
        analyse_stock(
            symbol=symbol,
            period="6mo",
            interval="1d",
            show_chart=True,
        )

    print("\n")
    print("=" * 70)
    print("APEXALPHA SCAN COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()