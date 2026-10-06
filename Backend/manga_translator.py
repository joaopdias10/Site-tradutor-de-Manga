import os
import re
import shutil

import cv2
import pytesseract
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw
from ultralytics import YOLO

from .lettering.lettering import spell
from .translator.LLM_translator import translate_page
from .translator.translator import translate

# ============================================================
# Tesseract (Windows + Linux / Render)
# ============================================================
tesseract_cmd = shutil.which("tesseract")

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    raise RuntimeError("Tesseract não encontrado no sistema")


# ============================================================
# Caminhos seguros
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "weight", "best.pt")
font_path = os.path.join(BASE_DIR, "font", "KOMIKAX_.ttf")

# ============================================================
# Carrega modelo UMA VEZ
# ============================================================
model = YOLO(MODEL_PATH)


# ============================================================
# Função principal
# ============================================================
def traduz_manga(input_image_path: str, output_image_path: str):
    # Lê imagem
    image = cv2.imread(input_image_path)
    if image is None:
        raise ValueError("Imagem não encontrada")

    # YOLO
    results = model(image)

    # OpenCV → PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)


    baloes = []
    for i,box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0]) #coordenadas

        cropped = image[y1:y2, x1:x2] #recorta a imagem
    #cv2.imwrite(f'scr_manga/outputs/recorte_{i}.jpg', cropped)

        config = r'--oem 3 --psm 6' #vi em um video e melhorou o resultado do ocr kk
        text = pytesseract.image_to_string(cropped,config=config) #pega o texto da imagem

        text = re.sub(r'\s+', ' ', text).strip() #remove quebra de linha
        if not text: #balão sem texto: nada a traduzir
            continue
        text = text.capitalize() #formata o texto

        baloes.append(((x1, y1, x2, y2), text)) #guarda pra traduzir a pagina toda de uma vez

    #ordem de leitura de mangá: de cima pra baixo, da direita pra esquerda
    baloes.sort(key=lambda b: (b[0][1] // 100, -b[0][2]))

    #traduz a pagina inteira numa chamada so ao Gemini (com contexto entre os baloes)
    textos = [t for _, t in baloes]
    traducoes = translate_page(textos)

    for i, ((x1, y1, x2, y2), traducao) in enumerate(zip([c for c, _ in baloes], traducoes)):
        print(f"Balão {i+1}: {textos[i]} -> {traducao}") #printa o balão
        spell(draw, traducao, x1, y1, x2, y2, "font/KOMIKAX_.ttf") #Escreve na imagem

    # Salva resultado
    image_pil.save(output_image_path)