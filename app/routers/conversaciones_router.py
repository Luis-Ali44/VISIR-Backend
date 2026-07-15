import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import get_user
from app.repositories.conversaciones_repository import (
    actualizar_contexto,
    actualizar_contexto_con_turno,
    construir_contexto_inicial,
    crear_sesion,
    eliminar_sesion,
    guardar_turno,
    listar_sesiones,
    obtener_sesion,
    obtener_turnos_por_sesion,
)
from app.schemas.conversacion import (
    ContinuarConversacionRequest,
    CrearConversacionRequest,
    FuenteCitadaConversacion,
    SesionContinuadaResponse,
    SesionCreadaResponse,
    SesionDetalleResponse,
    SesionListaItem,
    TurnoResponse,
)
from app.schemas.user_schema import UsuarioActual
from app.services.rag_service import RAGServiceLangGraph

router = APIRouter(prefix="/v1/conversaciones", tags=["conversaciones"])

_DEFAULT_COVERAGE_THRESHOLD = 0.35
_COVERAGE_THRESHOLD = float(os.getenv("RAG_COVERAGE_THRESHOLD", str(_DEFAULT_COVERAGE_THRESHOLD)))


def get_rag_service(request: Request) -> RAGServiceLangGraph:
    service = getattr(request.app.state, "rag_service", None)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAGService no inicializado en la aplicacion",
        )
    return service


def _calcular_cobertura(fuentes: list[dict]) -> bool:
    return any(f.get("similarity", 0.0) >= _COVERAGE_THRESHOLD for f in fuentes)


def _construir_fuentes(fuentes_raw: list[dict]) -> list[FuenteCitadaConversacion]:
    resultado = []
    for f in fuentes_raw:
        try:
            resultado.append(
                FuenteCitadaConversacion(
                    filename=f.get("filename", ""),
                    chunk_id=f.get("chunk_id", ""),
                    section=f.get("section", "sin_seccion"),
                    page_number=f.get("page_number"),
                    similarity=round(float(f.get("similarity", 0.0)), 4),
                    origen=f.get("origen", "ley"),
                )
            )
        except Exception:
            continue
    return resultado


def _contexto_a_historial(contexto: dict) -> list[dict[str, str]]:
    if not contexto:
        return []
    texto = json.dumps(contexto, ensure_ascii=False)
    return [{"rol": "asistente", "mensaje": f"Resumen de la conversacion: {texto}"}]


@router.post("", response_model=SesionCreadaResponse, status_code=status.HTTP_201_CREATED)
def crear_conversacion(
    body: CrearConversacionRequest,
    usuario: UsuarioActual = Depends(get_user),
    rag_service: RAGServiceLangGraph = Depends(get_rag_service),
) -> SesionCreadaResponse:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no esta vinculado a ninguna organizacion.",
        )

    sesion_id = crear_sesion(usuario.id, usuario.id_organizacion)
    if not sesion_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear la sesion de conversacion.",
        )

    try:
        respuesta, ruta, metadata = rag_service.ejecutar_consulta(
            pregunta=body.pregunta,
            usuario_id=usuario.id,
            id_organizacion=usuario.id_organizacion,
            top_k=body.top_k,
            historial=[],
        )

        guardar_turno(
            id_usuario=usuario.id,
            id_organizacion=usuario.id_organizacion,
            mensaje_usuario=body.pregunta,
            respuesta_sistema=respuesta,
            sesion_id=sesion_id,
        )

        contexto = construir_contexto_inicial(body.pregunta, respuesta, metadata)
        actualizar_contexto(sesion_id, usuario.id_organizacion, contexto)

        fuentes_raw: list[dict] = metadata.get("fuentes_recuperadas", [])
        fuentes_citadas = _construir_fuentes(fuentes_raw)
        tiene_cobertura_llm = metadata.get("tiene_cobertura")
        tiene_cobertura = (
            tiene_cobertura_llm
            if isinstance(tiene_cobertura_llm, bool)
            else _calcular_cobertura(fuentes_raw)
        )

        return SesionCreadaResponse(
            sesion_id=sesion_id,
            respuesta=respuesta,
            ruta_ejecutada=ruta,
            tiene_cobertura=tiene_cobertura,
            confianza_score=metadata.get("confianza_score"),
            accion_seleccionada=metadata.get("accion_seleccionada"),
            fuentes_citadas=fuentes_citadas,
            latencias_ms={"grafo_total": metadata["latencia_ms"]},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la consulta: {e!s}",
        )


@router.get("", response_model=list[SesionListaItem])
def listar_conversaciones(
    usuario: UsuarioActual = Depends(get_user),
) -> list[SesionListaItem]:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no esta vinculado a ninguna organizacion.",
        )

    sesiones = listar_sesiones(usuario.id, usuario.id_organizacion)
    return [
        SesionListaItem(
            sesion_id=s["sesion_id"],
            ultimo_mensaje=s.get("ultimo_mensaje"),
            created_at=s["created_at"],
            num_turnos=s["num_turnos"],
        )
        for s in sesiones
    ]


@router.get("/{sesion_id}", response_model=SesionDetalleResponse)
def obtener_conversacion(
    sesion_id: str,
    usuario: UsuarioActual = Depends(get_user),
) -> SesionDetalleResponse:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no esta vinculado a ninguna organizacion.",
        )

    sesion = obtener_sesion(sesion_id, usuario.id_organizacion)
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesion no encontrada.",
        )

    turnos = obtener_turnos_por_sesion(sesion_id, usuario.id_organizacion)
    return SesionDetalleResponse(
        sesion_id=sesion_id,
        contexto=sesion.get("contexto"),
        turnos=[
            TurnoResponse(
                id=str(t.get("id", "")),
                mensaje_usuario=t.get("mensaje_usuario", ""),
                respuesta_sistema=t.get("respuesta_sistema", ""),
                created_at=t["created_at"],
            )
            for t in turnos
        ],
    )


@router.put("/{sesion_id}", response_model=SesionContinuadaResponse)
def continuar_conversacion(
    sesion_id: str,
    body: ContinuarConversacionRequest,
    usuario: UsuarioActual = Depends(get_user),
    rag_service: RAGServiceLangGraph = Depends(get_rag_service),
) -> SesionContinuadaResponse:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no esta vinculado a ninguna organizacion.",
        )

    sesion = obtener_sesion(sesion_id, usuario.id_organizacion)
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesion no encontrada.",
        )

    try:
        contexto_actual = sesion.get("contexto") or {}
        historial = _contexto_a_historial(contexto_actual)

        respuesta, ruta, metadata = rag_service.ejecutar_consulta(
            pregunta=body.pregunta,
            usuario_id=usuario.id,
            id_organizacion=usuario.id_organizacion,
            top_k=body.top_k,
            historial=historial,
        )

        guardar_turno(
            id_usuario=usuario.id,
            id_organizacion=usuario.id_organizacion,
            mensaje_usuario=body.pregunta,
            respuesta_sistema=respuesta,
            sesion_id=sesion_id,
        )

        contexto_nuevo = actualizar_contexto_con_turno(
            contexto_actual, body.pregunta, respuesta, metadata
        )
        actualizar_contexto(sesion_id, usuario.id_organizacion, contexto_nuevo)

        fuentes_raw: list[dict] = metadata.get("fuentes_recuperadas", [])
        fuentes_citadas = _construir_fuentes(fuentes_raw)
        tiene_cobertura_llm = metadata.get("tiene_cobertura")
        tiene_cobertura = (
            tiene_cobertura_llm
            if isinstance(tiene_cobertura_llm, bool)
            else _calcular_cobertura(fuentes_raw)
        )

        return SesionContinuadaResponse(
            sesion_id=sesion_id,
            respuesta=respuesta,
            ruta_ejecutada=ruta,
            tiene_cobertura=tiene_cobertura,
            confianza_score=metadata.get("confianza_score"),
            accion_seleccionada=metadata.get("accion_seleccionada"),
            fuentes_citadas=fuentes_citadas,
            latencias_ms={"grafo_total": metadata["latencia_ms"]},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la consulta: {e!s}",
        )


@router.delete("/{sesion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_conversacion(
    sesion_id: str,
    usuario: UsuarioActual = Depends(get_user),
) -> None:
    if not usuario.id_organizacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario actual no esta vinculado a ninguna organizacion.",
        )

    ok = eliminar_sesion(sesion_id, usuario.id_organizacion)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesion no encontrada o no se pudo eliminar.",
        )
