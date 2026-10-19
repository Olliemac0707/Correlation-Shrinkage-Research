from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from numpy.testing import assert_allclose

from covariance_research.core import NumericalFailure
from covariance_research.historical import parse_chart, price_returns, sessions


def fixture_chart():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
    timestamps = [
        int(
            datetime.fromisoformat(day + "T09:30:00")
            .replace(tzinfo=ZoneInfo("America/New_York"))
            .timestamp()
        )
        for day in dates
    ]
    data = {
        "chart": {
            "error": None,
            "result": [
                {
                    "meta": {
                        "symbol": "SPY",
                        "currency": "USD",
                        "exchangeTimezoneName": "America/New_York",
                    },
                    "timestamp": timestamps,
                    "indicators": {
                        "adjclose": [{"adjclose": [100, 110, 99]}],
                        "quote": [{"close": [100, 110, 99]}],
                    },
                    "events": {},
                }
            ],
        }
    }
    return data, dates


def test_frozen_calendar_includes_special_exchange_closures():
    dates = sessions()
    assert len(dates) == 5283
    assert sum("2007-01-01" <= day <= "2025-12-31" for day in dates) == 4780
    for closure in ("2007-01-02", "2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"):
        assert closure not in dates
    assert dates[-1] == "2025-12-31"


def test_parser_accepts_correct_identity_and_complete_session_order():
    data, dates = fixture_chart()
    prices, _, close, events = parse_chart(data, "SPY", dates)
    assert_allclose(prices, [100, 110, 99])
    assert_allclose(close, prices)
    assert events == {}


@pytest.mark.parametrize(
    "problem",
    [
        "missing",
        "duplicate",
        "out_of_order",
        "currency",
        "identity",
        "timezone",
        "null",
        "negative",
        "provider_error",
    ],
)
def test_parser_rejects_bad_inputs_without_filling_or_deleting(problem):
    data, dates = fixture_chart()
    item = data["chart"]["result"][0]
    if problem == "missing":
        item["timestamp"].pop(1)
    elif problem == "duplicate":
        item["timestamp"][1] = item["timestamp"][0]
    elif problem == "out_of_order":
        item["timestamp"].reverse()
    elif problem == "currency":
        item["meta"]["currency"] = "GBP"
    elif problem == "identity":
        item["meta"]["symbol"] = "OTHER"
    elif problem == "timezone":
        item["meta"]["exchangeTimezoneName"] = "UTC"
    elif problem == "null":
        item["indicators"]["adjclose"][0]["adjclose"][1] = None
    elif problem == "negative":
        item["indicators"]["adjclose"][0]["adjclose"][1] = -1
    else:
        data["chart"]["error"] = {"code": "Forbidden"}
    with pytest.raises(NumericalFailure):
        parse_chart(data, "SPY", dates)


def test_timestamp_is_converted_to_exchange_date_not_utc_date():
    data, dates = fixture_chart()
    changed = deepcopy(data)
    changed["chart"]["result"][0]["timestamp"][0] = int(
        datetime.fromisoformat("2020-01-02T02:00:00+00:00").timestamp()
    )
    with pytest.raises(NumericalFailure):
        parse_chart(changed, "SPY", dates)


def test_simple_returns_preserve_portfolio_return_identity():
    prices = np.array([[100.0, 50.0], [110.0, 45.0], [99.0, 49.5]])
    returns = price_returns(prices)
    assert_allclose(returns, [[0.1, -0.1], [-0.1, 0.1]])
    weights = np.array([0.3, 0.7])
    assert_allclose(returns @ weights, [-0.04, 0.04])
    with pytest.raises(NumericalFailure):
        price_returns(np.array([[100.0, 50.0], [0.0, 50.0]]))
