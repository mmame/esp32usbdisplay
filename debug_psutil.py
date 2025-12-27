"""
Debug-Tool für psutil Sensoren
Zeigt alle verfügbaren System-Sensoren an
"""

import psutil
try:
    import GPUtil
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

print("=" * 60)
print("psutil - System Sensoren Debug")
print("=" * 60)
print()

# CPU
print("CPU:")
print("-" * 60)
print(f"  CPU Auslastung: {psutil.cpu_percent(interval=1)}%")
print(f"  CPU Kerne: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
print(f"  CPU Frequenz: {psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'} MHz")
print()

# CPU Temperaturen
print("CPU Temperaturen:")
print("-" * 60)
try:
    temps = psutil.sensors_temperatures()
    if temps:
        for name, entries in temps.items():
            print(f"  {name}:")
            for entry in entries:
                print(f"    {entry.label or 'N/A'}: {entry.current}°C (high={entry.high}, critical={entry.critical})")
    else:
        print("  ✗ Keine Temperatur-Sensoren verfügbar (Windows Einschränkung)")
        print("    → Benötigt LibreHardwareMonitor oder WMI-Tools")
except Exception as e:
    print(f"  ✗ Fehler: {e}")
print()

# Lüfter
print("Lüfter:")
print("-" * 60)
try:
    fans = psutil.sensors_fans()
    if fans:
        for name, entries in fans.items():
            print(f"  {name}:")
            for entry in entries:
                print(f"    {entry.label or 'N/A'}: {entry.current} RPM")
    else:
        print("  ✗ Keine Lüfter-Sensoren verfügbar (Windows Einschränkung)")
        print("    → Benötigt LibreHardwareMonitor oder WMI-Tools")
except Exception as e:
    print(f"  ✗ Fehler: {e}")
print()

# Batterie (falls Laptop)
print("Batterie:")
print("-" * 60)
try:
    battery = psutil.sensors_battery()
    if battery:
        print(f"  Ladung: {battery.percent}%")
        print(f"  Netzteil: {'Ja' if battery.power_plugged else 'Nein'}")
        if battery.secsleft != -1:
            print(f"  Zeit verbleibend: {battery.secsleft // 60} Minuten")
    else:
        print("  ✗ Keine Batterie (Desktop-PC)")
except Exception as e:
    print(f"  ✗ Fehler: {e}")
print()

# RAM
print("RAM:")
print("-" * 60)
memory = psutil.virtual_memory()
print(f"  Total: {memory.total / (1024**3):.2f} GB")
print(f"  Verwendet: {memory.used / (1024**3):.2f} GB ({memory.percent}%)")
print(f"  Verfügbar: {memory.available / (1024**3):.2f} GB")
print()

# GPU (via GPUtil)
print("GPU (via GPUtil):")
print("-" * 60)
if GPU_AVAILABLE:
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            for i, gpu in enumerate(gpus):
                print(f"  GPU {i}: {gpu.name}")
                print(f"    Temperatur: {gpu.temperature}°C")
                print(f"    Auslastung: {gpu.load * 100:.1f}%")
                print(f"    Memory: {gpu.memoryUsed}/{gpu.memoryTotal} MB ({gpu.memoryUtil * 100:.1f}%)")
        else:
            print("  ✗ Keine NVIDIA GPU gefunden")
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
else:
    print("  ✗ GPUtil nicht installiert")
    print("    → Installiere mit: pip install gputil")
print()

# Festplatten
print("Festplatten:")
print("-" * 60)
partitions = psutil.disk_partitions()
for partition in partitions:
    try:
        usage = psutil.disk_usage(partition.mountpoint)
        print(f"  {partition.device} ({partition.fstype})")
        print(f"    Mountpoint: {partition.mountpoint}")
        print(f"    Gesamt: {usage.total / (1024**3):.2f} GB")
        print(f"    Verwendet: {usage.used / (1024**3):.2f} GB ({usage.percent}%)")
    except:
        pass
print()

# Netzwerk
print("Netzwerk:")
print("-" * 60)
net_io = psutil.net_io_counters()
print(f"  Bytes gesendet: {net_io.bytes_sent / (1024**2):.2f} MB")
print(f"  Bytes empfangen: {net_io.bytes_recv / (1024**2):.2f} MB")
print()

print("=" * 60)
print()
print("Zusammenfassung:")
print("  ✓ CPU Auslastung: Verfügbar")
print("  ✓ RAM Auslastung: Verfügbar")
if GPU_AVAILABLE:
    print("  ✓ GPU (GPUtil): Verfügbar")
else:
    print("  ✗ GPU (GPUtil): Nicht installiert")

try:
    temps = psutil.sensors_temperatures()
    if temps:
        print("  ✓ Temperaturen: Verfügbar")
    else:
        print("  ✗ Temperaturen: Nicht verfügbar (Windows)")
except:
    print("  ✗ Temperaturen: Nicht verfügbar (Windows)")

try:
    fans = psutil.sensors_fans()
    if fans:
        print("  ✓ Lüfter: Verfügbar")
    else:
        print("  ✗ Lüfter: Nicht verfügbar (Windows)")
except:
    print("  ✗ Lüfter: Nicht verfügbar (Windows)")

print()
print("Hinweis: Unter Windows benötigt man für Temperaturen und Lüfter")
print("         LibreHardwareMonitor oder ähnliche Tools!")
