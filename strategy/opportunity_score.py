"""
===========================================================
ApexAlpha
Opportunity Scoring Engine
Version: 2.0
Author: Lourence Gonhovi
===========================================================

This module calculates a weighted ApexAlpha confidence score
for a trading setup and explains why the setup received its score.
"""

from __future__ import annotations

from typing import Any

from strategy.grading import get_confidence, get_trade_grade


WEIGHTS = {
    "golden_cross": 20,
    "bullish_alignment": 20,
    "trend": 10,
    "sma20": 5,
    "sma50": 5,
    "sma200": 10,
    "ema_bullish": 10,
    "bullish_fvg": 10,
    "strong_volume": 5,
    "low_risk": 5,
}


def get_setup_classification(score: int) -> str:
    if score >= 90:
        return "INSTITUTIONAL-GRADE SETUP"
    if score >= 80:
        return "STRONG SETUP"
    if score >= 70:
        return "MODERATE SETUP"
    if score >= 50:
        return "WEAK SETUP"
    return "NO-TRADE SETUP"


def get_verdict(score: int) -> str:
    if score >= 90:
        return "HIGH-CONFIDENCE BUY WATCHLIST"
    if score >= 80:
        return "STRONG BUY WATCHLIST"
    if score >= 70:
        return "WATCH FOR CONFIRMATION"
    if score >= 50:
        return "CAUTION — SETUP INCOMPLETE"
    return "AVOID FOR NOW"


def get_star_rating(score: int) -> str:
    if score >= 90:
        return "★★★★★"
    if score >= 80:
        return "★★★★☆"
    if score >= 70:
        return "★★★☆☆"
    if score >= 50:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def get_recommendation(score: int) -> str:
    if score >= 90:
        return (
            "ApexAlpha has detected a rare, high-confidence setup. "
            "Review execution price, stop-loss placement and position size."
        )
    if score >= 80:
        return (
            "The setup is strong. Watch closely for entry confirmation "
            "and favourable risk-to-reward."
        )
    if score >= 70:
        return (
            "The setup has potential but still needs confirmation "
            "before a trade is considered."
        )
    if score >= 50:
        return (
            "Some supportive signals exist, but the setup is not yet "
            "strong enough for a high-quality trade."
        )
    return (
        "No quality opportunity is currently detected. "
        "Preserve capital and wait for better alignment."
    )


def calculate_opportunity_score(
    trend: bool = False,
    sma20: bool = False,
    sma50: bool = False,
    bullish_fvg: bool = False,
    strong_volume: bool = False,
    low_risk: bool = False,
    *,
    sma200: bool = False,
    ema_bullish: bool = False,
    golden_cross: bool = False,
    bullish_alignment: bool = False,
    bearish_alignment: bool = False,
    death_cross: bool = False,
) -> dict[str, Any]:
    """Calculate a weighted ApexAlpha Opportunity Score."""

    signals = {
        "golden_cross": bool(golden_cross),
        "bullish_alignment": bool(bullish_alignment),
        "trend": bool(trend),
        "sma20": bool(sma20),
        "sma50": bool(sma50),
        "sma200": bool(sma200),
        "ema_bullish": bool(ema_bullish),
        "bullish_fvg": bool(bullish_fvg),
        "strong_volume": bool(strong_volume),
        "low_risk": bool(low_risk),
    }

    explanations = {
        "golden_cross": "Golden Cross detected",
        "bullish_alignment": "Bullish moving-average alignment confirmed",
        "trend": "Primary trend supports the bullish direction",
        "sma20": "Price is above SMA20",
        "sma50": "Price is above SMA50",
        "sma200": "Price is above SMA200",
        "ema_bullish": "EMA20 is above EMA50",
        "bullish_fvg": "Active bullish Fair Value Gap detected",
        "strong_volume": "Volume confirms stronger participation",
        "low_risk": "Price location indicates controlled risk",
    }

    weaknesses = {
        "golden_cross": "No new Golden Cross is present",
        "bullish_alignment": "Full bullish alignment is not confirmed",
        "trend": "The primary trend is not bullish",
        "sma20": "Price is below SMA20",
        "sma50": "Price is below SMA50",
        "sma200": "Price is below SMA200",
        "ema_bullish": "EMA20 is not above EMA50",
        "bullish_fvg": "No active bullish Fair Value Gap is present",
        "strong_volume": "Volume has not confirmed the setup",
        "low_risk": "Risk is elevated relative to SMA20",
    }

    score_breakdown: list[dict[str, Any]] = []
    strengths: list[str] = []
    missing_confirmations: list[str] = []

    score = 0

    for signal_name, passed in signals.items():
        weight = WEIGHTS[signal_name]
        awarded = weight if passed else 0
        score += awarded

        score_breakdown.append(
            {
                "signal": signal_name,
                "label": explanations[signal_name],
                "passed": passed,
                "weight": weight,
                "awarded": awarded,
            }
        )

        if passed:
            strengths.append(explanations[signal_name])
        else:
            missing_confirmations.append(weaknesses[signal_name])

    bearish_penalties: list[str] = []

    if bearish_alignment:
        score -= 25
        bearish_penalties.append(
            "Bearish moving-average alignment detected (-25)"
        )

    if death_cross:
        score -= 25
        bearish_penalties.append("Death Cross detected (-25)")

    score = max(0, min(100, score))

    return {
        "score": score,
        "grade": get_trade_grade(score),
        "confidence": get_confidence(score),
        "stars": get_star_rating(score),
        "classification": get_setup_classification(score),
        "verdict": get_verdict(score),
        "recommendation": get_recommendation(score),
        "breakdown": score_breakdown,
        "strengths": strengths,
        "missing_confirmations": missing_confirmations,
        "bearish_penalties": bearish_penalties,
    }


def display_opportunity_report(
    symbol: str,
    score_data: dict[str, Any],
    trend: str = "Unknown",
    fvg: str = "Unknown",
    risk: str = "Unknown",
) -> None:
    """Display the Sprint 12 ApexAlpha Intelligence Report."""

    print("\n" + "=" * 70)
    print(f"APEXALPHA INTELLIGENCE REPORT: {symbol}")
    print("=" * 70)

    print(f"Confidence Score : {score_data['score']}/100")
    print(
        f"Rating           : "
        f"{score_data['stars']} {score_data['classification']}"
    )
    print(f"Grade            : {score_data['grade']}")
    print(f"Confidence       : {score_data['confidence']}")
    print(f"Verdict          : {score_data['verdict']}")
    print(f"Trend            : {trend}")
    print(f"Fair Value Gap   : {fvg}")
    print(f"Risk             : {risk}")

    print("\nScore Breakdown")
    print("-" * 70)

    for item in score_data["breakdown"]:
        marker = "✓" if item["passed"] else "·"
        print(
            f"{marker} +{item['awarded']:>2}/{item['weight']:>2}  "
            f"{item['label']}"
        )

    if score_data["bearish_penalties"]:
        print("\nBearish Penalties")
        print("-" * 70)
        for penalty in score_data["bearish_penalties"]:
            print(f"✗ {penalty}")

    print("\nWhy ApexAlpha likes this setup")
    print("-" * 70)

    if score_data["strengths"]:
        for strength in score_data["strengths"]:
            print(f"✓ {strength}")
    else:
        print("No bullish confirmations are currently active.")

    print("\nMain weaknesses")
    print("-" * 70)

    if score_data["missing_confirmations"]:
        for weakness in score_data["missing_confirmations"][:4]:
            print(f"• {weakness}")
    else:
        print("No major bullish confirmation is missing.")

    print("\nRecommendation")
    print("-" * 70)
    print(score_data["recommendation"])
    print("=" * 70)
