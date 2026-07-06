import json
import logging
import time
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from app.services.routing_logic import analizar_lexico
from rag.retriever import FiscalRAGRetriever, OrgRAGRetriever
from rag.chain import FiscalRAGChain, ChainResult
from rag.config import RAGConfig, load_config_from_env
from app.schemas.consulta import VisirState, DecisionEnrutamiento
from app.repositories.extracciones_repository import get_extracciones_by_org, get_estadisticas_basicas

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
    ) -> None:
        self.chain = chain
        self.retriever = retriever

        config = rag_config or load_config_from_env()
        self.org_retriever = OrgRAGRetriever(config)

        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model

       
        self.router_llm = ChatOpenAI(
            model=llm_model,
            temperature=0,
            api_key=llm_api_key,
            base_url=llm_base_url
        ).with_structured_output(DecisionEnrutamiento)

        self.grafo = self._construir_grafo()

    def _nodo_analisis_lexico(self, state: VisirState) -> dict[str, Any]:

        return analizar_lexico(state["pregunta"])

    def _nodo_validacion_llm(self, state: VisirState) -> dict[str, Any]:

        prompt = ChatPromptTemplate.from_messages([("system", PROMPT_LLM_ROUTER)])
        chain_router = prompt | self.router_llm

        decision: DecisionEnrutamiento = chain_router.invoke({"pregunta": state["pregunta"]})
        return {
            "ruta_seleccionada": decision.ruta,
            "decision_enrutamiento": decision
        }


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
        contexto_txt = "\n\n".join([f"[{f['filename']}]: {f['text']}" for f in state["fragmentos_leyes"]])
        prompt = f"Responde como un Profesor Experto del SAT basándote exclusivamente en este contexto:\n{contexto_txt}\n\nPregunta: {state['pregunta']}"

        llm = ChatOpenAI(model=self.llm_model, temperature=0.1, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

    def _nodo_respuesta_cfdis(self, state: VisirState) -> dict[str, Any]:
        fragmentos_cfdis = state["datos_cfdi"].get("fragmentos_cfdis", [])

        if fragmentos_cfdis:
            cfdis_contexto = "\n\n".join([f"[CFDI {i+1}]: {f['text']}" for i, f in enumerate(fragmentos_cfdis)])
            prompt = (
                f"Genera un informe analítico ejecutivo basado en los siguientes CFDIs "
                f"del negocio del usuario (recuperados por relevancia semántica):\n\n"
                f"{cfdis_contexto}\n\n"
                f"Pregunta: {state['pregunta']}"
            )
        else:

            logger.warning(
                "No se encontraron fragmentos semánticos para org=%s, usando estadísticas SQL como fallback",
                state["id_organizacion"],
            )
            prompt = (
                f"Genera un informe analítico ejecutivo con base en estos datos numéricos reales del negocio:\n"
                f"{json.dumps(state['estadisticas_cfdi'])}\n\n"
                f"Pregunta: {state['pregunta']}"
            )

        llm = ChatOpenAI(model=self.llm_model, temperature=0.0, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

    def _nodo_sintesis_hibrida(self, state: VisirState) -> dict[str, Any]:
        contexto_leyes = "\n\n".join([f"[{f['filename']}]: {f['text']}" for f in state["fragmentos_leyes"]])

        fragmentos_cfdis = state["datos_cfdi"].get("fragmentos_cfdis", [])
        if fragmentos_cfdis:
            cfdis_contexto = "\n\n".join([f"[CFDI {i+1}]: {f['text']}" for i, f in enumerate(fragmentos_cfdis)])
        else:

            logger.warning(
                "Síntesis híbrida sin fragmentos semánticos para org=%s, usando estadísticas SQL",
                state["id_organizacion"],
            )
            cfdis_contexto = json.dumps(state["estadisticas_cfdi"])

        prompt = f"""Cruza los datos de facturación del usuario con las leyes fiscales mexicanas vigentes.

CFDIs del usuario (búsqueda semántica por relevancia):
{cfdis_contexto}

Leyes del SAT asociadas:
{contexto_leyes}

Pregunta: {state['pregunta']}"""

        llm = ChatOpenAI(model=self.llm_model, temperature=0.2, api_key=self.llm_api_key, base_url=self.llm_base_url)
        res = llm.invoke(prompt)
        return {"respuesta_final": res.content}

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

        return "sintesis_hibrida" if state["ruta_seleccionada"] == "HIBRIDO" else "responder_normativa"

    def _post_recuperar_cfdis(self, state: VisirState) -> str:

        return "sintesis_hibrida" if state["ruta_seleccionada"] == "HIBRIDO" else "responder_cfdis"


    def _construir_grafo(self) -> Any:
        workflow = StateGraph(VisirState)


        workflow.add_node("analisis_lexico", self._nodo_analisis_lexico)
        workflow.add_node("validacion_llm", self._nodo_validacion_llm)
        workflow.add_node("recuperar_leyes", self._nodo_recuperar_leyes)
        workflow.add_node("recuperar_cfdis", self._nodo_recuperar_cfdis)
        workflow.add_node("responder_normativa", self._nodo_respuesta_normativa)
        workflow.add_node("responder_cfdis", self._nodo_respuesta_cfdis)
        workflow.add_node("sintesis_hibrida", self._nodo_sintesis_hibrida)

        workflow.set_entry_point("analisis_lexico")

        workflow.add_conditional_edges(
            "analisis_lexico",
            self._enrutar_desde_lexico,
            {
                "ESCALAR_A_LLM": "validacion_llm",
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            }
        )


        workflow.add_conditional_edges(
            "validacion_llm",
            self._destino_por_ruta,
            {
                "IR_A_LEYES": "recuperar_leyes",
                "IR_A_CFDIS": "recuperar_cfdis",
            }
        )

        workflow.add_conditional_edges(
            "recuperar_leyes",
            self._post_recuperar_leyes,
            {"sintesis_hibrida": "sintesis_hibrida", "responder_normativa": "responder_normativa"},
        )
        workflow.add_conditional_edges(
            "recuperar_cfdis",
            self._post_recuperar_cfdis,
            {"sintesis_hibrida": "sintesis_hibrida", "responder_cfdis": "responder_cfdis"},
        )

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
            "respuesta_final": None,
            "fuentes_recuperadas": [],
        }

        estado_final = self.grafo.invoke(estado_inicial)
        latencia = (time.perf_counter() - t_inicio) * 1000

        fuentes: list[dict] = []

        for f in estado_final.get("fragmentos_leyes", []):
            fuentes.append({
                "filename": f.get("filename", ""),
                "chunk_id": f.get("chunk_id", ""),
                "section": f.get("section", "sin_sección"),
                "page_number": f.get("page_number"),
                "similarity": round(float(f.get("similarity", 0.0)), 4),
                "origen": "ley",
            })

        for f in estado_final.get("datos_cfdi", {}).get("fragmentos_cfdis", []):
            fuentes.append({
                "filename": f.get("filename", ""),
                "chunk_id": f.get("chunk_id", ""),
                "section": f.get("section", "sin_sección"),
                "page_number": f.get("page_number"),
                "similarity": round(float(f.get("similarity", 0.0)), 4),
                "origen": "cfdi",
            })

        fuentes.sort(key=lambda x: x["similarity"], reverse=True)

        metadata = {
            "ruta_ejecutada": estado_final["ruta_seleccionada"],
            "confianza_lexica": estado_final["confianza_lexica"],
            "palabras_clave": estado_final["palabras_clave_detectadas"],
            "latencia_ms": latencia,
            "fuentes_recuperadas": fuentes,
        }

        return estado_final["respuesta_final"], estado_final["ruta_seleccionada"], metadata
