# Quantitative NSE Trade Anomaly Detector 🚀

A high-throughput, multithreaded quantitative market scanner for the **Indian Stock Market (NSE)**. It dynamically scans **2,500+ publicly listed NSE equities** in parallel to detect unusual volume breakouts ($\Delta \ge 200\%$) indicating institutional accumulation, block deals, or smart-money activity.

`delta = (current_volume - rolling_baseline) / rolling_baseline`

Flagged when `delta >= 2.0` (Configurable threshold in `config.py` or directly in the GUI).

---

##  Key Features

* **🇮🇳 Complete NSE Coverage (~2,500+ Stocks)**: Dynamically fetches the official master list of all active equities directly from NSE India archives—zero hardcoded stock symbols.
* **⚡ High-Speed Parallel Engine**: Leverages Python's `ThreadPoolExecutor` to perform concurrent market scans across 2,500+ tickers in **under 30 seconds** (a 98% execution speedup).
* **🖥️ Dark Terminal GUI**: Custom charcoal/black UI theme featuring a structured tree table for flagged anomalies and real-time status metrics.
* **📊 Interactive Matplotlib Visuals**: Dual-panel chart rendering 1-month daily Close Price trends and Bullish (Green) / Bearish (Red) Volume distribution histograms.
* **⚡ In-Memory Smart Caching**: Caches historical price data locally to eliminate API rate limits (`429 Too Many Requests`) and prevent redundant network calls.
* **🎯 Target Price & Signal Analytics**: Displays Last Close, Day High/Low, and statistical target zones for flagged tickers.
* **🔌 Angel One SmartAPI Integration Ready**: Support for zero-delay live 5-minute candle feeds using official broker APIs (`smartapi-python`).

---

## 📐 The Math Behind It (`anomaly_engine.py`)

1. **Rolling Baseline Calculation**: Calculates a 20-day Simple Moving Average (SMA) of volume, excluding the current trading session:
   $$\text{Baseline} = \text{Mean}(\text{Volume}_{t-20} \dots \text{Volume}_{t-1})$$
2. **Volume Deviation ($\Delta$)**: Measures today's volume surge relative to normal historical levels:
   $$\Delta = \frac{\text{Volume}_{\text{today}} - \text{Baseline}}{\text{Baseline}}$$
3. **Anomaly Isolation**: Flags the security if $\Delta \ge \text{Threshold}$ (e.g., $200\%$ deviation = 3x normal volume). Focuses exclusively on the latest active trading session.

---

## 🛠️ Setup & Installation

## Setup

Clone this repo:
  ```
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
  ```

```bash
cd trade_anomaly_detector
pip install -r requirements.txt
```

### Required Packages (`requirements.txt`)
* `pandas`
* `requests`
* `yfinance`
* `matplotlib`
* `smartapi-python` (Optional: for Angel One live broker feed)
* `pyotp` (Optional: for TOTP authentication)

---

## 🚀 Running the Application

### 1. Launch the Dark Dashboard (Recommended)

```bash
python gui.py
```
* Custom threshold adjustment (e.g., enter `200` for 200% threshold).
* Click any stock from the flagged left table to instantly render its price/volume chart.

### 2. Command Line Interface (CLI)

```bash
python main.py                  # Default full scan
python main.py --threshold 3.0  # Require 300% volume surge
python main.py --equities-only  # Scan equities exclusively
```
---

## 📁 Project Architecture

text
├── config.py             <- Global parameters & dynamic NSE master list loader
├── anomaly_engine.py      <- Pure Python rolling baseline math engine (zero dependencies)
├── alerts.py             <- Terminal formatting & automated CSV alert logging
├── main.py               <- CLI entry point with ThreadPoolExecutor parallelization
├── gui.py                <- Dark Terminal GUI (Tkinter + Matplotlib Canvas + Local Cache)
└── data_sources/
    ├── equities.py       <- Stock data fetching engine (SmartAPI / Yahoo Finance)


---

## ⚙️ Configuration (`config.py`)

Custom tunables live in `config.py`:
* `DELTA_THRESHOLD`: Default volume multiplier (e.g., `2.0` = +200%).
* `BASELINE_WINDOW`: Moving average sample size (default: `20` trading days).
* `EQUITY_TICKERS`: Dynamically populated with all ~2,500+ NSE stock tickers via official NSE CSV archives.

---

## 📄 Disclaimer

This project is built for **educational and quantitative research purposes only**. Volume anomalies represent statistical deviations from baseline trends and do not constitute financial advice or explicit buy/sell signals.

