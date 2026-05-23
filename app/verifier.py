"""Верификатор безопасности для ИСПДн"""
import psutil
import platform
import socket
import os
from typing import List, Dict, Any
from datetime import datetime

class SecurityVerifier:
    """Упрощенный верификатор безопасности"""
    
    def perform_basic_checks(self) -> List[Dict[str, Any]]:
        """Выполнение базовых проверок безопасности"""
        checks = []
        
        try:
            # 1. Проверка CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_check = {
                "id": "cpu_usage",
                "name": "Загрузка процессора",
                "category": "Аппаратное обеспечение",
                "status": "passed" if cpu_percent < 70 else "warning" if cpu_percent < 85 else "failed",
                "description": f"Текущая загрузка CPU: {cpu_percent}%",
                "details": f"Порог предупреждения: 70%, Порог ошибки: 85%",
                "recommendation": "Оптимизируйте процессы при высокой загрузке" if cpu_percent > 70 else None
            }
            checks.append(cpu_check)
            
            # 2. Проверка памяти
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_check = {
                "id": "memory_usage",
                "name": "Использование памяти",
                "category": "Аппаратное обеспечение",
                "status": "passed" if memory_percent < 75 else "warning" if memory_percent < 85 else "failed",
                "description": f"Использовано памяти: {memory_percent}%",
                "details": f"Всего: {memory.total / 1024**3:.1f} ГБ, Использовано: {memory.used / 1024**3:.1f} ГБ",
                "recommendation": "Освободите память или увеличьте RAM" if memory_percent > 75 else None
            }
            checks.append(memory_check)
            
            # 3. Проверка дисков
            try:
                disk_usage = psutil.disk_usage('/')
                disk_check = {
                    "id": "disk_space",
                    "name": "Дисковое пространство",
                    "category": "Хранилище",
                    "status": "passed" if disk_usage.percent < 80 else "warning" if disk_usage.percent < 90 else "failed",
                    "description": f"Использовано места на диске: {disk_usage.percent}%",
                    "details": f"Всего: {disk_usage.total / 1024**3:.1f} ГБ, Свободно: {disk_usage.free / 1024**3:.1f} ГБ",
                    "recommendation": "Освободите место на диске" if disk_usage.percent > 80 else None
                }
                checks.append(disk_check)
            except:
                pass
            
            # 4. Проверка ОС
            os_check = {
                "id": "os_check",
                "name": "Операционная система",
                "category": "Программное обеспечение",
                "status": "passed",
                "description": "Операционная система определена",
                "details": f"ОС: {platform.system()} {platform.version()}",
                "recommendation": "Обновляйте ОС до актуальной версии"
            }
            checks.append(os_check)
            
            # 5. Проверка имени хоста
            try:
                hostname = socket.gethostname()
                hostname_check = {
                    "id": "hostname_check",
                    "name": "Имя хоста",
                    "category": "Сеть",
                    "status": "passed",
                    "description": "Имя хоста определено",
                    "details": f"Имя хоста: {hostname}",
                    "recommendation": "Используйте понятные имена хостов"
                }
                checks.append(hostname_check)
            except:
                pass
            
            # 6. Проверка Python версии
            python_check = {
                "id": "python_version",
                "name": "Версия Python",
                "category": "Программное обеспечение",
                "status": "passed",
                "description": "Версия Python определена",
                "details": f"Python {platform.python_version()}",
                "recommendation": "Обновляйте Python до актуальной версии"
            }
            checks.append(python_check)
            
            return checks
            
        except Exception as e:
            print(f"Ошибка в базовых проверках: {e}")
            # Возвращаем хотя бы одну проверку с ошибкой
            return [{
                "id": "error_check",
                "name": "Ошибка проверки",
                "category": "Системные ошибки",
                "status": "failed",
                "description": "Не удалось выполнить полную проверку",
                "details": str(e),
                "recommendation": "Проверьте доступ к системным ресурсам"
            }]
    
    def run_quick_check(self, system_info=None):
        """Алиас для совместимости"""
        return self.perform_basic_checks()
    
    def run_checks(self, system_info=None):
        """Алиас для совместимости"""
        return self.perform_basic_checks()