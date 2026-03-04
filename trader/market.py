"""Market data structures for the openclaw-trader."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Candle:
    """OHLCV candle representing a single time period."""

    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.open <= 0 or self.close <= 0 or self.high <= 0 or self.low <= 0:
            raise ValueError("price values must be positive")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")


@dataclass
class Portfolio:
    """Tracks cash and a single asset position."""

    cash: float
    position: float = 0.0

    def __post_init__(self):
        if self.cash < 0:
            raise ValueError("cash must be non-negative")
        if self.position < 0:
            raise ValueError("position must be non-negative")

    def equity(self, price: float) -> float:
        """Return total portfolio value at the given price."""
        return self.cash + self.position * price


@dataclass
class MarketSnapshot:
    """A window of recent candles available to an agent."""

    candles: List[Candle] = field(default_factory=list)

    @property
    def closes(self) -> List[float]:
        return [c.close for c in self.candles]

    @property
    def latest(self) -> Candle:
        if not self.candles:
            raise ValueError("no candles available")
        return self.candles[-1]
