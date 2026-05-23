# app/reporter.py
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class Reporter:
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_report(self, scan_data: Dict) -> Dict:
        """Генерация отчета из данных сканирования"""
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = {
            "id": report_id,
            "timestamp": datetime.now().isoformat(),
            "scan_data": scan_data,
            "summary": self._generate_summary(scan_data),
            "recommendations": self._generate_recommendations(scan_data)
        }
        
        # Сохраняем отчет в файл
        report_file = self.reports_dir / f"{report_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def _generate_summary(self, scan_data: Dict) -> Dict:
        """Генерация сводки отчета"""
        security_checks = scan_data.get("security_checks", [])
        
        passed = len([check for check in security_checks if check.get("status") == "passed"])
        failed = len([check for check in security_checks if check.get("status") == "failed"])
        warning = len([check for check in security_checks if check.get("status") == "warning"])
        
        return {
            "total_checks": len(security_checks),
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "score": scan_data.get("score", 0),
            "risk_level": self._calculate_risk_level(scan_data.get("score", 0))
        }
    
    def _calculate_risk_level(self, score: int) -> str:
        """Определение уровня риска"""
        if score >= 90:
            return "Низкий"
        elif score >= 75:
            return "Умеренный"
        elif score >= 60:
            return "Повышенный"
        elif score >= 40:
            return "Высокий"
        else:
            return "Критический"
    
    def _generate_recommendations(self, scan_data: Dict) -> List[Dict]:
        """Генерация рекомендаций"""
        recommendations = []
        security_checks = scan_data.get("security_checks", [])
        
        for check in security_checks:
            if check.get("status") in ["failed", "warning"]:
                recommendations.append({
                    "check_id": check.get("id"),
                    "check_name": check.get("name"),
                    "status": check.get("status"),
                    "issue": check.get("issue"),
                    "recommendation": check.get("recommendation", "Устраните выявленную проблему"),
                    "priority": "high" if check.get("status") == "failed" else "medium"
                })
        
        return recommendations
    
    def get_report(self, report_id: str) -> Dict:
        """Получение отчета по ID"""
        report_file = self.reports_dir / f"{report_id}.json"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def list_reports(self) -> List[str]:
        """Список всех отчетов"""
        reports = []
        for file in self.reports_dir.glob("report_*.json"):
            reports.append(file.stem)
        return sorted(reports, reverse=True)