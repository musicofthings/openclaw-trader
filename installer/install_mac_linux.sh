#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${HOME}/.openclaw-trader"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[1/5] Creating install directory at ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"


echo "[2/5] Copying strategy + agent files"
mkdir -p "${INSTALL_DIR}/plugin" "${INSTALL_DIR}/openplot_agent"
cp "${REPO_ROOT}/plugin/ma_rsi_atr_plugin.pine" "${INSTALL_DIR}/plugin/"
cp "${REPO_ROOT}/openplot_agent/bridge.py" "${INSTALL_DIR}/openplot_agent/"

if [[ ! -f "${INSTALL_DIR}/openplot_agent/config.json" ]]; then
  cp "${REPO_ROOT}/openplot_agent/config.example.json" "${INSTALL_DIR}/openplot_agent/config.json"
fi


echo "[3/5] Preparing Python environment"
"${PYTHON_BIN}" -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip playwright
"${INSTALL_DIR}/.venv/bin/python" -m playwright install chromium


echo "[4/5] Writing launchers"
cat > "${INSTALL_DIR}/run-openplot-agent.sh" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${BASE_DIR}/.venv/bin/python" "${BASE_DIR}/openplot_agent/bridge.py" --config "${BASE_DIR}/openplot_agent/config.json"
LAUNCH
chmod +x "${INSTALL_DIR}/run-openplot-agent.sh"

cat > "${INSTALL_DIR}/install-tradingview-script.sh" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${BASE_DIR}/.venv/bin/python" "${BASE_DIR}/automation/install_tradingview_script.py" --pine "${BASE_DIR}/plugin/ma_rsi_atr_plugin.pine"
LAUNCH
chmod +x "${INSTALL_DIR}/install-tradingview-script.sh"

mkdir -p "${INSTALL_DIR}/automation"
cp "${REPO_ROOT}/installer/install_tradingview_script.py" "${INSTALL_DIR}/automation/"


echo "[5/5] Done"
echo "Edit config: ${INSTALL_DIR}/openplot_agent/config.json"
echo "Run agent:   ${INSTALL_DIR}/run-openplot-agent.sh"
echo "Install script in TradingView via browser automation:"
echo "            ${INSTALL_DIR}/install-tradingview-script.sh"
