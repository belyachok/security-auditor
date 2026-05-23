"""Агент для сбора информации с реального ПК"""
import platform
import psutil
import socket
import subprocess
import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
import winreg  # Для Windows
import getpass


class SystemAgent:
    """Агент для сбора подробной информации о системе"""
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.system_type = platform.system()
        self.hostname = platform.node()
        self.current_user = getpass.getuser()
    
    def collect_all(self) -> Dict[str, Any]:
        """Собрать всю информацию о системе"""
        print(f"[AGENT] Сбор информации с {self.hostname} ({self.system_type})")
        
        data = {
            'agent_id': self.agent_id,
            'collection_time': datetime.now().isoformat(),
            'hostname': self.hostname,
            'current_user': self.current_user,
            'system': self._collect_system_info(),
            'hardware': self._collect_hardware_info(),
            'software': self._collect_software_info(),
            'security': self._collect_security_info(),
            'network': self._collect_network_info(),
            'users': self._collect_user_info(),
            'services': self._collect_service_info(),
            'processes': self._collect_process_info(),
            'drives': self._collect_drive_info()
        }
        
        return data
    
    def _collect_system_info(self) -> Dict:
        """Информация о системе"""
        return {
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
        }
    
    def _collect_hardware_info(self) -> Dict:
        """Информация об оборудовании"""
        try:
            # CPU
            cpu_info = {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else None,
                'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                'usage_percent': psutil.cpu_percent(interval=1)
            }
            
            # Память
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent,
                'free_gb': round(memory.free / (1024**3), 2)
            }
            
            # Диски
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': usage.percent
                    })
                except:
                    continue
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disks': disks
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _collect_software_info(self) -> Dict:
        """Информация о программном обеспечении"""
        software_info = {
            'installed_programs': self._get_installed_programs(),
            'windows_updates': self._get_windows_updates(),
            'running_services': len([s for s in psutil.win_service_iter() if s.status() == 'running']) if self.system_type == 'Windows' else 0
        }
        
        return software_info
    
    def _collect_security_info(self) -> Dict:
        """Информация о безопасности"""
        security_info = {
            'antivirus': self._check_antivirus(),
            'firewall': self._check_firewall(),
            'password_policy': self._check_password_policy(),
            'updates': self._check_update_status(),
            'bitlocker': self._check_bitlocker(),
            'audit_policy': self._check_audit_policy()
        }
        
        return security_info
    
    def _collect_network_info(self) -> Dict:
        """Сетевая информация"""
        try:
            # IP адреса
            ip_addresses = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip_addresses.append({
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
            
            # Открытые порты
            open_ports = self._check_open_ports()
            
            # Сетевые соединения
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    connections.append({
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
                except:
                    continue
            
            return {
                'hostname': socket.gethostname(),
                'ip_addresses': ip_addresses,
                'open_ports': open_ports,
                'connections': connections[:20]  # Первые 20 соединений
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _collect_user_info(self) -> List[Dict]:
        """Информация о пользователях"""
        users = []
        try:
            if self.system_type == 'Windows':
                # Для Windows
                import win32net  # Требуется pywin32
                users_info, _, _ = win32net.NetUserEnum(None, 0)
                for user in users_info[:10]:  # Первые 10 пользователей
                    users.append({
                        'name': user['name'],
                        'full_name': user.get('full_name', ''),
                        'account_disabled': user.get('flags', 0) & 0x2 == 0x2
                    })
            else:
                # Для Linux
                with open('/etc/passwd', 'r') as f:
                    lines = f.readlines()[:10]
                    for line in lines:
                        parts = line.split(':')
                        if len(parts) >= 7:
                            users.append({
                                'name': parts[0],
                                'uid': parts[2],
                                'gid': parts[3],
                                'home': parts[5],
                                'shell': parts[6].strip()
                            })
        except:
            # Простой список пользователей
            try:
                import pwd
                for user in pwd.getpwall()[:10]:
                    users.append({'name': user.pw_name})
            except:
                users = [{'name': self.current_user}]
        
        return users
    
    def _collect_service_info(self) -> List[Dict]:
        """Информация о службах"""
        services = []
        try:
            if self.system_type == 'Windows':
                for service in list(psutil.win_service_iter())[:20]:  # Первые 20 служб
                    try:
                        services.append({
                            'name': service.name(),
                            'display_name': service.display_name(),
                            'status': service.status(),
                            'start_type': service.start_type() if hasattr(service, 'start_type') else 'unknown'
                        })
                    except:
                        continue
            else:
                # Для Linux
                try:
                    result = subprocess.run(['systemctl', 'list-units', '--type=service', '--no-pager'], 
                                          capture_output=True, text=True, timeout=5)
                    lines = result.stdout.split('\n')
                    for line in lines[1:6]:  # Первые 5 служб
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                services.append({
                                    'name': parts[0],
                                    'status': parts[3]
                                })
                except:
                    pass
        except Exception as e:
            services = [{'error': str(e)}]
        
        return services
    
    def _collect_process_info(self) -> List[Dict]:
        """Информация о процессах"""
        processes = []
        try:
            for proc in list(psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']))[:15]:  # Первые 15 процессов
                try:
                    info = proc.info
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'user': info['username'],
                        'cpu_percent': info['cpu_percent'],
                        'memory_percent': info['memory_percent']
                    })
                except:
                    continue
        except:
            pass
        
        return processes
    
    def _collect_drive_info(self) -> Dict:
        """Информация о дисках и разделах"""
        drives = {}
        try:
            # Логические диски
            logical_drives = []
            for drive in ['C:', 'D:', 'E:', 'F:', 'G:']:
                if os.path.exists(drive + '\\'):
                    logical_drives.append(drive)
            
            drives['logical_drives'] = logical_drives
            
            # Размеры дисков
            disk_sizes = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_sizes[partition.device] = {
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': usage.percent
                    }
                except:
                    continue
            
            drives['disk_sizes'] = disk_sizes
            
        except Exception as e:
            drives['error'] = str(e)
        
        return drives
    
    # === Методы для Windows ===
    
    def _get_installed_programs(self) -> List[Dict]:
        """Получить список установленных программ (для Windows)"""
        programs = []
        
        if self.system_type != 'Windows':
            return programs
        
        try:
            # Реестр для 64-битных программ
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"  # Для 32-битных на 64-битной ОС
            ]
            
            for reg_path in reg_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if winreg.QueryValueEx(subkey, "DisplayVersion") else "Не указана"
                                publisher = winreg.QueryValueEx(subkey, "Publisher")[0] if winreg.QueryValueEx(subkey, "Publisher") else "Не указан"
                                
                                programs.append({
                                    'name': name,
                                    'version': version,
                                    'publisher': publisher
                                })
                            except:
                                continue
                                
                            winreg.CloseKey(subkey)
                        except:
                            continue
                    
                    winreg.CloseKey(key)
                except:
                    continue
            
            # Ограничим список 20 программами
            return programs[:20]
            
        except Exception as e:
            print(f"[AGENT] Ошибка при получении списка программ: {e}")
            return []
    
    def _get_windows_updates(self) -> List[Dict]:
        """Получить информацию об обновлениях Windows"""
        updates = []
        
        if self.system_type != 'Windows':
            return updates
        
        try:
            # Простая проверка через wmic (альтернатива)
            result = subprocess.run(
                ['wmic', 'qfe', 'get', 'Caption,Description,HotFixID,InstalledOn'],
                capture_output=True, text=True, encoding='cp866'
            )
            
            lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
            for line in lines:
                if line.strip():
                    parts = [p.strip() for p in line.split() if p.strip()]
                    if len(parts) >= 4:
                        updates.append({
                            'hotfix_id': parts[0],
                            'description': ' '.join(parts[1:-2]),
                            'installed_on': parts[-1]
                        })
            
            # Ограничим последними 10 обновлениями
            return updates[:10]
            
        except Exception as e:
            print(f"[AGENT] Ошибка при получении обновлений: {e}")
            return []
    
    def _check_antivirus(self) -> Dict:
        """Проверить наличие антивируса"""
        antivirus_info = {
            'installed': False,
            'name': 'Не обнаружен',
            'enabled': False,
            'updated': False
        }
        
        if self.system_type == 'Windows':
            try:
                # Проверка Windows Defender
                result = subprocess.run(
                    ['powershell', '-Command', 'Get-MpComputerStatus'],
                    capture_output=True, text=True
                )
                
                if 'AMServiceEnabled' in result.stdout:
                    antivirus_info['installed'] = True
                    antivirus_info['name'] = 'Windows Defender'
                    
                    # Парсим вывод PowerShell
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'AMServiceEnabled' in line and 'True' in line:
                            antivirus_info['enabled'] = True
                        if 'AntivirusSignatureLastUpdated' in line:
                            antivirus_info['updated'] = True
                
                # Проверка других антивирусов через реестр
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                    
                    antivirus_names = ['Kaspersky', 'Norton', 'Avast', 'AVG', 'McAfee', 'Eset', 'Bitdefender']
                    
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                for av_name in antivirus_names:
                                    if av_name.lower() in name.lower():
                                        antivirus_info['installed'] = True
                                        antivirus_info['name'] = name
                                        break
                            except:
                                pass
                                
                            winreg.CloseKey(subkey)
                        except:
                            continue
                    
                    winreg.CloseKey(key)
                except:
                    pass
                    
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке антивируса: {e}")
        
        return antivirus_info
    
    def _check_firewall(self) -> Dict:
        """Проверить настройки брандмауэра"""
        firewall_info = {
            'enabled': False,
            'profile': 'Неизвестно',
            'inbound_blocked': False,
            'outbound_blocked': False
        }
        
        if self.system_type == 'Windows':
            try:
                result = subprocess.run(
                    ['netsh', 'advfirewall', 'show', 'allprofiles'],
                    capture_output=True, text=True, encoding='cp866'
                )
                
                output = result.stdout
                
                # Проверяем включен ли фаервол
                if 'Состояние                           ВКЛ' in output or 'State                              ON' in output:
                    firewall_info['enabled'] = True
                
                # Определяем профиль
                if 'Профиль домена' in output or 'Domain Profile' in output:
                    firewall_info['profile'] = 'Domain'
                elif 'Частный профиль' in output or 'Private Profile' in output:
                    firewall_info['profile'] = 'Private'
                elif 'Общий профиль' in output or 'Public Profile' in output:
                    firewall_info['profile'] = 'Public'
                
                # Проверяем блокировку входящих/исходящих
                if 'Входящие подключения                 Блокировать' in output or 'Inbound connections                 Block' in output:
                    firewall_info['inbound_blocked'] = True
                if 'Исходящие подключения               Разрешить' in output or 'Outbound connections                Allow' in output:
                    firewall_info['outbound_blocked'] = True
                    
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке брандмауэра: {e}")
        
        return firewall_info
    
    def _check_password_policy(self) -> Dict:
        """Проверить политику паролей"""
        policy = {
            'min_length': 0,
            'complexity': False,
            'history': 0,
            'max_age': 0,
            'lockout_threshold': 0
        }
        
        if self.system_type == 'Windows':
            try:
                # Проверка минимальной длины пароля
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SYSTEM\CurrentControlSet\Services\Netlogon\Parameters")
                    policy['min_length'] = winreg.QueryValueEx(key, "MinimumPasswordLength")[0]
                    winreg.CloseKey(key)
                except:
                    policy['min_length'] = 0
                
                # Проверка сложности пароля
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SYSTEM\CurrentControlSet\Services\Netlogon\Parameters")
                    complexity = winreg.QueryValueEx(key, "PasswordComplexity")[0]
                    policy['complexity'] = bool(complexity)
                    winreg.CloseKey(key)
                except:
                    policy['complexity'] = False
                
                # Альтернативный способ через net accounts
                try:
                    result = subprocess.run(['net', 'accounts'], capture_output=True, text=True, encoding='cp866')
                    output = result.stdout
                    
                    # Парсим вывод
                    for line in output.split('\n'):
                        if 'Минимальная длина пароля' in line or 'Minimum password length' in line:
                            match = re.search(r'\d+', line)
                            if match:
                                policy['min_length'] = int(match.group())
                        elif 'Длина хранения пароля' in line or 'Length of password history maintained' in line:
                            match = re.search(r'\d+', line)
                            if match:
                                policy['history'] = int(match.group())
                        elif 'Максимальный срок действия пароля' in line or 'Maximum password age' in line:
                            match = re.search(r'\d+', line)
                            if match:
                                policy['max_age'] = int(match.group())
                        elif 'Пороговое значение блокировки' in line or 'Lockout threshold' in line:
                            match = re.search(r'\d+', line)
                            if match:
                                policy['lockout_threshold'] = int(match.group())
                except:
                    pass
                    
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке политики паролей: {e}")
        
        return policy
    
    def _check_update_status(self) -> Dict:
        """Проверить статус обновлений"""
        updates = {
            'last_check': datetime.now().strftime('%Y-%m-%d'),
            'available': 0,
            'installed': 0,
            'automatic_updates': False
        }
        
        if self.system_type == 'Windows':
            try:
                # Проверка настроек автоматических обновлений
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update")
                    au_options = winreg.QueryValueEx(key, "AUOptions")[0]
                    updates['automatic_updates'] = au_options in [2, 3, 4]  # 2-4 - автоматические обновления
                    winreg.CloseKey(key)
                except:
                    pass
                
                # Получаем информацию об установленных обновлениях
                installed = self._get_windows_updates()
                updates['installed'] = len(installed)
                
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке обновлений: {e}")
        
        return updates
    
    def _check_bitlocker(self) -> Dict:
        """Проверить BitLocker"""
        bitlocker = {
            'enabled': False,
            'protection_on': False,
            'drives': []
        }
        
        if self.system_type == 'Windows':
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 'Get-BitLockerVolume'],
                    capture_output=True, text=True
                )
                
                if 'VolumeStatus' in result.stdout:
                    bitlocker['enabled'] = True
                    
                    # Парсим вывод
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'C:' in line and 'FullyEncrypted' in line:
                            bitlocker['protection_on'] = True
                            bitlocker['drives'].append('C:')
                        if 'D:' in line and 'FullyEncrypted' in line:
                            bitlocker['drives'].append('D:')
                            
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке BitLocker: {e}")
        
        return bitlocker
    
    def _check_audit_policy(self) -> Dict:
        """Проверить политику аудита"""
        audit = {
            'audit_enabled': False,
            'audit_policy': {}
        }
        
        if self.system_type == 'Windows':
            try:
                result = subprocess.run(
                    ['auditpol', '/get', '/category:*'],
                    capture_output=True, text=True, encoding='cp866'
                )
                
                if 'Система аудита включена.' in result.stdout or 'System audit policy.' in result.stdout:
                    audit['audit_enabled'] = True
                    
                # Парсим основные категории
                categories = ['Вход в систему', 'Управление учетной записью', 'Отслеживание подробных процессов']
                for category in categories:
                    if category in result.stdout:
                        audit['audit_policy'][category] = 'Настроен'
                    else:
                        audit['audit_policy'][category] = 'Не настроен'
                        
            except Exception as e:
                print(f"[AGENT] Ошибка при проверке политики аудита: {e}")
        
        return audit
    
    def _check_open_ports(self) -> List[int]:
        """Проверить открытые порты"""
        open_ports = []
        
        # Проверяем только основные порты
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3389, 8080, 8443]
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                continue
        
        return open_ports
    
    def save_report(self, filename: str = None):
        """Сохранить отчет в файл"""
        data = self.collect_all()
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"system_report_{self.hostname}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[AGENT] Отчет сохранен в {filename}")
        return filename


# Утилита для запуска агента отдельно
if __name__ == "__main__":
    agent = SystemAgent()
    
    print(f"=== Агент безопасности v1.0 ===")
    print(f"Система: {agent.hostname} ({agent.system_type})")
    print(f"Пользователь: {agent.current_user}")
    print(f"ID агента: {agent.agent_id}")
    print("=" * 40)
    
    print("\n[1/4] Сбор информации о системе...")
    data = agent.collect_all()
    
    print("\n[2/4] Сохранение отчета...")
    filename = agent.save_report()
    
    print("\n[3/4] Краткая сводка:")
    print(f"  • ОС: {data['system']['os_name']} {data['system']['os_release']}")
    print(f"  • Процессор: {data['system']['processor'][:50]}...")
    print(f"  • Память: {data['hardware']['memory']['total_gb']} GB")
    print(f"  • Антивирус: {data['security']['antivirus']['name']} ({'Включен' if data['security']['antivirus']['enabled'] else 'Выключен'})")
    print(f"  • Брандмауэр: {'Включен' if data['security']['firewall']['enabled'] else 'Выключен'}")
    print(f"  • Открытые порты: {len(data['network']['open_ports'])}")
    
    print("\n[4/4] Отчет сохранен в файле:")
    print(f"  {filename}")
    print("\nДля отправки на сервер используйте:")
    print(f"  python -m app.agent --send http://localhost:8000")