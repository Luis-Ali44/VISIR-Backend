# Análisis: `/v1/documentos/cargar` — Flujo, problemas y mejoras

## 🔍 Diagnóstico del problema OOM (Exit 137)

### ¿Por qué murió el contenedor hace 9 horas?

El contenedor salió con **exit code 137 = OOM Kill** (Linux kernel mató el proceso por falta de memoria).

**Causas identificadas:**

1. **No hay límite de memoria en docker-compose**
   - El contenedor puede crecer sin restricción
   - Con modelos de PaddleOCR (200-500 MB) + ChromaDB + embeddings + múltiples requests = spike de RAM

2. **PaddleOCR mantiene modelos en caché global**
   ```python
   _paddle_ocr_instance: Any = None  # Singleton global
   ```
   - Primera llamada: descargar + cargar en RAM (~300-400 MB)
   - Llamadas siguientes: reutiliza la instancia (mejor)
   - Si se llama desde múltiples threads/procesos sin sincronización → memory leak posible

3. **ChromaDB + embeddings en background**
   - Después de guardar extracciones, `ingestar_cfdi_organizacion()` corre en `BackgroundTask`
   - Si se acumulan muchas tareas en background sin completar → memoria se llena
   - Los embeddings (Ollama) requieren buffer de contexto

4. **Ingesta de normativa SAT a la vez**
   - Si ejecutaste `/v1/ingest/run` mientras subías documentos → ambos compitiendo por memoria
   - ChromaDB abre archivos vectoriales completos en RAM

### Evidencia actual

En la prueba reciente:
- **Consumo del contenedor:** 255 MB (después del upload + OCR + Mistral + background tasks)
- **Consumo del proceso Python:** 37 MB
- **Modelos + runtime de Paddle/Mistral:** ~200-250 MB
- **Disponible en sistema:** 3.7 GB

Si el sistema host tenía **menos RAM disponible hace 9 horas** (otras apps corriendo) → OOM killer se activó.

---

## 📊 Flujo actual de `/v1/documentos/cargar`

```
POST /v1/documentos/cargar (imagen JPG de 164 KB)
   │
   ├─ 1. validate_document()                    ~0.1s  ✅
   │   └─ Verifica tipo MIME, tamaño máx (5MB)
   │
   ├─ 2. save_document_storage()                ~1-2s  ✅
   │   └─ Sube a Supabase Storage
   │
   ├─ 3. save_document_metadata()               ~0.5s  ✅
   │   └─ INSERT en tabla `documentos` → OK
   │
   ├─ 4. run_in_executor( procesar() )          ~40-50s ⚠️ CUELLO DE BOTELLA
   │   ├─ ocr_preprocess()                      ~2s
   │   │  └─ PDF/imagen → array numpy + CLAHE
   │   │
   │   ├─ PaddleOCR.predict() [CPU-only]        ~25-35s 🚫 PUNTO CRÍTICO
   │   │  └─ Modelos server-grade en CPU (Intel o ARM)
   │   │  └─ Memoria: 200-400 MB durante la ejecución
   │   │  └─ Sin GPU: procesamiento secuencial, lento
   │   │
   │   └─ Mistral API call (estructuración JSON) ~3-5s
   │      └─ HTTP a Groq/Mistral
   │
   ├─ 5. save_extracciones_repository()         ~0.1s  ✅
   │   └─ INSERT en tabla `extracciones` → fila guardada
   │
   └─ 6. background_tasks.add_task(             ~0s (async)
       ingestar_cfdi_organizacion()
   )
       └─ Genera embeddings + indexa en ChromaDB
       └─ Corre en background, no bloquea HTTP response

TIEMPO TOTAL: 42-55s (dominado por PaddleOCR)
```

**Problema crítico: PaddleOCR ocupa CPU 100% en CPU-only por 25-35 segundos**

---

## 🐛 Bugs encontrados durante el análisis

### Bug 1: RLS bloquea INSERT en `extracciones` (INCIDENCIA: ❌ Bloqueante)
**Estado:** Parcialmente resuelto en pruebas recientes

**Síntoma:** Error 500 "No se pudieron guardar las extracciones"

**Causa raíz:** Columnas `NOT NULL` en tabla `extracciones` pero el servicio envía `None`:
```sql
CREATE TABLE extracciones (
    folio_fiscal     varchar(255) NOT NULL,  ← puede ser null si OCR falla
    fecha_emision    timestamp NOT NULL,     ← puede ser null
    tipo_comprobante varchar(50) NOT NULL,   ← puede ser null
    metodo_pago      varchar(10) NOT NULL,   ← puede ser null
    rfc_emisor       varchar(15) NOT NULL,   ← puede ser null
    nombre_emisor    varchar(255) NOT NULL,  ← puede ser null
    rfc_receptor     varchar(15) NOT NULL,   ← puede ser null
    nombre_receptor  varchar(255) NOT NULL,  ← puede ser null
    id_forma_pago    uuid NOT NULL,          ← servicio NO envía este campo
    ...
);
```

**Impacto:** Si el LLM no extrae un campo → INSERT falla → 500 error al usuario

**Fix propuesto:** Rellenar valores por defecto seguros en `documents_service.py`:
```python
rows.append({
    "folio_fiscal": datos.get("folio_fiscal") or "SIN-UUID",
    "total": datos.get("total") or 0.0,
    "fecha_emision": fecha_iso or datetime.now().isoformat(),
    "tipo_comprobante": tipo_comp or "Ingreso",
    "metodo_pago": datos.get("metodo_pago") or "PUE",
    "rfc_emisor": rfc_emisor or "XAXX010101000",
    "nombre_emisor": nombre_emisor or "Sin nombre",
    "rfc_receptor": rfc_receptor or "XAXX010101000",
    "nombre_receptor": nombre_receptor or "Sin nombre",
    # ... rest
})
```

---

## ⚡ Mejoras para optimizar el endpoint

### Mejora 1: Usar GPU para PaddleOCR (reduce de 30s a 3-5s) — 🏆 MÁXIMO IMPACTO

**Problema:** PaddleOCR sin GPU = CPU puro, muy lento

**Solución:**
1. En `app/services/Extraccion/ocr_paddle.py`, detectar GPU disponible:
   ```python
   def _get_paddle_ocr() -> Any:
       global _paddle_ocr_instance
       if _paddle_ocr_instance is None:
           import paddle
           from paddleocr import PaddleOCR

           # Detectar GPU
           if paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
               device = "gpu"
               paddle.device.set_device("gpu:0")
           else:
               device = "cpu"
           
           ocr = PaddleOCR(
               use_doc_orientation_classify=False,
               use_doc_unwarping=False,
               lang="es",
               device=device,  # ← crucial
           )
       return _paddle_ocr_instance
   ```

2. En `docker-compose.yml`, agregar runtime de GPU:
   ```yaml
   services:
     api:
       runtime: nvidia  # ← si NVIDIA Docker está instalado
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

3. **Impacto:** PaddleOCR ~30s → ~3-5s (6-10x más rápido)

---

### Mejora 2: Limitar memoria en docker-compose — 🔒 PREVIENE OOM

**Problema:** Sin límite de memoria, el kernel mata el contenedor

**Solución:** Agregar límites en `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G           # máximo 2 GB
          cpus: '2.0'          # máximo 2 CPUs
        reservations:
          memory: 1G           # reservado 1 GB
          cpus: '1.5'
```

**Impacto:** 
- Evita OOM kill silencioso
- Contenedor recibe `MemoryError` en lugar de SIGKILL
- Permite debugging adecuado

---

### Mejora 3: Cachear instancia de PaddleOCR entre requests — ✅ YA HECHO

Actualmente el código ya hace esto con `_paddle_ocr_instance` global.

**Verificación:** Primera llamada (~30s), segunda llamada (~25s) = reutilización funciona.

---

### Mejora 4: Executar OCR en proceso separado con timeout — ⚠️ ROBUSTO

**Problema:** Si PaddleOCR cuelga, bloquea el request indefinidamente

**Solución:** Usar `asyncio.wait_for()` con timeout:
```python
async def subir_documento_service(...):
    ...
    try:
        data = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, partial(procesar, ruta_archivo=tmp_path, guardar_txt=False)
            ),
            timeout=60.0  # máximo 60 segundos
        )
    except asyncio.TimeoutError:
        logger.error("OCR timeout después de 60s")
        return documento_response  # devuelve documento sin extracciones
    except Exception as e:
        logger.exception("Error en OCR")
        return documento_response
```

**Impacto:** Previene requests colgados indefinidamente

---

### Mejora 5: Implementar chunk streaming para archivos grandes — 📦 ESCALABILIDAD

**Problema:** Archivos > 5MB llenos de páginas = memory spike

**Solución:** Procesar PDFs página por página:
```python
def procesar_paginado(ruta_archivo: Path, max_paginas: int = 10) -> dict:
    """Procesa solo las primeras N páginas de un PDF para evitar OOM"""
    
    with fitz.open(str(ruta_archivo)) as doc:
        paginas_a_procesar = min(len(doc), max_paginas)
        
        for num_page in range(paginas_a_procesar):
            # Procesa una página a la vez
            pagina = doc[num_page]
            # ... OCR
            # ... acumula resultados
```

**Impacto:** 
- Documentos de 100+ páginas sin OOM
- Primeras N páginas suelen tener datos suficientes (invoice siempre al inicio)

---

### Mejora 6: Usar endpoint async para background tasks — 🚀 RESPONSABILIDAD

**Problema:** Si background task (`ingestar_cfdi_organizacion`) falla silenciosamente

**Solución:** Agregar endpoint para monitorear estado de tareas:
```python
@router.get("/v1/documentos/{document_id}/status")
async def document_status(document_id: str):
    """Check status of background ingestion"""
    # Query tabla `documento_ingestion_log`
    return {
        "status": "pendiente|procesando|completado|error",
        "extraccion_count": 5,
        "vectores_indexados": 150,
        "error": None or "mensaje de error"
    }
```

---

### Mejora 7: Paralelizar requests de Mistral — ⏱️ MINOR

**Problema:** Si hay múltiples CFDIs en una imagen, se estructuran secuencialmente

**Solución:** Usar `asyncio.gather()` para estructurar en paralelo:
```python
async def _estructurar_con_mistral_batch(cfdis_textos: list[str]) -> list[dict]:
    """Estructura múltiples CFDIs en paralelo"""
    tasks = [
        asyncio.to_thread(_llamar_mistral, client, prompt)
        for prompt in prompts
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Impacto:** ~5% más rápido si hay 3+ CFDIs en la imagen

---

## 🎯 Recomendaciones de prioridad

| Mejora | Impacto | Effort | Prioridad |
|--------|--------|--------|-----------|
| 1. GPU para PaddleOCR | **6-10x más rápido** | Alto (infraestructura) | 🔴 CRÍTICA |
| 2. Límites de memoria | Previene OOM | Muy Bajo | 🔴 CRÍTICA |
| 3. Timeout en OCR | Robustez | Bajo | 🟠 ALTA |
| 4. Valores por defecto en extracciones | Evita 500 errors | Muy Bajo | 🟠 ALTA |
| 5. Procesar paginado | Maneja archivos grandes | Medio | 🟡 MEDIA |
| 6. Endpoint de status | Monitoreo | Medio | 🟡 MEDIA |
| 7. Paralelizar Mistral | +5% speed | Bajo | 🟢 BAJA |

---

## 📋 Checklist para implementar

- [ ] Agregar límites de memoria a docker-compose
- [ ] Agregar timeout a PaddleOCR en `run_in_executor()`
- [ ] Proveer valores por defecto en `documents_service.py` (campos NOT NULL)
- [ ] Agregar soporte GPU en Dockerfile (compilar PaddleOCR con CUDA)
- [ ] Configurar `docker-compose.yml` con runtime nvidia
- [ ] Agregar endpoint GET `/v1/documentos/{id}/status` para monitoreo
- [ ] Implementar procesar_paginado() para PDFs grandes (>100 páginas)
- [ ] Agregar logging detallado de memoria en lifespan

---

## 🧪 Cómo testear las mejoras

### Test 1: Validar que OCR no cuelga
```bash
# Subir imagen de 500 KB, verificar respuesta en <60s
curl -X POST http://localhost:8000/v1/documentos/cargar \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@cfdi_ejemplo.jpg"
```

### Test 2: Monitorear memoria durante ingesta
```bash
# Terminal 1: Monitoreo
watch -n 0.5 'docker stats visir-backend-api-1 --no-stream'

# Terminal 2: Upload múltiples archivos
for i in {1..5}; do
  curl -X POST ... -F "file=@cfdi_$i.jpg"
  sleep 5
done
```

### Test 3: Stress test con archivos grandes
```bash
# Crear PDF de 100+ páginas (simular peor caso)
# Verificar que no dispara OOM

# O usar un CFDI real de 50 MB escaneado
```

---

## 📌 Notas

- **Flujo actual es robusto:** OCR + Mistral + background tasks funcionan correctamente
- **Problema principal:** Latencia (42-55s) + consumo de RAM sin límite
- **OOM hace 9 horas:** Probablemente ingesta de normativa + múltiples uploads simultáneos
- **Recomendación inmediata:** Agregar límites de memoria en docker-compose + timeout en OCR

