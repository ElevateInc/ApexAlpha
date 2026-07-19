"""
===========================================================
ApexAlpha
Watchlist Manager
Version: 1.0
===========================================================
"""

WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
]


def get_watchlist() -> list[str]:
    """
    Returns the current ApexAlpha watchlist.
    """

    return WATCHLIST.copy()


def add_symbol(symbol: str) -> None:
    """
    Adds a symbol to the watchlist.
    """

    symbol = symbol.upper()

    if symbol not in WATCHLIST:
        WATCHLIST.append(symbol)


def remove_symbol(symbol: str) -> None:
    """
    Removes a symbol from the watchlist.
    """

    symbol = symbol.upper()

    if symbol in WATCHLIST:
        WATCHLIST.remove(symbol)


def display_watchlist() -> None:
    """
    Displays the current watchlist.
    """

    print("\nCurrent Watchlist")
    print("-" * 30)

    for symbol in WATCHLIST:
        print(symbol)