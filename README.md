# ESP32 USB Display - PC System Monitor

![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=flat&logo=espressif&logoColor=white)
![PlatformIO](https://img.shields.io/badge/PlatformIO-FF7F00?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUwMCIgaGVpZ2h0PSIyNTAwIiB2aWV3Qm94PSIwIDAgMjU2IDI1NiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCI+PHBhdGggZD0iTTEyOCAwQzkzLjgxIDAgNjEuNjY2IDEzLjMxNCAzNy40OSAzNy40OSAxMy4zMTQgNjEuNjY2IDAgOTMuODEgMCAxMjhjMCAzNC4xOSAxMy4zMTQgNjYuMzM0IDM3LjQ5IDkwLjUxQzYxLjY2NiAyNDIuNjg2IDkzLjgxIDI1NiAxMjggMjU2YzM0LjE5IDAgNjYuMzM0LTEzLjMxNCA5MC41MS0zNy40OUMyNDIuNjg2IDE5NC4zMzQgMjU2IDE2Mi4xOSAyNTYgMTI4YzAtMzQuMTktMTMuMzE0LTY2LjMzNC0zNy40OS05MC41MUMxOTQuMzM0IDEzLjMxNCAxNjIuMTkgMCAxMjggMCIgZmlsbD0iI0ZGN0YwMCIvPjwvc3ZnPg==&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Ein USB-Display-System, das PC-Systemdaten (CPU/GPU Temperatur, Lüfter, Auslastung) auf einem 320x240 TFT-Display am ESP32 anzeigt.

![ESP32 Display Demo](https://via.placeholder.com/600x200/1C9F77/FFFFFF?text=ESP32+USB+Display)

## ✨ Features

- 🌡️ **CPU/GPU Temperaturen** in Echtzeit
- 📊 **Auslastungsanzeige** mit Fortschrittsbalken
- 🌀 **Lüftergeschwindigkeiten** (RPM)
- 🔄 **Auto-Detection** des ESP32-Ports
- 📡 **LibreHardwareMonitor** Support für vollständige Sensor-Daten
- 🎨 **Farbcodierte Warnungen** (Grün/Gelb/Rot)
- ⚡ **Optimierte Sprite-Rendering** ohne Flackern

## 📋 Hardware

- **ESP32** Development Board
- **ILI9341 TFT Display** (320x240 Pixel)
- **USB-Kabel** (Verbindung PC ↔ ESP32)

### Display-Verkabelung (SPI)

| ESP32 Pin | Display Pin | Funktion |
|-----------|-------------|----------|
| GPIO 23   | MOSI        | Daten    |
| GPIO 18   | SCK         | Clock    |
| GPIO 5    | CS          | Chip Select |
| GPIO 2    | DC          | Data/Command |
| GPIO 4    | RST         | Reset    |
| 3.3V      | VCC         | Stromversorgung |
| GND       | GND         | Masse    |

## 🚀 Installation

### 1. ESP32 Firmware flashen

```bash
# Im Projekt-Verzeichnis
pio run --target upload
```

Oder über PlatformIO IDE: 
- "Build" (Ctrl+Alt+B)
- "Upload" (Ctrl+Alt+U)

### 2. Python-Umgebung einrichten

```bash
# Python-Pakete installieren
pip install -r requirements.txt
```

**Benötigte Pakete:**
- `pyserial` - Serial-Kommunikation
- `psutil` - System-Informationen (CPU, RAM)
- `gputil` - GPU-Informationen (NVIDIA)

### 3. COM-Port ermitteln

```bash
# Verfügbare Ports anzeigen
python pc_monitor.py --list
```

Beispiel-Ausgabe:
```
COM3 - USB-SERIAL CH340 (COM3)
COM5 - Intel(R) Active Management...
```

## 📊 Verwendung

### Basis-Nutzung

```bash
# Standard (Autosense)
python pc_monitor.py

# Eigener Port
python pc_monitor.py --port COM5

# Eigenes Update-Intervall (0.5 Sekunden)
python pc_monitor.py --interval 0.5
```

### Erweiterte Optionen

```bash
python pc_monitor.py --help
```

**Parameter:**
- `--port, -p` : Serial Port (default: COM3)
- `--baud, -b` : Baudrate (default: 115200)
- `--interval, -i` : Update-Intervall in Sekunden (default: 1.0)
- `--list, -l` : Liste verfügbare Serial-Ports

## 📡 Kommunikationsprotokoll

### JSON-Format (PC → ESP32)

```json
{
  "cpu_temp": 55.3,
  "cpu_usage": 42.5,
  "cpu_fan": 1800,
  "gpu_temp": 68.0,
  "gpu_usage": 85.2,
  "gpu_fan": 2400,
  "ram_usage": 67.8
}
```

**Datenfelder:**
- `cpu_temp` - CPU-Temperatur in °C
- `cpu_usage` - CPU-Auslastung in %
- `cpu_fan` - CPU-Lüfter in RPM
- `gpu_temp` - GPU-Temperatur in °C
- `gpu_usage` - GPU-Auslastung in %
- `gpu_fan` - GPU-Lüfter in RPM
- `ram_usage` - RAM-Auslastung in %

### Serial-Einstellungen

- **Baudrate:** 115200
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Format:** JSON-String mit `\n` (newline) am Ende

## 🎨 Display-Layout

```
┌────────────────────────────────┐
│    PC SYSTEM MONITOR           │ ← Header (Cyan)
├────────────────────────────────┤
│ CPU Temp          55.3 °C      │ ← Farbcodiert (Grün/Orange/Rot)
│ CPU Load          42.5 %       │
│ [████████░░░░░░░░░░]           │ ← Fortschrittsbalken
│ CPU Fan          1800 RPM      │
│                                │
│ GPU Temp          68.0 °C      │
│ GPU Load          85.2 %       │
│ [██████████████░░░░]           │
│ GPU Fan          2400 RPM      │
└────────────────────────────────┘
```

**Farbcodierung (Temperaturen):**
- 🟢 **Grün:** < Warn-Schwelle
- 🟠 **Orange:** ≥ Warn-Schwelle (CPU: 70°C, GPU: 75°C)
- 🔴 **Rot:** ≥ Kritisch (CPU: 85°C, GPU: 90°C)

**Fortschrittsbalken (Auslastung):**
- 🟢 **Grün:** < 70%
- 🟠 **Orange:** 70-90%
- 🔴 **Rot:** > 90%

## 🔧 Anpassungen

### Display-Pin-Konfiguration ändern

Bearbeite [platformio.ini](platformio.ini):

```ini
build_flags =
    -D TFT_MOSI=23    # Dein MOSI-Pin
    -D TFT_SCLK=18    # Dein SCK-Pin
    -D TFT_CS=5       # Dein CS-Pin
    -D TFT_DC=2       # Dein DC-Pin
    -D TFT_RST=4      # Dein RST-Pin
```

### Farben und Schwellwerte anpassen

Bearbeite [src/main.cpp](src/main.cpp):

```cpp
// Temperatur-Schwellwerte
drawValue(yPos, sysData.cpuTemp, "C", 70.0, 85.0);  // Warnung: 70°C, Kritisch: 85°C
drawValue(yPos, sysData.gpuTemp, "C", 75.0, 90.0);  // Warnung: 75°C, Kritisch: 90°C

// Farben
#define COLOR_WARN 0xFD20  // Orange
#define COLOR_CRIT 0xF800  // Rot
```

### Update-Intervall ändern

```bash
# Schnelleres Update (0.5 Sekunden)
python pc_monitor.py --interval 0.5

# Langsameres Update (3 Sekunden)
python pc_monitor.py --interval 3
```

## 🐛 Troubleshooting

### "Access Denied" beim COM-Port

**Problem:** Anderes Programm nutzt den Port (Arduino IDE, Serial Monitor)

**Lösung:** Alle Serial-Monitore schließen, dann neu verbinden

### Keine GPU-Daten (0.0 °C, 0%)

**Problem:** GPUtil unterstützt nur NVIDIA-Karten

**Lösungen:**
1. NVIDIA GPU: Sicherstellen dass GPU-Treiber installiert sind
2. AMD/Intel GPU: Erweiterte Monitoring-Tools benötigt (siehe unten)

### CPU-Temperatur = 0.0 °C

**Problem:** Windows unterstützt Sensoren nicht über psutil

**Lösung:** Erweiterte Monitoring-Tools nutzen:
- [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)
- [OpenHardwareMonitor](https://openhardwaremonitor.org/)

Diese Tools bieten WMI/REST APIs für vollständige Sensor-Daten.

### Display zeigt "Waiting for data..."

**Mögliche Ursachen:**
1. Python-Script nicht gestartet
2. Falscher COM-Port
3. ESP32 nicht verbunden
4. Baudrate stimmt nicht überein

**Debug:**
```bash
# Ports überprüfen
python pc_monitor.py --list

# Mit richtigem Port starten
python pc_monitor.py --port COMx
```

### "CONNECTION LOST" auf Display

**Problem:** Keine Daten seit 5 Sekunden empfangen

**Lösung:** Python-Script neu starten oder USB-Verbindung prüfen

## 📝 Erweiterungen

### Weitere Sensoren hinzufügen

1. **ESP32 (main.cpp):** Struct erweitern
```cpp
struct SystemData {
  float diskUsage = 0.0;  // Neu
  // ...
};
```

2. **Python (pc_monitor.py):** Daten sammeln
```python
def get_system_data(self):
    disk = psutil.disk_usage('/')
    data = {
        'disk_usage': round(disk.percent, 1),  # Neu
        # ...
    }
    return data
```

3. **Display aktualisieren:** In `updateDisplay()` zeichnen

### Autostart (Windows)

**Option 1: Task Scheduler**
1. Task Scheduler öffnen
2. "Einfache Aufgabe erstellen"
3. Trigger: "Bei Anmeldung"
4. Aktion: Python-Script starten

**Option 2: Startup-Ordner**
```bash
# Batch-Datei erstellen: start_monitor.bat
@echo off
cd /d "C:\Pfad\zum\Projekt"
python pc_monitor.py --port COM3
pause
```

Datei in Autostart-Ordner kopieren:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

## 📚 Libraries

- [TFT_eSPI](https://github.com/Bodmer/TFT_eSPI) - Display-Treiber
- [ArduinoJson](https://arduinojson.org/) - JSON-Parser
- [psutil](https://github.com/giampaolo/psutil) - System-Monitoring (Python)
- [GPUtil](https://github.com/anderskm/gputil) - GPU-Monitoring (Python)

## 📄 Lizenz

Open Source - frei verwendbar für eigene Projekte
