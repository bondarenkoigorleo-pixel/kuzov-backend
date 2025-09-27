import os
import uuid
import tempfile
import requests

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import replicate  # pip install replicate

app = FastAPI(title="Kuzov Backend")

# Если знаешь фронтовый домен, потом подставь вместо "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# ВАЖНО: правильная версия модели CodeFormer с твоего скрина
MODEL_ID = "sczhou/codeformer:cc495cd026fa5a7185d560cc9100fab1b8070a10165a8bb5eb6d443b020bb2"


@app.get("/")
def root():
    return {"message": "Backend работает!"}


@app.post("/api/restore")
async def restore(file: UploadFile = File(...)):
    if not REPLICATE_API_TOKEN:
        raise HTTPException(status_code=500, detail="REPLICATE_API_TOKEN не задан")

    # Сохраняем загруженный файл во временный путь
    suffix = os.path.splitext(file.filename or "")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        in_path = tmp.name

    try:
        # Репликейт читает токен из окружения
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

        # Запускаем CodeFormer
        output = replicate.run(
            MODEL_ID,
            input={
                "image": open(in_path, "rb"),
                "background_enhance": True,
                "face_upsample": True,
                "scale": 2,
                "codeformer_fidelity": 0.7,
            },
        )

        if not output:
            raise HTTPException(status_code=500, detail="Модель не вернула изображение")

        # Репликейт возвращает URL картинки
        out_url = output[0] if isinstance(output, list) else output
        resp = requests.get(out_url, timeout=120)
        resp.raise_for_status()

        out_path = os.path.join(tempfile.gettempdir(), f"restored_{uuid.uuid4().hex}.png")
        with open(out_path, "wb") as f:
            f.write(resp.content)

        return FileResponse(
            out_path,
            media_type="image/png",
            filename=f"restored_{os.path.basename(file.filename)}.png",
        )

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Не удалось скачать результат модели: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {e}")
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass
