import os
from dataclasses import dataclass

_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "embeddinggemma":           384,
    "embeddinggemma:latest":    384,
    "nomic-embed-text":         768,
    "nomic-embed-text:latest":  768,
    "mxbai-embed-large":        1024,
    "text-embedding-ada-002":   1536,
    "text-embedding-3-small":   1536,
    "text-embedding-3-large":   3072,
}


@dataclass
class RAGConfig:
    chroma_path:      str = "./chroma_db"
    collection_name:  str = "documentos_fiscales"
    topic_seed_path:  str = "./data/topic_seed.md"

    embedding_base_url:   str = "http://localhost:11434/v1"
    embedding_api_key:    str = "ollama"           # "ollama" para Ollama (valor ignorado)
    embedding_model_name: str = "embeddinggemma:latest"
    embedding_timeout:    int = 30
    embedding_max_retries: int = 3

    llm_base_url:    str = "https://api.groq.com/openai/v1"
    llm_api_key:     str = ""
    llm_model:       str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.2
    llm_max_tokens:  int = 1024


    semantic_breakpoint_threshold:   int = 88
    semantic_buffer_size:            int = 2
    min_section_length_for_semantic: int = 200

    default_importance: int = 3
    default_top_k:      int = 5

    @property
    def embedding_dimensions(self) -> int | None:
        model_base = self.embedding_model_name.split(":")[0]
        return (
            _EMBEDDING_DIMENSIONS.get(self.embedding_model_name)
            or _EMBEDDING_DIMENSIONS.get(model_base)
        )


def load_config_from_env(chroma_path: str = "./chroma_db") -> RAGConfig:
    return RAGConfig(
        chroma_path=chroma_path,
        collection_name=os.getenv("CHROMA_COLLECTION", "documentos_fiscales"),
        topic_seed_path=os.getenv("TOPIC_SEED_PATH", "./data/topic_seed.md"),

        # Embeddings
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", "http://ollama:11434/v1"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", "ollama"),
        embedding_model_name=os.getenv("EMBEDDING_MODEL", "embeddinggemma:latest"),
        embedding_timeout=int(os.getenv("EMBEDDING_TIMEOUT", "30")),
        embedding_max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3")),

        # LLM
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
    )


DEFAULT_CONFIG = RAGConfig()
