"""
===========================================================
ApexAlpha
Opportunity Scoring Engine
Version: 1.0
Author: Lourence Gonhovi
===========================================================

This module calculates an overall opportunity scorecsl

for a trading setup based on multiple strategy rules.
"""

from strategy.grading import get_trade_grade, get_confidence


def calculate_opportunity_score(
    trend=False,
    sma20=False,
    sma50=False,
    bullish_fvg=False,
    strong_volume=False,
    low_risk=False,
):
    """
    Calculates an ApexAlpha Opportunity Score.

    Parameters
    ----------
    trend : bool
        Trend confirmation.

    sma20 : bool
        Price above 20 SMA.

    sma50 : bool
        Price above 50 SMA.

    bullish_fvg : bool
        Bullish Fair Value Gap detected.

    strong_volume : bool
        Volume confirmation.

    low_risk : bool
        Risk within acceptable limits.

    Returns
    -------
    dict
        {
            "score": int,
            "grade": str,
            "confidence": str,
            "recommendation": str
        }
    """

    score = 0

    if trend:
        score += 20

    if sma20:
        score += 15

    if sma50:
        score += 15

    if bullish_fvg:
        score += 20

    if strong_volume:
        score += 15

    if low_risk:
        score += 15

    grade = get_trade_grade(score)

    confidence = get_confidence(score)

    if score >= 90:
        recommendation = "The market has something worth seeing."

    elif score >= 80:
        recommendation = "Watch closely for confirmation."

    elif score >= 70:
        recommendation = "Monitor carefully."

    else:
        recommendation = "No quality opportunity detected."

    return {
        "score": score,
        "grade": grade,
        "confidence": confidence,
        "recommendation": recommendation,
    }


def display_opportunity_report(
    symbol,
    score_data,
    trend="Unknown",
    fvg="Unknown",
    risk="Unknown",
):
    """
    Displays a formatted Opportunity Report.
    """

    print("\n" + "=" * 60)
    print("                APEXALPHA OPPORTUNITY REPORT")
    print("=" * 60)

    print(f"Ticker          : {symbol}")
    print(f"Score           : {score_data['score']}/100")
    print(f"Grade           : {score_data['grade']}")
    print(f"Confidence      : {score_data['confidence']}")
    print(f"Trend           : {trend}")
    print(f"Fair Value Gap  : {fvg}")
    print(f"Risk            : {risk}")

    print("\nRecommendation")
    print("------------------------------")
    print(score_data["recommendation"])

    print("=" * 60)