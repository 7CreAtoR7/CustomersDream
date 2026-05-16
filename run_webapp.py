"""Запускает ТОЛЬКО Mini App (FastAPI) без Telegram-бота.
Удобно для тестирования фронтенда локально: http://localhost:8080
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api.server:app", host="0.0.0.0", port=8080, reload=True)
