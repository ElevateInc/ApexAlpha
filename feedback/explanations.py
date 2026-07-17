from typing import List

from feedback.rule_result import RuleResult


def build_rule_explanation(
    rule_name: str,
    passed: bool,
) -> str:
    """
    Produces a plain-English explanation for each supported rule.
    """

    explanations = {
        "Price above 20-day SMA": {
            True: (
                "The latest closing price is above the 20-day moving average, "
                "which supports a bullish short-term trend."
            ),
            False: (
                "The latest closing price is below the 20-day moving average, "
                "which suggests that short-term trend confirmation is missing."
            ),
        },
        "Price increased today": {
            True: (
                "The latest closing price is above the previous closing price, "
                "showing positive short-term momentum."
            ),
            False: (
                "The latest closing price is not above the previous closing "
                "price, so immediate price momentum is weak."
            ),
        },
        "20-day SMA is rising": {
            True: (
                "The 20-day moving average is rising, suggesting that the "
                "underlying short-term trend is strengthening."
            ),
            False: (
                "The 20-day moving average is flat or falling, so the "
                "underlying short-term trend is not strengthening."
            ),
        },
        "Price above period average": {
            True: (
                "The latest price is above the average closing price for the "
                "downloaded period, supporting positive relative strength."
            ),
            False: (
                "The latest price is below the average closing price for the "
                "downloaded period, indicating weaker relative performance."
            ),
        },
    }

    default_explanation = (
        "The strategy condition passed."
        if passed
        else "The strategy condition did not pass."
    )

    return explanations.get(
        rule_name,
        {},
    ).get(
        passed,
        default_explanation,
    )


def identify_missing_confirmations(
    rule_results: List[RuleResult],
) -> List[str]:
    """
    Returns the names of all strategy rules that did not pass.
    """

    return [
        rule.name
        for rule in rule_results
        if not rule.passed
    ]