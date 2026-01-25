FROM python:3.10-slim

# 1. Instala Tesseract e bibliotecas (Igual ao anterior)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Configura Permissões de Usuário (Obrigatório no Hugging Face)
# O HF não gosta de rodar como 'root'. Criamos um usuário com ID 1000.
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# 3. Copia requirements e instala como o novo usuário
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Configura pasta temporária para o YOLO (evita erro de permissão)
ENV YOLO_CONFIG_DIR="/tmp"

# 4. Copia o resto dos arquivos com as permissões certas
COPY --chown=user . .

# 5. MUDANÇA CRÍTICA: Porta 7860
CMD ["uvicorn", "Backend.main:app", "--host", "0.0.0.0", "--port", "7860"]