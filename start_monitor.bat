@echo off
echo ========================================
echo ESP32 USB Display - System Monitor
echo ========================================
echo.
echo Starte Monitoring...
echo Druecke Ctrl+C zum Beenden
echo.

REM Auto-Detection verwenden
python pc_monitor.py

REM Falls Fehler, Fenster offen lassen
if errorlevel 1 (
    echo.
    echo [FEHLER] Monitoring konnte nicht gestartet werden
    pause
)
