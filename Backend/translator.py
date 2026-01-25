from ultralytics import YOLO
import cv2
import pytesseract
import re
import textwrap
import os
import shutil

from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw, ImageFont


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
# Cálculo dinâmico da melhor fonte
# ============================================================
def calcular_melhor_fonte(texto, largura_box, altura_box, caminho_fonte):
    """
    Versão ULTRA:
    Força o texto a quebrar linhas para ocupar a altura do balão.
    Ideal para balões redondos ou verticais.
    """
    tamanho_minimo = 14
    tamanho_maximo = 120  # antes: 90

    largura_util = largura_box
    altura_util = altura_box

    # Loop reverso: começa grande e vai diminuindo
    for tamanho in range(tamanho_maximo, tamanho_minimo, -2):
        try:
            font = ImageFont.truetype(caminho_fonte, size=tamanho)
        except IOError:
            font = ImageFont.load_default()

        # "Truque": força quebra de linha mais agressiva
        largura_media_letra = tamanho * 0.30
        chars_por_linha = max(int(largura_util / largura_media_letra), 1)

        linhas = textwrap.wrap(texto, width=chars_por_linha)

        ascent, descent = font.getmetrics()
        altura_linha = ascent + descent * 0.9
        altura_total = len(linhas) * altura_linha

        # Verifica se cabe na altura
        if altura_total > altura_util:
            continue

        # Verifica se cabe na largura
        largura_estourou = False
        for linha in linhas:
            if font.getlength(linha) > largura_util:
                largura_estourou = True
                break

        if not largura_estourou:
            return font, linhas, altura_linha

    # Fallback mínimo
    return (
        ImageFont.truetype(caminho_fonte, size=tamanho_minimo),
        textwrap.wrap(texto, width=15),
        20,
    )


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


    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cropped = image[y1:y2, x1:x2]

        config = r"--oem 3 --psm 6"
        text = pytesseract.image_to_string(cropped, config=config)

        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        text = text.capitalize()
        text = GoogleTranslator(source="en", target="pt").translate(text)

        # Pinta o balão de branco
        draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))

        largura_balao = x2 - x1
        altura_balao = y2 - y1

        font, linhas, altura_linha = calcular_melhor_fonte(
            text,
            largura_balao,
            altura_balao,
            font_path,
        )

        # Centralização vertical
        altura_total_bloco = len(linhas) * altura_linha
        y_atual = y1 + (altura_balao - altura_total_bloco) / 2

        # Desenha linha por linha
        for linha in linhas:
            largura_linha = font.getlength(linha)
            x_atual = x1 + (largura_balao - largura_linha) / 2

            draw.text(
                (x_atual, y_atual),
                linha,
                font=font,
                fill=(0, 0, 0),
            )
            y_atual += altura_linha

    # Salva resultado
    image_pil.save(output_image_path)