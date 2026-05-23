# app/advanced_checks.py
import subprocess
import json
import platform
import os
import re
from datetime import datetime

class AdvancedSecurityChecks:
    
    @staticmethod
    def safe_subprocess_run(cmd, shell=False):
        """Безопасный запуск команд с обработкой кодировок"""
        try:
            # Для Windows используем UTF-8 кодировку
            if platform.system() == 'Windows':
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    errors='replace',  # заменяем некорректные символы
                    shell=shell
                )
            else:
                # Для Linux используем системную кодировку
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    shell=shell
                )
            return result
        except Exception as e:
            return subprocess.CompletedProcess(
                cmd, 
                returncode=1, 
                stdout="", 
                stderr=str(e)
            )
    
    @staticmethod
    def check_windows_event_logs():
        """Анализ журналов событий Windows (исправленная версия)"""
        results = []
        try:
            if platform.system() == 'Windows':
                try:
                    cmd = ['powershell', '-Command', '''
                        Get-WinEvent -LogName Security -MaxEvents 10 | 
                        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
                        ConvertTo-Json -Compress
                    ''']
                    
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        try:
                            events = json.loads(result.stdout)
                            event_count = len(events) if isinstance(events, list) else 1
                            
                            results.append({
                                "id": "event_logs_check",
                                "name": "Анализ журналов событий Windows",
                                "status": "passed",
                                "description": f"Журналы событий доступны. Найдено событий: {event_count}",
                                "details": {
                                    "log_name": "Security",
                                    "events_analyzed": event_count,
                                    "check_performed": True
                                },
                                "recommendation": "Регулярно проверяйте журналы событий на наличие подозрительной активности"
                            })
                        except json.JSONDecodeError:
                            # Альтернативный способ получения событий
                            cmd2 = ['powershell', '-Command', '''
                                $events = Get-WinEvent -LogName Security -MaxEvents 5 -ErrorAction SilentlyContinue
                                if ($events) { 
                                    "Events found: " + $events.Count 
                                } else { 
                                    "No events found" 
                                }
                            ''']
                            result2 = AdvancedSecurityChecks.safe_subprocess_run(cmd2)
                            
                            if result2.returncode == 0:
                                results.append({
                                    "id": "event_logs_check",
                                    "name": "Анализ журналов событий Windows",
                                    "status": "info",
                                    "description": result2.stdout.strip(),
                                    "details": {"message": "Журналы доступны для анализа"},
                                    "recommendation": "Проверьте журналы вручную через Event Viewer"
                                })
                            else:
                                results.append({
                                    "id": "event_logs_check",
                                    "name": "Анализ журналов событий Windows",
                                    "status": "warning",
                                    "description": "Не удалось получить журналы событий",
                                    "details": {"error": result2.stderr[:200] if result2.stderr else "Unknown error"},
                                    "recommendation": "Проверьте права доступа к журналам событий"
                                })
                    else:
                        results.append({
                            "id": "event_logs_check",
                            "name": "Анализ журналов событий Windows",
                            "status": "info",
                            "description": "Журналы событий требуют прав администратора",
                            "details": {"error": result.stderr[:200] if result.stderr else "No output"},
                            "recommendation": "Запустите программу от имени администратора"
                        })
                except Exception as e:
                    results.append({
                        "id": "event_logs_check",
                        "name": "Анализ журналов событий Windows",
                        "status": "warning",
                        "description": f"Ошибка: {str(e)[:100]}",
                        "details": {"error": str(e)},
                        "recommendation": "Проверьте журналы вручную: Event Viewer → Журналы Windows → Безопасность"
                    })
            else:
                results.append({
                    "id": "event_logs_check",
                    "name": "Анализ журналов событий",
                    "status": "info",
                    "description": "Для Linux используйте journalctl",
                    "details": {"message": "Команда: sudo journalctl -r -n 20"},
                    "recommendation": "Для Linux: анализ /var/log/auth.log, journalctl, dmesg"
                })
                
        except Exception as e:
            results.append({
                "id": "event_logs_check",
                "name": "Анализ журналов событий",
                "status": "error",
                "description": f"Критическая ошибка: {str(e)[:100]}",
                "details": {"error": str(e)},
                "recommendation": "Проверьте доступ к журналам событий системы"
            })
        
        return results
    
    @staticmethod
    def check_group_policies():
        """Проверка настроек групповых политик"""
        results = []
        try:
            if platform.system() == 'Windows':
                try:
                    # Проверка групповых политик
                    cmd = ['gpresult', '/R']
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd)
                    
                    if result.returncode == 0:
                        output = result.stdout
                        
                        # Проверяем наличие политик
                        security_policies = []
                        
                        if "Параметры безопасности" in output or "Security Settings" in output:
                            security_policies.append("Общие параметры безопасности")
                        
                        if "Политика паролей" in output or "Password Policy" in output:
                            security_policies.append("Политики паролей")
                        
                        if "Блокировка учетных записей" in output or "Account Lockout Policy" in output:
                            security_policies.append("Политики блокировки учетных записей")
                        
                        results.append({
                            "id": "group_policy_check",
                            "name": "Проверка групповых политик",
                            "status": "passed" if security_policies else "warning",
                            "description": f"Групповые политики доступны. Найдено: {len(security_policies)}",
                            "details": {
                                "policies_found": security_policies,
                                "gpresult_available": True
                            },
                            "recommendation": "Настройте политики паролей и блокировки учетных записей через gpedit.msc"
                        })
                    else:
                        results.append({
                            "id": "group_policy_check",
                            "name": "Проверка групповых политик",
                            "status": "warning",
                            "description": "Не удалось получить информацию о политиках",
                            "details": {"error": result.stderr[:100] if result.stderr else "Unknown error"},
                            "recommendation": "Проверьте доступ к gpresult или используйте gpedit.msc вручную"
                        })
                except Exception as e:
                    results.append({
                        "id": "group_policy_check",
                        "name": "Проверка групповых политик",
                        "status": "warning",
                        "description": "Ошибка при проверке политик",
                        "details": {"error": str(e)},
                        "recommendation": "Проверьте политики вручную через gpedit.msc или rsop.msc"
                    })
            else:
                results.append({
                    "id": "group_policy_check",
                    "name": "Проверка политик безопасности",
                    "status": "info",
                    "description": "Только для Windows систем",
                    "details": {
                        "message": "Для Linux используйте PAM (Pluggable Authentication Modules) настройки"
                    }
                })
                
        except Exception as e:
            results.append({
                "id": "group_policy_check",
                "name": "Проверка групповых политик",
                "status": "failed",
                "description": "Ошибка проверки политик",
                "details": {"error": str(e)},
                "recommendation": "Установите и настройте групповые политики для улучшения безопасности"
            })
        
        return results
    
    @staticmethod
    def check_firewall_rules():
        """Анализ правил брандмауэра"""
        results = []
        try:
            if platform.system() == 'Windows':
                try:
                    # Проверка статуса брандмауэра
                    cmd = ['powershell', '-Command', '''
                        Get-NetFirewallProfile | 
                        Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
                        ConvertTo-Json
                    ''']
                    
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd)
                    
                    if result.returncode == 0 and result.stdout:
                        try:
                            profiles = json.loads(result.stdout)
                            enabled_profiles = []
                            
                            if isinstance(profiles, list):
                                for profile in profiles:
                                    if profile.get('Enabled'):
                                        enabled_profiles.append(profile.get('Name'))
                            elif isinstance(profiles, dict) and profiles.get('Enabled'):
                                enabled_profiles.append(profiles.get('Name'))
                            
                            status = "passed" if enabled_profiles else "warning"
                            description = f"Брандмауэр активен ({len(enabled_profiles)} профилей)" if enabled_profiles else "Брандмауэр не активен"
                            
                            results.append({
                                "id": "firewall_check",
                                "name": "Анализ правил брандмауэра",
                                "status": status,
                                "description": description,
                                "details": {
                                    "enabled_profiles": enabled_profiles,
                                    "total_profiles": len(profiles) if isinstance(profiles, list) else 1
                                },
                                "recommendation": "Проверьте правила входящих/исходящих соединений через wf.msc или PowerShell"
                            })
                        except json.JSONDecodeError:
                            results.append({
                                "id": "firewall_check",
                                "name": "Анализ правил брандмауэра",
                                "status": "warning",
                                "description": "Не удалось разобрать информацию о брандмауэре",
                                "details": {"message": "Формат данных не поддерживается"}
                            })
                    else:
                        results.append({
                            "id": "firewall_check",
                            "name": "Анализ правил брандмауэра",
                            "status": "warning",
                            "description": "Не удалось получить информацию о брандмауэре",
                            "details": {"error": result.stderr[:100] if result.stderr else "Unknown error"}
                        })
                except Exception as e:
                    results.append({
                        "id": "firewall_check",
                        "name": "Анализ правил брандмауэра",
                        "status": "warning",
                        "description": "Ошибка при проверке брандмауэра",
                        "details": {"error": str(e)},
                        "recommendation": "Проверьте брандмауэр вручную через wf.msc"
                    })
            else:
                # Для Linux
                try:
                    cmd = ['which', 'ufw']
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd)
                    
                    if result.returncode == 0:
                        results.append({
                            "id": "firewall_check",
                            "name": "Анализ брандмауэра Linux (UFW)",
                            "status": "info",
                            "description": "Обнаружен UFW (Uncomplicated Firewall)",
                            "details": {
                                "firewall": "UFW",
                                "message": "Используйте команды: sudo ufw status для проверки"
                            },
                            "recommendation": "Настройте UFW: sudo ufw enable, sudo ufw default deny"
                        })
                    else:
                        results.append({
                            "id": "firewall_check",
                            "name": "Анализ брандмауэра",
                            "status": "warning",
                            "description": "Брандмауэр не обнаружен",
                            "details": {"message": "Для Linux используйте iptables или firewalld"}
                        })
                except Exception as e:
                    results.append({
                        "id": "firewall_check",
                        "name": "Анализ брандмауэра",
                        "status": "warning",
                        "description": "Ошибка проверки брандмауэра",
                        "details": {"error": str(e)}
                    })
                    
        except Exception as e:
            results.append({
                "id": "firewall_check",
                "name": "Анализ правил брандмауэра",
                "status": "failed",
                "description": "Ошибка проверки брандмауэра",
                "details": {"error": str(e)},
                "recommendation": "Настройте брандмауэр для защиты от сетевых атак"
            })
        
        return results
    
    @staticmethod
    def check_antivirus_settings():
        """Проверка настроек антивируса"""
        results = []
        try:
            if platform.system() == 'Windows':
                try:
                    # Проверка антивируса через WMI
                    cmd = ['powershell', '-Command', '''
                        Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct |
                        Select-Object displayName, productState |
                        ConvertTo-Json
                    ''']
                    
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd)
                    
                    if result.returncode == 0 and result.stdout:
                        try:
                            av_data = json.loads(result.stdout)
                            antivirus_list = []
                            
                            if isinstance(av_data, list):
                                for av in av_data:
                                    name = av.get('displayName', 'Неизвестно')
                                    state = av.get('productState', 0)
                                    is_enabled = (state & 0xFFF0) == 0x10
                                    
                                    antivirus_list.append({
                                        "name": name,
                                        "enabled": is_enabled,
                                        "state": f"0x{state:X}"
                                    })
                            elif isinstance(av_data, dict):
                                name = av_data.get('displayName', 'Неизвестно')
                                state = av_data.get('productState', 0)
                                is_enabled = (state & 0xFFF0) == 0x10
                                
                                antivirus_list.append({
                                    "name": name,
                                    "enabled": is_enabled,
                                    "state": f"0x{state:X}"
                                })
                            
                            if antivirus_list:
                                enabled_av = [av for av in antivirus_list if av['enabled']]
                                status = "passed" if enabled_av else "warning"
                                description = f"Антивирус обнаружен: {len(antivirus_list)}" + (", активен" if enabled_av else ", не активен")
                                
                                results.append({
                                    "id": "antivirus_check",
                                    "name": "Проверка антивирусной защиты",
                                    "status": status,
                                    "description": description,
                                    "details": {
                                        "antivirus_list": antivirus_list,
                                        "enabled_count": len(enabled_av)
                                    },
                                    "recommendation": "Обновляйте антивирусные базы ежедневно" if enabled_av else "Включите и настройте антивирусную защиту"
                                })
                            else:
                                results.append({
                                    "id": "antivirus_check",
                                    "name": "Проверка антивирусной защиты",
                                    "status": "warning",
                                    "description": "Антивирус не обнаружен",
                                    "details": {"message": "Рекомендуется установить антивирусное ПО"},
                                    "recommendation": "Установите антивирусное ПО (Windows Defender или стороннее решение)"
                                })
                        except json.JSONDecodeError:
                            results.append({
                                "id": "antivirus_check",
                                "name": "Проверка антивирусной защиты",
                                "status": "warning",
                                "description": "Не удалось разобрать информацию об антивирусе",
                                "details": {"message": "Формат данных не поддерживается"}
                            })
                    else:
                        results.append({
                            "id": "antivirus_check",
                            "name": "Проверка антивирусной защиты",
                            "status": "info",
                            "description": "Не удалось проверить антивирус",
                            "details": {"message": "Используйте ручную проверку"},
                            "recommendation": "Откройте интерфейс антивирусной программы и проверьте настройки"
                        })
                except Exception as e:
                    results.append({
                        "id": "antivirus_check",
                        "name": "Проверка настроек антивируса",
                        "status": "warning",
                        "description": "Ошибка при проверке антивируса",
                        "details": {"error": str(e)},
                        "recommendation": "Проверьте антивирус вручную через его интерфейс"
                    })
            else:
                results.append({
                    "id": "antivirus_check",
                    "name": "Проверка антивирусной защиты Linux",
                    "status": "info",
                    "description": "Проверка антивируса для Linux",
                    "details": {
                        "message": "Для Linux рекомендуется использовать ClamAV или другие решения"
                    },
                    "recommendation": "Установите и настройте ClamAV: sudo apt-get install clamav clamav-daemon"
                })
                
        except Exception as e:
            results.append({
                "id": "antivirus_check",
                "name": "Проверка настроек антивируса",
                "status": "failed",
                "description": "Ошибка проверки антивируса",
                "details": {"error": str(e)},
                "recommendation": "Установите и настройте антивирусное ПО"
            })
        
        return results
    
    @staticmethod
    def check_database_security():
        """Проверка безопасности баз данных"""
        results = []
        try:
            # Проверка служб баз данных
            db_services = []
            
            if platform.system() == 'Windows':
                try:
                    cmd = ['sc', 'query']
                    result = AdvancedSecurityChecks.safe_subprocess_run(cmd, shell=True)
                    
                    if result.returncode == 0:
                        output = result.stdout
                        
                        db_service_patterns = [
                            ('MySQL', ['MySQL', 'mysql']),
                            ('PostgreSQL', ['postgresql', 'PostgreSQL']),
                            ('SQL Server', ['MSSQL', 'SQL Server', 'MSSQLSERVER']),
                            ('MongoDB', ['MongoDB']),
                            ('Oracle', ['OracleService', 'Oracle']),
                            ('SQLite', ['SQLite'])
                        ]
                        
                        for db_name, patterns in db_service_patterns:
                            for pattern in patterns:
                                if pattern in output:
                                    db_services.append(db_name)
                                    break
                except:
                    pass
            
            if db_services:
                results.append({
                    "id": "database_check",
                    "name": "Обнаружение служб баз данных",
                    "status": "warning",
                    "description": f"Обнаружены СУБД: {', '.join(db_services)}",
                    "details": {
                        "services_found": db_services,
                        "message": "Требуется дополнительная проверка безопасности БД"
                    },
                    "recommendation": "Проверьте настройки безопасности СУБД: пароли, права доступа, шифрование, обновления"
                })
            else:
                results.append({
                    "id": "database_check",
                    "name": "Проверка служб баз данных",
                    "status": "passed",
                    "description": "Службы баз данных не обнаружены",
                    "details": {"message": "Система не использует локальные СУБД"},
                    "recommendation": "При установке СУБД настройте безопасность согласно лучшим практикам"
                })
                
        except Exception as e:
            results.append({
                "id": "database_check",
                "name": "Проверка безопасности баз данных",
                "status": "info",
                "description": "Ошибка проверки БД",
                "details": {"error": str(e)}
            })
        
        return results
    
    @staticmethod
    def check_cloud_services():
        """Проверка подключенных облачных сервисов"""
        results = []
        try:
            cloud_clients = []
            
            # Проверка OneDrive
            if platform.system() == 'Windows':
                onedrive_paths = [
                    os.path.expanduser('~\\OneDrive'),
                    os.path.expanduser('~\\Documents\\OneDrive'),
                    'C:\\Program Files\\Microsoft OneDrive',
                    'C:\\Program Files (x86)\\Microsoft OneDrive'
                ]
            else:
                onedrive_paths = [
                    os.path.expanduser('~/OneDrive'),
                    os.path.expanduser('~/Documents/OneDrive')
                ]
            
            for path in onedrive_paths:
                if os.path.exists(path):
                    cloud_clients.append('Microsoft OneDrive')
                    break
            
            # Проверка Google Drive
            gdrive_paths = [
                os.path.expanduser('~/Google Drive'),
                os.path.expanduser('~/.config/google-drive'),
                os.path.expanduser('~/AppData/Local/Google/DriveFS')
            ]
            
            for path in gdrive_paths:
                if os.path.exists(path):
                    cloud_clients.append('Google Drive')
                    break
            
            # Проверка Dropbox
            dropbox_path = os.path.expanduser('~/Dropbox')
            if os.path.exists(dropbox_path):
                cloud_clients.append('Dropbox')
            
            if cloud_clients:
                results.append({
                    "id": "cloud_check",
                    "name": "Обнаружение облачных сервисов",
                    "status": "warning",
                    "description": f"Обнаружены клиенты облачных сервисов: {', '.join(cloud_clients)}",
                    "details": {
                        "clients_found": cloud_clients
                    },
                    "recommendation": "Настройте двухфакторную аутентификацию и шифрование для облачных сервисов"
                })
            else:
                results.append({
                    "id": "cloud_check",
                    "name": "Проверка облачных сервисов",
                    "status": "passed",
                    "description": "Клиенты облачных сервисов не обнаружены",
                    "details": {"message": "Система не использует облачные синхронизаторы"},
                    "recommendation": "При использовании облачных сервисов настройте их безопасность"
                })
                
        except Exception as e:
            results.append({
                "id": "cloud_check",
                "name": "Проверка облачных сервисов",
                "status": "info",
                "description": "Ошиба проверки облачных сервисов",
                "details": {"error": str(e)}
            })
        
        return results
    
    @staticmethod
    def perform_advanced_checks():
        """Выполнение всех расширенных проверок"""
        all_checks = []
        
        # Добавляем проверки
        all_checks.extend(AdvancedSecurityChecks.check_windows_event_logs())
        all_checks.extend(AdvancedSecurityChecks.check_group_policies())
        all_checks.extend(AdvancedSecurityChecks.check_firewall_rules())
        all_checks.extend(AdvancedSecurityChecks.check_antivirus_settings())
        all_checks.extend(AdvancedSecurityChecks.check_database_security())
        all_checks.extend(AdvancedSecurityChecks.check_cloud_services())
        
        # Добавляем рекомендации
        all_checks.append({
            "id": "advanced_recommendations",
            "name": "Рекомендации по углубленной проверке",
            "status": "info",
            "description": "Дополнительные меры для улучшения безопасности",
            "details": {
                "recommendations": [
                    "Использовать специализированные инструменты аудита (Nessus, OpenVAS)",
                    "Провести ручной анализ критических систем",
                    "Организовать регулярный мониторинг безопасности",
                    "Внедрить систему управления уязвимостями"
                ]
            },
            "recommendation": "Регулярно проводите комплексные проверки безопасности"
        })
        
        return all_checks