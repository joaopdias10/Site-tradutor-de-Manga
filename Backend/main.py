from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import uuid
import os
from .translator import traduz_manga

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/traduzir")
async def traduzir(file: UploadFile = File(...)):
    nome = str(uuid.uuid4())

    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/{nome}.jpg"
    output_path = f"temp/{nome}_pt.jpg"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    traduz_manga(input_path, output_path)

    return FileResponse(
        output_path,
        media_type="image/jpeg"
    )