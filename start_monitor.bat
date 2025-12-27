@echo off
echo ========================================
echo ESP32 USB Display - System Monitor
echo ========================================
echo.

REM Pruefe ob LibreHardwareMonitor vorhanden ist
if exist "LibreHardwareMonitor\LibreHardwareMonitor.exe" (
    echo [INFO] Starte LibreHardwareMonitor...
    
    REM Pruefe ob bereits laeuft
    tasklist /FI "IMAGENAME eq LibreHardwareMonitor.exe" 2>NUL | find /I /N "LibreHardwareMonitor.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo [OK] LibreHardwareMonitor laeuft bereits
    ) else (
        REM Starte LibreHardwareMonitor im Hintergrund
        start "" "LibreHardwareMonitor\LibreHardwareMonitor.exe"
        echo [OK] LibreHardwareMonitor gestartet
        echo [INFO] Warte 3 Sekunden auf Initialisierung...
        timeout /t 3 /nobreak >nul
    )
    echo.
) else (
    echo [WARNUNG] LibreHardwareMonitor nicht gefunden in: LibreHardwareMonitor\
    echo            Script funktioniert mit eingeschraenkten Sensor-Daten.
    echo            Fuehre setup.bat aus um LibreHardwareMonitor zu installieren.
    echo.
)

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
