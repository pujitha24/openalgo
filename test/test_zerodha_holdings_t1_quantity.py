from broker.zerodha.mapping.order_data import (
    calculate_portfolio_statistics,
    transform_holdings_data,
)


def _row(quantity, t1_quantity):
    return {
        "tradingsymbol": "SBIN",
        "exchange": "NSE",
        "product": "CNC",
        "quantity": quantity,
        "t1_quantity": t1_quantity,
        "average_price": 100.0,
        "last_price": 110.0,
        "pnl": 100.0,
    }


def test_t1_quantity_counts_toward_holding_quantity():
    [row] = transform_holdings_data([_row(0, 10)])
    assert row["quantity"] == 10
    assert row["t1_quantity"] == 10


def test_settled_and_t1_quantity_are_summed():
    [row] = transform_holdings_data([_row(5, 10)])
    assert row["quantity"] == 15


def test_missing_t1_quantity_is_unchanged():
    raw = _row(7, 0)
    del raw["t1_quantity"]
    [row] = transform_holdings_data([raw])
    assert row["quantity"] == 7


def test_statistics_include_t1_quantity():
    stats = calculate_portfolio_statistics([_row(0, 10)])
    assert stats["totalholdingvalue"] == 1100.0
    assert stats["totalinvvalue"] == 1000.0
