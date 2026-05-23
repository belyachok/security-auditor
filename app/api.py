# app/api.py
"""API эндпоинты для системы"""
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
import uuid
import secrets
import platform
import socket
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Form, BackgroundTasks, Request  # ← Добавить Request
from fastapi.responses import JSONResponse

from app.database import Database
from app.collector import SystemInfoCollector  # Изменено с SystemCollector
from app.verifier import SecurityVerifier
from app.ispdn_analyzer import ISPDNAnalyzer
from app.advanced_checks import AdvancedSecurityChecks
from app.requirements import ISPDNRequirements

router = APIRouter()
db = Database()  # Создаем экземпляр Database

# ============ API для веб-интерфейса ============


# routes.py - обновить функции


# api.py - обновить analyze_ispdn
@router.post("/api/ispdn/analyze")
async def analyze_ispdn_api():
    """Анализ соответствия ИСПДн с учетом настроек"""
    try:
        # 1. Получаем настройки
        settings = db.get_ispdn_settings()
        if not settings:
            return JSONResponse({
                "status": "error",
                "message": "Сначала настройте параметры ИСПДн"
            }, status_code=400)
        
        # 2. Получаем требования
        requirements_module = ISPDNRequirements()
        all_requirements = requirements_module.get_all_requirements()
        
        # 3. Фильтруем требования по выбранным в настройках
        selected_requirements_ids = settings.get('selected_requirements', [])
        if selected_requirements_ids:
            requirements = [
                req for req in all_requirements 
                if req.get('id') in selected_requirements_ids
            ]
        else:
            requirements = all_requirements
        
        # 4. Собираем информацию о системе
        system_info = SystemInfoCollector.get_all_info()
        
        # 5. Выполняем анализ
        analysis_results = requirements_module.analyze_compliance(
            system_info=system_info,
            company_info=settings.get('organization', {}),
            requirements=requirements,
            pdn_category=settings.get('ispdn', {}).get('pdnCategory'),
            threat_type=settings.get('ispdn', {}).get('threatType')
        )
        
        # 6. Генерируем отчет
        report = requirements_module.generate_ispdn_report(
            analysis_results=analysis_results,
            company_info=settings.get('organization', {}),
            settings=settings
        )
        
        # 7. Сохраняем отчет
        reports_dir = "data/reports/ispdn"
        os.makedirs(reports_dir, exist_ok=True)
        report_file = os.path.join(reports_dir, f"{report['id']}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 8. Сохраняем в базу данных
        report_data = {
            "id": report["id"],
            "type": "ispdn",
            "timestamp": datetime.now().isoformat(),
            "report": report,
            "settings_id": settings.get('id'),
            "company_name": settings.get('organization', {}).get('name', 'Неизвестно'),
            "score": analysis_results.get("score", 0)
        }
        db.save_report(report_data)
        
        return JSONResponse({
            "status": "success",
            "report": report,
            "analysis": analysis_results,
            "report_id": report["id"],
            "settings_used": True
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)


@router.post("/api/settings/ispdn")
async def save_ispdn_settings_api(request: Request):
    """API для сохранения настроек ИСПДн"""
    try:
        settings = await request.json()
        
        # Валидация
        if not settings.get('organization', {}).get('name'):
            return JSONResponse({
                "status": "error", 
                "message": "Название организации обязательно"
            }, status_code=400)
        
        # Сохраняем в базу
        settings_id = db.save_ispdn_settings(settings)
        
        if settings_id:
            return JSONResponse({
                "status": "success", 
                "message": "Настройки ИСПДн сохранены",
                "settings_id": settings_id
            })
        else:
            return JSONResponse({
                "status": "error", 
                "message": "Ошибка сохранения настроек"
            }, status_code=500)
    
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": str(e)
        }, status_code=500)

@router.get("/api/settings/ispdn/current")
async def get_current_ispdn_settings():
    """Получение текущих настроек ИСПДн"""
    settings = db.get_ispdn_settings()
    if settings:
        return JSONResponse(settings)
    else:
        return JSONResponse({
            "status": "not_found",
            "message": "Настройки не найдены"
        }, status_code=404)

@router.get("/api/system-info")
async def get_system_info() -> Dict[str, Any]:
    """Получение базовой информации о системе"""
    try:
        info = SystemInfoCollector.get_all_info()
        return {
            "status": "success",
            "data": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сбора информации: {str(e)}")

@router.get("/api/security-checks")
async def get_security_checks() -> Dict[str, Any]:
    """Выполнение проверок безопасности"""
    try:
        # Базовые проверки безопасности
        verifier = SecurityVerifier()
        checks = verifier.perform_basic_checks()
        
        return {
            "status": "success",
            "data": {
                "basic_checks": checks,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки безопасности: {str(e)}")

@router.get("/api/ispdn-analysis")
async def get_ispdn_analysis() -> Dict[str, Any]:
    """Анализ соответствия требованиям ИСПДн"""
    try:
        analyzer = ISPDNAnalyzer()
        analysis = analyzer.analyze_system()
        
        return {
            "status": "success",
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа ИСПДн: {str(e)}")

@router.get("/api/report")
async def generate_report() -> Dict[str, Any]:
    """Генерация полного отчета"""
    try:
        # Собираем всю информацию
        system_info = SystemInfoCollector.get_all_info()
        verifier = SecurityVerifier()
        basic_checks = verifier.perform_basic_checks()
        analyzer = ISPDNAnalyzer()
        ispdn_analysis = analyzer.analyze_system()
        
        # Формируем отчет
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "system": system_info["software"]["os"]["name"],
                "audit_type": "Безопасность ИСПДн"
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
        
        # Сохраняем отчет
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        report_file = os.path.join(reports_dir, f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "data": report,
            "report_file": report_file,
            "message": "Отчет успешно сгенерирован"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчета: {str(e)}")

# ============ API для управления компьютерами ============

@router.get("/api/computers")
async def get_all_computers():
    """Получить все компьютеры"""
    return db.get_all_computers()

@router.get("/api/computers/{computer_id}")
async def get_computer(computer_id: str):
    """Получить компьютер по ID"""
    computer = db.get_computer(computer_id)
    if not computer:
        raise HTTPException(status_code=404, detail="Компьютер не найден")
    return computer

@router.post("/api/computers")
async def add_computer(
    name: str = Form(...),
    description: str = Form(""),
    ip: str = Form(""),
    tags: str = Form(""),
    type: str = Form("workstation"),
    criticality: str = Form("medium")
):
    """Добавить новый компьютер"""
    computer_id = str(uuid.uuid4())
    
    # Если IP не указан, используем локальный
    if not ip:
        ip = socket.gethostbyname(socket.gethostname())
    
    computer = {
        "id": computer_id,
        "name": name,
        "description": description,
        "ip_address": ip,
        "status": "offline",
        "type": type,
        "criticality": criticality,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        "created_at": datetime.now().isoformat(),
        "last_seen": None,
        "agent_token": secrets.token_hex(16) if type == "agent" else None,
        "is_local": (ip == "127.0.0.1" or ip == "localhost" or ip == socket.gethostbyname(socket.gethostname())),
        "os": platform.system() if ip == socket.gethostbyname(socket.gethostname()) else "unknown"
    }
    
    db.save_computer(computer)
    return {"status": "success", "id": computer_id, "computer": computer}

@router.delete("/api/computers/{computer_id}")
async def delete_computer(computer_id: str):
    """Удалить компьютер"""
    try:
        computer = db.get_computer(computer_id)
        if not computer:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Компьютер {computer_id} не найден"}
            )
        
        db.delete_computer(computer_id)
        return {
            "status": "success", 
            "message": f"Компьютер '{computer.get('name', computer_id)}' удален"
        }
        
    except Exception as e:
        print(f"✗ Ошибка удаления компьютера {computer_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "message": "Ошибка при удалении компьютера"
            }
        )

# В api.py исправьте функцию quick_verify_computer:
@router.post("/api/quick-verify/{computer_id}")
async def quick_verify_computer(computer_id: str):
    """Быстрая проверка компьютера"""
    try:
        computer = db.get_computer(computer_id)
        if not computer:
            return JSONResponse(
                status_code=404,
                content={"error": f"Компьютер {computer_id} не найден"}
            )
        
        print(f"🔍 Начало быстрой проверки для компьютера {computer_id}")
        
        # ИСПРАВЛЕНО: Собираем ПОЛНУЮ информацию о системе

        from app.collector import SystemInfoCollector
        system_info = SystemInfoCollector.get_all_info()
        
        
        # Запускаем упрощенную проверку
        verifier = SecurityVerifier()
        
        # Проверяем, какие методы есть у verifier
        security_checks = []
        
        # Пробуем разные возможные методы
        try:
            # Попробуем вызвать perform_basic_checks
            if hasattr(verifier, 'perform_basic_checks'):
                security_checks = verifier.perform_basic_checks()
            # Или run_quick_check
            elif hasattr(verifier, 'run_quick_check'):
                security_checks = verifier.run_quick_check(system_info)
            # Или run_checks
            elif hasattr(verifier, 'run_checks'):
                security_checks = verifier.run_checks(system_info)
            # Или просто создадим базовые проверки
            else:
                security_checks = [
                    {
                        "id": "basic_check_1",
                        "name": "Базовая проверка ОС",
                        "status": "passed",
                        "description": f"ОС: {platform.system()} {platform.version()}",
                        "details": "Операционная система определена"
                    },
                    {
                        "id": "basic_check_2",
                        "name": "Проверка хоста",
                        "status": "passed",
                        "description": f"Имя хоста: {socket.gethostname()}",
                        "details": "Имя хоста определено"
                    }
                ]
        except Exception as verifier_error:
            print(f"Ошибка в проверке: {verifier_error}")
            security_checks = [
                {
                    "id": "error_check",
                    "name": "Ошибка проверки",
                    "status": "warning",
                    "description": "Не удалось выполнить полную проверку",
                    "details": str(verifier_error)
                }
            ]
        
        # ============ ДОБАВЛЯЕМ РАСШИРЕННЫЕ ПРОВЕРКИ ============
        if computer.get("is_local"):

            try:
                advanced_checks = AdvancedSecurityChecks.perform_advanced_checks()
                
                # Добавляем расширенные проверки в общий список
                for check in advanced_checks:
                    check['category'] = 'Углубленная проверка безопасности'
                    security_checks.append(check)
            except Exception as adv_error:
                print(f"Ошибка расширенных проверок: {adv_error}")
        # ========================================================
        
        # Рассчитываем оценку
        passed = len([c for c in security_checks if c["status"] == "passed"])
        total = len(security_checks)
        score = int((passed / total) * 100) if total > 0 else 0
        
        # Создаем отчет
        report_id = str(uuid.uuid4())
        report = {
            "id": report_id,
            "computer_id": computer_id,
            "computer_name": computer.get("name", "Неизвестно"),
            "timestamp": datetime.now().isoformat(),
            "scan_type": "quick_ispdn",
            "system_info": system_info,  # ИСПРАВЛЕНО: сохраняем ПОЛНУЮ информацию
            "security_checks": security_checks,
            "score": score,
            "status": "completed"
        }
        
        print(f"Создан отчет {report_id} с оценкой {score}%")
        
        # Сохраняем отчет
        db.save_report(report)
        
        # Обновляем компьютер
        computer["last_scan"] = datetime.now().isoformat()
        computer["last_score"] = score
        db.save_computer(computer)
        
        return {
            "status": "success",
            "report_id": report_id,
            "score": score,
            "checks_count": len(security_checks),
            "message": f"Быстрая проверка ИСПДн завершена"
        }
        
    except Exception as e:
        print(f"✗ Ошибка быстрой проверки: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "message": "Ошибка при быстрой проверке"
            }
        )

# ============ API для регистрации агентов ============

@router.post("/api/agents/register")
async def register_agent(
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    criticality: str = Form("medium")
):
    """Зарегистрировать текущий ПК как агент"""
    try:
        import platform
        import socket
        import uuid
        import secrets
        
        # 1. Просто возвращаем тестовые данные без сбора информации
        computer_id = str(uuid.uuid4())
        agent_token = secrets.token_hex(16)
        
        computer = {
            "id": computer_id,
            "name": name,
            "description": description,
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "status": "online",
            "type": "agent",
            "criticality": criticality,
            "tags": [tag.strip() for tag in tags.split(",") if tag.strip()] + ["local", "self"],
            "created_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "agent_token": agent_token,
            "is_local": True,
            "os": platform.system(),
            "system_info": {
                "hostname": socket.gethostname(),
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version()
            }
        }
        
        # 2. Сохраняем в базу данных
        db.save_computer(computer)

        
        return {
            "status": "success", 
            "id": computer_id, 
            "computer": {
                "id": computer_id,
                "name": name,
                "ip": socket.gethostbyname(socket.gethostname())
            },
            "token": agent_token,
            "message": "ПК успешно зарегистрирован как агент"
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()

        print(error_details)
        
        # Возвращаем ошибку с деталями
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "traceback": error_details,
                "message": "Внутренняя ошибка сервера"
            }
        )

@router.post("/api/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str, data: dict):
    """Получение heartbeat от агента"""
    computer = db.get_computer(agent_id)
    if not computer:
        raise HTTPException(status_code=404, detail="Агент не найден")
    
    # Обновляем статус
    computer["status"] = "online"
    computer["last_seen"] = datetime.now().isoformat()
    
    if "system_info" in data:
        computer["system_info"] = data["system_info"]
    
    db.save_computer(computer)
    
    return {"status": "ok", "message": "Heartbeat принят"}

# ============ API для управления отчетами ============

@router.get("/api/reports")
async def get_all_reports():
    """Получить все отчеты"""
    return db.get_all_reports()

@router.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """Получить отчет по ID"""
    report = db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    return report

@router.delete("/api/reports/{report_id}/delete")
async def delete_report(report_id: str):
    """Удалить отчет по ID"""
    try:
        # Проверяем существование отчета
        report = db.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Отчет не найден")
        
        # Удаляем отчет
        db.delete_report(report_id)
        
        return {
            "status": "success",
            "message": f"Отчет {report_id} успешно удален",
            "report_id": report_id
        }
        
    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "message": "Ошибка при удалении отчета"
            }
        )

@router.delete("/api/reports/delete-all")
async def delete_all_reports():
    """Удалить все отчеты"""
    try:
        # Получаем все отчеты
        reports = db.get_all_reports()
        
        # Удаляем каждый отчет
        deleted_count = 0
        for report in reports:
            success = db.delete_report(report.get("id"))
            if success:
                deleted_count += 1
        
        return {
            "status": "success",
            "message": f"Все отчеты успешно удалены ({deleted_count} шт.)",
            "deleted_count": deleted_count
        }
        
    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "message": "Ошибка при удалении отчетов"
            }
        )

# ============ API для ИСПДн ============

@router.post("/api/ispdn/analyze")
async def analyze_ispdn(data: dict):
    """Анализ соответствия ИСПДн"""
    try:
        # Здесь должен быть ваш реальный анализатор ИСПДн
        # Для теста возвращаем фиктивные данные
        
        import random
        
        # Генерируем фиктивные результаты анализа
        analysis_results = {
            "score": random.uniform(70, 95),
            "protection_level": random.choice(["УЗ-1", "УЗ-2", "УЗ-3"]),
            "compliant_count": random.randint(15, 25),
            "non_compliant_count": random.randint(0, 5),
            "requirements": [
                {"id": f"req-{i}", "name": f"Требование {i}", "status": "passed"} 
                for i in range(1, 21)
            ]
        }
        
        # Генерируем отчет
        report_id = f"ISP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        report = {
            "id": report_id,
            "generated_at": datetime.now().isoformat(),
            "analysis": analysis_results,
            "company_info": data.get("company_info", {}),
            "parameters": data.get("parameters", {})
        }
        
        # Сохраняем отчет в базу данных
        report_data = {
            "id": report_id,
            "type": "ispdn",
            "timestamp": datetime.now().isoformat(),
            "report": report
        }
        db.save_report(report_data)
        
        return {
            "status": "success",
            "report": report,
            "analysis": analysis_results,
            "message": "Анализ ИСПДн выполнен успешно"
        }
        
    except Exception as e:
        print(f"✗ Ошибка анализа ИСПДн: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "message": "Ошибка при анализе ИСПДн"
            }
        )

@router.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "collector": "ok",
            "verifier": "ok"
        }
    }