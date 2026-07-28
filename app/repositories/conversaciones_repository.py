import json
import logging
from typing import Any

from app.core.database import ExecCtx
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

MAX_HISTORIAL = 6


class ConversacionesRepository(BaseRepository):
    def __init__(self, ctx: ExecCtx):
        super().__init__(ctx)

    def crear_sesion(self, id_usuario: str, id_organizacion: str) -> str | None:
        payload = {
            "id_usuario": id_usuario,
            "id_organizacion": id_organizacion,
            "contexto": {
                "palabras_clave": [],
                "periodos_mencionados": [],
                "intercambios": [],
                "turnos_totales": 0,
            },
        }
        try:
            response = self.scoped("sesiones_conversacion").insert(payload).execute()
            data = response.data
            if data and isinstance(data, list) and len(data) > 0:
                return str(data[0].get("id", ""))
        except Exception as exc:
            logger.error("Error al crear sesion: %s", exc)
        return None

    def listar_sesiones(self, id_usuario: str, id_organizacion: str) -> list[dict[str, Any]]:
        try:
            response = (
                self.scoped("sesiones_conversacion")
                .select("id, created_at, contexto->>'turnos_totales' as num_turnos_str, contexto")
                .eq("id_usuario", id_usuario)
                .eq("id_organizacion", id_organizacion)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            rows = response.data if response.data else []
            resultado = []
            for row in rows:
                contexto_raw = row.get("contexto")
                contexto = {}
                if isinstance(contexto_raw, str):
                    try:
                        contexto = json.loads(contexto_raw)
                    except (json.JSONDecodeError, TypeError):
                        contexto = {}
                elif isinstance(contexto_raw, dict):
                    contexto = contexto_raw
                intercambios = contexto.get("intercambios", [])
                ultimo = intercambios[-1] if intercambios else None
                ultimo_msg = None
                if ultimo:
                    ultimo_msg = ultimo.get("usuario", "")[:120]
                resultado.append(
                    {
                        "sesion_id": str(row.get("id", "")),
                        "ultimo_mensaje": ultimo_msg,
                        "created_at": row.get("created_at"),
                        "num_turnos": contexto.get("turnos_totales", 0),
                    }
                )
            return resultado
        except Exception as exc:
            logger.error("Error al listar sesiones: %s", exc)
            return []

    def obtener_sesion(self, sesion_id: str, id_organizacion: str) -> dict[str, Any] | None:
        try:
            response = (
                self.scoped("sesiones_conversacion")
                .select("*")
                .eq("id", sesion_id)
                .eq("id_organizacion", id_organizacion)
                .maybe_single()
                .execute()
            )
            if response.data and isinstance(response.data, dict):
                row = dict(response.data)
                contexto_raw = row.get("contexto")
                if isinstance(contexto_raw, str):
                    try:
                        row["contexto"] = json.loads(contexto_raw)
                    except (json.JSONDecodeError, TypeError):
                        row["contexto"] = {}
                return row
            return None
        except Exception as exc:
            logger.error("Error al obtener sesion %s: %s", sesion_id, exc)
            return None

    def obtener_turnos_por_sesion(
        self, sesion_id: str, id_organizacion: str
    ) -> list[dict[str, Any]]:
        try:
            response = (
                self.scoped("conversaciones")
                .select("id, mensaje_usuario, respuesta_sistema, created_at")
                .eq("sesion_id", sesion_id)
                .eq("id_organizacion", id_organizacion)
                .order("created_at", asc=True)
                .execute()
            )
            return list(response.data) if response.data else []
        except Exception as exc:
            logger.error("Error al obtener turnos de sesion %s: %s", sesion_id, exc)
            return []

    def eliminar_sesion(self, sesion_id: str, id_organizacion: str) -> bool:
        try:
            self.scoped("conversaciones").delete().eq("sesion_id", sesion_id).eq(
                "id_organizacion", id_organizacion
            ).execute()
            response = (
                self.scoped("sesiones_conversacion")
                .delete()
                .eq("id", sesion_id)
                .eq("id_organizacion", id_organizacion)
                .execute()
            )
            return bool(response.data)
        except Exception as exc:
            logger.error("Error al eliminar sesion %s: %s", sesion_id, exc)
            return False

    def actualizar_contexto(
        self, sesion_id: str, id_organizacion: str, contexto: dict[str, Any]
    ) -> None:
        try:
            self.scoped("sesiones_conversacion").update({"contexto": contexto}).eq(
                "id", sesion_id
            ).eq("id_organizacion", id_organizacion).execute()
        except Exception as exc:
            logger.error("Error al actualizar contexto de sesion %s: %s", sesion_id, exc)

    def guardar_turno(
        self,
        id_usuario: str,
        id_organizacion: str,
        mensaje_usuario: str,
        respuesta_sistema: str,
        sesion_id: str | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {
            "id_usuario": id_usuario,
            "id_organizacion": id_organizacion,
            "mensaje_usuario": mensaje_usuario,
            "respuesta_sistema": respuesta_sistema,
        }
        if sesion_id is not None:
            payload["sesion_id"] = sesion_id
        try:
            response = self.scoped("conversaciones").insert(payload).execute()
            data = response.data
            if data and isinstance(data, list) and len(data) > 0:
                return str(data[0].get("id", ""))
        except Exception as exc:
            logger.error("Error al guardar turno en conversaciones: %s", exc)
        return None

    def obtener_historial(
        self,
        id_usuario: str,
        id_organizacion: str,
        limite: int = MAX_HISTORIAL,
        sesion_id: str | None = None,
    ) -> list[dict[str, str]]:
        try:
            query = (
                self.scoped("conversaciones")
                .select("mensaje_usuario,respuesta_sistema")
                .eq("id_usuario", id_usuario)
                .eq("id_organizacion", id_organizacion)
            )
            if sesion_id is not None:
                query = query.eq("sesion_id", sesion_id)
            response = query.order("created_at", desc=True).limit(limite).execute()
            rows = response.data if response.data else []
            historial: list[dict[str, str]] = []
            for row in reversed(rows):
                if row.get("mensaje_usuario"):
                    historial.append({"rol": "usuario", "mensaje": row["mensaje_usuario"]})
                if row.get("respuesta_sistema"):
                    historial.append({"rol": "asistente", "mensaje": row["respuesta_sistema"]})
            return historial
        except Exception as exc:
            logger.error("Error al obtener historial de conversaciones: %s", exc)
            return []

    def extraer_keywords(self, pregunta: str) -> list[str]:
        from app.services.confidence_features import detectar_tipo_consulta

        palabras = set(pregunta.lower().split())
        terminos_fiscales = {
            "iva",
            "isr",
            "cfdi",
            "sat",
            "rfc",
            "deduccion",
            "deducciones",
            "gasto",
            "gastos",
            "factura",
            "facturas",
            "ingreso",
            "ingresos",
            "impuesto",
            "impuestos",
            "pago",
            "pagos",
            "declaracion",
            "proveedor",
            "proveedores",
            "comprobante",
            "comprobantes",
            "nomina",
            "nominas",
            "retencion",
            "retenciones",
        }
        encontradas = palabras & terminos_fiscales
        tipo = detectar_tipo_consulta(pregunta)
        if tipo.get("detectado") and isinstance(tipo.get("valor"), list):
            encontradas.update(t.lower() for t in tipo["valor"])
        return sorted(encontradas)

    def construir_contexto_inicial(
        self, pregunta: str, respuesta: str, metadatos: dict[str, Any]
    ) -> dict[str, Any]:
        from app.services.confidence_features import detectar_periodo

        periodo = detectar_periodo(pregunta)
        periodos = []
        if periodo.get("detectado") and periodo.get("valor"):
            periodos.append(str(periodo["valor"]))

        return {
            "palabras_clave": self.extraer_keywords(pregunta),
            "periodos_mencionados": periodos,
            "intercambios": [
                {
                    "usuario": pregunta[:300],
                    "asistente": respuesta[:500],
                    "confianza": metadatos.get("confianza_score"),
                }
            ],
            "turnos_totales": 1,
        }

    def actualizar_contexto_con_turno(
        self,
        contexto_actual: dict[str, Any],
        pregunta: str,
        respuesta: str,
        metadatos: dict[str, Any],
    ) -> dict[str, Any]:
        from app.services.confidence_features import detectar_periodo

        contexto = dict(contexto_actual)
        intercambios = list(contexto.get("intercambios", []))
        intercambios.append(
            {
                "usuario": pregunta[:300],
                "asistente": respuesta[:500],
                "confianza": metadatos.get("confianza_score"),
            }
        )
        if len(intercambios) > 10:
            intercambios = intercambios[-10:]

        palabras = set(contexto.get("palabras_clave", []))
        nuevas = self.extraer_keywords(pregunta)
        palabras.update(nuevas)
        contexto["palabras_clave"] = sorted(palabras)

        periodo = detectar_periodo(pregunta)
        if periodo.get("detectado") and periodo.get("valor"):
            periodos = set(contexto.get("periodos_mencionados", []))
            periodos.add(str(periodo["valor"]))
            contexto["periodos_mencionados"] = sorted(periodos)

        contexto["intercambios"] = intercambios
        contexto["turnos_totales"] = contexto.get("turnos_totales", 0) + 1
        return contexto
