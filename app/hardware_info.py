# app/hardware_info.py - исправленная версия
import platform
import psutil
import cpuinfo
import socket
import uuid
from datetime import datetime

class HardwareInfoCollector:
    
    @staticmethod
    def get_cpu_info():
        """Получение информации о процессоре"""
        try:
            # Отладка

            
            # Получаем информацию через cpuinfo
            info = cpuinfo.get_cpu_info()

            
            # Получаем информацию через psutil
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # Пробуем получить частоту
            freq = psutil.cpu_freq()
            if freq:
                current_freq = f"{freq.current:.2f} MHz"
                max_freq = f"{freq.max:.2f} MHz" if freq.max else "Неизвестно"
            else:
                current_freq = "Неизвестно"
                max_freq = "Неизвестно"
            
            cpu_data = {
                "model": info.get('brand_raw', platform.processor()),
                "brand_raw": info.get('brand_raw', platform.processor()),
                "vendor_id": info.get('vendor_id_raw', 'Неизвестно'),
                "family": info.get('family', 'Неизвестно'),
                "model_id": info.get('model', 'Неизвестно'),
                "stepping": info.get('stepping', 'Неизвестно'),
                "cores": cpu_count_physical if cpu_count_physical else "Неизвестно",
                "logical_cores": cpu_count_logical if cpu_count_logical else "Неизвестно",
                "hz_actual": current_freq,
                "hz_advertised": max_freq,
                "hz_advertised_raw": info.get('hz_advertised', 'Неизвестно'),
                "arch": info.get('arch', platform.architecture()[0]),
                "bits": info.get('bits', platform.architecture()[0].replace('bit', '')),
                "usage_percent": psutil.cpu_percent(interval=0.5)
            }
            

            return cpu_data
            
        except Exception as e:

            # Возвращаем минимальную информацию при ошибке
            return {
                "model": platform.processor(),
                "brand_raw": platform.processor(),
                "cores": "Неизвестно",
                "logical_cores": "Неизвестно",
                "hz_actual": "Неизвестно",
                "usage_percent": 0
            }
    
    @staticmethod
    def get_memory_info():
        """Получение информации об оперативной памяти"""
        try:

            mem = psutil.virtual_memory()
            
            memory_data = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "free_gb": round(mem.free / (1024**3), 2),
                "percent": mem.percent
            }
            

            return memory_data
            
        except Exception as e:

            return {
                "total_gb": 0,
                "available_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percent": 0
            }
    
    @staticmethod
    def get_disk_info():
        """Получение информации о дисках"""

        disks = []
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    }
                    disks.append(disk_info)

                except Exception as e:

                    continue
        except Exception as e:
            print(f"[DEBUG DISK] Общая ошибка получения дисков: {e}")
        
        return disks
    
    @staticmethod
    def get_network_info():
        """Получение сетевой информации"""
        try:

            hostname = socket.gethostname()
            
            # Получаем IP адрес
            try:
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "127.0.0.1"
            
            # Получение MAC адреса
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,8*6,8)][::-1])
            except:
                mac = "00:00:00:00:00:00"
            
            network_data = {
                "hostname": hostname,
                "ip_address": ip_address,
                "mac_address": mac
            }
            

            return network_data
            
        except Exception as e:

            return {
                "hostname": platform.node(),
                "ip_address": "Неизвестно",
                "mac_address": "Неизвестно"
            }
    
    @staticmethod
    def get_all_hardware_info():
        """Получить всю аппаратную информацию"""

        
        try:
            cpu_info = HardwareInfoCollector.get_cpu_info()
            memory_info = HardwareInfoCollector.get_memory_info()
            disks_info = HardwareInfoCollector.get_disk_info()
            network_info = HardwareInfoCollector.get_network_info()
            
            result = {
                "cpu": cpu_info,
                "memory": memory_info,
                "disks": disks_info,
                "network": network_info,
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "python_implementation": platform.python_implementation()
                }
            }
            

            
            return result
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            
            return {
                "cpu": {"model": "Ошибка сбора данных", "brand_raw": "Ошибка"},
                "memory": {"total_gb": 0},
                "disks": [],
                "network": {"hostname": "Ошибка"},
                "platform": {"system": platform.system()}
            }