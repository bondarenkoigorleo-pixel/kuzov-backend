import os
import uuid
import tempfile
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import replicate  # pip install replicate

app = FastAPI(title="Kuzov Backend")

# CORS (позже можно ограничить доменом фронта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Токен берём из переменной окружения Render
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Модель и «прикреплённая» версия (рабочая на сегодня)
MODEL = "sczhou/codeformer"
PINNED_VERSION = "cc495dc26fa5a718d55d60cc9100fab1b8070a10165a8bb5ebd6443b020bb2"


@app.get("/")
def root():
    return {"message": "Backend работает!"}


def run_codeformer_with_fallback(image_path: str):
    """
    1) Пробуем закреплённую версию модели.
    2) Если Replicate вернул 'Invalid version ...', автоматически берём самую свежую версию модели и запускаем снова.
    """
    if not REPLICATE_API_TOKEN:
        raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN не задан в окружении")

    # Реплике нужен токен в env
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

    inputs = {
        "image": open(image_path, "rb"),
        "background_enhance": True,
        "face_upsample": True,
        "scale": 2,
        "codeformer_fidelity": 0.7,
    }

    model_id_pinned = f"{MODEL}:{PINNED_VERSION}"

    # 1) Пытаемся запустить «прикреплённую» версию
    try:
        return replicate.run(model_id_pinned, input=inputs)
    except Exception as e:
        msg = str(e)
        # типичный текст от Replicate: "Invalid version or not permitted ... does not exist ..."
        if "Invalid version" in msg or "does not exist" in msg or "not permitted" in msg:
            # 2) Берём последнюю доступную версию у модели и пробуем снова
            try:
                latest_version = replicate.models.get(MODEL).versions.list()[0].id
                model_id_latest = f"{MODEL}:{latest_version}"
                return replicate.run(model_id_latest, input=inputs)
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Replicate: не удалось запустить модель (latest): {e2}")
        # Любая другая ошибка
        raise HTTPException(status_code=500, detail=f"Replicate: ошибка запуска модели: {e}")


@app.post("/api/restore")
def restore(file: UploadFile = File(...)):
    # Сохраняем входной файл
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    in_path = os.path.join(tempfile.gettempdir(), f"in_{uuid.uuid4().hex}{ext}")
    with open(in_path, "wb") as f:
        f.write(file.file.read())

    # Запускаем модель
    output_urls = run_codeformer_with_fallback(in_path)

    if not output_urls:
        raise HTTPException(status_code=500, detail="Модель не вернула изображение")

    # Скачиваем результат
    out_url = output_urls[0]
    try:
        resp = requests.get(out_url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Не удалось скачать результат модели: {e}")

    out_path = os.path.join(tempfile.gettempdir(), f"restored_{uuid.uuid4().hex}.png")
    with open(out_path, "wb") as f:
        f.write(resp.content)

    return FileResponse(
        out_path,
        media_type="image/png",
        filename=f"restored_{os.path.basename(file.filename)}.png",
    )
