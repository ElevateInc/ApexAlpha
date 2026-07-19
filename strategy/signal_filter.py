"""
===========================================================
ApexAlpha
Signal Filter
Version: 1.0
===========================================================
"""


def should_notify(
    score: int,
    minimum_score: int = 85,
) -> bool:
    """
    Decide whether an opportunity score is strong enough
    to trigger an ApexAlpha notification.

    Parameters
    ----------
    score : int
        The opportunity score from 0 to 100.

    minimum_score : int
        The minimum score required for notification.

    Returns
    -------
    bool
        True when the score reaches the threshold.
    """

    return score >= minimum_score