from dataclasses import dataclass
from typing import Any


@dataclass
class FairValueGap:
    """
    Represents one bullish or bearish Fair Value Gap.
    """

    symbol: str
    direction: str
    lower_boundary: float
    upper_boundary: float
    formation_time: Any
    candle_position: int
    gap_size: float

    status: str = "UNTOUCHED"
    mitigation_percentage: float = 0.0
    age_candles: int = 0
    entry_time: Any = None
    invalidation_time: Any = None

    @property
    def midpoint(self) -> float:
        """
        Returns the 50% level of the Fair Value Gap.
        """

        return (
            self.lower_boundary + self.upper_boundary
        ) / 2

    def contains_price(self, price: float) -> bool:
        """
        Returns True when a price is inside the FVG zone.
        """

        return (
            self.lower_boundary
            <= price
            <= self.upper_boundary
        )

    def is_active(self) -> bool:
        """
        Returns True when the FVG may still be monitored.
        """

        active_statuses = {
            "UNTOUCHED",
            "ENTERED",
            "PARTIALLY_MITIGATED",
        }

        return self.status in active_statuses

    def display_zone(self) -> str:
        """
        Returns readable FVG boundaries.
        """

        return (
            f"${self.lower_boundary:.2f} - "
            f"${self.upper_boundary:.2f}"
        )