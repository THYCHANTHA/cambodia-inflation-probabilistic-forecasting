import pandas as pd
import pytest

from cambodia_inflation.data.parsing import (
    DateParseError,
    detect_day_month_swap,
    parse_portal_month,
    parse_portal_months,
    repair_swapped_iso_months,
)


# 1. M/1/YYYY parsing
@pytest.mark.parametrize(
    ("text", "expected"),
    [("1/1/2005", "2005-01"), ("2/1/2005", "2005-02"), ("12/1/2025", "2025-12"), (" 10/1/2016 ", "2016-10")],
)
def test_parse_month_first_strings(text, expected):
    assert parse_portal_month(text) == pd.Period(expected, freq="M")


def test_parse_sequence_keeps_order_and_frequency():
    idx = parse_portal_months(["11/1/2005", "12/1/2005", "1/1/2006"])
    assert list(idx.astype(str)) == ["2005-11", "2005-12", "2006-01"]
    assert idx.freqstr == "M"


@pytest.mark.parametrize("text", ["1/2/2005", "13/1/2005", "0/1/2005", "2005-02-01", "Feb 2005", "2/1/05", ""])
def test_rejects_anything_not_month_first_with_day_one(text):
    with pytest.raises(DateParseError):
        parse_portal_month(text)


def test_day_field_other_than_one_signals_day_first_file():
    # "1/2/2005" is 1 Feb 2005 in a DD/MM file; this parser must refuse it rather than read January.
    with pytest.raises(DateParseError, match="day 1"):
        parse_portal_month("1/2/2005")


# 2. Detection of the incorrect DD/MM/YYYY interpretation
def test_detects_portal_api_swap_signature():
    # What the JSON API returns for Jan-Apr 2005 after reading "M/1/YYYY" as "DD/MM/YYYY".
    swapped = ["2005-01-01", "2005-01-02", "2005-01-03", "2005-01-04"]
    assert detect_day_month_swap(swapped)
    repaired = repair_swapped_iso_months(swapped)
    assert list(repaired.astype(str)) == ["2005-01", "2005-02", "2005-03", "2005-04"]


def test_swap_across_year_boundary():
    swapped = ["2005-01-11", "2005-01-12", "2006-01-01", "2006-01-02"]
    assert detect_day_month_swap(swapped)
    assert list(repair_swapped_iso_months(swapped).astype(str)) == ["2005-11", "2005-12", "2006-01", "2006-02"]


@pytest.mark.parametrize(
    "dates",
    [
        ["2005-01-01", "2005-02-01", "2005-03-01"],  # correct ISO months
        ["2005-01-01"],  # one date is not evidence
        ["2005-01-01", "2005-01-13"],  # day 13 cannot be a month
        ["2005-01-01", "2005-01-03"],  # swapped reading is not consecutive
    ],
)
def test_no_false_positive(dates):
    assert not detect_day_month_swap(dates)


def test_repair_refuses_without_signature():
    with pytest.raises(DateParseError):
        repair_swapped_iso_months(["2005-01-01", "2005-02-01"])
