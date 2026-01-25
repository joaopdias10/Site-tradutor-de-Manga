from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import uuid
import os

from .translator import traduz_manga


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://site-tradutor-de-manga.vercel.app"],  # Permite só meu site hospedado na Vercel
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Permite GET e POST
    allow_headers=["*"],  # Permite todos os cabeçalhos
)


@app.get("/")
def root():
    return {"status": "ok"}


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