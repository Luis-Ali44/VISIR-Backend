import json
import logging
import os
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from app.repositories.extracciones_repositories import get_estadisticas_basicas
from app.schemas.consulta import DecisionEnrutamiento, VisirState
from app.services.confidence_features import (
    data_completeness as _data_completeness,
)
from app.services.confidence_features import (
    detectar_periodo as _detectar_periodo,
)
from app.services.confidence_features import (
    detectar_tipo_consulta as _detectar_tipo_consulta,
)
from app.services.confidence_features import (
    question_clarity as _question_clarity,
)
from app.services.confidence_features import (
    rag_coverage as _rag_coverage,
)
from app.services.confidence_features import (
    routing_certainty as _routing_certainty,
)
from app.services.confidence_scoring import ConfidenceScorer
from app.services.llm_cascade import (
    LLMCascadeRouter,
    cascada_desde_env,
    evaluar_complejidad,
)
from app.services.routing_logic import analizar_lexico
from rag.chain import ChainResult, FiscalRAGChain, RespuestaLLM, format_context
from rag.config import RAGConfig, load_config_from_env
from rag.retriever import FiscalRAGRetriever, OrgRAGRetriever, RetrievalContext

logger = logging.getLogger(__name__)

PROMPT_LLM_ROUTER = """Eres el enrutador de IA de alta precisión para el sistema fiscal mexicano VISIR.
Tu trabajo es clasificar la consulta del contribuyente cuando las reglas léxicas fallan.

Pregunta del usuario: "{pregunta}"

Debes clasificar estrictamente en una de estas tres opciones:
- NORMATIVA: Dudas teóricas sobre leyes del SAT, reglamentos o esquemas de impuestos.
- CFDI_PROPIOS: Consultas sobre los números de sus facturas, dinero gastado, montos o proveedores del negocio.
- HIBRIDO: Preguntas que requieren verificar sus datos de facturación REALES y cruzarlos con las leyes del SAT.
"""


class RAGServiceLangGraph:
    def __init__(
        self,
        chain: FiscalRAGChain,
        retriever: FiscalRAGRetriever,
        llm_api_key: str,
        llm_base_url: str,
        llm_model: str,
        rag_config: RAGConfig | None = None,
        cascada: LLMCascadeRouter | None = None,
    ) -> None:
        self.chain = chain
        self.retriever = retriever

        config = rag_config or load_config_from_env()
        self.org_retriever = OrgRAGRetriever(config)

        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model

        self.router_llm = ChatOpenAI(
            model=llm_model, temperature=0, api_key=llm_api_key, base_url=llm_base_url
        ).with_structured_output(DecisionEnrutamiento)

        self.cascada = cascada or cascada_desde_env()

        modelo_path = os.getenv("MODELO_CONFIANZA_PATH", "")
        self.scorer = ConfidenceScorer(modelo_path)

        self.grafo = self._construir_grafo()

    def _crear_contextos(self, state: VisirState) -> list[RetrievalContext]:
        ctx = []
        for f in state.get("fragmentos_leyes", []):
            if isinstance(f, dict):
                ctx.append(
                    RetrievalContext(
                        rank=0,
                        chunk_id=f.get("chunk_id", ""),
                        text=f.get("text", ""),
                        similarity=float(f.get("similarity", 0.0)),
                        doc_id="",
                        source="ley",
                        filename=f.get("filename", ""),
                        section=f.get("section", ""),
                        page_number=f.get("page_number"),
                    )
                )
        for f in state.get("datos_cfdi", {}).get("fragmentos_cfdis", []):
            if isinstance(f, dict):
                ctx.append(
                    RetrievalContext(
                        rank=0,
                        chunk_id=f.get("chunk_id", ""),
                        text=f.get("text", ""),
                        similarity=float(f.get("similarity", 0.0)),
                        doc_id="",
                        source="cfdi",
                        filename=f.get("filename", ""),
                        section=f.get("section", ""),
                        page_number=f.get("page_number"),
                    )
                )
        return ctx

    def _invocar_con_esquema(
        self,
        mensajes: list,
        temperature: float,
        complejidad: float,
        id_organizacion: str | None = None,
    ) -> ChainResult:
        resultado = self.cascada.invocar(
            mensajes=mensajes,
            schema=RespuestaLLM,
            temperature=temperature,
            complejidad=complejidad,
            id_organizacion=id_organizacion,
        )
        respuesta: RespuestaLLM = resultado.texto_esquema
        return ChainResult(
            texto=respuesta.respuesta,
            tiene_cobertura=respuesta.tiene_cobertura,
            fuentes_citadas=respuesta.fuentes_citadas,
            tokens_entrada=resultado.tokens_entrada,
            tokens_salida=resultado.tokens_salida,
        )

    def _formatear_historial(self, historial: list[dict[str, str]]) -> str:
        if not historial:
            return ""
        partes = ["Historial de la conversación:"]
        for turno in historial[-6:]:
            rol = turno.get("rol", "desconocido")
            mensaje = turno.get("mensaje", "")
            etiqueta = "Usuario" if rol == "usuario" else "Asistente"
            partes.append(f"{etiqueta}: {mensaje}")
        partes.append("---")
        return "\n".join(partes)

    def _nodo_analisis_lexico(self, state: VisirState) -> dict[str, Any]:

        return analizar_lexico(state["pregunta"])

    def _nodo_validacion_llm(self, state: VisirState) -> dict[str, Any]:

        prompt = ChatPromptTemplate.from_messages([("system", PROMPT_LLM_ROUTER)])
        chain_router = prompt | self.router_llm

        decision: DecisionEnrutamiento = chain_router.invoke({"pregunta": state["pregunta"]})
        return {"ruta_seleccionada": decision.ruta, "decision_enrutamiento": decision}

    def _nodo_recuperar_leyes(self, state: VisirState) -> dict[str, Any]:
        fragmentos = self.retriever.retrieve(query=state["pregunta"], top_k=state["top_k"])
        fragmentos_dict = [
            {
                "filename": f.filename,
                "chunk_id": f.chunk_id,
                "text": f.text,
                "section": f.section,
                "page_number": f.page_number,
                "similarity": getattr(f, "similarity", 0.9),
            }
            for f in fragmentos
        ]
        return {"fragmentos_leyes": fragmentos_dict}

    def _nodo_recuperar_cfdis(self, state: VisirState) -> dict[str, Any]:
        fragmentos = self.org_retriever.retrieve(
            query=state["pregunta"],
            id_organizacion=state["id_organizacion"],
            top_k=state["top_k"],
            tipo_documento="cfdi",
        )

        fragmentos_dict = [
            {
                "filename": f.filename,
                "chunk_id": f.chunk_id,
                "text": f.text,
                "section": f.section,
                "page_number": f.page_number,
                "similarity": f.similarity,
            }
            for f in fragmentos
        ]

        stats = get_estadisticas_basicas(id_organizacion=state["id_organizacion"])

        return {
            "datos_cfdi": {"fragmentos_cfdis": fragmentos_dict},
            "estadisticas_cfdi": stats,
        }

    def _nodo_respuesta_normativa(self, state: VisirState) -> dict[str, Any]:
        contextos = self._crear_contextos(state)
        historial_txt = self._formatear_historial(state.get("historial", []))
        sys_msg = "Eres un asistente fiscal especializado en la normativa del SAT de México. Responde ÚNICAMENTE con información presente en el contexto proporcionado."
        if historial_txt:
            sys_msg = f"{historial_txt}\n\n{sys_msg}"
        mensajes = [
            ("system", sys_msg),
            (
                "human",
                f"Contexto fiscal recuperado:\n{format_context(contextos)}\n\nPregunta del usuario: {state['pregunta']}",
            ),
        ]
        complejidad = evaluar_complejidad(
            state["pregunta"], state["ruta_seleccionada"], len(contextos)
        )
        result = self._invocar_con_esquema(
            mensajes,
            temperature=0.1,
            complejidad=complejidad,
            id_organizacion=state.get("id_organizacion"),
        )
        respuesta = result.texto
        if state.get("accion_seleccionada") == "responder_con_advertencia":
            respuesta = (
                "⚠️ **Respuesta con confianza parcial** — algunos supuestos "
                "(período, tipo de consulta, ambigüedad) fueron inferidos.\n\n" + respuesta
            )
        return {
            "respuesta_final": respuesta,
            "tokens_entrada": result.tokens_entrada,
            "tokens_salida": result.tokens_salida,
            "tiene_cobertura": result.tiene_cobertura,
        }

    def _nodo_respuesta_cfdis(self, state: VisirState) -> dict[str, Any]:
        contextos = self._crear_contextos(state)
        fragmentos_cfdis = state["datos_cfdi"].get("fragmentos_cfdis", [])

        if fragmentos_cfdis:
            contexto_txt = format_context(contextos)
            prompt = (
                f"Contexto de CFDIs del negocio:\n{contexto_txt}\n\nPregunta: {state['pregunta']}"
            )
        else:
            prompt = (
                f"Genera un informe analítico ejecutivo con base en estos datos numéricos reales del negocio:\n"
                f"{json.dumps(state['estadisticas_cfdi'])}\n\n"
                f"Pregunta: {state['pregunta']}"
            )

        historial_txt = self._formatear_historial(state.get("historial", []))
        sys_msg = "Eres un asistente fiscal especializado en análisis de CFDIs. Genera informes ejecutivos basados exclusivamente en los datos proporcionados."
        if historial_txt:
            sys_msg = f"{historial_txt}\n\n{sys_msg}"
        mensajes = [
            ("system", sys_msg),
            ("human", prompt),
        ]
        complejidad = evaluar_complejidad(
            state["pregunta"], state["ruta_seleccionada"], len(contextos)
        )
        result = self._invocar_con_esquema(
            mensajes,
            temperature=0.0,
            complejidad=complejidad,
            id_organizacion=state.get("id_organizacion"),
        )
        respuesta = result.texto
        if state.get("accion_seleccionada") == "responder_con_advertencia":
            respuesta = (
                "⚠️ **Respuesta con confianza parcial** — algunos supuestos "
                "(período, tipo de consulta, ambigüedad) fueron inferidos.\n\n" + respuesta
            )
        return {
            "respuesta_final": respuesta,
            "tokens_entrada": result.tokens_entrada,
            "tokens_salida": result.tokens_salida,
            "tiene_cobertura": result.tiene_cobertura,
        }

    def _nodo_sintesis_hibrida(self, state: VisirState) -> dict[str, Any]:
        contextos = self._crear_contextos(state)
        contexto_txt = format_context(contextos)

        fragmentos_cfdis = state["datos_cfdi"].get("fragmentos_cfdis", [])
        cfdis_contexto = ""
        if fragmentos_cfdis:
            cfdis_contexto = "\n".join(
                [f"[CFDI {i + 1}]: {f['text']}" for i, f in enumerate(fragmentos_cfdis)]
            )
        else:
            cfdis_contexto = json.dumps(state["estadisticas_cfdi"])

        prompt = (
            f"Leyes del SAT asociadas:\n{contexto_txt}\n\n"
            f"Datos del contribuyente:\n{cfdis_contexto}\n\n"
            f"Pregunta: {state['pregunta']}"
        )
        historial_txt = self._formatear_historial(state.get("historial", []))
        sys_msg = "Eres un asistente fiscal que cruza datos de facturación del contribuyente con las leyes fiscales mexicanas vigentes. Responde basándote exclusivamente en ambos contextos."
        if historial_txt:
            sys_msg = f"{historial_txt}\n\n{sys_msg}"
        mensajes = [
            ("system", sys_msg),
            ("human", prompt),
        ]
        complejidad = evaluar_complejidad(
            state["pregunta"], state["ruta_seleccionada"], len(contextos)
        )
        result = self._invocar_con_esquema(
            mensajes,
            temperature=0.2,
            complejidad=complejidad,
            id_organizacion=state.get("id_organizacion"),
        )
        respuesta = result.texto
        if state.get("accion_seleccionada") == "responder_con_advertencia":
            respuesta = (
                "⚠️ **Respuesta con confianza parcial** — algunos supuestos "
                "(período, tipo de consulta, ambigüedad) fueron inferidos.\n\n" + respuesta
            )
        return {
            "respuesta_final": respuesta,
            "tokens_entrada": result.tokens_entrada,
            "tokens_salida": result.tokens_salida,
            "tiene_cobertura": result.tiene_cobertura,
        }

    def _nodo_decidir_accion(self, state: VisirState) -> dict[str, Any]:
        pregunta = state["pregunta"]
        fragmentos_leyes = state.get("fragmentos_leyes", [])
        datos_cfdi = state.get("datos_cfdi", {})
        fragmentos_cfdis = (
            datos_cfdi.get("fragmentos_cfdis", []) if isinstance(datos_cfdi, dict) else []
        )

        fuentes_todas = [f for f in fragmentos_leyes if isinstance(f, dict)]
        fuentes_todas.extend(f for f in fragmentos_cfdis if isinstance(f, dict))

        periodo = _detectar_periodo(pregunta)
        tipo = _detectar_tipo_consulta(pregunta)
        n_total = len(fuentes_todas)
        tiene_contexto_previo = bool(state.get("historial", []))

        features = {
            "rag_coverage": _rag_coverage(fuentes_todas),
            "routing_certainty": _routing_certainty(state.get("palabras_clave_detectadas", [])),
            "question_clarity": _question_clarity(pregunta, tiene_contexto_previo),
            "data_completeness": _data_completeness(n_total, periodo["detectado"]),
            "campo_periodo_faltante": 0.0 if periodo["detectado"] else 1.0,
            "campo_tipo_faltante": 0.0 if tipo["detectado"] else 1.0,
        }

        score = self.scorer.calcular(features)
        accion = self.scorer.decidir_accion(score)

        supuestos = []
        if features["campo_periodo_faltante"] > 0.5:
            supuestos.append("periodo_no_especificado")
        if features["campo_tipo_faltante"] > 0.5:
            supuestos.append("tipo_consulta_no_especificado")
        if features["question_clarity"] < 0.6:
            supuestos.append("pregunta_ambigua")
        if features["rag_coverage"] < 0.7:
            supuestos.append("cobertura_baja")

        logger.info(
            "Confianza=%.4f accion=%s cov=%.4f routing=%.4f clarity=%.4f completeness=%.4f "
            "periodo_falt=%.4f tipo_falt=%.4f tiene_ctx=%s supuestos=%s",
            score,
            accion,
            features["rag_coverage"],
            features["routing_certainty"],
            features["question_clarity"],
            features["data_completeness"],
            features["campo_periodo_faltante"],
            features["campo_tipo_faltante"],
            tiene_contexto_previo,
            supuestos or "ninguno",
        )

        return {"confianza_score": score, "accion_seleccionada": accion}

    def _nodo_preparar_pregunta(self, state: VisirState) -> dict[str, Any]:
        return {
            "respuesta_final": (
                "No tengo suficiente información para responder con confianza tu pregunta. "
                "¿Podrías proporcionar más detalles, como el tipo de comprobante fiscal, "
                "el período específico que consultas, o alguna referencia legal concreta?"
            )
        }

    def _destino_desde_accion(self, state: VisirState) -> str:
        accion = state.get("accion_seleccionada", "responder")
        ruta = state["ruta_seleccionada"]
        if accion == "preguntar":
            return "preparar_pregunta"
        if ruta == "HIBRIDO":
            return "sintesis_hibrida"
        if ruta == "CFDI_PROPIOS":
            return "responder_cfdis"
        return "responder_normativa"

    def _destino_por_ruta(self, state: VisirState) -> str | list[Send]:
        ruta = state["ruta_seleccionada"]
        if ruta == "HIBRIDO":
            return [Send("recuperar_leyes", state), Send("recuperar_cfdis", state)]
        elif ruta == "CFDI_PROPIOS":
            return "IR_A_CFDIS"
        return "IR_A_LEYES"

    def _enrutar_desde_lexico(self, state: VisirState) -> str | list[Send]:
        if state["confianza_lexica"] < 0.85:
            return "ESCALAR_A_LLM"
        return self._destino_por_ruta(state)

    def _post_recuperar_leyes(self, state: VisirState) -> str:

        return "decidir_accion"

    def _post_recuperar_cfdis(self, state: VisirState) -> str:

        return "decidir_accion"

    def _construir_grafo(self) -> Any:
        workflow = StateGraph(VisirState)

        workflow.add_node("analisis_lexico", self._nodo_analisis_lexico)
        workflow.add_node("validacion_llm", self._nodo_validacion_llm)
        workflow.add_node("recuperar_leyes", self._nodo_recuperar_leyes)
        workflow.add_node("recuperar_cfdis", self._nodo_recuperar_cfdis)
        workflow.add_node("responder_normativa", self._nodo_respuesta_normativa)
        workflow.add_node("responder_cfdis", self._nodo_respuesta_cfdis)
        workflow.add_node("sintesis_hibrida", self._nodo_sintesis_hibrida)
        workflow.add_node("decidir_accion", self._nodo_decidir_accion)
        workflow.add_node("preparar_pregunta", self._nodo_preparar_pregunta)

        workflow.set_entry_point("analisis_lexico")

        workflow.add_conditional_edges(
            "analisis_lexico",
            self._enrutar_desde_lexico,
            {
                "ESCALAR_A_LLM": "validacion_llm",
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            },
        )

        workflow.add_conditional_edges(
            "validacion_llm",
            self._destino_por_ruta,
            {
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            },
        )

        workflow.add_conditional_edges(
            "recuperar_leyes",
            self._post_recuperar_leyes,
            {"decidir_accion": "decidir_accion"},
        )
        workflow.add_conditional_edges(
            "recuperar_cfdis",
            self._post_recuperar_cfdis,
            {"decidir_accion": "decidir_accion"},
        )

        workflow.add_conditional_edges(
            "decidir_accion",
            self._destino_desde_accion,
            {
                "responder_normativa": "responder_normativa",
                "responder_cfdis": "responder_cfdis",
                "sintesis_hibrida": "sintesis_hibrida",
                "preparar_pregunta": "preparar_pregunta",
            },
        )

        workflow.add_edge("responder_normativa", END)
        workflow.add_edge("responder_cfdis", END)
        workflow.add_edge("sintesis_hibrida", END)
        workflow.add_edge("preparar_pregunta", END)

        return workflow.compile()

    def ejecutar_consulta(
        self,
        pregunta: str,
        usuario_id: str,
        id_organizacion: str,
        top_k: int = 5,
        historial: list[dict[str, str]] | None = None,
    ) -> tuple[str, str, dict[str, Any]]:
        t_inicio = time.perf_counter()

        estado_inicial: VisirState = {
            "pregunta": pregunta,
            "usuario_id": usuario_id,
            "id_organizacion": id_organizacion,
            "top_k": top_k,
            "ruta_seleccionada": None,
            "confianza_lexica": 0.0,
            "palabras_clave_detectadas": [],
            "decision_enrutamiento": None,
            "fragmentos_leyes": [],
            "datos_cfdi": {},
            "estadisticas_cfdi": {},
            "respuesta_final": None,
            "fuentes_recuperadas": [],
            "confianza_score": 0.0,
            "accion_seleccionada": None,
            "tokens_entrada": 0,
            "tokens_salida": 0,
            "tiene_cobertura": False,
            "historial": historial or [],
        }

        estado_final = self.grafo.invoke(estado_inicial)
        latencia = (time.perf_counter() - t_inicio) * 1000

        fuentes: list[dict] = []

        for f in estado_final.get("fragmentos_leyes", []):
            fuentes.append(
                {
                    "filename": f.get("filename", ""),
                    "chunk_id": f.get("chunk_id", ""),
                    "section": f.get("section", "sin_sección"),
                    "page_number": f.get("page_number"),
                    "similarity": round(float(f.get("similarity", 0.0)), 4),
                    "origen": "ley",
                    "text": f.get("text", ""),
                }
            )

        for f in estado_final.get("datos_cfdi", {}).get("fragmentos_cfdis", []):
            fuentes.append(
                {
                    "filename": f.get("filename", ""),
                    "chunk_id": f.get("chunk_id", ""),
                    "section": f.get("section", "sin_sección"),
                    "page_number": f.get("page_number"),
                    "similarity": round(float(f.get("similarity", 0.0)), 4),
                    "origen": "cfdi",
                    "text": f.get("text", ""),
                }
            )

        fuentes.sort(key=lambda x: x["similarity"], reverse=True)

        metadata = {
            "ruta_ejecutada": estado_final["ruta_seleccionada"],
            "confianza_lexica": estado_final["confianza_lexica"],
            "palabras_clave": estado_final["palabras_clave_detectadas"],
            "confianza_score": estado_final.get("confianza_score", 0.0),
            "accion_seleccionada": estado_final.get("accion_seleccionada"),
            "tokens_entrada": estado_final.get("tokens_entrada", 0),
            "tokens_salida": estado_final.get("tokens_salida", 0),
            "tiene_cobertura": estado_final.get("tiene_cobertura", False),
            "latencia_ms": latencia,
            "fuentes_recuperadas": fuentes,
        }

        return estado_final["respuesta_final"], estado_final["ruta_seleccionada"], metadata
