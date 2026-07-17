from __future__ import annotations

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
from strategy.trend_strategy import analyse_trend


def get_single_series(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Extracts one numeric Series from either standard columns
    or Yahoo Finance MultiIndex columns.
    """

    if dataframe.empty:
        raise ValueError(
            "Cannot extract market values from an empty DataFrame."
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


def create_strategy_rules(
    current_price: float,
    previous_close: float,
    current_sma: float,
    previous_sma: float,
    average_price: float,
) -> list[RuleResult]:
    """
    Creates the current ApexAlpha trend-following strategy rules.
    """

    rules = [
        RuleResult(
            name="Price above SMA 20",
            passed=current_price > current_sma,
            explanation=(
                "The current price is above the 20-day moving average."
                if current_price > current_sma
                else
                "The current price is below the 20-day moving average."
            ),
            category="required",
        ),
        RuleResult(
            name="Price increased today",
            passed=current_price > previous_close,
            explanation=(
                "The latest closing price is above the previous close."
                if current_price > previous_close
                else
                "The latest closing price did not rise above the previous close."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="SMA 20 is rising",
            passed=current_sma > previous_sma,
            explanation=(
                "The 20-day moving average is rising."
                if current_sma > previous_sma
                else
                "The 20-day moving average is flat or falling."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price above recent average",
            passed=current_price > average_price,
            explanation=(
                "The current price is above its recent average price."
                if current_price > average_price
                else
                "The current price is below its recent average price."
            ),
            category="confirmation",
        ),
    ]

    return rules


def analyse_stock(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
    show_chart: bool = True,
) -> None:
    """
    Downloads and analyses one market symbol.

    The analysis includes:

    - Current market summary
    - SMA 20
    - Trend direction
    - Fair Value Gap detection
    - Fair Value Gap lifecycle tracking
    - Strategy feedback
    - Candlestick chart with FVG overlays
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
            print(
                f"No market data was returned for {symbol}."
            )
            return

        data = calculate_sma(
            dataframe=data,
            period=20,
        )

        close_prices = get_single_series(
            dataframe=data,
            column_name="Close",
        )

        sma_20 = get_single_series(
            dataframe=data,
            column_name="SMA_20",
        )

        valid_market_data = pd.DataFrame(
            {
                "Close": close_prices,
                "SMA_20": sma_20,
            }
        ).dropna()

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

        current_sma = float(
            valid_market_data["SMA_20"].iloc[-1]
        )

        previous_sma = float(
            valid_market_data["SMA_20"].iloc[-2]
        )

        average_price = float(
            valid_market_data["Close"].tail(20).mean()
        )

        price_change = current_price - previous_close

        price_change_percentage = (
            price_change / previous_close
        ) * 100

        trend = analyse_trend(
            current_price=current_price,
            moving_average=current_sma,
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
        print(f"SMA 20:              {current_sma:.2f}")
        print(f"Recent average:      {average_price:.2f}")
        print(f"Trend:               {trend}")

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

        print("\nStrategy Feedback")
        print("-" * 50)

        strategy_rules = create_strategy_rules(
            current_price=current_price,
            previous_close=previous_close,
            current_sma=current_sma,
            previous_sma=previous_sma,
            average_price=average_price,
        )

        strategy_feedback = generate_strategy_feedback(
            rules=strategy_rules,
            direction=trend,
        )

        strategy_feedback.display()

        if show_chart:
            display_market_chart(
                dataframe=data,
                symbol=symbol,
                fair_value_gaps=updated_fair_value_gaps,
                candle_limit=80,
            )

    except Exception as error:
        print(
            f"\nApexAlpha could not analyse {symbol}."
        )
        print(
            f"Error: {error}"
        )


def main() -> None:
    """
    ApexAlpha application entry point.
    """

    print("\n")
    print("=" * 70)
    print("APEXALPHA")
    print("Market Intelligence and Strategy Analysis Platform")
    print("=" * 70)

    symbols = [
        "AAPL",
        "MSFT",
        "NVDA",
        "GOOGL",
        "AMZN",
    ]

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