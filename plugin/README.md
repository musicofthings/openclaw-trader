# OpenClaw TradingView Plugin + OpenPlot Agent Bridge

This package includes:
- A Pine Script v5 strategy (`ma_rsi_atr_plugin.pine`), and
- An installable OpenPlot agent bridge that receives TradingView webhook alerts and forwards them to OpenPlot.

## Files
- `ma_rsi_atr_plugin.pine` - strategy logic + webhook-ready alert payload templates.

## One-command installation

### macOS / Linux
```bash
./installer/install_mac_linux.sh
```

### Windows (PowerShell)
```powershell
.\installer\install_windows.ps1
```

Both installers will:
1. Copy strategy + agent files to `~/.openclaw-trader` (or `%USERPROFILE%\.openclaw-trader`).
2. Create a Python virtual environment.
3. Install Playwright + Chromium for browser automation.
4. Create launchers for:
   - `run-openplot-agent` (webhook bridge)
   - `install-tradingview-script` (automated script installation in TradingView UI)

## Automated TradingView script installation (no copy/paste)
Run:
- macOS/Linux: `~/.openclaw-trader/install-tradingview-script.sh`
- Windows: `%USERPROFILE%\.openclaw-trader\install-tradingview-script.bat`

This launches a browser automation flow to open TradingView and inject the strategy code into the Pine editor.

## OpenPlot agent configuration
Edit generated config:
- macOS/Linux: `~/.openclaw-trader/openplot_agent/config.json`
- Windows: `%USERPROFILE%\.openclaw-trader\openplot_agent\config.json`

Set:
- `shared_secret`: must match the `OpenPlot Agent Token` input in the Pine strategy.
- `openplot_ingest_url`: your OpenPlot ingest endpoint.
- `openplot_api_token`: API token for OpenPlot.

Run the bridge:
- macOS/Linux: `~/.openclaw-trader/run-openplot-agent.sh`
- Windows: `%USERPROFILE%\.openclaw-trader\run-openplot-agent.bat`

## Notes
- This is for strategy research/backtesting and signal automation; it is not financial advice.
- For options workflows, use these underlying signals and execute options-specific logic in your execution stack.
