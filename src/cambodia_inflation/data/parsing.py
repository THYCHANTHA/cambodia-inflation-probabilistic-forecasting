"""Date parsing for the Data EF CPI file.

The CSV writes months as ``M/1/YYYY`` (``2/1/2005`` is February 2005) although the portal metadata declares
``DD/MM/YYYY``. Reading the strings as DD/MM gives 2005-01-02 for February 2005, which is what the portal's JSON API
returns. This module parses the strings explicitly and detects that swap; it never relies on the declared format.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from itertools import pairwise

import pandas as pd

_PORTAL_RE = re.compile(r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$")
_ISO_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


class DateParseError(ValueError):
    """A date string does not have the expected structure."""


def parse_portal_month(value: str) -> pd.Period:
    """Parse one ``M/1/YYYY`` string into a monthly period.

    Raises ``DateParseError`` if the string is not of that form, if the middle field is not 1 (which would mean the
    file is not month-first), or if the month is outside 1-12.
    """
    match = _PORTAL_RE.match(value)
    if match is None:
        raise DateParseError(f"not an M/1/YYYY date: {value!r}")
    month, day, year = (int(g) for g in match.groups())
    if day != 1:
        raise DateParseError(f"expected day 1 in M/1/YYYY, got {value!r} (file may not be month-first)")
    if not 1 <= month <= 12:
        raise DateParseError(f"month out of range in {value!r}")
    return pd.Period(year=year, month=month, freq="M")


def parse_portal_months(values: Iterable[str]) -> pd.PeriodIndex:
    """Parse a sequence of ``M/1/YYYY`` strings into a monthly ``PeriodIndex`` (order preserved)."""
    return pd.PeriodIndex([parse_portal_month(v) for v in values], freq="M")


def _iso_parts(values: Sequence[str]) -> list[tuple[int, int, int]]:
    parts = []
    for v in values:
        match = _ISO_RE.match(v)
        if match is None:
            raise DateParseError(f"not an ISO YYYY-MM-DD date: {v!r}")
        parts.append(tuple(int(g) for g in match.groups()))
    return parts


def _is_consecutive_monthly(months: list[tuple[int, int]]) -> bool:
    if not months:
        return False
    ordinals = [y * 12 + (m - 1) for y, m in months]
    return all(b - a == 1 for a, b in pairwise(ordinals))


def detect_day_month_swap(iso_dates: Sequence[str]) -> bool:
    """Return True if ISO dates look like ``M/1/YYYY`` strings that were read as ``DD/MM/YYYY``.

    The signature of the swap: taken at face value the (year, month) pairs repeat or are not monthly, every day field is
    within 1-12, and reading the day field as the month gives a consecutive monthly sequence. A single date is not
    enough evidence and returns False.
    """
    parts = _iso_parts(iso_dates)
    if len(parts) < 2:
        return False
    as_is = [(y, m) for y, m, _ in parts]
    swapped = [(y, d) for y, _, d in parts]
    if _is_consecutive_monthly(as_is):
        return False
    if any(not 1 <= d <= 12 for _, _, d in parts):
        return False
    if any(m != 1 for _, m, _ in parts):
        return False
    return _is_consecutive_monthly(swapped)


def repair_swapped_iso_months(iso_dates: Sequence[str]) -> pd.PeriodIndex:
    """Convert swapped ISO dates (e.g. ``2005-01-02`` meaning February 2005) to monthly periods.

    Raises ``DateParseError`` unless :func:`detect_day_month_swap` confirms the swap.
    """
    if not detect_day_month_swap(iso_dates):
        raise DateParseError("dates do not show the M/1/YYYY-read-as-DD/MM/YYYY signature; refusing to repair")
    return pd.PeriodIndex([pd.Period(year=y, month=d, freq="M") for y, _, d in _iso_parts(iso_dates)], freq="M")
