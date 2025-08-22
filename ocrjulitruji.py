import os
from pathlib import Path
import tempfile

import streamlit as st
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import openai

# -------------- Configuración ------------------
st.set_page_config(page_title="OCR + GPT", page_icon="🧾")

openai.api_key = st.secrets["OPENAI_API_KEY"]  # o usa os.getenv
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # ruta en contenedor

st.title("OCR de facturas + análisis con OpenAI")
st.write("Sube una **imagen** o **PDF** y obtén el texto y un resumen GPT.")

# -------------- Carga de archivos --------------
uploaded_file = st.file_uploader(
    "Selecciona la factura",
    type=["png", "jpg", "jpeg", "pdf"],
)

def pdf_to_images(pdf_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        return convert_from_path(tmp.name, dpi=300)

def ocr_image(img: Image.Image):
    """Devuelve texto plano usando Tesseract."""
    return pytesseract.image_to_string(img, lang="spa+eng")

if uploaded_file:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf":
        pages = pdf_to_images(uploaded_file.read())
    else:
        pages = [Image.open(uploaded_file)]

    full_text = ""
    for i, page in enumerate(pages, 1):
        st.image(page, caption=f"Página {i}", use_column_width=True)
        text = ocr_image(page)
        st.subheader(f"Texto OCR · Página {i}")
        st.code(text, language="text")
        full_text += text + "\n"

    # -------------- Procesamiento con GPT --------------
    if st.button("Analizar con GPT"):
        with st.spinner("Generando respuesta…"):
            prompt = (
                "Extrae los campos clave de la factura (número, fecha, total, "
                "impuestos, proveedor, NIT) y devuélvelos en JSON. "
                "Si falta algún dato usa null.\n\n"
                f"FACTURA OCR:\n{full_text}"
            )
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # o el que tengas disponible
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            st.subheader("JSON extraído")
            st.json(response.choices[0].message.content)

