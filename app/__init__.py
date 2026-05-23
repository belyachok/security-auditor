# app/__init__.py
from app.requirements import ISPDNRequirements

def init_requirements():
    """Инициализация требований при запуске"""
    req_manager = ISPDNRequirements()
    print(f"Загружено {len(req_manager.requirements)} требований ИСПДн")
    
    # Создаем пример настроек, если их нет
    import os
    import json
    
    settings_file = "data/settings/ispdn_settings.json"
    if not os.path.exists(settings_file):
        default_settings = {
            "organization": {
                "name": "Тестовая организация",
                "inn": "0000000000"
            },
            "ispdn": {
                "pdnCategory": "Иные",
                "threatType": "TYPE3"
            }
        }
        
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=2)
        
        print("Созданы настройки по умолчанию")