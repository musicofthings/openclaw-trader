"""Tests for trading agents."""

import pytest

from trader.market import Candle, MarketSnapshot, Portfolio
from trader.agent import (
    Action,
    HoldAgent,
    SimpleMomentumAgent,
    ThresholdAgent,
    TradeSignal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_snapshot(closes):
    """Build a MarketSnapshot from a list of close prices (all OHLCV identical)."""
    candles = [Candle(open=p, high=p, low=p, close=p, volume=100.0) for p in closes]
    return MarketSnapshot(candles=candles)


def make_portfolio(cash=10_000.0, position=0.0):
    return Portfolio(cash=cash, position=position)


# ---------------------------------------------------------------------------
# TradeSignal
# ---------------------------------------------------------------------------


class TestTradeSignal:
    def test_buy_signal(self):
        sig = TradeSignal(Action.BUY, quantity=5.0, reason="test")
        assert sig.action == Action.BUY
        assert sig.quantity == 5.0

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError):
            TradeSignal(Action.BUY, quantity=-1.0)

    def test_repr(self):
        sig = TradeSignal(Action.HOLD)
        assert "HOLD" in repr(sig)


# ---------------------------------------------------------------------------
# Candle & Portfolio validation
# ---------------------------------------------------------------------------


class TestCandle:
    def test_valid_candle(self):
        c = Candle(open=100, high=110, low=90, close=105, volume=500)
        assert c.close == 105

    def test_high_below_low_raises(self):
        with pytest.raises(ValueError):
            Candle(open=100, high=80, low=90, close=95)

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            Candle(open=-1, high=10, low=5, close=8)

    def test_negative_volume_raises(self):
        with pytest.raises(ValueError):
            Candle(open=10, high=15, low=8, close=12, volume=-5)


class TestPortfolio:
    def test_equity(self):
        p = Portfolio(cash=1000.0, position=10.0)
        assert p.equity(50.0) == pytest.approx(1500.0)

    def test_negative_cash_raises(self):
        with pytest.raises(ValueError):
            Portfolio(cash=-1.0)

    def test_negative_position_raises(self):
        with pytest.raises(ValueError):
            Portfolio(cash=100.0, position=-1.0)


class TestMarketSnapshot:
    def test_closes(self):
        snap = make_snapshot([10, 20, 30])
        assert snap.closes == [10, 20, 30]

    def test_latest(self):
        snap = make_snapshot([10, 20, 30])
        assert snap.latest.close == 30

    def test_latest_empty_raises(self):
        snap = MarketSnapshot()
        with pytest.raises(ValueError):
            _ = snap.latest


# ---------------------------------------------------------------------------
# HoldAgent
# ---------------------------------------------------------------------------


class TestHoldAgent:
    def test_always_holds(self):
        agent = HoldAgent()
        snap = make_snapshot([100, 105, 110])
        port = make_portfolio()
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD

    def test_hold_with_empty_snapshot(self):
        agent = HoldAgent()
        snap = MarketSnapshot()
        port = make_portfolio()
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD


# ---------------------------------------------------------------------------
# SimpleMomentumAgent
# ---------------------------------------------------------------------------


class TestSimpleMomentumAgent:
    def test_buy_when_price_above_average(self):
        # window=2, avg of last 2 candles before latest = avg([100, 100]) = 100
        # latest close = 110 > 100 → BUY
        agent = SimpleMomentumAgent(window=2)
        snap = make_snapshot([100, 100, 110])
        port = make_portfolio(cash=1000.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.BUY
        assert signal.quantity > 0

    def test_sell_when_price_below_average(self):
        # window=2, avg([110, 110]) = 110, latest=90 < 110 → SELL
        agent = SimpleMomentumAgent(window=2)
        snap = make_snapshot([110, 110, 90])
        port = make_portfolio(cash=0.0, position=10.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.SELL
        assert signal.quantity == pytest.approx(10.0)

    def test_hold_when_price_equals_average(self):
        agent = SimpleMomentumAgent(window=2)
        snap = make_snapshot([100, 100, 100])
        port = make_portfolio(cash=500.0, position=5.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD

    def test_hold_when_insufficient_data(self):
        agent = SimpleMomentumAgent(window=3)
        snap = make_snapshot([100, 110])  # only 2 candles, need 4
        port = make_portfolio()
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD

    def test_no_sell_without_position(self):
        agent = SimpleMomentumAgent(window=2)
        snap = make_snapshot([110, 110, 90])
        port = make_portfolio(cash=1000.0, position=0.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            SimpleMomentumAgent(window=0)

    def test_invalid_trade_fraction_raises(self):
        with pytest.raises(ValueError):
            SimpleMomentumAgent(trade_fraction=0.0)

    def test_trade_fraction_respected(self):
        agent = SimpleMomentumAgent(window=1, trade_fraction=0.5)
        snap = make_snapshot([100, 110])
        port = make_portfolio(cash=1000.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.BUY
        # 0.5 * 1000 / 110 ≈ 4.545...
        assert signal.quantity == pytest.approx(0.5 * 1000.0 / 110.0)


# ---------------------------------------------------------------------------
# ThresholdAgent
# ---------------------------------------------------------------------------


class TestThresholdAgent:
    def test_hold_initially(self):
        agent = ThresholdAgent(buy_threshold=0.1, sell_threshold=0.1)
        snap = make_snapshot([100])
        port = make_portfolio(cash=1000.0)
        signal = agent.decide(snap, port)
        assert signal.action == Action.HOLD

    def test_buy_when_price_drops_enough(self):
        agent = ThresholdAgent(buy_threshold=0.1, sell_threshold=0.1)
        port = make_portfolio(cash=1000.0)
        # Establish peak at 100
        agent.decide(make_snapshot([100]), port)
        # Price drops 10 % → should BUY
        signal = agent.decide(make_snapshot([90]), port)
        assert signal.action == Action.BUY
        assert signal.quantity == pytest.approx(1000.0 / 90.0)

    def test_no_buy_when_drop_insufficient(self):
        agent = ThresholdAgent(buy_threshold=0.1, sell_threshold=0.1)
        port = make_portfolio(cash=1000.0)
        agent.decide(make_snapshot([100]), port)
        signal = agent.decide(make_snapshot([95]), port)
        assert signal.action == Action.HOLD

    def test_sell_when_price_rises_enough(self):
        agent = ThresholdAgent(buy_threshold=0.1, sell_threshold=0.1)
        port = make_portfolio(cash=0.0, position=10.0)
        # Establish trough at 90
        agent.decide(make_snapshot([90]), port)
        # Price rises 10 % → should SELL
        signal = agent.decide(make_snapshot([99]), port)
        assert signal.action == Action.SELL
        assert signal.quantity == pytest.approx(10.0)

    def test_no_sell_without_position(self):
        agent = ThresholdAgent(buy_threshold=0.1, sell_threshold=0.1)
        port = make_portfolio(cash=1000.0, position=0.0)
        agent.decide(make_snapshot([90]), port)
        signal = agent.decide(make_snapshot([100]), port)
        assert signal.action != Action.SELL

    def test_reset_clears_state(self):
        agent = ThresholdAgent(buy_threshold=0.1)
        port = make_portfolio(cash=1000.0)
        agent.decide(make_snapshot([100]), port)
        agent.reset()
        assert agent._peak is None
        assert agent._trough is None

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            ThresholdAgent(buy_threshold=0.0)

    def test_invalid_sell_threshold_raises(self):
        with pytest.raises(ValueError):
            ThresholdAgent(sell_threshold=-0.1)
