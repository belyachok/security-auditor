import json
import os
from typing import Dict, List, Any
from datetime import datetime
from .requirements import ISPDNRequirements

class ISPDNAnalyzer:
    
    def __init__(self):
        self.requirements = ISPDNRequirements()
    
    def analyze_system(self):
        """Основной метод анализа системы на соответствие ИСПДн"""
        try:
            # Сбор информации о системе (можно расширить)
            system_info = self.collect_system_info()
            
            # Информация об организации (из настроек или ввода)
            company_info = self.load_company_info()
            
            # Проведение анализа соответствия
            analysis_results = self.requirements.analyze_compliance(
                system_info, 
                company_info
            )
            
            # Генерация отчета
            report = self.requirements.generate_ispdn_report(
                analysis_results, 
                company_info
            )
            
            return {
                "status": "success",
                "report": report,
                "analysis": analysis_results,
                "system_info": system_info,
                "company_info": company_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "report": None
            }
    
    def collect_system_info(self):
        """Сбор информации о системе для анализа"""
        import platform
        import psutil
        import socket
        
        return {
            "os": {
                "name": platform.system(),
                "version": platform.version()
            },
            "security": {
                "password_policy": self.check_password_policy(),
                "firewall_enabled": self.check_firewall(),
                "antivirus": self.check_antivirus()
            },
            "network": {
                "hostname": socket.gethostname(),
                "domain": self.check_domain()
            },
            "collection_time": datetime.now().isoformat()
        }
    
    def load_company_info(self):
        """Загрузка информации об организации"""
        settings_file = "data/settings/ispdn_settings.json"
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Значения по умолчанию
        return {
            "name": "Тестовая организация",
            "inn": "0000000000",
            "pdn_category": "Иные",
            "subjects_count": "less_100k",
            "has_security_policy": False,
            "has_consent_forms": False
        }
    
    def check_password_policy(self):
        """Проверка политики паролей"""
        # Здесь должна быть реальная проверка
        # Для примера возвращаем заглушку
        return False
    
    def check_firewall(self):
        """Проверка брандмауэра"""
        import platform
        
        if platform.system() == "Windows":
            try:
                import subprocess
                result = subprocess.run(
                    ['powershell', 'Get-NetFirewallProfile | Select-Object Enabled'],
                    capture_output=True, 
                    text=True
                )
                return "True" in result.stdout
            except:
                return False
        return False
    
    def check_antivirus(self):
        """Проверка антивируса"""
        # Упрощенная проверка
        return True
    
    def check_domain(self):
        """Проверка домена"""
        import socket
        return socket.getfqdn()
    
    def generate_detailed_report(self, report_data: Dict):
        """Генерация детализированного отчета"""
        report = report_data.get("report", {})
        analysis = report_data.get("analysis", {})
        
        detailed_report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_id": report.get("id", "unknown"),
                "analyzer_version": "2.0"
            },
            "executive_summary": self.generate_executive_summary(analysis),
            "compliance_assessment": self.generate_compliance_assessment(analysis),
            "risk_assessment": self.generate_risk_assessment(analysis),
            "detailed_findings": self.generate_detailed_findings(report),
            "remediation_plan": self.generate_remediation_plan(report),
            "certification_readiness": self.check_certification_readiness(analysis),
            "appendices": self.generate_appendices(report)
        }
        
        return detailed_report
    
    def generate_executive_summary(self, analysis: Dict):
        """Генерация исполнительного резюме"""
        score = analysis.get("score", 0)
        protection_level = analysis.get("protection_level", "Не определен")
        
        return {
            "overall_score": score,
            "protection_level": protection_level,
            "compliant_requirements": analysis.get("compliant_count", 0),
            "total_requirements": analysis.get("total_requirements", 0),
            "compliance_percentage": f"{score}%",
            "key_findings": [
                "Оценка соответствия требованиям ИСПДн",
                f"Уровень защищенности: {protection_level}",
                f"Общий балл: {score}/100"
            ],
            "recommendations_summary": [
                "Разработать недостающую документацию",
                "Реализовать технические меры защиты",
                "Провести обучение сотрудников"
            ]
        }
    
    def generate_compliance_assessment(self, analysis: Dict):
        """Генерация оценки соответствия"""
        results = analysis.get("results", [])
        
        assessment = {
            "by_standard": {},
            "by_category": {},
            "by_severity": {}
        }
        
        for result in results:
            requirement = result["requirement"]
            standard = requirement.get("standard", "Unknown")
            category = requirement.get("category", "Unknown")
            severity = requirement.get("severity", "medium")
            
            # Группировка по стандартам
            if standard not in assessment["by_standard"]:
                assessment["by_standard"][standard] = {"total": 0, "compliant": 0}
            assessment["by_standard"][standard]["total"] += 1
            if result["compliant"]:
                assessment["by_standard"][standard]["compliant"] += 1
            
            # Группировка по категориям
            if category not in assessment["by_category"]:
                assessment["by_category"][category] = {"total": 0, "compliant": 0}
            assessment["by_category"][category]["total"] += 1
            if result["compliant"]:
                assessment["by_category"][category]["compliant"] += 1
            
            # Группировка по важности
            if severity not in assessment["by_severity"]:
                assessment["by_severity"][severity] = {"total": 0, "compliant": 0}
            assessment["by_severity"][severity]["total"] += 1
            if result["compliant"]:
                assessment["by_severity"][severity]["compliant"] += 1
        
        return assessment
    
    def generate_risk_assessment(self, analysis: Dict):
        """Генерация оценки рисков"""
        results = analysis.get("results", [])
        
        risks = []
        for result in results:
            if not result["compliant"]:
                requirement = result["requirement"]
                
                risk_level = "Высокий" if requirement.get("severity") == "high" else "Средний"
                
                risks.append({
                    "requirement": requirement["name"],
                    "risk_level": risk_level,
                    "potential_impact": self.estimate_impact(requirement),
                    "probability": self.estimate_probability(requirement),
                    "mitigation_measures": result.get("recommendations", []),
                    "estimated_cost": self.estimate_remediation_cost(requirement)
                })
        
        return {
            "total_risks": len(risks),
            "high_risks": len([r for r in risks if r["risk_level"] == "Высокий"]),
            "medium_risks": len([r for r in risks if r["risk_level"] == "Средний"]),
            "detailed_risks": risks
        }
    
    def estimate_impact(self, requirement: Dict):
        """Оценка воздействия"""
        if requirement.get("severity") == "high":
            return "Высокое (штрафы, репутационные потери, остановка деятельности)"
        else:
            return "Среднее (незначительные штрафы, рекомендации)"
    
    def estimate_probability(self, requirement: Dict):
        """Оценка вероятности"""
        if "fz152" in requirement.get("id", ""):
            return "Высокая (регулярные проверки Роскомнадзора)"
        else:
            return "Средняя (выборочные проверки)"
    
    def generate_detailed_findings(self, report: Dict):
        """Генерация детальных результатов"""
        matrix = report.get("compliance_matrix", [])
        
        findings = []
        for item in matrix:
            findings.append({
                "Требование": item["Требование"],
                "Стандарт": item["Стандарт"],
                "Соответствие": item["Соответствие"],
                "Доказательства": item.get("Причины соответствия", []),
                "Проблемы": item.get("Причины несоответствия", []),
                "Ссылка_на_закон": self.get_legal_reference(item["Стандарт"])
            })
        
        return findings
    
    def get_legal_reference(self, standard: str):
        """Получение ссылки на нормативный документ"""
        references = {
            "ФЗ-152": "Федеральный закон от 27.07.2006 № 152-ФЗ",
            "ФСТЭК Приказ 17": "Приказ ФСТЭК России от 11.02.2013 № 17",
            "ФСТЭК Приказ 21": "Приказ ФСТЭК России от 18.02.2013 № 21",
            "ГОСТ Р 57580.1-2017": "Национальный стандарт РФ",
            "ГОСТ Р ИСО/МЭК 27001": "Международный стандарт"
        }
        
        return references.get(standard, "Неизвестный стандарт")
    
    def generate_remediation_plan(self, report: Dict):
        """Генерация плана устранения несоответствий"""
        recommendations = report.get("recommendations", [])
        
        plan = {
            "total_actions": len(recommendations),
            "high_priority": len([r for r in recommendations if r.get("priority") == "Высокий"]),
            "timeline": self.generate_timeline(recommendations),
            "actions": recommendations
        }
        
        return plan
    
    def generate_timeline(self, recommendations: List):
        """Генерация временной шкалы"""
        timeline = {
            "immediate": [],    # 7 дней
            "short_term": [],   # 30 дней
            "medium_term": [],  # 90 дней
            "long_term": []     # 180+ дней
        }
        
        for rec in recommendations:
            deadline = rec.get("deadline", "")
            
            if "7" in deadline or "немедленно" in deadline.lower():
                timeline["immediate"].append(rec)
            elif "30" in deadline:
                timeline["short_term"].append(rec)
            elif "90" in deadline:
                timeline["medium_term"].append(rec)
            else:
                timeline["long_term"].append(rec)
        
        return timeline
    
    def check_certification_readiness(self, analysis: Dict):
        """Проверка готовности к сертификации"""
        checklist = analysis.get("certification_checklist", [])
        
        total = len(checklist)
        compliant = len([c for c in checklist if c.get("compliant", False)])
        
        readiness = {
            "total_requirements": total,
            "compliant_requirements": compliant,
            "readiness_percentage": (compliant / total * 100) if total > 0 else 0,
            "can_certify": compliant == total and total > 0,
            "missing_requirements": [
                item["requirement_name"] 
                for item in checklist 
                if not item.get("compliant", False)
            ]
        }
        
        return readiness
    
    def generate_appendices(self, report: Dict):
        """Генерация приложений к отчету"""
        return {
            "appendix_a": {
                "title": "Нормативные документы",
                "content": [
                    "Федеральный закон от 27.07.2006 № 152-ФЗ",
                    "Приказ ФСТЭК России от 11.02.2013 № 17",
                    "Приказ ФСТЭК России от 18.02.2013 № 21",
                    "ГОСТ Р 57580.1-2017",
                    "ГОСТ Р ИСО/МЭК 27001-2006"
                ]
            },
            "appendix_b": {
                "title": "Методики оценки",
                "content": [
                    "Методика оценки соответствия требованиям ФЗ-152",
                    "Методика оценки технических мер защиты",
                    "Методика оценки организационных мер"
                ]
            },
            "appendix_c": {
                "title": "Глоссарий",
                "content": {
                    "ПДн": "Персональные данные",
                    "ИСПДн": "Информационная система персональных данных",
                    "УЗ": "Уровень защищенности",
                    "СЗИ": "Средства защиты информации",
                    "СМИБ": "Система менеджмента информационной безопасности"
                }
            }
        }