# app/software_info.py
import platform
import subprocess
import os
import json
import sys
import psutil

class SoftwareInfoCollector:
    
    @staticmethod
    def get_os_info():
        """Получение информации об операционной системе"""
        system = platform.system()
        
        if system == "Windows":
            try:
                cmd = ['powershell', '-Command', '''
                    (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion").ProductName
                ''']
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                os_name = result.stdout.strip() if result.returncode == 0 else platform.version()
            except:
                os_name = platform.version()
        elif system == "Linux":
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            os_name = line.split('=')[1].strip().strip('"')
                            break
                    else:
                        os_name = platform.platform()
            except:
                os_name = platform.platform()
        else:
            os_name = platform.platform()
        
        return {
            "name": os_name,
            "system": system,
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }
    
    @staticmethod
    def get_installed_software():
        """Получение списка установленного ПО"""
        software_list = []
        
        if platform.system() == "Windows":
            try:
                # Для Windows используем WMI или реестр
                cmd = ['powershell', '-Command', '''
                    Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*,
                                 HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*,
                                 HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
                    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
                    Where-Object {$_.DisplayName -ne $null} |
                    ConvertTo-Json -Compress
                ''']
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0 and result.stdout.strip():
                    software_list = json.loads(result.stdout)
            except:
                pass
        elif platform.system() == "Linux":
            try:
                # Для Linux (Debian/Ubuntu)
                cmd = ['dpkg', '-l']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[5:]  # Пропускаем заголовки
                    for line in lines:
                        if line:
                            parts = line.split()
                            if len(parts) >= 3:
                                software_list.append({
                                    "DisplayName": parts[1],
                                    "DisplayVersion": parts[2],
                                    "Publisher": ""
                                })
            except:
                pass
        
        return software_list
    
    # app/software_info.py - дополните этот метод
    @staticmethod
    def get_all_software_info():
        """Получить всю программную информацию"""
        try:
            os_info = SoftwareInfoCollector.get_os_info()
            installed_software = SoftwareInfoCollector.get_installed_software()
            
            # Собираем информацию о службах
            services = []
            try:
                for service in psutil.win_service_iter() if platform.system() == "Windows" else []:
                    services.append({
                        "name": service.name(),
                        "display_name": service.display_name(),
                        "status": service.status()
                    })
            except:
                pass
            
            return {
                "os": os_info,
                "installed_programs": installed_software,
                "services": services,
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation()
                }
            }
        except Exception as e:
            print(f"Ошибка в get_all_software_info: {e}")
            return {
                "os": {},
                "installed_programs": [],
                "services": [],
                "python": {}
            }