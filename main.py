from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from charts import display_market_chart
from data.market_data import download_stock_data
from feedback import (
    RuleResult,
    generate_strategy_feedback,
)
from indicators.moving_averages import (
    add_moving_averages,
    has_sufficient_history,
)
from patterns.fvg_detector import (
    detect_fair_value_gaps,
    display_latest_fair_value_gap,
    get_latest_active_fair_value_gap,
)
from patterns.fvg_tracker import update_all_fvg_statuses
from strategy.opportunity_score import (
    calculate_opportunity_score,
    display_opportunity_report,
)
from patterns.support_resistance import (
    detect_support_resistance,
    nearest_support,
    nearest_resistance,
    percent_distance,
)
from strategy.signal_filter import should_notify
from strategy.trend_strategy import analyse_trend
from strategy.watchlist import get_watchlist


NOTIFICATION_STATE_FILE = Path("database/notification_state.json")


def get_single_series(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.Series:
    """
    Extract one numeric Series from either normal columns
    or Yahoo Finance MultiIndex columns.
    """

    if dataframe is None or dataframe.empty:
        raise ValueError(
            "Cannot extract market values from an empty DataFrame."
        )

    if isinstance(dataframe.columns, pd.MultiIndex):
        first_level_columns = dataframe.columns.get_level_values(0)

        if column_name not in first_level_columns:
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


def add_chart_compatibility_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Preserve the old SMA_20 and SMA_50 names for chart code
    while Sprint 11 uses SMA20 and SMA50 internally.
    """

    result = dataframe.copy()

    result["SMA_20"] = get_single_series(
        dataframe=result,
        column_name="SMA20",
    )
    result["SMA_50"] = get_single_series(
        dataframe=result,
        column_name="SMA50",
    )

    return result


def get_fvg_value(
    fair_value_gap: Any,
    possible_names: tuple[str, ...],
) -> Any:
    """
    Extract a value safely from either an FVG dictionary
    or an FVG object.
    """

    if fair_value_gap is None:
        return None

    if isinstance(fair_value_gap, dict):
        for name in possible_names:
            if name in fair_value_gap:
                return fair_value_gap[name]

        return None

    for name in possible_names:
        if hasattr(fair_value_gap, name):
            return getattr(fair_value_gap, name)

    return None


def is_bullish_fvg(
    fair_value_gap: Any,
) -> bool:
    """
    Determine whether the latest active Fair Value Gap is bullish.
    """

    if fair_value_gap is None:
        return False

    direction = get_fvg_value(
        fair_value_gap=fair_value_gap,
        possible_names=(
            "direction",
            "type",
            "gap_type",
            "fvg_type",
            "side",
        ),
    )

    if direction is None:
        return False

    direction_text = str(direction).strip().lower()

    bullish_terms = (
        "bullish",
        "bull",
        "buy",
        "long",
        "up",
    )

    return any(
        term in direction_text
        for term in bullish_terms
    )


def load_notification_state() -> dict[str, dict[str, Any]]:
    """
    Load saved notification states so alignment alerts are not
    repeated every time ApexAlpha runs.
    """

    if not NOTIFICATION_STATE_FILE.exists():
        return {}

    try:
        with NOTIFICATION_STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as state_file:
            data = json.load(state_file)

        if isinstance(data, dict):
            return data

    except (OSError, json.JSONDecodeError):
        pass

    return {}


def save_notification_state(
    state: dict[str, dict[str, Any]],
) -> None:
    """
    Save notification states locally.
    """

    NOTIFICATION_STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with NOTIFICATION_STATE_FILE.open(
        "w",
        encoding="utf-8",
    ) as state_file:
        json.dump(
            state,
            state_file,
            indent=2,
        )


def show_desktop_popup(
    title: str,
    message: str,
) -> None:
    """
    Show a desktop popup when available.

    If the desktop interface is unavailable, ApexAlpha still prints
    the alert in the terminal.
    """

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        messagebox.showinfo(
            title=title,
            message=message,
            parent=root,
        )

        root.destroy()

    except Exception:
        print(
            "\nDesktop popup was unavailable; "
            "the terminal alert remains active."
        )


def display_special_signal_alert(
    symbol: str,
    signal_name: str,
    explanation: str,
    priority: str,
    enable_desktop_popup: bool,
) -> None:
    """
    Display a high-visibility ApexAlpha trend notification.
    """

    print("\n" + "!" * 70)
    print(f"APEXALPHA {signal_name}: {symbol}")
    print(f"Priority: {priority}")
    print(explanation)
    print("!" * 70)

    if enable_desktop_popup:
        show_desktop_popup(
            title=f"ApexAlpha — {signal_name}",
            message=(
                f"{symbol}\n\n"
                f"{explanation}\n\n"
                f"Priority: {priority}"
            ),
        )


def classify_moving_average_structure(
    current_price: float,
    current_sma_50: float,
    previous_sma_50: float,
    current_sma_200: float,
    previous_sma_200: float,
    current_ema_20: float,
    current_ema_50: float,
) -> dict[str, bool | str]:
    """
    Detect Golden Cross, Death Cross, bullish alignment,
    bearish alignment, and the current long-term structure.
    """

    golden_cross = bool(
        previous_sma_50 <= previous_sma_200
        and current_sma_50 > current_sma_200
    )

    death_cross = bool(
        previous_sma_50 >= previous_sma_200
        and current_sma_50 < current_sma_200
    )

    bullish_alignment = bool(
        current_price > current_ema_20
        and current_ema_20 > current_ema_50
        and current_sma_50 > current_sma_200
        and current_price > current_sma_200
    )

    bearish_alignment = bool(
        current_price < current_ema_20
        and current_ema_20 < current_ema_50
        and current_sma_50 < current_sma_200
        and current_price < current_sma_200
    )

    if bullish_alignment:
        alignment = "BULLISH_ALIGNMENT"
    elif bearish_alignment:
        alignment = "BEARISH_ALIGNMENT"
    else:
        alignment = "NEUTRAL_OR_TRANSITION"

    return {
        "golden_cross": golden_cross,
        "death_cross": death_cross,
        "bullish_alignment": bullish_alignment,
        "bearish_alignment": bearish_alignment,
        "alignment": alignment,
    }


def process_special_notifications(
    symbol: str,
    market_structure: dict[str, bool | str],
    signal_date: str,
    enable_desktop_popup: bool,
) -> None:
    """
    Notify only when a crossover is new or when alignment changes.
    """

    state = load_notification_state()
    symbol_state = state.get(
        symbol,
        {
            "alignment": None,
            "golden_cross_date": None,
            "death_cross_date": None,
        },
    )

    if (
        market_structure["golden_cross"]
        and symbol_state.get("golden_cross_date") != signal_date
    ):
        display_special_signal_alert(
            symbol=symbol,
            signal_name="GOLDEN CROSS DETECTED",
            explanation=(
                "SMA50 has crossed above SMA200. "
                "Long-term bullish momentum may be developing."
            ),
            priority="CRITICAL BULLISH",
            enable_desktop_popup=enable_desktop_popup,
        )
        symbol_state["golden_cross_date"] = signal_date

    if (
        market_structure["death_cross"]
        and symbol_state.get("death_cross_date") != signal_date
    ):
        display_special_signal_alert(
            symbol=symbol,
            signal_name="DEATH CROSS DETECTED",
            explanation=(
                "SMA50 has crossed below SMA200. "
                "Long-term market structure may be weakening."
            ),
            priority="CRITICAL BEARISH",
            enable_desktop_popup=enable_desktop_popup,
        )
        symbol_state["death_cross_date"] = signal_date

    current_alignment = str(
        market_structure["alignment"]
    )
    previous_alignment = symbol_state.get("alignment")

    if current_alignment != previous_alignment:
        if current_alignment == "BULLISH_ALIGNMENT":
            display_special_signal_alert(
                symbol=symbol,
                signal_name="BULLISH ALIGNMENT CONFIRMED",
                explanation=(
                    "Price is above EMA20 and SMA200, EMA20 is above "
                    "EMA50, and SMA50 is above SMA200."
                ),
                priority="HIGH BULLISH",
                enable_desktop_popup=enable_desktop_popup,
            )

        elif current_alignment == "BEARISH_ALIGNMENT":
            display_special_signal_alert(
                symbol=symbol,
                signal_name="BEARISH ALIGNMENT DETECTED",
                explanation=(
                    "Price is below EMA20 and SMA200, EMA20 is below "
                    "EMA50, and SMA50 is below SMA200."
                ),
                priority="HIGH BEARISH",
                enable_desktop_popup=enable_desktop_popup,
            )

        symbol_state["alignment"] = current_alignment

    state[symbol] = symbol_state
    save_notification_state(state)


def create_strategy_rules(
    current_price: float,
    previous_close: float,
    current_sma_20: float,
    previous_sma_20: float,
    current_sma_50: float,
    current_sma_200: float,
    current_ema_20: float,
    current_ema_50: float,
    average_price: float,
    bullish_fvg: bool,
    strong_volume: bool,
) -> list[RuleResult]:
    """
    Create the current ApexAlpha strategy rules.
    """

    price_above_sma_20 = current_price > current_sma_20
    price_above_sma_50 = current_price > current_sma_50
    price_above_sma_200 = current_price > current_sma_200
    price_increased = current_price > previous_close
    sma_20_rising = current_sma_20 > previous_sma_20
    ema_bullish = current_ema_20 > current_ema_50
    price_above_average = current_price > average_price

    return [
        RuleResult(
            name="Price above SMA 20",
            passed=price_above_sma_20,
            explanation=(
                "The current price is above the 20-day moving average."
                if price_above_sma_20
                else
                "The current price is below the 20-day moving average."
            ),
            category="required",
        ),
        RuleResult(
            name="Price above SMA 50",
            passed=price_above_sma_50,
            explanation=(
                "The current price is above the 50-day moving average."
                if price_above_sma_50
                else
                "The current price is below the 50-day moving average."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price above SMA 200",
            passed=price_above_sma_200,
            explanation=(
                "The price is above its long-term 200-day average."
                if price_above_sma_200
                else
                "The price is below its long-term 200-day average."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="EMA 20 above EMA 50",
            passed=ema_bullish,
            explanation=(
                "Short-term exponential momentum is bullish."
                if ema_bullish
                else
                "Short-term exponential momentum is not bullish."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price increased today",
            passed=price_increased,
            explanation=(
                "The latest closing price is above the previous close."
                if price_increased
                else
                "The latest closing price did not rise above "
                "the previous close."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="SMA 20 is rising",
            passed=sma_20_rising,
            explanation=(
                "The 20-day moving average is rising."
                if sma_20_rising
                else
                "The 20-day moving average is flat or falling."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Price above recent average",
            passed=price_above_average,
            explanation=(
                "The current price is above its recent average."
                if price_above_average
                else
                "The current price is below its recent average."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Bullish Fair Value Gap",
            passed=bullish_fvg,
            explanation=(
                "An active bullish Fair Value Gap was detected."
                if bullish_fvg
                else
                "No active bullish Fair Value Gap was detected."
            ),
            category="confirmation",
        ),
        RuleResult(
            name="Strong volume",
            passed=strong_volume,
            explanation=(
                "Current volume is above the confirmation threshold."
                if strong_volume
                else
                "Current volume is below the confirmation threshold."
            ),
            category="confirmation",
        ),
    ]


def analyse_stock(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    show_chart: bool = True,
    enable_desktop_popups: bool = True,
) -> None:
    """
    Download and analyse one market symbol.
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
            print(f"No market data was returned for {symbol}.")
            return

        if not has_sufficient_history(data):
            print(
                f"WARNING: {symbol} has insufficient history for SMA200. "
                f"Only {len(data)} rows are available."
            )
            return

        data = add_moving_averages(data)
        data = add_chart_compatibility_columns(data)

        close_prices = get_single_series(
            dataframe=data,
            column_name="Close",
        )

        high_prices = get_single_series(
            dataframe=data,
            column_name="High",
        )

        low_prices = get_single_series(
            dataframe=data,
            column_name="Low",
        )

        sma_20 = get_single_series(
            dataframe=data,
            column_name="SMA20",
        )

        sma_50 = get_single_series(
            dataframe=data,
            column_name="SMA50",
        )
        
        sma_200 = get_single_series(
            dataframe=data,
            column_name="SMA200",
        )
        ema_20 = get_single_series(
            dataframe=data,
            column_name="EMA20",
        )
        ema_50 = get_single_series(
            dataframe=data,
            column_name="EMA50",
        )

        try:
            volume = get_single_series(
                dataframe=data,
                column_name="Volume",
            )
        except ValueError:
            volume = pd.Series(
                index=data.index,
                dtype="float64",
            )

        market_values = pd.DataFrame(
    {
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "SMA20": sma_20,
        "SMA50": sma_50,
        "SMA200": sma_200,
        "EMA20": ema_20,
        "EMA50": ema_50,
        "Volume": volume,
    }
)
        

        valid_market_data = market_values.dropna(
    subset=[
        "High",
        "Low",
        "Close",
        "SMA20",
        "SMA50",
        "SMA200",
        "EMA20",
        "EMA50",
    ]
)
        
        if len(valid_market_data) < 2:
            print(
                f"Not enough valid market data exists for {symbol}."
            )
            return

        current_row = valid_market_data.iloc[-1]
        previous_row = valid_market_data.iloc[-2]

        current_price = float(current_row["Close"])
        previous_close = float(previous_row["Close"])

        current_sma_20 = float(current_row["SMA20"])
        previous_sma_20 = float(previous_row["SMA20"])

        current_sma_50 = float(current_row["SMA50"])
        previous_sma_50 = float(previous_row["SMA50"])

        current_sma_200 = float(current_row["SMA200"])
        previous_sma_200 = float(previous_row["SMA200"])

        current_ema_20 = float(current_row["EMA20"])
        current_ema_50 = float(current_row["EMA50"])

        average_price = float(
            valid_market_data["Close"]
            .tail(20)
            .mean()
        )

        volume_values = valid_market_data[
            "Volume"
        ].dropna()

        if volume_values.empty:
            current_volume = None
            average_volume = None
            strong_volume = False
        else:
            current_volume = float(
                volume_values.iloc[-1]
            )
            average_volume = float(
                volume_values.tail(20).mean()
            )
            strong_volume = bool(
                average_volume > 0
                and current_volume >= average_volume * 1.20
            )

        price_change = current_price - previous_close

        if previous_close != 0:
            price_change_percentage = (
                price_change / previous_close
            ) * 100
        else:
            price_change_percentage = 0.0

        trend = analyse_trend(
            current_price=current_price,
            moving_average=current_sma_20,
        )
        trend_text = str(trend)

        trend_confirmed = any(
            word in trend_text.lower()
            for word in (
                "buy",
                "bull",
                "up",
                "long",
            )
        )
        # -----------------------------
        # SUPPORT & RESISTANCE
        # -----------------------------
        supports, resistances = detect_support_resistance(valid_market_data)

        closest_support = nearest_support(current_price, supports)
        closest_resistance = nearest_resistance(current_price, resistances)

        support_distance = percent_distance(current_price, closest_support)
        resistance_distance = percent_distance(current_price, closest_resistance)

        market_structure = classify_moving_average_structure(
            current_price=current_price,
            current_sma_50=current_sma_50,
            previous_sma_50=previous_sma_50,
            current_sma_200=current_sma_200,
            previous_sma_200=previous_sma_200,
            current_ema_20=current_ema_20,
            current_ema_50=current_ema_50,
        )

        signal_date = str(
            valid_market_data.index[-1]
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
        print(f"SMA 20:              {current_sma_20:.2f}")
        print(f"SMA 50:              {current_sma_50:.2f}")
        print(f"SMA 200:             {current_sma_200:.2f}")
        print(f"EMA 20:              {current_ema_20:.2f}")
        print(f"EMA 50:              {current_ema_50:.2f}")
        print(f"Recent average:      {average_price:.2f}")
        print(f"Trend:               {trend_text}")
        print(
            f"MA structure:        "
            f"{str(market_structure['alignment']).replace('_', ' ').title()}"
        )
        print(
            f"Golden Cross today:  "
            f"{'Yes' if market_structure['golden_cross'] else 'No'}"
        )
        print(
            f"Death Cross today:   "
            f"{'Yes' if market_structure['death_cross'] else 'No'}"
        )

        if current_volume is not None:
            print(f"Current volume:      {current_volume:,.0f}")

        if average_volume is not None:
            print(f"Average volume:      {average_volume:,.0f}")

        print(
            "Volume confirmation: "
            f"{'Strong' if strong_volume else 'Normal'}"
        )

        process_special_notifications(
            symbol=symbol,
            market_structure=market_structure,
            signal_date=signal_date,
            enable_desktop_popup=enable_desktop_popups,
        )

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

        bullish_fvg = is_bullish_fvg(
            fair_value_gap=latest_fvg
        )

        if current_sma_20 != 0:
            price_distance_from_sma_20 = abs(
                (
                    current_price - current_sma_20
                )
                / current_sma_20
            ) * 100
        else:
            price_distance_from_sma_20 = float("inf")

        low_risk = bool(
            current_price > current_sma_20
            and price_distance_from_sma_20 <= 5
        )

        risk_label = (
            "Controlled"
            if low_risk
            else "Elevated"
        )

        if bullish_fvg:
            fvg_label = "Active Bullish"
        elif latest_fvg is not None:
            fvg_label = "Active Non-Bullish"
        else:
            fvg_label = "None"

        print("\nStrategy Feedback")
        print("-" * 50)

        strategy_rules = create_strategy_rules(
            current_price=current_price,
            previous_close=previous_close,
            current_sma_20=current_sma_20,
            previous_sma_20=previous_sma_20,
            current_sma_50=current_sma_50,
            current_sma_200=current_sma_200,
            current_ema_20=current_ema_20,
            current_ema_50=current_ema_50,
            average_price=average_price,
            bullish_fvg=bullish_fvg,
            strong_volume=strong_volume,
        )

        strategy_feedback = generate_strategy_feedback(
            rules=strategy_rules,
            direction=trend_text,
        )

        strategy_feedback.display()

        score_data = calculate_opportunity_score(
    trend=trend_confirmed,
    sma20=current_price > current_sma_20,
    sma50=current_price > current_sma_50,
    sma200=current_price > current_sma_200,
    ema_bullish=current_ema_20 > current_ema_50,
    golden_cross=market_structure["golden_cross"],
    bullish_alignment=market_structure["bullish_alignment"],
    bearish_alignment=market_structure["bearish_alignment"],
    death_cross=market_structure["death_cross"],
    bullish_fvg=bullish_fvg,
    strong_volume=strong_volume,
    low_risk=low_risk,
)
        display_opportunity_report(
            symbol=symbol,
            score_data=score_data,
            trend=trend_text,
            fvg=fvg_label,
            risk=risk_label,
        )

        # ----------------------------------------
        # SUPPORT & RESISTANCE REPORT
        # ----------------------------------------

        print("\nSUPPORT & RESISTANCE")
        print("-" * 40)

        if closest_support is not None:
            print(
                f"Nearest Support    : {closest_support:.2f} "
                f"({support_distance:.2f}% away)"
            )
        else:
            print("Nearest Support    : None")

        if closest_resistance is not None:
            print(
                f"Nearest Resistance : {closest_resistance:.2f} "
                f"({resistance_distance:.2f}% away)"
            )
        else:
            print("Nearest Resistance : None")

        print("\nPRICE LOCATION")

        if (
            resistance_distance is not None
            and resistance_distance < 2
        ):
            print("⚠️ Price is approaching resistance.")
            print("Wait for a breakout confirmation.")

        elif (
            support_distance is not None
            and support_distance < 2
        ):
            print("✅ Price is trading near support.")
            print("Watch for a bullish bounce.")

        else:
            print("Price is between major support and resistance.")

        notification_required = should_notify(
            score=score_data["score"],
            minimum_score=85,
        )
        
        if notification_required:
            print("\n" + "!" * 70)
            print(f"APEXALPHA OPPORTUNITY ALERT: {symbol}")
            print("The market has something worth seeing.")
            print("!" * 70)
        else:
            print(
                "\nApexAlpha remains silent: "
                "the opportunity has not reached "
                "the notification threshold."
            )

        if show_chart:
            display_market_chart(
                dataframe=data,
                symbol=symbol,
                fair_value_gaps=updated_fair_value_gaps,
                candle_limit=80,
            )

    except Exception as error:
        print(f"\nApexAlpha could not analyse {symbol}.")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")


def main() -> None:
    """
    ApexAlpha application entry point.
    """

    print("\n")
    print("=" * 70)
    print("APEXALPHA")
    print("Market Intelligence and Strategy Analysis Platform")
    print("=" * 70)

    symbols = get_watchlist()

    if not symbols:
        print("\nThe ApexAlpha watchlist is empty.")
        return

    print(
        f"\nScanning {len(symbols)} symbols: "
        f"{', '.join(symbols)}"
    )

    for symbol in symbols:
        analyse_stock(
            symbol=symbol,
            period="2y",
            interval="1d",
            show_chart=True,
            enable_desktop_popups=True,
        )

    print("\n")
    print("=" * 70)
    print("APEXALPHA SCAN COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
