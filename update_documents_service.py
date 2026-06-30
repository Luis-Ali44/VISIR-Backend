#!/usr/bin/env python
"""Update documents_service.py with timeout and default values."""

content = open('app/services/documents_service.py', 'r', encoding='utf-8').read()

# 1. Add datetime import
if 'from datetime import datetime' not in content:
    content = content.replace(
        'import asyncio\nimport logging\nimport tempfile\nimport traceback',
        'import asyncio\nimport logging\nimport tempfile\nimport traceback\nfrom datetime import datetime'
    )
    print("✅ Import datetime added")

# 2. Add timeout to OCR executor
old_block = """        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, partial(procesar, ruta_archivo=tmp_path, guardar_txt=False)
            )
        except Exception:
            logger.exception(
                "No se pudo procesar el archivo con OCR/parser de CFDI",
                extra={"id_documento": id_documento, "archivo": archivo.filename},
            )
            return documento_response"""

new_block = """        try:
            data = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, partial(procesar, ruta_archivo=tmp_path, guardar_txt=False)
                ),
                timeout=90.0  # máximo 90 segundos para OCR + Mistral
            )
        except asyncio.TimeoutError:
            logger.error(
                "OCR timeout después de 90 segundos",
                extra={"id_documento": id_documento, "archivo": archivo.filename},
            )
            return documento_response
        except Exception:
            logger.exception(
                "No se pudo procesar el archivo con OCR/parser de CFDI",
                extra={"id_documento": id_documento, "archivo": archivo.filename},
            )
            return documento_response"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Timeout added to OCR executor")

# 3. Add default values for NOT NULL columns
old_rows = """    rows: list[dict[str, Any]] = []
    for datos in cfdis_datos:
        forma_pago = datos.get("forma_pago")
        fecha_emision_raw = datos.get("fecha_emision")
        tipo_comprobante_raw = datos.get("tipo_de_comprobante")

        rows.append(
            {
                "folio_fiscal": datos.get("folio_fiscal"),
                "total": datos.get("total"),
                "metadatos": datos,
                "fecha_emision": parse_fecha(str(fecha_emision_raw)).isoformat()
                if fecha_emision_raw is not None
                else None,
                "tipo_comprobante": map_tipo_comprobante(str(tipo_comprobante_raw))
                if tipo_comprobante_raw is not None
                else None,
                "metodo_pago": datos.get("metodo_pago"),
                "estado": "procesado",
                "rfc_emisor": datos.get("emisor", {}).get("RFC"),
                "nombre_emisor": datos.get("emisor", {}).get("nombre"),
                "rfc_receptor": datos.get("receptor", {}).get("RFC"),
                "nombre_receptor": datos.get("receptor", {}).get("nombre"),
                "id_documento": id_documento,
                "id_organizacion": id_organizacion,
                "forma_pago": get_nombre_forma_pago(str(forma_pago)) if forma_pago else None,
            }
        )"""

new_rows = """    rows: list[dict[str, Any]] = []
    for datos in cfdis_datos:
        forma_pago = datos.get("forma_pago")
        fecha_emision_raw = datos.get("fecha_emision")
        tipo_comprobante_raw = datos.get("tipo_de_comprobante")

        # Parse fecha — fallback a now() si el LLM no extrajo una fecha válida
        try:
            fecha_iso: str | None = (
                parse_fecha(str(fecha_emision_raw)).isoformat()
                if fecha_emision_raw is not None
                else None
            )
        except ValueError:
            fecha_iso = None

        emisor = datos.get("emisor") or {}
        receptor = datos.get("receptor") or {}

        rows.append(
            {
                # Columnas NOT NULL — proveer defaults seguros
                "folio_fiscal": datos.get("folio_fiscal") or "SIN-UUID",
                "total": float(datos.get("total") or 0.0),
                "metadatos": datos,
                "fecha_emision": fecha_iso or datetime.now().isoformat(),
                "tipo_comprobante": (
                    map_tipo_comprobante(str(tipo_comprobante_raw))
                    if tipo_comprobante_raw is not None
                    else None
                ) or "Ingreso",
                "metodo_pago": datos.get("metodo_pago") or "PUE",
                "estado": "procesado",
                "rfc_emisor": emisor.get("RFC") or "XAXX010101000",
                "nombre_emisor": emisor.get("nombre") or "Sin nombre",
                "rfc_receptor": receptor.get("RFC") or "XAXX010101000",
                "nombre_receptor": receptor.get("nombre") or "Sin nombre",
                "id_documento": id_documento,
                "id_organizacion": id_organizacion,
                "forma_pago": get_nombre_forma_pago(str(forma_pago)) if forma_pago else None,
            }
        )"""

if old_rows in content:
    content = content.replace(old_rows, new_rows)
    print("✅ Default values added for NOT NULL columns")

with open('app/services/documents_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ documents_service.py updated successfully!")
