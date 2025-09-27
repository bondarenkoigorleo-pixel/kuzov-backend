from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil, uuid, os

app = FastAPI()

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@app.post("/api/restore")
async def restore(image: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    orig_path = os.path.join(UPLOAD_DIR, f"{file_id}_{image.filename}")
    with open(orig_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    # имитация результата — просто копируем файл
    result_path = os.path.join(RESULT_DIR, f"restored_{file_id}.png")
    shutil.copy(orig_path, result_path)
    return JSONResponse({"url": f"/{result_path}"})
