"""Главный файл запуска системы"""
from fastapi import FastAPI, Form 
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback
import os  # Добавьте эту строку

from app.config import Config
from app.routes import router as web_router
from app.api import router as api_router

# Создаем приложение
app = FastAPI(
    title=Config.APP_NAME,
    description=Config.DESCRIPTION,
    version=Config.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем необходимые директории при запуске
directories = [
    "data/settings",
    "data/reports/ispdn",
    "static/css",
    "static/js",
    "templates"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Подключаем маршруты
app.include_router(web_router)
app.include_router(api_router)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=Config.STATIC_DIR), name="static")

@app.get("/api/health")
async def health():
    """Проверка здоровья"""
    return {"status": "ok", "version": Config.VERSION}

@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"message": f"Добро пожаловать в {Config.APP_NAME}", "version": Config.VERSION}

# УДАЛИТЬ этот дублирующийся endpoint (он уже в api.py или routes.py)
# @app.post("/api/test-simple")
# async def test_simple(
#     name: str = Form(...)
# ):
#     """Простой тестовый endpoint"""
#     try:
#         return {
#             "status": "success",
#             "name": name,
#             "message": "Тест пройден"
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }

if __name__ == "__main__":
    print(f"🚀 {Config.APP_NAME} v{Config.VERSION} запущен")
    print(f"🌐 Веб-интерфейс: http://{Config.HOST}:{Config.PORT}")
    print(f"📖 API документация: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"📊 API документация (альтернативная): http://{Config.HOST}:{Config.PORT}/redoc")
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )