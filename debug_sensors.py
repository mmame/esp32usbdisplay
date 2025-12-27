"""
Debug-Tool für LibreHardwareMonitor
Zeigt alle verfügbaren Sensoren an
"""

import requests
import json

def get_all_sensors():
    """Holt und zeigt alle Sensoren von LibreHardwareMonitor"""
    try:
        response = requests.get("http://localhost:8085/data.json", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Fehler: {e}")
        return None

def print_tree(data, indent=0):
    """Zeigt die Sensor-Hierarchie"""
    if isinstance(data, dict):
        text = data.get('Text', '')
        value = data.get('Value', '')
        
        if text:
            print("  " * indent + f"├─ {text}", end="")
            if value:
                print(f" = {value}", end="")
            print()
        
        if 'Children' in data:
            for child in data['Children']:
                print_tree(child, indent + 1)
    elif isinstance(data, list):
        for item in data:
            print_tree(item, indent)

print("=" * 60)
print("LibreHardwareMonitor - Sensor Debug")
print("=" * 60)
print()

data = get_all_sensors()
if data:
    print("✓ Verbunden mit LibreHardwareMonitor")
    print()
    print("Verfügbare Sensoren:")
    print("-" * 60)
    print_tree(data)
    print("-" * 60)
    print()
    print("Tipp: Kopiere diese Ausgabe und schicke sie,")
    print("      damit die Sensor-Namen angepasst werden können.")
else:
    print("✗ Keine Verbindung zu LibreHardwareMonitor")
    print()
    print("Prüfe:")
    print("  1. LibreHardwareMonitor als Admin gestartet?")
    print("  2. Options -> Remote Web Server aktiviert?")
    print("  3. Port 8085 frei?")
