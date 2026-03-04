# OpenClaw TradingView Plugin (Pine Script v5)

This plugin package contains a backtestable TradingView strategy based on:
- MA crossover entries,
- RSI filtering,
- ATR-based stop-loss and take-profit exits.

## File
- `ma_rsi_atr_plugin.pine`

## Install in TradingView
1. Open any chart in TradingView.
2. Open **Pine Editor**.
3. Copy all contents of `ma_rsi_atr_plugin.pine` and paste into the editor.
4. Click **Add to chart**.

## Inputs to tune
- `Short MA Length` / `Long MA Length`
- `RSI Length`, `RSI Overbought`, `RSI Oversold`
- `ATR Length`
- `ATR Stop (X)` and `ATR Target (X)`
- Optional date filter inputs for bounded backtests

## Notes
- This strategy is for research and backtesting; it is not financial advice.
- For options workflows, use this as an underlying signal and execute options logic separately.
- Always include slippage/commission assumptions and validate across multiple market regimes.
