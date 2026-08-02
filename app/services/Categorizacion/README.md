# Modelo de categorización de c_ClaveProdServ

Este módulo implementa la categorización de descripciones libres de conceptos en CFDIs a la clave SAT `c_ClaveProdServ`.

## Qué hace

El objetivo es sugerir la mejor clave de producto/servicio dentro del catálogo SAT usando una búsqueda semántica sobre embeddings.

La lógica se usa desde `app/services/Extraccion/pipeline.py` en la función `_categorizar_conceptos`, donde:
- se omite la categorización si la fuente es XML y el concepto ya trae `clave_prod_serv`
- se consulta el modelo solo para conceptos con descripción textual
- se guarda el resultado en los campos adicionales:
  - `clave_prod_serv_sugerida`
  - `categoria_confianza`
  - `categoria_fuente`

## Implementación actual

El código principal está en `app/services/Categorizacion/modelo.py`.

### Algoritmo

1. Carga un modelo `sentence-transformers` (`intfloat/multilingual-e5-small`) o ruta local si se configura.
2. Construye un contexto semántico para cada entrada usando la descripción del catálogo SAT.
3. Genera embeddings normalizados para el catálogo completo.
4. Convierte la descripción del concepto a un embedding y calcula similitud de coseno contra el catálogo.
5. Retorna las top-k claves ordenadas por score.
6. Solo acepta una sugerencia como válida si el score supera el umbral `UMBRAL_CONFIANZA = 0.80`.

### Artefactos de datos

El módulo utiliza estos archivos:
- `data/catalogo_prodserv_sat.json`: catálogo completo de claves SAT.
- `models/embeddings/catalogo_codigos.json`: lista de códigos guardados en caché.
- `models/embeddings/catalogo_embeddings.npy`: embeddings del catálogo guardados en caché.

Si el caché no existe, se genera automáticamente en el primer uso.

## API del módulo

La función pública principal es:

```python
from app.services.Categorizacion.modelo import categorizar_concepto

sugerencia = categorizar_concepto(descripcion)
```

Donde `sugerencia` es un objeto `SugerenciaCategoria` con los campos:
- `clave_prod_serv`: clave sugerida o `None` si la confianza es baja
- `descripcion_catalogo`: texto asociado en el catálogo SAT
- `confianza`: score de similitud de coseno
- `top_k`: lista de pares `(clave, descripción, score)`
- `categorizado`: booleano

## Uso dentro del pipeline de extracción

En `app/services/Extraccion/pipeline.py`, los conceptos extraídos por OCR o XML son procesados así:

- si la fuente es `xml` y existe `clave_prod_serv`, la clave original se mantiene.
- si la fuente es `ocr`, el modelo sugiere `clave_prod_serv_sugerida` y marca la confianza.

Los valores resultantes se agregan a la extracción como soporte adicional para la revisión o para decisiones posteriores.

## Dependencias

- `sentence-transformers`
- `numpy`

El repositorio también instala `torch` como dependencia transitiva de `sentence-transformers`.

## Limitaciones actuales

- La clasificación es semántica, no exacta. Si la descripción es ambigua, el sistema puede devolver `None`.
- El umbral fijo `0.80` puede requerir ajuste según la calidad de los datos.

## Notas prácticas

- Si agrega o actualiza el catálogo SAT, borre las cachés en `models/embeddings/` para regenerar embeddings.
- El módulo está pensado como sugerencia complementaria; la extracción principal de CFDI sigue dependiendo de validaciones XML/OCR.
