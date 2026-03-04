"""Trading agents for openclaw-trader.

Each agent receives a :class:`~trader.market.MarketSnapshot` and a
:class:`~trader.market.Portfolio` and returns a :class:`TradeSignal`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from trader.market import MarketSnapshot, Portfolio


class Action(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeSignal:
    """The decision produced by a trading agent."""

    def __init__(self, action: Action, quantity: float = 0.0, reason: str = ""):
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        self.action = action
        self.quantity = quantity
        self.reason = reason

    def __repr__(self) -> str:
        return f"TradeSignal(action={self.action}, quantity={self.quantity}, reason={self.reason!r})"


class TradingAgent(ABC):
    """Abstract base class for all trading agents."""

    @abstractmethod
    def decide(self, snapshot: MarketSnapshot, portfolio: Portfolio) -> TradeSignal:
        """Return a trading decision based on the current market and portfolio."""


class HoldAgent(TradingAgent):
    """Always holds — useful as a baseline."""

    def decide(self, snapshot: MarketSnapshot, portfolio: Portfolio) -> TradeSignal:
        return TradeSignal(Action.HOLD, reason="hold strategy")


class SimpleMomentumAgent(TradingAgent):
    """Buys when the latest close is above the short-term average; sells otherwise.

    Parameters
    ----------
    window:
        Number of candles used for the moving average (default 3).
    trade_fraction:
        Fraction of available cash/position to trade (0 < trade_fraction <= 1).
    """

    def __init__(self, window: int = 3, trade_fraction: float = 1.0):
        if window < 1:
            raise ValueError("window must be >= 1")
        if not (0 < trade_fraction <= 1):
            raise ValueError("trade_fraction must be in (0, 1]")
        self.window = window
        self.trade_fraction = trade_fraction

    def decide(self, snapshot: MarketSnapshot, portfolio: Portfolio) -> TradeSignal:
        closes = snapshot.closes
        if len(closes) < self.window + 1:
            return TradeSignal(Action.HOLD, reason="insufficient data")

        avg = sum(closes[-self.window - 1 : -1]) / self.window
        latest_close = closes[-1]

        if latest_close > avg:
            qty = (portfolio.cash * self.trade_fraction) / latest_close
            return TradeSignal(Action.BUY, quantity=qty, reason="price above average")

        if latest_close < avg and portfolio.position > 0:
            qty = portfolio.position * self.trade_fraction
            return TradeSignal(Action.SELL, quantity=qty, reason="price below average")

        return TradeSignal(Action.HOLD, reason="no clear signal")


class ThresholdAgent(TradingAgent):
    """Buys when price drops by *buy_threshold* from peak; sells when it rises by *sell_threshold*.

    Parameters
    ----------
    buy_threshold:
        Fractional drop from peak to trigger a buy (e.g. 0.05 for 5 %).
    sell_threshold:
        Fractional rise from trough to trigger a sell (e.g. 0.05 for 5 %).
    trade_fraction:
        Fraction of available cash/position to trade.
    """

    def __init__(
        self,
        buy_threshold: float = 0.05,
        sell_threshold: float = 0.05,
        trade_fraction: float = 1.0,
    ):
        if buy_threshold <= 0 or sell_threshold <= 0:
            raise ValueError("thresholds must be positive")
        if not (0 < trade_fraction <= 1):
            raise ValueError("trade_fraction must be in (0, 1]")
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.trade_fraction = trade_fraction
        self._peak: float | None = None
        self._trough: float | None = None

    def reset(self):
        """Reset tracked peak/trough state."""
        self._peak = None
        self._trough = None

    def decide(self, snapshot: MarketSnapshot, portfolio: Portfolio) -> TradeSignal:
        if not snapshot.candles:
            return TradeSignal(Action.HOLD, reason="no data")

        price = snapshot.latest.close
        self._peak = max(self._peak, price) if self._peak is not None else price
        self._trough = min(self._trough, price) if self._trough is not None else price

        if portfolio.cash > 0 and self._peak > 0:
            drop = (self._peak - price) / self._peak
            if drop >= self.buy_threshold:
                qty = (portfolio.cash * self.trade_fraction) / price
                self._trough = price
                return TradeSignal(Action.BUY, quantity=qty, reason=f"price dropped {drop:.1%} from peak")

        if portfolio.position > 0 and self._trough is not None and self._trough > 0:
            rise = (price - self._trough) / self._trough
            if rise >= self.sell_threshold:
                qty = portfolio.position * self.trade_fraction
                self._peak = price
                return TradeSignal(Action.SELL, quantity=qty, reason=f"price rose {rise:.1%} from trough")

        return TradeSignal(Action.HOLD, reason="no threshold crossed")
