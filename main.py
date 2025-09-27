import os
import uuid
import tempfile
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import replicate  # pip install replicate

app = FastAPI(title="Kuzov Backend")

# Если уже знаешь фронтовый домен — подставь сюда вместо "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # лучше потом ограничить своим доменом
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
        # Replicate: CodeFormer — рабочая модель восстановления изображений
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

        output_urls = replicate.run(
            "sczhou/codeformer:6e61e0b8b46e8f2f4a3b8d20c13959a56e30c3d4d54eecfe25c7d5c9f2e5e9c3",
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
