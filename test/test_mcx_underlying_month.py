"""An option is priced off the future of its own month, not the soonest one.

MCX options expire a few days before their own future, so CRUDEOIL 17NOV26
belongs to CRUDEOIL19NOV26FUT. Resolving to the soonest unexpired future priced
it off the October contract.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

import services.option_symbol_service as oss


class _Row:
    def __init__(self, symbol, expiry):
        self.symbol, self.expiry, self.exchange = symbol, expiry, "MCX"


_FUTS = [
    _Row("CRUDEOIL19OCT26FUT", "19-OCT-26"),
    _Row("CRUDEOIL19NOV26FUT", "19-NOV-26"),
    _Row("CRUDEOIL18DEC26FUT", "18-DEC-26"),
    _Row("CRUDEOILM19NOV26FUT", "19-NOV-26"),  # a different product
]


@pytest.fixture
def on_day(monkeypatch):
    def _set(today):
        token = MagicMock()
        token.query.filter.return_value.all.return_value = _FUTS

        class _FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.combine(today, datetime.min.time())

        monkeypatch.setattr(oss, "SymToken", token)
        monkeypatch.setattr(oss, "datetime", _FixedDatetime)

    return _set


def test_next_month_options_use_next_month_future_on_front_expiry_day(on_day):
    on_day(date(2026, 10, 19))
    assert oss.resolve_underlying_quote("CRUDEOIL", "MCX", "17NOV26") == (
        "CRUDEOIL19NOV26FUT",
        "MCX",
    )


def test_far_expiry_uses_its_own_future(on_day):
    on_day(date(2026, 10, 20))
    assert oss.resolve_underlying_quote("CRUDEOIL", "MCX", "16DEC26") == (
        "CRUDEOIL18DEC26FUT",
        "MCX",
    )


def test_hyphenated_expiry_is_accepted(on_day):
    on_day(date(2026, 10, 20))
    assert oss.resolve_underlying_quote("CRUDEOIL", "MCX", "16-DEC-26")[0] == "CRUDEOIL18DEC26FUT"


def test_no_expiry_keeps_the_nearest_future(on_day):
    on_day(date(2026, 10, 19))
    assert oss.resolve_underlying_quote("CRUDEOIL", "MCX") == ("CRUDEOIL19OCT26FUT", "MCX")


def test_unparseable_expiry_keeps_the_nearest_future(on_day):
    on_day(date(2026, 10, 19))
    assert oss.resolve_underlying_quote("CRUDEOIL", "MCX", "garbage")[0] == "CRUDEOIL19OCT26FUT"


def test_past_expiry_never_goes_before_today(on_day):
    on_day(date(2026, 10, 20))
    assert (
        oss.find_near_month_futures("CRUDEOIL", "MCX", on_or_after=date(2026, 1, 1))["symbol"]
        == "CRUDEOIL19NOV26FUT"
    )


def test_spot_exchanges_are_unchanged():
    assert oss.resolve_underlying_quote("NIFTY", "NFO", "28OCT26") == ("NIFTY", "NFO")
