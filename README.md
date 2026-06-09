# CFDI Pipeline 

Pipeline de extracción de facturas CFDI mexicanas PDF/imagen y XML.

## Archivos

| Archivo | Rol |
|---|---|
| `pipeline.py` | Punto de entrada. Orquesta todo el flujo. |
| `ocr_preprocess.py` | Clasificación de página, renderizado y preprocesamiento de imagen. |
| `ocr_paddle.py` | Extracción de texto con PaddleOCR (preprocesamiento + OCR). |
| `llm_extractor.py` | Estructuración con Mistral + normalización + fallback regex. |
| `xml_parser.py` | Parser directo para archivos XML CFDI. |
| `schema.py` | Validación Pydantic del JSON extraído. |
| `catalogos.py` | Catálogos SAT y funciones de normalización. |

## Flujo

```
PDF/Imagen → ocr_preprocess (clasifica página) → ocr_paddle (extrae texto)
           → pipeline (detecta versión/UUID) → Mistral (estructura JSON)
           → schema (valida Pydantic) → JSON final

XML → xml_parser → schema (valida Pydantic) → JSON final
```

## Requisitos previos

- Python 3.12
- Cuenta en [Mistral AI](https://console.mistral.ai/) para obtener API key

## Instalación

### 1. Crear y activar entorno virtual

**Git Bash (Windows):**
```bash
python -m venv .venv
source .venv/Scripts/activate
```


### 2. Actualizar pip

```bash
python -m pip install --upgrade pip
```

### 3. Instalar numpy primero (versión fija requerida por PaddlePaddle)

```bash
python -m pip install numpy==1.26.4
```

### 4. Instalar PaddlePaddle

**CPU (Git Bash / Windows):**
```bash
python -m pip install paddlepaddle==3.2.1
```

### 5. Instalar PaddleOCR

```bash
python -m pip install paddleocr==3.5.0
```

### 6. Instalar el resto de dependencias

```bash
python -m pip install PyMuPDF==1.27.2.3 opencv-python==4.11.0.86 Pillow==11.1.0 mistralai==2.4.5 pydantic requests==2.34.2
```

### 7. Verificar instalación

```bash
python -c "import paddle; import paddleocr; import fitz; import cv2; import PIL; import mistralai; import pydantic; print('Todo OK')"
```

Debes ver `Todo OK`. Los warnings de `ccache` y `oneDNN` son normales y no afectan el funcionamiento.

## Configuración

Configura tu API key de Mistral antes de correr el pipeline:

```bash
export MISTRAL_API_KEY=tu_clave_aqui
```

## Uso

```bash
# Un archivo
python pipeline.py cfdi_ejemplo.jpg

# Una carpeta completa
python pipeline.py ./facturas/
```

El pipeline genera dos archivos junto al archivo de entrada:
- `<nombre>_ocr.txt` — texto crudo extraído por PaddleOCR (para verificación)
- `<nombre>_cfdis.json` — datos estructurados y validados (el json a guardar)

## Archivos en Drive para pruebas 

link al dataset en drive: https://drive.google.com/drive/folders/1ff7dVfDPQoh53ahYL4vCWp_kgwzYkD9y?usp=sharing