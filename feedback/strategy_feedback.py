from dataclasses import dataclass

from feedback.rule_result import RuleResult


@dataclass
class StrategyFeedback:
    """
    Summarises the result of a group of strategy rules.
    """

    direction: str
    verdict: str
    match_percentage: float
    passed_rules: list[RuleResult]
    failed_rules: list[RuleResult]
    missing_confirmations: list[RuleResult]
    risk_guidance: str

    def display(self) -> None:
        """
        Prints a readable strategy-feedback report.
        """

        print(f"Direction:            {self.direction}")
        print(f"Verdict:              {self.verdict}")
        print(
            f"Strategy match:       "
            f"{self.match_percentage:.1f}%"
        )

        print("\nPassed Rules")
        print("-" * 50)

        if self.passed_rules:
            for rule in self.passed_rules:
                print(f"✓ {rule.name}")
                print(f"  {rule.explanation}")
        else:
            print("No strategy rules passed.")

        print("\nFailed Rules")
        print("-" * 50)

        if self.failed_rules:
            for rule in self.failed_rules:
                print(f"✗ {rule.name}")
                print(f"  {rule.explanation}")
        else:
            print("No strategy rules failed.")

        print("\nMissing Confirmations")
        print("-" * 50)

        if self.missing_confirmations:
            for rule in self.missing_confirmations:
                print(f"- {rule.name}")
        else:
            print("No confirmations are missing.")

        print("\nRisk Guidance")
        print("-" * 50)
        print(self.risk_guidance)


def generate_strategy_feedback(
    rules: list[RuleResult],
    direction: str,
) -> StrategyFeedback:
    """
    Generates a strategy-feedback report from rule results.
    """

    if not rules:
        return StrategyFeedback(
            direction=direction,
            verdict="NO RULES",
            match_percentage=0.0,
            passed_rules=[],
            failed_rules=[],
            missing_confirmations=[],
            risk_guidance=(
                "No strategy rules were provided. "
                "A trading decision cannot be evaluated."
            ),
        )

    passed_rules = [
        rule
        for rule in rules
        if rule.passed
    ]

    failed_rules = [
        rule
        for rule in rules
        if not rule.passed
    ]

    required_rules = [
        rule
        for rule in rules
        if rule.category == "required"
    ]

    failed_required_rules = [
        rule
        for rule in required_rules
        if not rule.passed
    ]

    missing_confirmations = [
        rule
        for rule in failed_rules
        if rule.category == "confirmation"
    ]

    match_percentage = (
        len(passed_rules) / len(rules)
    ) * 100

    if failed_required_rules:
        verdict = "SETUP NOT VALID"

        risk_guidance = (
            "One or more required strategy rules failed. "
            "The setup should not be treated as valid."
        )

    elif match_percentage == 100:
        verdict = "SETUP ACHIEVED"

        risk_guidance = (
            "All required and confirmation rules passed. "
            "Risk management is still essential before entering a trade."
        )

    elif match_percentage >= 75:
        verdict = "STRONG SETUP"

        risk_guidance = (
            "The strategy has a strong directional bias, "
            "but some confirmation rules are missing. "
            "Consider waiting for stronger confirmation."
        )

    elif match_percentage >= 50:
        verdict = "FORMING SETUP"

        risk_guidance = (
            "Some strategy conditions have passed, "
            "but the setup remains incomplete."
        )

    else:
        verdict = "WEAK SETUP"

        risk_guidance = (
            "Most strategy rules have not passed. "
            "Avoid forcing a trade."
        )

    return StrategyFeedback(
        direction=direction,
        verdict=verdict,
        match_percentage=match_percentage,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        missing_confirmations=missing_confirmations,
        risk_guidance=risk_guidance,
    )