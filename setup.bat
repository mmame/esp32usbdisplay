@echo off
echo ========================================
echo ESP32 USB Display - Setup
echo ========================================
echo.

REM Python-Version pruefen
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    echo Bitte Python von https://www.python.org installieren
    pause
    exit /b 1
)

echo [OK] Python gefunden:
python --version
echo.

REM Python-Pakete installieren
echo [INFO] Installiere benoetigte Pakete...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [FEHLER] Installation fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [OK] Python-Pakete installiert!
echo ========================================
echo.

REM LibreHardwareMonitor Setup
echo ========================================
echo LibreHardwareMonitor Setup
echo ========================================
echo.
echo Fuer vollstaendige Sensor-Daten (CPU-Temp, Luefter, etc.)
echo wird LibreHardwareMonitor benoetigt.
echo.
echo Moechten Sie LibreHardwareMonitor jetzt herunterladen? (J/N)
set /p INSTALL_LHM=
if /i "%INSTALL_LHM%"=="J" (
    echo.
    echo [INFO] Lade LibreHardwareMonitor herunter...
    
    REM Download mit PowerShell
    powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest/download/LibreHardwareMonitor-net472.zip' -OutFile 'LibreHardwareMonitor.zip'}"
    
    if exist LibreHardwareMonitor.zip (
        echo [OK] Download erfolgreich
        echo [INFO] Entpacke Dateien...
        
        REM Entpacken mit PowerShell
        powershell -Command "& {Expand-Archive -Path 'LibreHardwareMonitor.zip' -DestinationPath 'LibreHardwareMonitor' -Force}"
        
        del LibreHardwareMonitor.zip
        
        echo [OK] LibreHardwareMonitor entpackt nach: LibreHardwareMonitor\
        echo.
        echo ========================================
        echo WICHTIG - Vor dem Start des Monitors:
        echo ========================================
        echo   1. LibreHardwareMonitor\LibreHardwareMonitor.exe als ADMINISTRATOR starten
        echo   2. Options -^> Remote Web Server -^> Run aktivieren (Checkbox anklicken!)
        echo   3. Port sollte auf 8085 stehen (Standard)
        echo   4. LibreHardwareMonitor laufen lassen (im Hintergrund)
        echo   5. Dann erst start_monitor.bat ausfuehren
        echo.
        echo HINWEIS: Der Webserver MUSS aktiviert sein, sonst funktioniert
        echo          das Monitoring nicht!
        echo.
    ) else (
        echo [FEHLER] Download fehlgeschlagen
        echo Bitte manuell herunterladen von:
        echo https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
        echo.
    )
) else (
    echo.
    echo [INFO] Ueberspringe LibreHardwareMonitor Installation
    echo.
    echo Script funktioniert auch ohne, aber mit eingeschraenkten Sensor-Daten.
    echo Manueller Download spaeter moeglich von:
    echo https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
    echo.
)

echo ========================================
echo [OK] Setup erfolgreich abgeschlossen!
echo ========================================
echo.
echo WICHTIGER HINWEIS:
echo   Vor dem ersten Start von start_monitor.bat muessen Sie:
echo   1. LibreHardwareMonitor als ADMINISTRATOR starten
echo   2. Im Menu: Options -^> Remote Web Server -^> "Run" aktivieren!
echo   3. LibreHardwareMonitor im Hintergrund laufen lassen
echo.
echo Starte das Monitoring dann mit:
echo   start_monitor.bat
echo.
echo Oder manuell:
echo   python pc_monitor.py
echo.
pause
