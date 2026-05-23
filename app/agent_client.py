import requests
import json
import platform
import socket
import uuid
from datetime import datetime

class SecurityAgent:
    def __init__(self, agent_id, agent_token, server_url="http://localhost:8000"):
        self.agent_id = agent_id
        self.agent_token = agent_token
        self.server_url = server_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {agent_token}",
            "Content-Type": "application/json"
        })
    
    def send_heartbeat(self):
        """Отправка heartbeat на сервер"""
        data = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "system_info": self.collect_system_info()
        }
        
        try:
            response = self.session.post(
                f"{self.server_url}/api/agents/{self.agent_id}/heartbeat",
                json=data
            )
            return response.json()
        except Exception as e:
            print(f"Ошибка отправки heartbeat: {e}")
            return None
    
    def collect_system_info(self):
        """Сбор информации о системе"""
        info = {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
        return info
    
    def run_security_check(self):
        """Запуск проверки безопасности и отправка на сервер"""
        # Здесь собираем данные проверки
        from app.collector import SystemCollector
        from app.verifier import SecurityVerifier
        
        collector = SystemCollector()
        verifier = SecurityVerifier()
        
        # Собираем информацию
        system_info = collector.collect_all()
        
        # Проверяем безопасность
        security_results = verifier.run_checks(system_info)
        
        # Формируем отчет
        report = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "system_info": system_info,
            "security_checks": security_results,
            "score": verifier.calculate_score(security_results),
            "status": "completed"
        }
        
        # Отправляем на сервер
        try:
            response = self.session.post(
                f"{self.server_url}/api/reports/upload",
                json=report
            )
            print(f"Отчет отправлен. ID: {response.json().get('report_id')}")
            return response.json()
        except Exception as e:
            print(f"Ошибка отправки отчета: {e}")
            return None

# Пример использования агента
if __name__ == "__main__":
    # Эти данные вы получаете при регистрации
    AGENT_ID = "ваш_id_из_регистрации"
    AGENT_TOKEN = "ваш_токен_из_регистрации"
    
    agent = SecurityAgent(AGENT_ID, AGENT_TOKEN)
    
    print("1. Отправляем heartbeat...")
    heartbeat_result = agent.send_heartbeat()
    print(f"Heartbeat отправлен: {heartbeat_result}")
    
    print("\n2. Запускаем проверку безопасности...")
    check_result = agent.run_security_check()
    print(f"Проверка завершена: {check_result}")