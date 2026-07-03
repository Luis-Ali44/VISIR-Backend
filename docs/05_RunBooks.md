# Runbook de Despliegue y Operaciones - Visir API

Este documento detalla los pasos para levantar el entorno operativo, la configuración del pipeline automatizado y los procedimientos de monitoreo en producción de Visir API.

---

## 1. Prerrequisitos del Entorno
Asegúrate de contar con las siguientes herramientas instaladas en el host de ejecución:
- Docker y Docker Compose
- Python 3.12+ 

---

## 2. Configuración de Variables de Entorno (.env)
El archivo .env debe ubicarse en la raíz del proyecto y estar estrictamente registrado en el archivo .gitignore.

### Estructura de producción / desarrollo:
ENVIRONMENT=development
SUPABASE_URL=url_de_supabase
SUPABASE_PUBLIC_KEY=llave_publica
SUPABASE_SECRET_KEY=llave_secreta
MISTRAL_API_KEY=token_de_mistral

---

## 3. Pipeline de Integración Continua (CI) y Despliegue Continuo (CD)

El ciclo de vida del código está automatizado mediante GitHub Actions y se compone de dos flujos:

### Flujo de CI (.github/workflows/ci.yml)
Se ejecuta de forma obligatoria en cada Pull Request o Push directo a la rama main. Realiza las siguientes validaciones de calidad antes de permitir un despliegue:
1. Sincronización: Configura el entorno usando astral-sh/setup-uv para habilitar y usar la herramienta uv, lo que permite una instalación de dependencias.

2. Ruff: Valida la calidad y el formato del código fuente dentro de la carpeta app.

3. Mypy: Verifica que los tipos de datos en la carpeta app cumplan con los estándares de Python.

4. Pruebas Unitarias (Pytest): Ejecuta las pruebas del sistema inyectando las credenciales de Supabase y Mistral configuradas para testing.

5. Compilación de Imagen: Ejecuta "docker build -t visir-api ." para simular y garantizar que el Dockerfile multi-stage ensamble de forma óptima y compacta sin errores estructurales.

### Flujo de CD (.github/workflows/cd.yml)
Se dispara únicamente cuando el job de CI se completa con éxito tras un push a main.
- Ejecuta un Webhook seguro mediante un comando curl que notifica automáticamente a la plataforma de producción para que descargue los nuevos cambios y actualice la API.

---

## 4. Control de Calidad Manual (Pre-Push)
Para evitar que el pipeline remoto de GitHub Actions falle, los desarrolladores deben validar localmente su código antes de hacer un push ejecutan los siguientes comandos:
- uv run ruff check app  # Ejecuta el linter
- uv run mypy app       # Valida el tipado estático
- uv run pytest         # Corre los tests locales

---

## 5. Monitoreo y Mitigación de Errores en Producción

### Diagnóstico de Fallas de Ingesta y RAM
El procesamiento masivo de CFDIs pesados o la ejecución de los módulos de extracción de texto mediante OCR pueden provocar picos altos en el uso de memoria.
1. Acceder a la consola de administración de la plataforma de despliegue donde corre la Visir API.
2. Monitorear los flujos de salida en tiempo real (logs).
3. Verificar que los errores provocados por archivos XML inválidos o registros duplicados interceptados por las validaciones de base de datos devuelvan los códigos de estado HTTP correspondientes, evitando que colapse el contenedor del backend.