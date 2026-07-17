from dataclasses import dataclass
from typing import Any


@dataclass
class RuleResult:
    """
    Represents the outcome of one ApexAlpha strategy rule.
    """

    name: str
    passed: bool
    explanation: str

    category: str = "confirmation"
    actual_value: Any = None
    expected_value: str = ""