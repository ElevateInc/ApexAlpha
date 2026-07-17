from dataclasses import dataclass
from typing import List

from feedback.explanations import identify_missing_confirmations
from feedback.rule_result import RuleResult


@dataclass
class StrategyFeedback:
    """
    Contains the complete Apex feedback for one asset.
    """

    direction: str
    verdict: str
    match_percentage: float
    passed_rules: int
    total_rules: int
    rule_results: List[RuleResult]
    missing_confirmations: List[str]
    risk_message: str


def determine_direction(
    passed_rules: int,
    total_rules: int,
) -> str:
    """
    Determines the broad market direction from the number of rules passed.
    """

    if total_rules == 0:
        return "NEUTRAL"

    match_percentage = (passed_rules / total_rules) * 100

    if match_percentage >= 75:
        return "BULLISH"

    if match_percentage <= 25:
        return "BEARISH"

    return "NEUTRAL"


def determine_verdict(match_percentage: float) -> str:
    """
    Converts the strategy match percentage into a readable verdict.
    """

    if match_percentage >= 80:
        return "STRONG MATCH"

    if match_percentage >= 60:
        return "PARTIAL MATCH"

    if match_percentage >= 40:
        return "WEAK MATCH"

    return "NO CONFIRMATION"


def build_risk_message(
    direction: str,
    match_percentage: float,
) -> str:
    """
    Creates a responsible risk message.

    Apex supports decision-making but does not guarantee trade outcomes.
    """

    if direction == "BULLISH" and match_percentage >= 80:
        return (
            "The strategy shows strong bullish confirmation. However, "
            "historical or technical confirmation does not guarantee that "
            "the trade will be profitable."
        )

    if direction == "BULLISH":
        return (
            "The strategy has a bullish bias, but some confirmation rules "
            "are missing. Consider waiting for stronger confirmation."
        )

    if direction == "BEARISH":
        return (
            "The strategy currently shows weak or bearish conditions. "
            "A bullish entry may carry increased risk."
        )

    return (
        "The strategy does not currently show a clear directional advantage. "
        "Consider waiting until more rules agree."
    )


def analyse_strategy_feedback(
    rule_results: List[RuleResult],
) -> StrategyFeedback:
    """
    Analyses all supplied rules and produces an overall strategy verdict.
    """

    total_rules = len(rule_results)

    if total_rules == 0:
        return StrategyFeedback(
            direction="NEUTRAL",
            verdict="NO RULES AVAILABLE",
            match_percentage=0.0,
            passed_rules=0,
            total_rules=0,
            rule_results=[],
            missing_confirmations=[],
            risk_message=(
                "No strategy rules were available, so Apex could not "
                "evaluate the setup."
            ),
        )

    passed_rules = sum(
        1
        for rule in rule_results
        if rule.passed
    )

    match_percentage = (
        passed_rules / total_rules
    ) * 100

    direction = determine_direction(
        passed_rules=passed_rules,
        total_rules=total_rules,
    )

    verdict = determine_verdict(match_percentage)

    missing_confirmations = identify_missing_confirmations(
        rule_results
    )

    risk_message = build_risk_message(
        direction=direction,
        match_percentage=match_percentage,
    )

    return StrategyFeedback(
        direction=direction,
        verdict=verdict,
        match_percentage=match_percentage,
        passed_rules=passed_rules,
        total_rules=total_rules,
        rule_results=rule_results,
        missing_confirmations=missing_confirmations,
        risk_message=risk_message,
    )


def display_strategy_feedback(
    symbol: str,
    feedback: StrategyFeedback,
) -> None:
    """
    Prints the Apex strategy feedback in a readable format.
    """

    print("\n" + "=" * 50)
    print(f"APEX STRATEGY FEEDBACK — {symbol}")
    print("=" * 50)

    print(f"Direction      : {feedback.direction}")
    print(f"Verdict        : {feedback.verdict}")
    print(
        f"Strategy Match : "
        f"{feedback.match_percentage:.0f}%"
    )
    print(
        f"Rules Passed   : "
        f"{feedback.passed_rules} of "
        f"{feedback.total_rules}"
    )

    print("\nRule Analysis")
    print("-" * 50)

    for rule in feedback.rule_results:
        status = "PASS" if rule.passed else "FAIL"

        print(f"[{status}] {rule.name}")
        print(f"       Actual   : {rule.actual_value}")
        print(f"       Required : {rule.expected_value}")
        print(f"       Analysis : {rule.explanation}")

    print("\nMissing Confirmations")
    print("-" * 50)

    if feedback.missing_confirmations:
        for missing_rule in feedback.missing_confirmations:
            print(f"- {missing_rule}")
    else:
        print("No confirmations are currently missing.")

    print("\nRisk Guidance")
    print("-" * 50)
    print(feedback.risk_message)