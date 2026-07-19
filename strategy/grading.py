"""
===========================================================
ApexAlpha
Grading Engine
Version: 1.0
===========================================================
"""


def get_trade_grade(score: int) -> str:
    """
    Converts an opportunity score into a trade grade.
    """

    if score >= 95:
        return "A+"

    elif score >= 90:
        return "A"

    elif score >= 85:
        return "B+"

    elif score >= 80:
        return "B"

    elif score >= 70:
        return "C"

    else:
        return "Avoid"


def get_confidence(score: int) -> str:
    """
    Returns confidence level based on score.
    """

    if score >= 95:
        return "Exceptional"

    elif score >= 90:
        return "Very High"

    elif score >= 85:
        return "High"

    elif score >= 80:
        return "Moderate"

    elif score >= 70:
        return "Low"

    else:
        return "Very Low"