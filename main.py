import os
import uuid
import tempfile
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import replicate  # pip install replicate

app = FastAPI(title="Kuzov Backend")

# Разрешаем CORS (лучше потом ограничить доменом фронта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Токен берём из Render → Environment
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


@app.get("/")
def root():
    return {"message": "Backend работает!"}


@app.post("/api/restore")
def restore(file: UploadFile = File(...)):
    if not REPLICATE_API_TOKEN:
        raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN не задан")

    # Сохраняем входной файл
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    in_path = os.path.join(tempfile.gettempdir(), f"in_{uuid.uuid4().hex}{ext}")
    with open(in_path, "wb") as f:
        f.write(file.file.read())

    try:
        # Указываем токен для Replicate
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

        # 🚀 Вызов модели CodeFormer (актуальная версия)
        output_urls = replicate.run(
            "sczhou/codeformer:cc495dc26fa5a718d55d60cc9100fab1b8070a10165a8bb5ebd6443b020bb2",
            input={
                "image": open(in_path, "rb"),
                "background_enhance": True,
                "face_upsample": True,
                "scale": 2,
                "codeformer_fidelity": 0.7
            }
        )

        if not output_urls:
            raise HTTPException(status_code=500, detail="Модель не вернула изображение")

        # Скачиваем готовое фото
        out_url = output_urls[0]
        resp = requests.get(out_url, timeout=60)
        resp.raise_for_status()

        out_path = os.path.join(tempfile.gettempdir(), f"restored_{uuid.uuid4().hex}.png")
        with open(out_path, "wb") as f:
            f.write(resp.content)

        return FileResponse(
            out_path,
            media_type="image/png",
            filename=f"restored_{os.path.basename(file.filename)}.png"
        )

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Не удалось скачать результат модели: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {e}")
