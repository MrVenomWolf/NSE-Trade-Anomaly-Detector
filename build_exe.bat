@echo off
REM Run this on Windows, inside the project folder, after
REM   pip install -r requirements.txt
REM Produces dist\TradeAnomalyDetector.exe (a single file you can
REM double-click, no Python install needed on the machine that runs it).

pyinstaller --noconfirm --onefile --windowed ^
  --name TradeAnomalyDetector ^
  --hidden-import=yfinance ^
  --hidden-import=pandas ^
  --hidden-import=feedparser ^
  gui.py

echo.
echo Done. Find your exe at dist\TradeAnomalyDetector.exe
pause
