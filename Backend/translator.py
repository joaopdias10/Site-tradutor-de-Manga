from ultralytics import YOLO
import cv2
import pytesseract
import re
from deep_translator import GoogleTranslator
import textwrap
from PIL import Image, ImageDraw, ImageFont
import os

# =========================
# Caminhos seguros
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MODEL_PATH = os.path.join(BASE_DIR, "weight", "best.pt")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "arial.ttf")

# =========================
# Carrega modelo UMA VEZ
# =========================
model = YOLO(MODEL_PATH)

# =========================
# Função principal
# =========================
def traduz_manga(input_image_path: str, output_image_path: str):
    # lê imagem
    image = cv2.imread(input_image_path)
    if image is None:
        raise ValueError("Imagem não encontrada")

    # YOLO
    results = model(image)

    # OpenCV → PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)

    font = ImageFont.truetype(FONT_PATH, size=20)

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cropped = image[y1:y2, x1:x2]

        config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(cropped, config=config)

        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            continue

        text = text.capitalize()
        text = GoogleTranslator(source="en", target="pt").translate(text)

        # pinta o balão de branco
        draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))

        # quebra de linha automática
        max_chars = max(((x2 - x1) // 10), 1)
        linhas = textwrap.wrap(text, width=max_chars)

        ty = y1 + 5
        for linha in linhas:
            draw.text((x1 + 5, ty), linha, font=font, fill=(0, 0, 0))
            ty += 25

    # salva resultado
    image_pil.save(output_image_path)