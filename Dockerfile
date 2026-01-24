# Usa uma versão leve do Python
FROM python:3.10-slim

# 1. Instala Tesseract e bibliotecas do sistema necessárias para OpenCV/YOLO
# O comando 'rm -rf' no final limpa o cache para deixar a imagem menor
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Define a pasta de trabalho dentro do container
WORKDIR /app

# 2. Copia o requirements e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia todo o resto do projeto (pasta backend, frontend, etc) para o container
COPY . .

# 4. Comando para iniciar o servidor (FastAPI + Uvicorn)
# Aponta para a pasta 'backend' onde está o main.py
CMD ["uvicorn", "Backend.main:app", "--host", "0.0.0.0", "--port", "10000"]