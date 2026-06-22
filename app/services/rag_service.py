# app/services/rag_service.py
import json
import logging
import time
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from rag.retriever import FiscalRAGRetriever
from rag.chain import FiscalRAGChain, ChainResult
from app.schemas.consulta import VisirState, DecisionEnrutamiento
from app.repositories.extracciones_repository import get_extracciones_by_org, get_estadisticas_basicas

logger = logging.getLogger(__name__)

# Palabras clave extraídas directamente de las reglas de negocio fijadas
PALABRAS_NORMATIVA = {"régimen", "regimen", "obligación", "obligacion", "impuesto", "deducible", "ley", "sat", "articulo", "artículo", "norma"}
PALABRAS_NUMERICA = {"gasto", "total", "mes", "cuánto", "cuanto", "ingresos", "reporte", "facturas", "proveedor"}

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
    ) -> None:
        # NOTA: FiscalRAGChain (rag/chain.py) NO expone api_key/base_url/model
        # como atributos de instancia, solo los usa internamente para construir
        # su propio ChatOpenAI y los descarta. Por eso este servicio recibe
        # esos valores por separado, en vez de leerlos de `chain`.
        self.chain = chain
        self.retriever = retriever
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model

        # LLM Router con Structured Output
        self.router_llm = ChatOpenAI(
            model=llm_model,
            temperature=0,
            api_key=llm_api_key,
            base_url=llm_base_url
        ).with_structured_output(DecisionEnrutamiento)

        self.grafo = self._construir_grafo()

    # ============================================================================
    # NODOS DE LA MÁQUINA DE ESTADOS (PROCESO DE CLASIFICACIÓN)
    # ============================================================================

    def _nodo_analisis_lexico(self, state: VisirState) -> dict[str, Any]:
        """Nodo 1: Analiza la semántica superficial por palabras clave (FSM Init)."""
        pregunta_clean = state["pregunta"].lower().split()
        palabras_usuario = set(pregunta_clean)

        match_normativa = len(palabras_usuario & PALABRAS_NORMATIVA)
        match_numerica = len(palabras_usuario & PALABRAS_NUMERICA)

        detectadas = list(palabras_usuario & (PALABRAS_NORMATIVA | PALABRAS_NUMERICA))

        # Determinar estado determinista provisional
        if match_normativa > 0 and match_numerica > 0:
            return {"ruta_seleccionada": "HIBRIDO", "confianza_lexica": 0.85, "palabras_clave_detectadas": detectadas}
        elif match_numerica > match_normativa:
            return {"ruta_seleccionada": "CFDI_PROPIOS", "confianza_lexica": 0.90, "palabras_clave_detectadas": detectadas}
        elif match_normativa > 0:
            return {"ruta_seleccionada": "NORMATIVA", "confianza_lexica": 0.90, "palabras_clave_detectadas": detectadas}

        # Si no hace match con nada, confianza 0.0 para forzar el paso al LLM
        return {"ruta_seleccionada": "NORMATIVA", "confianza_lexica": 0.0, "palabras_clave_detectadas": detectadas}

    def _nodo_validacion_llm(self, state: VisirState) -> dict[str, Any]:
        """Nodo 2: Nodo de escape inteligente ejecutado cuando hay ambigüedad (Confianza < 0.85)."""
        prompt = ChatPromptTemplate.from_messages([("system", PROMPT_LLM_ROUTER)])
        chain_router = prompt | self.router_llm

        decision: DecisionEnrutamiento = chain_router.invoke({"pregunta": state["pregunta"]})
        return {
            "ruta_seleccionada": decision.ruta,
            "decision_enrutamiento": decision
        }

    # ============================================================================
    # NODOS DE PROCESAMIENTO (RAG + SQL REPOSITORIES)
    # ============================================================================

    def _nodo_recuperar_leyes(self, state: VisirState) -> dict[str, Any]:
        fragmentos = self.retriever.retrieve(query=state["pregunta"], top_k=state["top_k"])
        # Serializamos los objetos RetrievalContext a diccionarios simples para mantener compatibilidad pura con TypedDict
        fragmentos_dict = [{"filename": f.filename, "text": f.text, "similarity": getattr(f, 'similarity', 0.9)} for f in fragmentos]
        return {"fragmentos_leyes": fragmentos_dict}

    def _nodo_recuperar_cfdis(self, state: VisirState) -> dict[str, Any]:
        # Tarea V-05: Filtro mandatorio por organización para aislamiento seguro de datos
        # NOTA (Gap 1, documentado, sin tocar): este filtro es solo por id_organizacion.
        # La tabla `extracciones` no tiene columna id_usuario en su migración actual,
        # así que no se puede filtrar también por usuario sin antes alterar el esquema.
        datos = get_extracciones_by_org(id_organizacion=state["id_organizacion"], limit=50)
        stats = get_estadisticas_basicas(id_organizacion=state["id_organizacion"])
        return {"datos_cfdi": {"facturas": datos}, "estadisticas_cfdi": stats}

    # ============================================================================
    # NODOS DE GENERACIÓN DE RESPUESTA (LLM CHAINS)
    # ============================================================================

    def _nodo_respuesta_normativa(self, state: VisirState) -> dict[str, Any]:
        contexto_txt = "\n\n".join([f"[{f['filename']}]: {f['text']}" for f in state["fragmentos_leyes"]])
        prompt = f"Responde como un Profesor Experto del SAT basándote exclusivamente en este contexto:\n{contexto_txt}\n\nPregunta: {state['pregunta']}"

        llm = ChatOpenAI(model=self.llm_model, temperature=0.1, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

    def _nodo_respuesta_cfdis(self, state: VisirState) -> dict[str, Any]:
        prompt = f"Genera un informe analítico ejecutivo con base en estos datos numéricos reales del negocio:\n{json.dumps(state['estadisticas_cfdi'])}\n\nPregunta: {state['pregunta']}"
        llm = ChatOpenAI(model=self.llm_model, temperature=0.0, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

    def _nodo_sintesis_hibrida(self, state: VisirState) -> dict[str, Any]:
        contexto_txt = "\n\n".join([f"[{f['filename']}]: {f['text']}" for f in state["fragmentos_leyes"]])
        prompt = f"""Cruza los datos de facturación del usuario con las leyes fiscales mexicanas vigentes.

        Datos numéricos del usuario: {json.dumps(state['estadisticas_cfdi'])}
        Leyes del SAT asociadas: {contexto_txt}

        Pregunta: {state['pregunta']}"""

        llm = ChatOpenAI(model=self.llm_model, temperature=0.2, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

    # ============================================================================
    # BORDES CONDICIONALES DE LA MÁQUINA DE ESTADOS
    # ============================================================================

    def _destino_por_ruta(self, state: VisirState) -> str | list[Send]:
        """
        Determina a dónde despachar tras decidir la ruta.
        Para HIBRIDO se usa Send() para lograr paralelismo real en LangGraph
        (una lista de strings no es válida como retorno de un edge condicional).
        """
        ruta = state["ruta_seleccionada"]
        if ruta == "HIBRIDO":
            return [Send("recuperar_leyes", state), Send("recuperar_cfdis", state)]
        elif ruta == "CFDI_PROPIOS":
            return "IR_A_CFDIS"
        return "IR_A_LEYES"

    def _enrutar_desde_lexico(self, state: VisirState) -> str | list[Send]:
        """
        Único punto de decisión tras el análisis léxico.
        Combina la evaluación de confianza y el destino de procesamiento
        en una sola función, porque LangGraph solo permite UN borde
        condicional saliente por nodo.
        """
        if state["confianza_lexica"] < 0.85:
            return "ESCALAR_A_LLM"
        return self._destino_por_ruta(state)

    def _post_recuperar_leyes(self, state: VisirState) -> str:
        """Tras recuperar leyes: si la ruta es HIBRIDO va a síntesis, si no, a respuesta normativa."""
        return "sintesis_hibrida" if state["ruta_seleccionada"] == "HIBRIDO" else "responder_normativa"

    def _post_recuperar_cfdis(self, state: VisirState) -> str:
        """Tras recuperar CFDIs: si la ruta es HIBRIDO va a síntesis, si no, a respuesta de CFDIs."""
        return "sintesis_hibrida" if state["ruta_seleccionada"] == "HIBRIDO" else "responder_cfdis"

    # ============================================================================
    # ENSAMBLAJE DE LA MÁQUINA DE ESTADOS (CONSTRUCCIÓN DEL GRAFO)
    # ============================================================================

    def _construir_grafo(self) -> Any:
        workflow = StateGraph(VisirState)

        # Registro de Nodos en la estructura central
        workflow.add_node("analisis_lexico", self._nodo_analisis_lexico)
        workflow.add_node("validacion_llm", self._nodo_validacion_llm)
        workflow.add_node("recuperar_leyes", self._nodo_recuperar_leyes)
        workflow.add_node("recuperar_cfdis", self._nodo_recuperar_cfdis)
        workflow.add_node("responder_normativa", self._nodo_respuesta_normativa)
        workflow.add_node("responder_cfdis", self._nodo_respuesta_cfdis)
        workflow.add_node("sintesis_hibrida", self._nodo_sintesis_hibrida)

        # Entrada
        workflow.set_entry_point("analisis_lexico")

        # Borde condicional único desde analisis_lexico: combina confianza
        # léxica y destino de procesamiento (reemplaza los dos bordes
        # conflictivos que existían antes sobre el mismo nodo).
        workflow.add_conditional_edges(
            "analisis_lexico",
            self._enrutar_desde_lexico,
            {
                "ESCALAR_A_LLM": "validacion_llm",
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            }
        )

        # Borde condicional desde validacion_llm hacia el mismo destino por ruta
        workflow.add_conditional_edges(
            "validacion_llm",
            self._destino_por_ruta,
            {
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            }
        )

        # Tras recuperar leyes: a síntesis híbrida SOLO si la ruta es HIBRIDO,
        # si no, a la respuesta normativa normal (ya no hay edge incondicional duplicado).
        workflow.add_conditional_edges(
            "recuperar_leyes",
            self._post_recuperar_leyes,
            {"sintesis_hibrida": "sintesis_hibrida", "responder_normativa": "responder_normativa"},
        )

        # Tras recuperar CFDIs: a síntesis híbrida SOLO si la ruta es HIBRIDO,
        # si no, a la respuesta de CFDIs normal.
        workflow.add_conditional_edges(
            "recuperar_cfdis",
            self._post_recuperar_cfdis,
            {"sintesis_hibrida": "sintesis_hibrida", "responder_cfdis": "responder_cfdis"},
        )

        # Terminaciones explícitas de los estados de salida
        workflow.add_edge("responder_normativa", END)
        workflow.add_edge("responder_cfdis", END)
        workflow.add_edge("sintesis_hibrida", END)

        return workflow.compile()

    def ejecutar_consulta(self, pregunta: str, usuario_id: str, id_organizacion: str, top_k: int = 5) -> tuple[str, str, dict[str, Any]]:
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
            "respuesta_final": None
        }

        estado_final = self.grafo.invoke(estado_inicial)
        latencia = (time.perf_counter() - t_inicio) * 1000

        metadata = {
            "ruta_ejecutada": estado_final["ruta_seleccionada"],
            "confianza_lexica": estado_final["confianza_lexica"],
            "palabras_clave": estado_final["palabras_clave_detectadas"],
            "latencia_ms": latencia
        }

        return estado_final["respuesta_final"], estado_final["ruta_seleccionada"], metadata
