# app/database.py
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.computers_file = self.data_dir / "computers.json"
        self.reports_file = self.data_dir / "reports.json"
        
        # Инициализация файлов, если их нет
        if not self.computers_file.exists():
            self._save_file(self.computers_file, [])
        if not self.reports_file.exists():
            self._save_file(self.reports_file, [])
    
    def _load_file(self, file_path: Path) -> List[Dict]:
        """Загрузка данных из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_file(self, file_path: Path, data: List[Dict]):
        """Сохранение данных в файл"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Методы для компьютеров
    def get_all_computers(self) -> List[Dict]:
        """Получить все компьютеры"""
        return self._load_file(self.computers_file)
    
    def get_computer(self, computer_id: str) -> Optional[Dict]:
        """Получить компьютер по ID"""
        computers = self.get_all_computers()
        for computer in computers:
            if computer.get("id") == computer_id:
                return computer
        return None
    
    def save_computer(self, computer_data: Dict):
        """Сохранить компьютер"""
        computers = self.get_all_computers()
        computer_id = computer_data.get("id")
        
        if not computer_id:
            return
        
        # Ищем существующий компьютер
        found = False
        for i, comp in enumerate(computers):
            if comp.get("id") == computer_id:
                computers[i] = computer_data
                found = True
                break
        
        # Если не нашли, добавляем новый
        if not found:
            computers.append(computer_data)
        
        self._save_file(self.computers_file, computers)
    
    def delete_computer(self, computer_id: str):
        """Удалить компьютер"""
        computers = self.get_all_computers()
        computers = [c for c in computers if c.get("id") != computer_id]
        self._save_file(self.computers_file, computers)
    
    # Методы для отчетов
    def get_all_reports(self) -> List[Dict]:
        """Получить все отчеты"""
        return self._load_file(self.reports_file)
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """Получить отчет по ID"""
        reports = self.get_all_reports()
        for report in reports:
            if report.get("id") == report_id:
                return report
        return None
    
    def save_report(self, report_data: Dict):
        """Сохранить отчет"""
        reports = self.get_all_reports()
        report_id = report_data.get("id")
        
        if not report_id:
            return
        
        # Ищем существующий отчет
        found = False
        for i, report in enumerate(reports):
            if report.get("id") == report_id:
                reports[i] = report_data
                found = True
                break
        
        # Если не нашли, добавляем новый
        if not found:
            reports.append(report_data)
        
        self._save_file(self.reports_file, reports)
    
    def delete_report(self, report_id: str):
        """Удалить отчет"""
        reports = self.get_all_reports()
        reports = [r for r in reports if r.get("id") != report_id]
        self._save_file(self.reports_file, reports)
    
    # Синонимы для совместимости
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Получить агента (синоним для get_computer)"""
        return self.get_computer(agent_id)
    
    def save_agent(self, agent_data: Dict):
        """Сохранить агента (синоним для save_computer)"""
        return self.save_computer(agent_data)
    
    def delete_report(self, report_id: str):
        """Удалить отчет"""
        reports = self.get_all_reports()
        reports = [r for r in reports if r.get("id") != report_id]
        self._save_file(self.reports_file, reports)

    def get_ispdn_report(self, report_id: str) -> Optional[Dict]:
        """Получить отчет ISPDN по ID"""
        # Пробуем найти в основной базе
        report = self.get_report(report_id)
        if report and report.get("type") == "ispdn":
            return report
        
        # Проверяем файлы в директории ISPDN
        reports_dir = Path("data/reports/ispdn")
        if reports_dir.exists():
            for file in reports_dir.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get("id") == report_id or f"{report_id}.json" == file.name:
                            return data
                except:
                    continue
        
        return None
    
    def debug_search_report(self, report_id: str):
        """Отладочный поиск отчета"""
        print(f"🔍 DEBUG Поиск отчета: {report_id}")
        
        # 1. Ищем в основной базе
        reports = self.get_all_reports()
        print(f"📊 Всего отчетов в базе: {len(reports)}")
        
        for i, report in enumerate(reports):
            print(f"  [{i}] ID: {report.get('id')}, Тип: {report.get('type', 'unknown')}")
            if report.get("id") == report_id:
                print(f"  ✅ НАЙДЕН в основной базе!")
                return report
        
        print(f"  ❌ Не найден в основной базе")
        
        # 2. Проверяем файлы ISPDN
        ispdn_dir = Path("data/reports/ispdn")
        if ispdn_dir.exists():
            print(f"📁 Проверяем директорию: {ispdn_dir}")
            for file in ispdn_dir.glob("*.json"):
                print(f"  📄 Файл: {file.name}")
        
        return None
    
    # database.py - добавить методы
def save_ispdn_settings(self, settings):
    """Сохранение настроек ИСПДн"""
    try:
        # Если настройки уже есть - обновляем
        existing = self.get_ispdn_settings()
        if existing:
            settings['id'] = existing['id']
            settings['updated_at'] = datetime.now().isoformat()
        else:
            settings['id'] = str(uuid.uuid4())
            settings['created_at'] = datetime.now().isoformat()
            settings['updated_at'] = settings['created_at']
        
        # Сохраняем в файл
        settings_path = os.path.join(self.data_dir, "ispdn_settings.json")
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return settings['id']
    except Exception as e:
        print(f"Ошибка сохранения настроек ИСПДн: {e}")
        return None

def get_ispdn_settings(self):
    """Получение настроек ИСПДн"""
    try:
        settings_path = os.path.join(self.data_dir, "ispdn_settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Ошибка загрузки настроек ИСПДн: {e}")
        return None