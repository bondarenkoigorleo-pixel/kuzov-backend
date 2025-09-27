
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend работает!"}

@app.post("/api/restore")
async def restore(file: UploadFile = File(...)):
    # Здесь можно вставить реальную обработку фото
    contents = await file.read()
    size_kb = len(contents) / 1024
    return JSONResponse(content={"filename": file.filename, "size_kb": round(size_kb, 2)})
