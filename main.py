import pandas as pd

from data.market_data import download_stock
from feedback.explanations import build_rule_explanation
from feedback.rule_result import RuleResult
from feedback.strategy_feedback import (
    analyse_strategy_feedback,
    display_strategy_feedback,
)
from indicators.moving_averages import add_simple_moving_average
from strategy.trend_strategy import analyse_trend


def get_single_series(dataframe, column_name):
    """
    Returns one pandas Series even when a market-data provider
    returns the selected column as a one-column DataFrame.
    """

    values = dataframe[column_name]

    if values.ndim == 2:
        values = values.iloc[:, 0]

    return values.dropna()


def create_strategy_rules(
    latest_close,
    previous_close,
    latest_sma_20,
    previous_sma_20,
    average_close,
):
    """
    Creates the current Apex Alpha strategy rules.

    These rules can later be replaced or extended by rules created
    through the interactive strategy builder.
    """

    strategy_rules = []

    price_above_sma = latest_close > latest_sma_20

    strategy_rules.append(
        RuleResult(
            name="Price above 20-day SMA",
            passed=price_above_sma,
            actual_value=f"${latest_close:.2f}",
            expected_value=f"Above ${latest_sma_20:.2f}",
            explanation=build_rule_explanation(
                rule_name="Price above 20-day SMA",
                passed=price_above_sma,
            ),
        )
    )

    price_increased = latest_close > previous_close

    strategy_rules.append(
        RuleResult(
            name="Price increased today",
            passed=price_increased,
            actual_value=(
                f"${latest_close:.2f} versus "
                f"${previous_close:.2f}"
            ),
            expected_value="Latest close above previous close",
            explanation=build_rule_explanation(
                rule_name="Price increased today",
                passed=price_increased,
            ),
        )
    )

    sma_is_rising = latest_sma_20 > previous_sma_20

    strategy_rules.append(
        RuleResult(
            name="20-day SMA is rising",
            passed=sma_is_rising,
            actual_value=(
                f"${latest_sma_20:.2f} versus "
                f"${previous_sma_20:.2f}"
            ),
            expected_value="Latest SMA above previous SMA",
            explanation=build_rule_explanation(
                rule_name="20-day SMA is rising",
                passed=sma_is_rising,
            ),
        )
    )

    price_above_average = latest_close > average_close

    strategy_rules.append(
        RuleResult(
            name="Price above period average",
            passed=price_above_average,
            actual_value=f"${latest_close:.2f}",
            expected_value=f"Above ${average_close:.2f}",
            explanation=build_rule_explanation(
                rule_name="Price above period average",
                passed=price_above_average,
            ),
        )
    )

    return strategy_rules


def analyse_stock(stock):
    """
    Downloads, analyses, and displays results for one stock.
    """

    print(f"\nScanning {stock}...")

    data = download_stock(stock)

    if data.empty:
        print(
            f"{stock} could not be analysed because "
            f"no data was returned."
        )
        return

    data = add_simple_moving_average(
        data,
        period=20,
    )

    close_prices = get_single_series(
        dataframe=data,
        column_name="Close",
    )

    sma_20_values = get_single_series(
        dataframe=data,
        column_name="SMA_20",
    )

    if len(close_prices) < 2:
        print(
            f"{stock} could not be analysed because there "
            f"are not enough closing-price records."
        )
        return

    if len(sma_20_values) < 2:
        print(
            f"{stock} could not be analysed because there "
            f"are not enough 20-day SMA records."
        )
        return

    latest_close = float(close_prices.iloc[-1])
    previous_close = float(close_prices.iloc[-2])

    highest_close = float(close_prices.max())
    lowest_close = float(close_prices.min())
    average_close = float(close_prices.mean())

    latest_sma_20 = float(sma_20_values.iloc[-1])
    previous_sma_20 = float(sma_20_values.iloc[-2])

    values_to_validate = [
        latest_close,
        previous_close,
        highest_close,
        lowest_close,
        average_close,
        latest_sma_20,
        previous_sma_20,
    ]

    if any(pd.isna(value) for value in values_to_validate):
        print(
            f"{stock} could not be analysed because one or "
            f"more required values are missing."
        )
        return

    trend_decision = analyse_trend(
        latest_close=latest_close,
        sma_20=latest_sma_20,
    )

    print(f"\n{stock} Market Summary")
    print("-" * 45)
    print(f"Latest Close : ${latest_close:.2f}")
    print(f"Previous Close: ${previous_close:.2f}")
    print(f"Highest Close: ${highest_close:.2f}")
    print(f"Lowest Close : ${lowest_close:.2f}")
    print(f"Average Close: ${average_close:.2f}")
    print(f"20-Day SMA   : ${latest_sma_20:.2f}")
    print(f"Trend Signal : {trend_decision}")

    strategy_rules = create_strategy_rules(
        latest_close=latest_close,
        previous_close=previous_close,
        latest_sma_20=latest_sma_20,
        previous_sma_20=previous_sma_20,
        average_close=average_close,
    )

    strategy_feedback = analyse_strategy_feedback(
        rule_results=strategy_rules
    )

    display_strategy_feedback(
        symbol=stock,
        feedback=strategy_feedback,
    )


def main():
    """
    Main Apex Alpha scanner entry point.
    """

    print("=" * 50)
    print("APEX ALPHA")
    print("Investment Intelligence Platform")
    print("=" * 50)

    stocks = [
        "AAPL",
        "MSFT",
        "NVDA",
        "GOOGL",
        "AMZN",
    ]

    for stock in stocks:
        try:
            analyse_stock(stock)

        except Exception as error:
            print(
                f"\n{stock} could not be analysed because "
                f"an unexpected error occurred:"
            )
            print(error)


if __name__ == "__main__":
    main()