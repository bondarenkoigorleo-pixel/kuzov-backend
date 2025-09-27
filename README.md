
# Kuzov Backend

## Установка и запуск локально

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Деплой на Render

1. Залей файлы в GitHub (main.py, requirements.txt).
2. Создай новый Web Service на Render.
3. Настрой:

- Environment: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`

После деплоя API будет доступен по адресу:  
`https://<твой-сервис>.onrender.com`

Документация Swagger:  
`https://<твой-сервис>.onrender.com/docs`
