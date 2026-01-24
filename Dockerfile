# Usa uma versão leve do Python
FROM python:3.10-slim

# 1. Instala Tesseract e bibliotecas do sistema (OpenCV/YOLO precisam disso)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho
WORKDIR /app

# 2. Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- MELHORIA 1: Corrige o aviso do Ultralytics (YOLO) ---
# Define a pasta de configuração do YOLO para /tmp (que é gravável)
# Isso elimina aquele "WARNING ⚠️ user config directory is not writable"
ENV YOLO_CONFIG_DIR="/tmp"

# 3. Copia o código do projeto
COPY . .

# --- MELHORIA 2: Porta Dinâmica ---
# Usar a variável de ambiente $PORT é mais seguro para o Render.
# O "sh -c" é necessário para que o Docker entenda a variável $PORT.
CMD sh -c "uvicorn Backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"