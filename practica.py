from pathlib import Path

from ocr_paddle import extraer_texto_paddle
from xml_parser import extraer_desde_xml

archivo = "cfdi_ejemplo.jpg"

def detectar_archivo(archivo):
    ruta = Path(archivo)

    # caso 1: ya es XML directamente
    if ruta.suffix.lower() == ".xml":
        return {"texto": extraer_desde_xml(archivo), "mensaje": "XML directo"}

    # caso 2: es PDF/imagen pero tiene XML hermano
    xml_hermano = ruta.with_suffix(".xml")
    if xml_hermano.exists():
        return {"texto": extraer_desde_xml(xml_hermano), "mensaje": "XML hermano encontrado"}

    # caso 3: solo hay PDF/imagen, fallback OCR
    return {"texto": extraer_texto_paddle(archivo), "mensaje": "OCR fallback"}


detectar_archivo(archivo)


resultado = detectar_archivo(archivo)
print(resultado)
