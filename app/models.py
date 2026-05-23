"""Модели данных"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class Computer(BaseModel):
    """Модель компьютера"""
    name: str = Field(..., min_length=1, max_length=100)
    ip: Optional[str] = None
    os: str = "Windows 10"
    location: str = ""
    description: str = ""
    tags: List[str] = []
    criticality: str = "medium"  # low, medium, high, critical


class VerificationResult(BaseModel):
    """Результат проверки"""
    requirement_id: str
    name: str
    status: str  # passed, failed, warning
    description: str
    details: Dict = {}
    recommendation: str = ""


class SystemInfo(BaseModel):
    """Информация о системе"""
    timestamp: datetime
    hardware: Dict
    software: Dict
    network: Dict
    security: Dict

# models.py - добавить класс
# app/models.py - добавить к существующим моделям

class ISPDNRequirement(BaseModel):
    """Модель требования ИСПДн"""
    id: str = Field(..., description="Идентификатор требования")
    standard: str = Field(..., description="Стандарт (ФЗ-152, ФСТЭК-17 и т.д.)")
    name: str = Field(..., description="Название требования")
    description: str = Field("", description="Описание требования")
    category: str = Field("", description="Категория")
    severity: str = Field("medium", description="Важность: high/medium/low")
    weight: float = Field(1.0, description="Вес в оценке (от 0.5 до 3.0)")
    verification_method: str = Field("", description="Метод проверки")
    recommendation: str = Field("", description="Рекомендация")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "fz152_1",
                "standard": "ФЗ-152",
                "name": "Политика обработки ПДн",
                "description": "Оператор должен разработать и утвердить документ, определяющий политику в отношении обработки персональных данных",
                "category": "Организационные меры",
                "severity": "high",
                "weight": 2.0,
                "verification_method": "Проверка документации",
                "recommendation": "Разработать Политику обработки ПДн и утвердить приказом"
            }
        }
# app/models.py - обновим ISPDNSettings

class ISPDNSettings(BaseModel):
    """Модель настроек ИСПДн"""
    
    id: Optional[str] = None
    organization_name: str = ""
    inn: str = ""
    ogrn: str = ""
    okved: str = ""
    address: str = ""
    pdn_category: str = "Иные"
    has_employees: bool = False
    subjects_count: str = "less_100k"
    threat_type: str = "TYPE3"
    check_frequency: str = "weekly"
    report_detail: str = "detailed"
    notification_email: str = ""
    selected_requirements: List[str] = []  # Выбранные требования
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "organization_name": "ООО 'Примерная Компания'",
                "inn": "7701234567",
                "pdn_category": "Иные",
                "selected_requirements": ["fz152_1", "fstek21_1"],
                "created_at": "2024-01-15T10:30:00"
            }
        }