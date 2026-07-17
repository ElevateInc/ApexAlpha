from dataclasses import dataclass
from typing import Any


@dataclass
class RuleResult:
    """
    Represents the outcome of one strategy rule.

    Example:
        Price above 20-day SMA = passed
        Latest close above previous close = failed
    """

    name: str
    passed: bool
    actual_value: Any
    expected_value: str
    explanation: str