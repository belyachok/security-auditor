"""Конфигурация приложения"""
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Настройки системы"""
    
    # Основные настройки
    APP_NAME = "Security Auditor"
    VERSION = "1.0.0"
    DESCRIPTION = "Система проверки безопасности ИСПДн"
    
    # Сервер
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = True
    
    # Пути
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    REPORTS_DIR = BASE_DIR / "reports"
    TEMPLATES_DIR = BASE_DIR / "templates"
    STATIC_DIR = BASE_DIR / "static"
    
    # Цветовая схема
    COLORS = {
        'primary': "#225715",
        'secondary': "#2a80c7",
        'success': "#2FD129",
        'warning': "#FFEE03",
        'danger': "#692d2d",
        'light': '#88b8e6',
        'dark': '#212529',
        'gray': '#6c757d',
        'gray-light': "#88b8e6",
        'page_bg': "#59cfb8"
    }
    
    # Требования безопасности
    REQUIREMENTS = {
        'password_policy': {
            'name': 'Парольная политика',
            'checks': [
                'Минимальная длина пароля - 12 символов',
                'Требование сложности пароля',
                'Блокировка после 5 неудачных попыток',
                'Срок действия пароля - не более 90 дней'
            ]
        },
        'antivirus': {
            'name': 'Антивирусная защита',
            'checks': [
                'Наличие антивирусного ПО',
                'Актуальность сигнатур',
                'Автоматическое обновление'
            ]
        },
        'firewall': {
            'name': 'Сетевой экран',
            'checks': [
                'Активность брандмауэра',
                'Настройка правил фильтрации'
            ]
        },
        'updates': {
            'name': 'Обновления системы',
            'checks': [
                'Установка критических обновлений',
                'Регулярное обновление ПО'
            ]
        },
        'audit': {
            'name': 'Аудит безопасности',
            'checks': [
                'Ведение журналов событий',
                'Хранение журналов не менее 90 дней'
            ]
        }
    }
    
    @classmethod
    def setup_directories(cls):
        """Создание необходимых директорий"""
        directories = [
            cls.DATA_DIR,
            cls.REPORTS_DIR,
            cls.TEMPLATES_DIR,
            cls.STATIC_DIR / "css",
            cls.STATIC_DIR / "js",
            cls.DATA_DIR / "collected"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        return True
