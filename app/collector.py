# app/collector.py - исправленная версия
import platform
import psutil
import socket
import uuid
import os
import subprocess
import json
from datetime import datetime
from .hardware_info import HardwareInfoCollector
from .software_info import SoftwareInfoCollector

class SystemInfoCollector:
    
    @staticmethod
    def get_all_info():
        """Получить всю информацию о системе"""
        
        try:
            # Используем новые сборщики
            hardware_info = HardwareInfoCollector.get_all_hardware_info()
            
            software_info = SoftwareInfoCollector.get_os_info()
            
            # Получаем установленное ПО
            installed_software = []
            try:
                installed_software = SoftwareInfoCollector.get_installed_software()

            except Exception as e:

                installed_software = []
            
            # Получаем сетевые подключения

            network_connections = []
            try:
                for conn in psutil.net_connections(kind='inet'):
                    try:
                        conn_data = {
                            "family": str(conn.family),
                            "type": str(conn.type),
                            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                            "pid": conn.pid
                        }
                        network_connections.append(conn_data)
                    except:
                        continue

            except Exception as e:
                print(f"[SYSTEM INFO] Ошибка сбора подключений: {e}")
            
            # Собираем полную информацию
            system_data = {
                "hardware": {
                    "cpu": hardware_info.get("cpu", {}),
                    "memory": hardware_info.get("memory", {}),
                    "disks": hardware_info.get("disks", []),
                    "network": hardware_info.get("network", {}),
                    "platform": hardware_info.get("platform", {})
                },
                "software": {
                    "os": software_info,
                    "python": {
                        "version": platform.python_version(),
                        "implementation": platform.python_implementation(),
                        "compiler": platform.python_compiler(),
                        "build": platform.python_build()
                    },
                    "installed_programs": installed_software,
                    "network_connections": network_connections
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                        for elements in range(0,8*6,8)][::-1]),
                "collector_version": "2.0"
            }
            

            return system_data
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            
            # Возвращаем минимальную информацию в случае ошибки
            return {
                "hardware": {
                    "cpu": {"model": platform.processor(), "brand_raw": platform.processor()},
                    "memory": {"total_gb": 0},
                    "disks": [],
                    "network": {"hostname": socket.gethostname()}
                },
                "software": {
                    "os": {"name": platform.system(), "system": platform.system()},
                    "python": {"version": platform.python_version()}
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }