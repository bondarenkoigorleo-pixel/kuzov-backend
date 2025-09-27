import os
import uuid
import tempfile
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import replicate  # pip install replicate

app = FastAPI(title="Kuzov Backend")

# Если уже знаешь фронтовый домен — подставь сюда, например "https://kuzov-bel.ru"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потом лучше заменить на конкретный домен
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # Replicate: InstructPix2Pix — редактирование по тексту
        # Документация: https://replicate.com/timothybrooks/instruct-pix2pix
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

        output_urls = replicate.run(
            "timothybrooks/instruct-pix2pix:7e9d5a87b76d8ea88b0b43f701d67f4a3d7a6a2d9a52bc2d7d15b2831f4e5d0e",
            input={
                "image": open(in_path, "rb"),
                "prompt": (
                    "restore the car to factory condition, remove all dents, "
                    "scratches and broken parts, keep same color and model, "
                    "photo-realistic, high details"
                ),
                "num_inference_steps": 50,
                "image_guidance_scale": 1.5,
                "guidance_scale": 7.0
            }
        )

        if not output_urls:
            raise HTTPException(status_code=500, detail="Модель не вернула изображение")

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
