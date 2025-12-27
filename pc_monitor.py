"""
PC System Monitor für ESP32 USB Display
Sendet CPU/GPU Temperaturen, Lüftergeschwindigkeiten und Auslastung über Serial
"""

import serial
import json
import time
import psutil
import os
import sys

# LibreHardwareMonitor Support (optional)
try:
    from librehardwaremonitor_client import LibreHardwareMonitorClient
    LHM_AVAILABLE = True
except ImportError:
    LHM_AVAILABLE = False

# GPU und erweiterte Sensor-Unterstützung
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("Info: GPUtil nicht installiert. GPU-Daten eingeschränkt.")
    print("      Installiere mit: pip install gputil")

class SystemMonitor:
    def __init__(self, port=None, baudrate=115200):
        """
        Initialisiert System-Monitor
        
        Args:
            port: COM-Port des ESP32 (z.B. 'COM3') oder None für Auto-Detection
            baudrate: Baudrate (Standard: 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lhm_client = None
        
        # LibreHardwareMonitor initialisieren falls verfügbar
        if LHM_AVAILABLE:
            self.lhm_client = LibreHardwareMonitorClient()
            test_data = self.lhm_client.get_system_data()
            if test_data:
                print("✓ LibreHardwareMonitor verbunden (vollständige Sensor-Daten)")
            else:
                print("ℹ LibreHardwareMonitor nicht verfügbar (psutil-Fallback)")
                self.lhm_client = None
        
        # Auto-Detection wenn kein Port angegeben
        if self.port is None or self.port.lower() == 'auto':
            self.port = self.auto_detect_port()
            if self.port is None:
                print("\nKein ESP32 gefunden!")
                print("Verfügbare Ports:")
                self.list_ports()
                sys.exit(1)
        
        self.connect()
    
    @staticmethod
    def auto_detect_port():
        """
        Automatische Erkennung des ESP32-Ports
        Sucht nach bekannten USB-Serial-Chips (CH340, CP2102, CP2104, FTDI, etc.)
        
        Returns:
            str: Erkannter Port oder None
        """
        import serial.tools.list_ports
        
        # Bekannte ESP32 USB-Serial-Chip-IDs und Namen
        ESP32_IDENTIFIERS = [
            # CH340/CH341 (häufigster Chip bei günstigen ESP32)
            ('1A86', '7523'),  # Vendor ID, Product ID
            'CH340',
            'CH341',
            # CP210x (Silicon Labs - bei vielen DevKits)
            ('10C4', 'EA60'),
            'CP2102',
            'CP2104',
            'CP210',
            'Silicon Labs',
            # FTDI
            ('0403', '6001'),
            'FT232',
            'FTDI',
            # Direkt ESP32-S2/S3/C3 (mit native USB)
            'USB JTAG',
            'ESP32',
        ]
        
        ports = serial.tools.list_ports.comports()
        candidates = []
        
        for port in ports:
            # Prüfe VID:PID
            vid_pid = f"{port.vid:04X}:{port.pid:04X}" if port.vid and port.pid else ""
            
            for identifier in ESP32_IDENTIFIERS:
                if isinstance(identifier, tuple):
                    # VID:PID Check
                    if port.vid and port.pid:
                        vid = f"{port.vid:04X}"
                        pid = f"{port.pid:04X}"
                        if vid == identifier[0].upper() and pid == identifier[1].upper():
                            candidates.append((port.device, port.description, 100))
                            break
                else:
                    # String-Check in Description
                    if identifier.lower() in port.description.lower():
                        candidates.append((port.device, port.description, 50))
                        break
        
        if candidates:
            # Sortiere nach Priorität (höchste zuerst)
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            # IMMER Identifikation via Magic-Request versuchen
            print(f"\n🔍 {len(candidates)} mögliche ESP32-Geräte gefunden:")
            for i, (port, desc, _) in enumerate(candidates, 1):
                print(f"  {i}. {port} - {desc}")
            print("\n→ Versuche Identifikation via Magic-Request...")
            
            verified_port = SystemMonitor.verify_usb_display(candidates)
            if verified_port:
                return verified_port
            
            # Fallback: Verwende ersten Kandidaten
            print("⚠ Keine eindeutige Identifikation möglich.")
            print(f"  Verwende ersten Kandidaten: {candidates[0][0]}")
            print(f"  Falls falsch, starte mit: python pc_monitor.py --port COMx")
            
            detected_port = candidates[0][0]
            print(f"✓ ESP32 automatisch erkannt: {detected_port}")
            print(f"  → {candidates[0][1]}")
            
            return detected_port
        
        return None
        
    def connect(self):
        """Verbindet mit ESP32 über Serial"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"✓ Verbunden mit {self.port} @ {self.baudrate} baud")
            time.sleep(2)  # ESP32 Reset nach Serial-Verbindung
        except serial.SerialException as e:
            print(f"✗ Fehler beim Verbinden mit {self.port}: {e}")
            print("\nVerfügbare Ports:")
            self.list_ports()
            sys.exit(1)
    
    @staticmethod
    def verify_usb_display(candidates):
        """
        Verifiziert USB Display über Magic-Request
        Sendet Identifikations-Anfrage und wartet auf korrekte Antwort
        
        Args:
            candidates: Liste von (port, description, priority) Tupeln
            
        Returns:
            str: Verifizierter Port oder None
        """
        MAGIC_REQUEST = "IDENTIFY\n"
        MAGIC_RESPONSE = "USB_DISPLAY"
        TIMEOUT = 3.0
        
        for port_device, port_desc, _ in candidates:
            print(f"  Teste {port_device}...", end=" ")
            try:
                # Verbinde mit Port
                ser = serial.Serial(port_device, 115200, timeout=1)
                time.sleep(1.0)  # ESP32 Boot-Zeit nach Serial-Connect (erhöht)
                
                # Leere Buffer
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # Sende Magic-Request
                ser.write(MAGIC_REQUEST.encode('utf-8'))
                ser.flush()
                
                # Warte auf Antwort
                start_time = time.time()
                response_buffer = ""
                
                while time.time() - start_time < TIMEOUT:
                    if ser.in_waiting > 0:
                        chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        response_buffer += chunk
                        
                        # Prüfe ob Magic-Response enthalten
                        if MAGIC_RESPONSE in response_buffer:
                            ser.close()
                            print(f"✓ USB_DISPLAY gefunden!")
                            print(f"  ✓ USB Display identifiziert: {port_device}")
                            print(f"    → {port_desc}")
                            return port_device
                    
                    time.sleep(0.05)
                
                # Timeout - keine korrekte Antwort
                ser.close()
                print(f"✗ Keine Antwort (empfangen: {repr(response_buffer[:50])})")
                
            except (serial.SerialException, Exception) as e:
                # Port nicht verfügbar oder Fehler - weiter zum nächsten
                print(f"✗ Fehler ({str(e)[:30]})")
        
        return None
    
    @staticmethod
    def list_ports():
        """Listet alle verfügbaren Serial-Ports auf"""
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("  Keine Serial-Ports gefunden")
            return
        
        for port in ports:
            vid_pid = f"[{port.vid:04X}:{port.pid:04X}]" if port.vid and port.pid else ""
            print(f"  {port.device} - {port.description} {vid_pid}")
    
    def get_cpu_temp(self):
        """
        Liest CPU-Temperatur
        Nutzt psutil falls verfügbar, sonst Dummy-Wert
        """
        try:
            # Windows: Temperaturen oft nur über WMI/LibreHardwareMonitor verfügbar
            temps = psutil.sensors_temperatures()
            if temps:
                # Suche nach CPU-Temperatur
                for name, entries in temps.items():
                    if 'coretemp' in name.lower() or 'cpu' in name.lower():
                        if entries:
                            return entries[0].current
            return 0.0  # Nicht verfügbar
        except:
            return 0.0
    
    def get_cpu_fan_speed(self):
        """
        Liest CPU-Lüftergeschwindigkeit
        Benötigt erweiterte Tools wie OpenHardwareMonitor
        """
        try:
            fans = psutil.sensors_fans()
            if fans:
                for name, entries in fans.items():
                    if entries:
                        return int(entries[0].current)
            return 0
        except:
            return 0
    
    def get_gpu_info(self):
        """
        Liest GPU-Informationen (Temperatur, Auslastung, Lüfter)
        """
        if not GPU_AVAILABLE:
            return 0.0, 0.0, 0
        
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Erste GPU
                return gpu.temperature, gpu.load * 100, 0  # Fan-Speed nicht von GPUtil unterstützt
            return 0.0, 0.0, 0
        except:
            return 0.0, 0.0, 0
    
    def get_system_data(self):
        """
        Sammelt alle System-Daten
        
        Returns:
            dict: System-Daten im JSON-Format
        """
        # Versuche zuerst LibreHardwareMonitor
        if self.lhm_client:
            lhm_data = self.lhm_client.get_system_data()
            if lhm_data:
                return lhm_data
        
        # Fallback: psutil
        # CPU-Daten
        cpu_temp = self.get_cpu_temp()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_fan = self.get_cpu_fan_speed()
        
        # GPU-Daten
        gpu_temp, gpu_usage, gpu_fan = self.get_gpu_info()
        
        # RAM
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        
        data = {
            'cpu_temp': round(cpu_temp, 1),
            'cpu_usage': round(cpu_usage, 1),
            'cpu_fan': cpu_fan,
            'gpu_temp': round(gpu_temp, 1),
            'gpu_usage': round(gpu_usage, 1),
            'gpu_fan': gpu_fan,
            'ram_usage': round(ram_usage, 1)
        }
        
        return data
    
    def send_data(self, data):
        """Sendet Daten als JSON über Serial"""
        try:
            if self.ser is None or not self.ser.is_open:
                print("⚠ Serial-Verbindung nicht aktiv!")
                return
                
            json_str = json.dumps(data) + '\n'
            self.ser.write(json_str.encode('utf-8'))
            self.ser.flush()
        except Exception as e:
            print(f"✗ Fehler beim Senden: {e}")
    
    def run(self, interval=1.0):
        """
        Hauptschleife: Sammelt und sendet Daten in regelmäßigen Abständen
        
        Args:
            interval: Update-Intervall in Sekunden
        """
        print(f"\n{'='*50}")
        print(f"Starte Monitoring (Update alle {interval}s)")
        print(f"Port: {self.port} @ {self.baudrate} baud")
        print(f"Serial Status: {'✓ OFFEN' if self.ser and self.ser.is_open else '✗ GESCHLOSSEN'}")
        print(f"{'='*50}")
        print("Drücke Ctrl+C zum Beenden\n")
        
        try:
            packet_count = 0
            while True:
                # Daten sammeln
                data = self.get_system_data()
                packet_count += 1
                
                # Ausgabe in Konsole - überschreibe vorherige Zeilen
                # Cursor 3 Zeilen nach oben und lösche bis Ende
                print(f"\033[3A\033[J", end='')
                print(f"[#{packet_count:04d}] CPU: {data['cpu_temp']:5.1f}°C | {data['cpu_usage']:5.1f}% | {data['cpu_fan']:4d} RPM")
                print(f"         GPU: {data['gpu_temp']:5.1f}°C | {data['gpu_usage']:5.1f}% | {data['gpu_fan']:4d} RPM")
                print(f"         RAM: {data['ram_usage']:5.1f}% | ✓ Gesendet an {self.port}")
                
                # An ESP32 senden
                self.send_data(data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring beendet")
        finally:
            if self.ser:
                self.ser.close()


def main():
    """Hauptfunktion mit Argument-Parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PC System Monitor für ESP32 Display')
    parser.add_argument('--port', '-p', default=None, help='Serial Port (default: Auto-Detection)')
    parser.add_argument('--baud', '-b', type=int, default=115200, help='Baudrate (default: 115200)')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Update-Intervall in Sekunden (default: 1.0)')
    parser.add_argument('--list', '-l', action='store_true', help='Liste verfügbare Serial-Ports')
    
    args = parser.parse_args()
    
    if args.list:
        print("Verfügbare Serial-Ports:")
        SystemMonitor.list_ports()
        return
    
    # Monitor starten
    monitor = SystemMonitor(port=args.port, baudrate=args.baud)
    monitor.run(interval=args.interval)


if __name__ == '__main__':
    main()
