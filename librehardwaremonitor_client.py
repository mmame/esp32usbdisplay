"""
LibreHardwareMonitor Integration für vollständige Sensor-Daten
Benötigt LibreHardwareMonitor als Admin gestartet mit aktiviertem Remote Server
Download: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
"""

import requests
import json

class LibreHardwareMonitorClient:
    def __init__(self, host='localhost', port=8085):
        self.base_url = f"http://{host}:{port}/data.json"
        
    def get_sensor_data(self):
        """
        Holt alle Sensor-Daten von LibreHardwareMonitor
        
        Returns:
            dict: Sensor-Daten oder None bei Fehler
        """
        try:
            response = requests.get(self.base_url, timeout=2)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def find_sensor(self, data, hardware_type, sensor_type, name_contains):
        """
        Sucht spezifischen Sensor in den Daten
        
        Args:
            data: JSON-Daten von LibreHardwareMonitor
            hardware_type: z.B. 'CPU', 'GpuNvidia'
            sensor_type: z.B. 'Temperature', 'Load', 'Fan'
            name_contains: Teil des Sensor-Namens
            
        Returns:
            float: Sensor-Wert oder None
        """
        if not data or 'Children' not in data:
            return None
        
        def search_children(items):
            for item in items:
                # Prüfe Hardware-Typ
                if 'Text' in item and hardware_type.lower() in item.get('Text', '').lower():
                    # Durchsuche Sensoren
                    if 'Children' in item:
                        for sensor_group in item['Children']:
                            if sensor_group.get('Text', '').lower() == sensor_type.lower():
                                if 'Children' in sensor_group:
                                    for sensor in sensor_group['Children']:
                                        if name_contains.lower() in sensor.get('Text', '').lower():
                                            value_str = sensor.get('Value', '0')
                                            # Entferne Einheiten (°C, %, RPM, etc.)
                                            value_str = value_str.replace('°C', '').replace('%', '').replace('RPM', '').strip()
                                            try:
                                                return float(value_str)
                                            except:
                                                return None
                
                # Rekursiv durchsuchen
                if 'Children' in item:
                    result = search_children(item['Children'])
                    if result is not None:
                        return result
            return None
        
        return search_children(data['Children'])
    
    def get_system_data(self):
        """
        Sammelt alle relevanten System-Daten
        
        Returns:
            dict: System-Daten oder None bei Fehler
        """
        data = self.get_sensor_data()
        if not data:
            return None
        
        # CPU-Daten
        cpu_temp = self.find_sensor(data, 'Intel', 'Temperatures', 'Core Average') or \
                   self.find_sensor(data, 'Intel', 'Temperatures', 'CPU Package') or \
                   self.find_sensor(data, 'Intel', 'Temperatures', 'Core Max') or \
                   self.find_sensor(data, 'AMD', 'Temperatures', 'Core (Tctl/Tdie)') or 0.0
        
        cpu_usage = self.find_sensor(data, 'Intel', 'Load', 'CPU Total') or \
                    self.find_sensor(data, 'AMD', 'Load', 'CPU Total') or 0.0
        
        # CPU-Lüfter (falls vorhanden, sonst 0)
        cpu_fan = self.find_sensor(data, 'HP', 'Fans', 'Fan') or \
                  self.find_sensor(data, 'Mainboard', 'Fans', 'Fan #1') or \
                  self.find_sensor(data, 'Mainboard', 'Fans', 'CPU Fan') or 0
        
        # GPU-Daten (NVIDIA)
        gpu_temp = self.find_sensor(data, 'NVIDIA', 'Temperatures', 'GPU Core') or \
                   self.find_sensor(data, 'AMD', 'Temperatures', 'GPU Core') or 0.0
        
        gpu_usage = self.find_sensor(data, 'NVIDIA', 'Load', 'GPU Core') or \
                    self.find_sensor(data, 'AMD', 'Load', 'GPU Core') or 0.0
        
        gpu_fan = self.find_sensor(data, 'NVIDIA', 'Fans', 'GPU Fan') or \
                  self.find_sensor(data, 'AMD', 'Fans', 'GPU Fan') or 0
        
        # RAM
        ram_usage = self.find_sensor(data, 'Memory', 'Load', 'Memory') or 0.0
        
        return {
            'cpu_temp': round(cpu_temp, 1),
            'cpu_usage': round(cpu_usage, 1),
            'cpu_fan': int(cpu_fan),
            'gpu_temp': round(gpu_temp, 1),
            'gpu_usage': round(gpu_usage, 1),
            'gpu_fan': int(gpu_fan),
            'ram_usage': round(ram_usage, 1)
        }


# Test-Funktion
if __name__ == '__main__':
    client = LibreHardwareMonitorClient()
    print("Teste LibreHardwareMonitor-Verbindung...")
    print("(LibreHardwareMonitor muss als Admin laufen mit 'Remote Web Server' aktiviert)")
    print()
    
    data = client.get_system_data()
    if data:
        print("✓ Verbindung erfolgreich!")
        print(f"CPU: {data['cpu_temp']}°C | {data['cpu_usage']}% | {data['cpu_fan']} RPM")
        print(f"GPU: {data['gpu_temp']}°C | {data['gpu_usage']}% | {data['gpu_fan']} RPM")
        print(f"RAM: {data['ram_usage']}%")
    else:
        print("✗ Keine Verbindung zu LibreHardwareMonitor")
        print("  1. LibreHardwareMonitor als Administrator starten")
        print("  2. Options -> Remote Web Server aktivieren")
        print("  3. Dieses Script erneut ausführen")
