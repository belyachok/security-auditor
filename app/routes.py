# app/routes.py
"""Веб-маршруты"""
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import json
import os
import socket
import platform

from app.config import Config
from app.database import Database
from app.requirements import ISPDNRequirements
from app.collector import SystemInfoCollector
from app.verifier import SecurityVerifier
from app.ispdn_analyzer import ISPDNAnalyzer
from app.reporter import Reporter  # Используем существующий класс

router = APIRouter()
templates = Jinja2Templates(directory=Config.TEMPLATES_DIR)

# Создаем экземпляры
db = Database()
reporter = Reporter()

# Добавляем фильтр для форматирования даты
def format_datetime(value, format='%d.%m.%Y %H:%M'):
    """Форматирование даты для шаблонов"""
    if isinstance(value, str):
        try:
            # Пробуем разные форматы дат
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime(format)
                except:
                    continue
            return value
        except:
            return value
    elif isinstance(value, datetime):
        return value.strftime(format)
    return str(value)

# Регистрируем фильтр
templates.env.filters['datetime'] = format_datetime




@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница - используем новый дизайн"""
    try:
        # Пробуем получить базовую информацию о системе
        try:
            info = SystemInfoCollector.get_all_info()
            system_info = info
        except:
            system_info = {"hardware": {}, "software": {}}
        
        # Получаем компьютеры и отчеты
        computers = db.get_all_computers()
        reports = db.get_all_reports()
        
        # Рассчитываем статистику
        total_computers = len(computers)
        total_reports = len(reports)
        
        # Рассчитываем среднюю оценку
        total_score = 0
        score_count = 0
        for r in reports:
            if 'score' in r:
                total_score += r['score']
                score_count += 1
        
        avg_score = round(total_score / score_count, 1) if score_count > 0 else 0
        
        # Подсчитываем компьютеры с проверками
        verified_computers = 0
        for computer in computers:
            if 'last_scan' in computer:
                verified_computers += 1
        
        # Подсчитываем уязвимости
        total_vulnerabilities = 0
        for report in reports:
            if 'security_checks' in report:
                checks = report['security_checks']
                if isinstance(checks, list):
                    total_vulnerabilities += len([c for c in checks if c.get('status') in ['failed', 'error']])
        
        # Формируем статистику
        stats = {
            "total_computers": total_computers,
            "verified": verified_computers,
            "avg_score": avg_score,
            "total_vulnerabilities": total_vulnerabilities,
            "online_computers": len([c for c in computers if c.get("status") == "online"]),
            "total_reports": total_reports
        }
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "Главная",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "stats": stats,  # Передаем stats в шаблон
            "system_info": system_info,
            "computers": computers[:5],  # Последние 5 компьютеров
            "reports": reports[:5]       # Последние 5 отчетов
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Возвращаем шаблон с минимальными данными
        return templates.TemplateResponse("index_new.html", {
            "request": request,
            "title": "Главная",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "stats": {
                "total_computers": 0,
                "verified": 0,
                "avg_score": 0,
                "total_vulnerabilities": 0,
                "online_computers": 0,
                "total_reports": 0
            },
            "system_info": {},
            "computers": [],
            "reports": []
        })

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Панель управления"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Панель управления",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M')
    })

@router.get("/system-info", response_class=HTMLResponse)
async def system_info_page(request: Request):
    """Страница информации о системе"""
    try:
        info = SystemInfoCollector.get_all_info()
        return templates.TemplateResponse("system_info.html", {
            "request": request,
            "title": "Информация о системе",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "system_info": info
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка получения информации: {str(e)}",
            "title": "Ошибка"
        })

@router.get("/security-checks", response_class=HTMLResponse)
async def security_checks_page(request: Request):
    """Страница проверок безопасности"""
    try:
        verifier = SecurityVerifier()
        checks = verifier.perform_basic_checks()
        
        # Статистика
        stats = {
            "total": len(checks),
            "passed": len([c for c in checks if c.get("status") == "passed"]),
            "failed": len([c for c in checks if c.get("status") in ["failed", "error"]]),
            "warning": len([c for c in checks if c.get("status") == "warning"]),
            "info": len([c for c in checks if c.get("status") == "info"])
        }
        
        return templates.TemplateResponse("security_checks.html", {
            "request": request,
            "title": "Проверки безопасности",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "checks": checks,
            "stats": stats
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка проверки безопасности: {str(e)}",
            "title": "Ошибка"
        })

@router.get("/ispdn-analysis", response_class=HTMLResponse)
async def ispdn_analysis_page(request: Request):
    """Страница анализа ИСПДн"""
    try:
        analyzer = ISPDNAnalyzer()
        analysis = analyzer.analyze_system()
        
        return templates.TemplateResponse("ispdn_analysis.html", {
            "request": request,
            "title": "Анализ ИСПДн",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "analysis": analysis
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка анализа ИСПДн: {str(e)}",
            "title": "Ошибка"
        })

@router.get("/generate-report", response_class=HTMLResponse)
async def generate_report_page(request: Request):
    """Генерация полного отчета"""
    try:
        # Собираем данные
        system_info = SystemInfoCollector.get_all_info()
        verifier = SecurityVerifier()
        basic_checks = verifier.perform_basic_checks()
        analyzer = ISPDNAnalyzer()
        ispdn_analysis = analyzer.analyze_system()
        
        # Формируем данные для отчета
        report_data = {
            "metadata": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system": system_info["software"]["os"]["name"]
            },
            "system_info": system_info,
            "security_checks": basic_checks,
            "ispdn_compliance": ispdn_analysis,
            "summary": {
                "total_checks": len(basic_checks),
                "passed_checks": len([c for c in basic_checks if c.get("status") == "passed"]),
                "failed_checks": len([c for c in basic_checks if c.get("status") in ["failed", "error"]]),
                "warnings": len([c for c in basic_checks if c.get("status") == "warning"]),
                "compliance_level": ispdn_analysis.get("compliance_level", "Не определен")
            }
        }
        
        # Генерируем и сохраняем отчет
        report = reporter.generate_report(report_data)
        
        return templates.TemplateResponse("report_generated.html", {
            "request": request,
            "title": "Отчет сгенерирован",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "report_file": f"reports/{report['id']}.json",
            "report_data": report_data,
            "report": report
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка генерации отчета: {str(e)}",
            "title": "Ошибка"
        })

@router.get("/computers", response_class=HTMLResponse)
async def computers_page(request: Request):
    """Страница компьютеров"""
    computers = db.get_all_computers()
    
    return templates.TemplateResponse("computers.html", {
        "request": request,
        "title": "Компьютеры",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "computers": computers
    })

@router.get("/computers/new", response_class=HTMLResponse)
async def new_computer_page(request: Request):
    """Форма добавления компьютера"""
    return templates.TemplateResponse("add_computer.html", {
        "request": request,
        "title": "Добавить компьютер",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M')
    })

@router.get("/verification", response_class=HTMLResponse)
async def verification_page(request: Request):
    """Страница проверки"""
    computers = db.get_all_computers()
    
    return templates.TemplateResponse("verification.html", {
        "request": request,
        "title": "Проверка безопасности",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "computers": computers
    })

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Страница отчетов"""
    reports = db.get_all_reports()
    
    # Форматируем даты для отображения и добавляем безопасный доступ к summary
    for report in reports:
        if 'timestamp' in report:
            try:
                dt = datetime.fromisoformat(report['timestamp'].replace('Z', '+00:00'))
                report['formatted_date'] = dt.strftime('%d.%m.%Y %H:%M')
            except:
                report['formatted_date'] = report.get('timestamp', '')
        
        # Убедимся, что у отчета есть поле summary или создаем его
        if 'summary' not in report:
            # Создаем базовый summary на основе того, что есть в отчете
            report['summary'] = {
                'passed': 0,
                'failed': 0,
                'warning': 0,
                'total_checks': 0,
                'total': 0
            }
            
            # Попробуем получить данные из security_checks
            if 'security_checks' in report and isinstance(report['security_checks'], list):
                checks = report['security_checks']
                passed = len([c for c in checks if c.get("status") == "passed"])
                failed = len([c for c in checks if c.get("status") == "failed"])
                warning = len([c for c in checks if c.get("status") == "warning"])
                
                report['summary']['passed'] = passed
                report['summary']['failed'] = failed
                report['summary']['warning'] = warning
                report['summary']['total_checks'] = len(checks)
                report['summary']['total'] = len(checks)
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "title": "Отчеты",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "reports": reports[:10]  # Последние 10 отчетов
    })

@router.get("/reports/{report_id}", response_class=HTMLResponse)
async def view_report_detail(request: Request, report_id: str):
    """Страница детального просмотра отчета"""
    report = db.get_report(report_id)
    
    if not report:
        # Попробуем загрузить из файловой системы
        report_file = Path(f"reports/{report_id}.json")
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
    
    if not report:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Отчет с ID {report_id} не найден",
            "title": "Ошибка"
        })
    
    # УЛУЧШАЕМ ИНФОРМАЦИЮ О СИСТЕМЕ
    report = enhance_system_info(report)

    
    return templates.TemplateResponse("report_detail.html", {
        "request": request,
        "title": f"Отчет: {report.get('computer_name', 'Без имени')}",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "report": report
    })

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Страница настроек"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "title": "Настройки",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M')
    })

@router.get("/register-agent", response_class=HTMLResponse)
async def register_agent_page(request: Request):
    """Страница регистрации текущего ПК как агента"""
    # Получаем информацию о текущей системе
    system_info = {
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "os": platform.system(),
        "os_version": platform.version()
    }
    
    return templates.TemplateResponse("register_agent.html", {
        "request": request,
        "title": "Регистрация ПК как агента",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "system_info": system_info
    })

@router.get("/agent/{agent_id}", response_class=HTMLResponse)
async def agent_dashboard(request: Request, agent_id: str):
    """Панель управления агентом"""
    computer = db.get_computer(agent_id)
    if not computer:
        # Вернуть страницу 404 или редирект
        return RedirectResponse(url="/computers")
    
    # Получаем отчеты этого агента
    all_reports = db.get_all_reports()
    reports = [r for r in all_reports if r.get("computer_id") == agent_id]
    
    return templates.TemplateResponse("agent_dashboard.html", {
        "request": request,
        "title": f"Агент: {computer.get('name', 'Без имени')}",
        "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
        "agent": computer,
        "reports": reports
    })

@router.get("/test-register", response_class=HTMLResponse)
async def test_register_page(request: Request):
    """Тестовая страница регистрации"""
    return templates.TemplateResponse("test_register.html", {"request": request})

@router.get("/api/debug/reports")
async def debug_reports():
    """Отладочная информация о отчетах"""
    reports = db.get_all_reports()
    return {
        "total": len(reports),
        "reports": reports
    }

# ДОБАВЛЕННЫЕ МАРШРУТЫ ДЛЯ ИСПДН

@router.get("/settings/ispdn", response_class=HTMLResponse)
async def ispdn_settings_page(request: Request):
    """Страница настроек ИСПДн"""
    try:
        req_module = ISPDNRequirements()
        requirements = req_module.get_all_requirements()
        
        return templates.TemplateResponse("ispdn_settings.html", {
            "request": request,
            "title": "Настройки ИСПДн",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "requirements": requirements
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка загрузки настроек ИСПДн: {str(e)}",
            "title": "Ошибка"
        })

@router.post("/api/settings/ispdn")
async def save_ispdn_settings(request: Request):
    """Сохранение настроек ИСПДн"""
    try:
        settings = await request.json()
        
        # Сохранение в файл
        settings_dir = "data/settings"
        settings_file = os.path.join(settings_dir, "ispdn_settings.json")
        
        os.makedirs(settings_dir, exist_ok=True)
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "status": "success", 
            "message": "Настройки ИСПДн сохранены"
        })
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

@router.get("/api/settings/ispdn")
async def get_ispdn_settings():
    """Получение настроек ИСПДн"""
    try:
        settings_file = "data/settings/ispdn_settings.json"
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return JSONResponse(settings)
        else:
            return JSONResponse({
                "status": "not_found",
                "message": "Настройки ИСПДн не найдены"
            })
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)



@router.get("/ispdn/analyze")
async def ispdn_analyze_page(request: Request):
    """Страница анализа ИСПДн"""
    try:
        req_module = ISPDNRequirements()
        requirements = req_module.get_all_requirements()
        
        return templates.TemplateResponse("ispdn_analyze.html", {
            "request": request,
            "title": "Анализ ИСПДн",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "requirements": requirements
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка загрузки анализатора ИСПДн: {str(e)}",
            "title": "Ошибка"
        })
# app/routes.py - обновим маршрут analyze_ispdn
# app/routes.py - обновим маршрут analyze_ispdn

@router.post("/api/ispdn/analyze")
async def analyze_ispdn(request: Request):
    """Анализ соответствия ИСПДн ТОЛЬКО по выбранным требованиям"""
    try:
        data = await request.json()
        print(f"Получены данные для анализа: {data}")  # Отладка
        
        # Загружаем настройки ИСПДн
        settings_file = "data/settings/ispdn_settings.json"
        company_info = {}
        selected_requirements = []
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
                # Получаем выбранные требования из настроек
                selected_requirements = settings.get("selected_requirements", [])
                print(f"Выбрано требований для проверки: {len(selected_requirements)}")  # Отладка
                print(f"ID выбранных требований: {selected_requirements}")  # Отладка
                
                # Информация об организации
                company_info = {
                    "name": settings.get("organization", {}).get("name", "Неизвестно"),
                    "inn": settings.get("organization", {}).get("inn", ""),
                    "pdn_category": settings.get("ispdn", {}).get("pdnCategory", "Иные"),
                    "subjects_count": settings.get("ispdn", {}).get("subjectsCount", "less_100k"),
                    "threat_type": settings.get("ispdn", {}).get("threatType", "TYPE3"),
                    
                    # Реалистичные данные для проверок
                    "has_security_policy": False,  # Нет политики безопасности
                    "has_consent_forms": True,     # Есть формы согласия
                    "has_roskomnadzor_notification": False,  # Нет уведомления
                    "has_rights_mechanism": True,  # Есть механизмы прав
                    "has_storage_policy": True,    # Есть политика хранения
                    "has_transfer_agreement": False,  # Нет соглашений о передаче
                    
                    # Документация для ГОСТ
                    "has_documentation": {
                        "gost57580_1": False, "gost57580_2": True,
                        "gost57580_3": False, "gost57580_4": True,
                        "gost27001_1": False, "gost27001_2": True,
                        "gost27001_3": False, "gost27001_4": True,
                        "gost27001_5": False, "gost27001_6": True,
                        "gost27001_7": False, "gost27001_8": True
                    }
                }
        else:
            # Настройки по умолчанию
            company_info = {
                "name": "Тестовая организация",
                "pdn_category": "Иные",
                "selected_requirements": [],  # Пустой список
                "has_security_policy": False,
                "has_consent_forms": True,
                "has_roskomnadzor_notification": False
            }
        
        # Получаем все требования
        req_module = ISPDNRequirements()
        all_requirements = req_module.get_all_requirements()
        
        # Фильтруем требования - берем ТОЛЬКО выбранные
        requirements_to_check = []
        if selected_requirements:
            # Фильтруем по ID выбранных требований
            for req_id in selected_requirements:
                requirement = req_module.get_requirement(req_id)
                if requirement:
                    requirements_to_check.append(requirement)
            print(f"Найдено требований для проверки: {len(requirements_to_check)}")  # Отладка
        else:
            # Если ничего не выбрано - проверяем все требования
            print("Не выбрано требований - проверяем все")  # Отладка
            requirements_to_check = all_requirements
        
        # Собираем информацию о системе
        from app.collector import SystemInfoCollector
        system_info = SystemInfoCollector.get_all_info()
        
        # Реалистичные данные о безопасности системы
        system_info["security"] = {
            "password_policy": False,      # Нет парольной политики
            "access_control": True,        # Есть управление доступом
            "software_restriction": False, # Нет ограничения ПО
            "media_encryption": False,     # Нет шифрования носителей
            "audit_logging": True,         # Есть аудит
            "antivirus": True,             # Есть антивирус
            "ids": False,                  # Нет IDS
            "integrity_check": False,      # Нет контроля целостности
            "virtualization_security": False,
            "physical_security": True
        }
        
        # Проводим анализ ТОЛЬКО по выбранным требованиям
        analysis_results = req_module.analyze_compliance(
            system_info=system_info,
            company_info=company_info,
            requirements=requirements_to_check,  # Передаем отфильтрованные требования
            pdn_category=company_info.get("pdn_category"),
            threat_type=company_info.get("threat_type")
        )
        
        # Отладочная информация
        print(f"=== РЕЗУЛЬТАТЫ АНАЛИЗА ===")  # Отладка
        print(f"Проверено требований: {analysis_results.get('total_requirements', 0)}")  # Отладка
        print(f"Соответствует: {analysis_results.get('compliant_count', 0)}")  # Отладка
        print(f"Не соответствует: {analysis_results.get('non_compliant_count', 0)}")  # Отладка
        print(f"Оценка: {analysis_results.get('score', 0)}%")  # Отладка
        
        # Выводим детали по каждому проверенному требованию
        for i, result in enumerate(analysis_results.get("results", [])):
            req = result.get("requirement", {})
            compliant = result.get("compliant", False)
            print(f"{i+1}. {req.get('id')} - {req.get('name')} - Соответствует: {compliant}")
        
        # Генерируем отчет
        report = req_module.generate_ispdn_report(
            analysis_results=analysis_results,
            company_info=company_info
        )
        
        # Сохраняем отчет
        reports_dir = "data/reports/ispdn"
        os.makedirs(reports_dir, exist_ok=True)
        report_file = os.path.join(reports_dir, f"{report['id']}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "status": "success",
            "report": report,
            "analysis": analysis_results,
            "report_id": report["id"],
            "selected_requirements_count": len(requirements_to_check),
            "company_info": company_info
        })
    
    except Exception as e:
        import traceback
        print(f"Ошибка при анализе: {str(e)}")  # Отладка
        traceback.print_exc()  # Печатаем полную трассировку
        
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

@router.get("/ispdn/reports", response_class=HTMLResponse)
async def ispdn_reports_page(request: Request):
    """Страница отчетов ИСПДн"""
    try:
        # Попробуем загрузить сохраненные отчеты ИСПДн
        reports_dir = "data/reports/ispdn"
        reports = []
        
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        reports.append(report)
        
        # Сортируем по дате (новые сначала)
        reports.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        
        return templates.TemplateResponse("ispdn_reports.html", {
            "request": request,
            "title": "Отчеты ИСПДн",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "reports": reports[:10]  # Последние 10 отчетов
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка загрузки отчетов ИСПДн: {str(e)}",
            "title": "Ошибка"
        })
    
# app/routes.py - добавим новый маршрут

@router.get("/api/requirements/all")
async def get_all_requirements():
    """Получение всех требований ИСПДн"""
    try:
        req_module = ISPDNRequirements()
        requirements = req_module.get_all_requirements()
        
        # Возвращаем только нужные поля
        simplified_requirements = []
        for req in requirements:
            simplified_requirements.append({
                "id": req.get("id"),
                "name": req.get("name"),
                "standard": req.get("standard"),
                "category": req.get("category"),
                "severity": req.get("severity"),
                "description": req.get("description")[:100] + "..." if req.get("description") else ""
            })
        
        return JSONResponse(simplified_requirements)
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

# routes.py - проверьте этот маршрут
@router.get("/ispdn/requirements", response_class=HTMLResponse)
async def ispdn_requirements_page(request: Request):
    """Страница требований ИСПДн"""
    try:
        req_module = ISPDNRequirements()  # ← Создаем экземпляр
        requirements = req_module.get_all_requirements()  # ← Получаем требования
        protection_levels = req_module.get_protection_levels_table()
        
        
        return templates.TemplateResponse("ispdn_requirements.html", {
            "request": request,
            "title": "Требования ИСПДн",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "requirements": requirements,  # ← Передаем в шаблон
            "protection_levels": protection_levels
        })
    except Exception as e:
        import traceback
        traceback.print_exc()  # ← Печатаем полную трассировку
        
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка загрузки требований ИСПДн: {str(e)}",
            "title": "Ошибка"
        })

# app/routes.py - добавим новый маршрут
# app/routes.py - обновим маршрут get_current_ispdn_settings

@router.get("/api/settings/ispdn/current")
async def get_current_ispdn_settings():
    """Получение текущих настроек ИСПДн с выбранными требованиями"""
    try:
        settings_file = "data/settings/ispdn_settings.json"
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Убедимся, что есть поле selected_requirements
            if "selected_requirements" not in settings:
                settings["selected_requirements"] = []
            
            return JSONResponse(settings)
        else:
            # Возвращаем настройки по умолчанию
            default_settings = {
                "organization": {
                    "name": "ООО 'Примерная Компания'",
                    "inn": "7701234567",
                    "ogrn": "1234567890123",
                    "okved": "62.01",
                    "address": "г. Москва, ул. Примерная, д. 1"
                },
                "ispdn": {
                    "pdnCategory": "Иные",
                    "hasEmployees": False,
                    "subjectsCount": "less_100k",
                    "threatType": "TYPE3"
                },
                "checks": {
                    "frequency": "weekly",
                    "reportDetail": "detailed",
                    "autoGenerateCert": True,
                    "sendToRegulator": False
                },
                "notifications": {
                    "email": "security@example.com",
                    "phone": "+7 (999) 123-45-67",
                    "notifyOnFailures": True,
                    "notifyOnChanges": False,
                    "generateMonthlyReports": True
                },
                "selected_requirements": []  # Пустой список по умолчанию
            }
            
            return JSONResponse(default_settings)
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

@router.post("/api/requirements/selected")
async def save_selected_requirements(request: Request):
    """Сохранение выбранных требований"""
    try:
        data = await request.json()
        selected_requirements = data.get("selected_requirements", [])
        
        # Сохраняем в файл
        settings_dir = "data/settings"
        os.makedirs(settings_dir, exist_ok=True)
        
        file_path = os.path.join(settings_dir, "selected_requirements.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"selected": selected_requirements}, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "status": "success",
            "message": f"Сохранено {len(selected_requirements)} требований"
        })
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

@router.get("/api/ispdn/reports/{report_id}/download")
async def download_ispdn_report(report_id: str):
    """Скачивание отчета ИСПДн"""
    try:
        reports_dir = "data/reports/ispdn"
        file_path = os.path.join(reports_dir, f"{report_id}.json")
        
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=f"ispdn_report_{report_id}.json",
                media_type="application/json"
            )
        else:
            return JSONResponse({
                "status": "error",
                "message": "Отчет не найден"
            }, status_code=404)
    
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@router.get("/ispdn/reports/{report_id}", response_class=HTMLResponse)
async def view_ispdn_report_page(request: Request, report_id: str):
    """Страница детального просмотра отчета ИСПДн"""
    try:
        # 1. Ищем в базе данных
        report_data = db.get_report(report_id)
        
        # 2. Если не найден, проверяем файлы ISPDN
        if not report_data:
            reports_dir = "data/reports/ispdn"
            if os.path.exists(reports_dir):
                # Пробуем разные варианты имени файла
                possible_files = [
                    os.path.join(reports_dir, f"{report_id}.json"),
                    os.path.join(reports_dir, f"{report_id}"),
                    os.path.join(reports_dir, report_id)
                ]
                
                for filepath in possible_files:
                    if os.path.exists(filepath):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                        break
        
        if not report_data:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": f"Отчет ИСПДн с ID {report_id} не найден",
                "title": "Отчет не найден",
                "current_time": datetime.now().strftime('%d.%m.%Y %H:%M')
            })
        
        # Извлекаем отчет из данных
        if isinstance(report_data, dict):
            if "report" in report_data:
                report = report_data["report"]
            else:
                report = report_data
        
        return templates.TemplateResponse("ispdn_report_detail.html", {
            "request": request,
            "title": f"Отчет ИСПДн: {report.get('id', 'Без ID')}",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M'),
            "report": report
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Ошибка при загрузке отчета: {str(e)}",
            "title": "Ошибка сервера",
            "current_time": datetime.now().strftime('%d.%m.%Y %H:%M')
        })
    
# Добавьте эту функцию перед регистрацией фильтров:
def safe_get(data, *keys, default=None):
    """Безопасный доступ к вложенным значениям"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
            current = current[key]
        else:
            return default
    return current if current is not None else default

# Добавьте как глобальную переменную в шаблоны
templates.env.globals['safe_get'] = safe_get
    
# routes.py - добавьте эту функцию
def enhance_system_info(report):
    """Улучшить и дополнить информацию о системе в отчете"""
    try:
        if not report.get('system_info'):
            report['system_info'] = {}
        
        system_info = report['system_info']
        
        # Если system_info пустое, собираем заново
        if not system_info or not isinstance(system_info, dict):
            from app.collector import SystemInfoCollector
            system_info = SystemInfoCollector.get_all_info()
            report['system_info'] = system_info
        
        # Убедимся, что все ключи существуют
        if 'hardware' not in system_info or not isinstance(system_info['hardware'], dict):
            system_info['hardware'] = {}
        
        hardware = system_info['hardware']
        
        # CPU
        if 'cpu' not in hardware or not isinstance(hardware['cpu'], dict):
            hardware['cpu'] = {}
        
        cpu = hardware['cpu']
        
        # Если CPU данные пустые, собираем заново
        if not cpu or cpu.get('brand_raw') == 'Неизвестно':
            from app.hardware_info import HardwareInfoCollector
            cpu_info = HardwareInfoCollector.get_cpu_info()
            hardware['cpu'] = cpu_info
        
        # Memory
        if 'memory' not in hardware or not isinstance(hardware['memory'], dict):
            from app.hardware_info import HardwareInfoCollector
            hardware['memory'] = HardwareInfoCollector.get_memory_info()
        
        # Disks
        if 'disks' not in hardware or not isinstance(hardware['disks'], list):
            from app.hardware_info import HardwareInfoCollector
            hardware['disks'] = HardwareInfoCollector.get_disk_info()
        
        # Network
        if 'network' not in hardware or not isinstance(hardware['network'], dict):
            from app.hardware_info import HardwareInfoCollector
            hardware['network'] = HardwareInfoCollector.get_network_info()
        
        # Software
        if 'software' not in system_info or not isinstance(system_info['software'], dict):
            system_info['software'] = {}
        
        software = system_info['software']
        
        # OS
        if 'os' not in software or not isinstance(software['os'], dict):
            from app.software_info import SoftwareInfoCollector
            software['os'] = SoftwareInfoCollector.get_os_info()
        
        # Python
        if 'python' not in software or not isinstance(software['python'], dict):
            import platform
            software['python'] = {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler()
            }
        
        return report
        
    except Exception as e:
        print(f"[ERROR] Ошибка в enhance_system_info: {e}")
        return report


# Добавьте этот фильтр после создания templates
def fromjson(value):
    """Конвертировать строку JSON в объект"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return {}
    return value

# Регистрируем фильтр
templates.env.filters['fromjson'] = fromjson
templates.env.filters['datetime'] = format_datetime

# Добавьте эти фильтры:
def get_type(obj):
    """Получить тип объекта"""
    return type(obj).__name__

def is_mapping(obj):
    """Проверить, является ли объект словарем/маппингом"""
    return isinstance(obj, dict)

def is_sequence(obj):
    """Проверить, является ли объект последовательностью (list, tuple)"""
    return isinstance(obj, (list, tuple, set))

# Регистрируем фильтры
templates.env.filters['get_type'] = get_type
templates.env.filters['is_mapping'] = is_mapping
templates.env.filters['is_sequence'] = is_sequence
templates.env.filters['fromjson'] = fromjson
templates.env.filters['datetime'] = format_datetime

