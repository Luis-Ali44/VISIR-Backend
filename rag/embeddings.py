from __future__ import annotations

import logging
import time

import requests
from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from llama_index.core.bridge.pydantic import Field
from pydantic import PrivateAttr

logger = logging.getLogger(__name__)


class OpenAICompatibleEmbeddingModel(BaseEmbedding):

    model_name:       str = Field(description="Nombre del modelo de embeddings")
    base_url:         str = Field(description="URL base del proveedor (sin /embeddings)")
    api_key:          str = Field(description="API key (usa 'ollama' para Ollama)")
    timeout:          int = Field(description="Timeout por petición en segundos")
    max_retries:      int = Field(description="Máximos reintentos ante fallo transitorio")
    embed_batch_size: int = Field(description="Tamaño del batch de embeddings")

    _session: requests.Session = PrivateAttr()

    def __init__(
        self,
        model_name:       str = "embeddinggemma:latest",
        base_url:         str = "http://localhost:11434/v1",
        api_key:          str = "ollama",
        timeout:          int = 30,
        max_retries:      int = 3,
        embed_batch_size: int = 32,
        **kwargs,
    ):
        super().__init__(
            model_name=model_name,
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            embed_batch_size=embed_batch_size,
            **kwargs,
        )
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self._verify_connection()


    def _verify_connection(self) -> None:

        for probe in ["/models", "/"]:
            try:
                resp = self._session.get(f"{self.base_url}{probe}", timeout=5)
                if resp.status_code < 500:
                    logger.info("[Embeddings] Conexión verificada en %s", self.base_url)
                    return
            except requests.exceptions.ConnectionError:
                pass
            except requests.exceptions.Timeout:
                pass

        logger.warning(
            "[Embeddings] No se pudo verificar conexión en %s — se intentará al primer uso",
            self.base_url,
        )

    # ── Embedding individual (delega en el batch de tamaño 1) ────────────────

    def _embed_with_retry(self, text: str) -> list[float]:
        return self._embed_batch_with_retry([text])[0]

    # ── Embedding por lote — UNA sola petición HTTP para todo el lote ────────

    def _embed_batch_with_retry(self, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings para una lista de textos en una sola petición HTTP.

        El endpoint /embeddings estilo OpenAI acepta `input` como lista,
        devolviendo un embedding por texto en el mismo orden (o con un
        campo "index" que permite reordenar). Esto reemplaza el patrón
        anterior de una petición HTTP por texto.
        """
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.post(
                    url,
                    json={"model": self.model_name, "input": texts},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()

                if "data" in data and data["data"]:
                    ordered = sorted(data["data"], key=lambda d: d.get("index", 0))
                    return [d["embedding"] for d in ordered]

                # Fallback: formato Ollama nativo /api/embed (batch real)
                if "embeddings" in data:
                    return data["embeddings"]

                raise ValueError(f"Respuesta inesperada del servidor: {list(data.keys())}")

            except requests.exceptions.Timeout:
                wait = 2 ** attempt
                logger.warning(
                    "[Embeddings] Timeout en intento %d/%d (lote=%d). Reintentando en %ds...",
                    attempt, self.max_retries, len(texts), wait,
                )
                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"[ERROR] Servidor de embeddings no respondió en {self.timeout}s "
                        f"tras {self.max_retries} intentos (lote de {len(texts)} textos).\n"
                        f"  URL: {self.base_url}\n"
                        f"  Aumenta EMBEDDING_TIMEOUT en .env o reduce embed_batch_size."
                    )
                time.sleep(wait)

            except requests.exceptions.ConnectionError as e:
                raise RuntimeError(
                    f"[ERROR] Conexión perdida con el servidor de embeddings: {e}\n"
                    f"  URL: {self.base_url}\n"
                    f"  Verifica que el servidor siga corriendo."
                )

            except requests.exceptions.HTTPError as e:
                if resp.status_code in (503, 429):
                    wait = 2 ** attempt
                    logger.warning(
                        "[Embeddings] HTTP %d en intento %d/%d. Reintentando en %ds...",
                        resp.status_code, attempt, self.max_retries, wait,
                    )
                    time.sleep(wait)
                elif resp.status_code in (400, 413) and len(texts) > 1:
                    # El servidor rechazó el lote completo (demasiado grande
                    # para su límite interno) — se subdivide a la mitad en
                    # vez de fallar.
                    logger.warning(
                        "[Embeddings] El servidor rechazó el lote de %d textos "
                        "(HTTP %d). Dividiendo en lotes más pequeños...",
                        len(texts), resp.status_code,
                    )
                    mid = len(texts) // 2
                    return (
                        self._embed_batch_with_retry(texts[:mid])
                        + self._embed_batch_with_retry(texts[mid:])
                    )
                else:
                    raise RuntimeError(
                        f"[ERROR] HTTP {resp.status_code} del servidor de embeddings: {e}\n"
                        f"  URL: {url}\n"
                        f"  Verifica el modelo ({self.model_name}) y la API key."
                    )

        raise RuntimeError(f"Embedding fallido tras {self.max_retries} intentos.")


    def _get_text_embedding(self, text: str) -> Embedding:
        return self._embed_with_retry(text)

    def _get_query_embedding(self, query: str) -> Embedding:
        return self._embed_with_retry(query)

    async def _aget_text_embedding(self, text: str) -> Embedding:
        return self._embed_with_retry(text)

    async def _aget_query_embedding(self, query: str) -> Embedding:
        return self._embed_with_retry(query)

    def _get_text_embeddings(self, texts: list[str]) -> list[Embedding]:
        # Antes: [self._embed_with_retry(t) for t in texts]  → N peticiones HTTP
        # Ahora: una sola petición HTTP para todo el sub-lote.
        return self._embed_batch_with_retry(texts)


def build_index_embed_model(
    base_url:    str = "http://localhost:11434/v1",
    model_name:  str = "embeddinggemma:latest",
    api_key:     str = "ollama",
    timeout:     int = 30,
    max_retries: int = 3,
) -> OpenAICompatibleEmbeddingModel:
    return OpenAICompatibleEmbeddingModel(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        embed_batch_size=32,
    )


def build_query_embed_model(
    base_url:    str = "http://localhost:11434/v1",
    model_name:  str = "embeddinggemma:latest",
    api_key:     str = "ollama",
    timeout:     int = 30,
    max_retries: int = 3,
) -> OpenAICompatibleEmbeddingModel:
    return OpenAICompatibleEmbeddingModel(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        embed_batch_size=1,
    )

OllamaEmbeddingModel = OpenAICompatibleEmbeddingModel
