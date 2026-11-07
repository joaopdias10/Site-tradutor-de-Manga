import os
import re
import shutil

import cv2
import pytesseract
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw
from ultralytics import YOLO

from .inpaint.inpainter import remover_texto
from .lettering.lettering import cores_para_fundo, spell
from .ocr.ocr import IDIOMAS, decidir_idiomas, ler
from .translator.LLM_translator import translate_page

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
MODEL_PATH = os.path.join(BASE_DIR, "weight", "best_lote12.pt") #modelo v1 (classes ENG e JP)
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


    #etapa 4: remove o texto original de todas as caixas de uma vez.
    caixas = [tuple(map(int, box.xyxy[0])) for box in results[0].boxes]
    image_limpa, relatorio = remover_texto(image, caixas, metodo="auto")
    #fundo que ficou em cada caixa: decide texto preto ou branco na etapa 5.
    #indexado pela caixa (e nao pela posicao) porque `baloes` e filtrado e reordenado
    info_por_caixa = dict(zip(caixas, relatorio))

    # OpenCV → PIL
    image_pil = Image.fromarray(cv2.cvtColor(image_limpa, cv2.COLOR_BGR2RGB)) #converte do opencv para pil
    draw = ImageDraw.Draw(image_pil) #objeto de desenho    

    #etapa 2: o idioma de cada caixa vem da classe do YOLO (ENG ou JP)
    idiomas = decidir_idiomas(results[0])
    print("[idioma]", {k: idiomas.count(k) for k in IDIOMAS if k in idiomas})

    baloes = [] #(coordenadas, texto, idioma) de cada balao com texto

    for i, (x1, y1, x2, y2) in enumerate(caixas):
        cropped = image[y1:y2, x1:x2] #recorta a imagem
    #cv2.imwrite(f'scr_manga/outputs/recorte_{i}.jpg', cropped)

        #ingles -> Tesseract, japones -> Manga-OCR
        text = ler(cropped, idiomas[i])
        if not text: #balão sem texto: nada a traduzir
            continue

        baloes.append(((x1, y1, x2, y2), text, idiomas[i])) #guarda pra traduzir a pagina toda de uma vez

    #ordem de leitura de mangá: de cima pra baixo, da direita pra esquerda
    baloes.sort(key=lambda b: (b[0][1] // 100, -b[0][2]))

    #traduz a pagina inteira numa chamada so (com contexto entre os baloes)
    textos = [t for _, t, _ in baloes]
    idiomas_pagina = sorted({idi for _, _, idi in baloes})
    traducoes = translate_page(textos, idiomas=idiomas_pagina)

    for i, ((x1, y1, x2, y2), traducao) in enumerate(zip([c for c, _, _ in baloes], traducoes)):
        print(f"Balão {i+1} [{baloes[i][2]}]: {textos[i]} -> {traducao}") #printa o balão
        info = info_por_caixa[(x1, y1, x2, y2)]
        #texto sobre arte ganha contorno: a mediana do fundo nao garante contraste em todo ponto
        cor, contorno = cores_para_fundo(info.get("fundo"), com_contorno=info["tipo"] == "arte")
        spell(draw, traducao, x1, y1, x2, y2, font_path, cor=cor, contorno=contorno) #Escreve na imagem

    # Salva resultado
    image_pil.save(output_image_path)