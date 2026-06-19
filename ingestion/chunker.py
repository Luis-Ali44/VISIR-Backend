import re
from dataclasses import dataclass

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode


FISCAL_SECTION_PATTERNS = [

    r"Apéndice\s+\d+[\w\s\.,áéíóúÁÉÍÓÚüÜñÑ]{0,80}",

    r"Nodo:\s*[\wáéíóúÁÉÍÓÚüÜñÑ][\w\s]{0,50}",

    r"^(?:I{1,3}V?|VI{0,3}|IX|X)\.\s+[A-ZÁÉÍÓÚÜÑ][\w\s,áéíóúÁÉÍÓÚüÜñÑ]{5,80}",

    r"^\d{1,2}\.\s+¿[^?]{10,150}\?",

    r"^\d+\.\s+Emisión\s+(?:de|del|un)\s+[\wáéíóúÁÉÍÓÚüÜñÑ\s]{5,80}",

    r"Control de cambios",

    r"^Glosario$",
]


_COMBINED_PATTERN = re.compile(
    r"(" + "|".join(FISCAL_SECTION_PATTERNS) + r")",
    re.MULTILINE | re.UNICODE,
)


@dataclass
class Section:
    """Representa una sección detectada del documento."""
    title: str
    content: str
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.content)


def split_into_sections(text: str, min_content_chars: int = 60) -> list[Section]:
    parts = _COMBINED_PATTERN.split(text)

    sections: list[Section] = []
    current_title = "introduccion"
    current_content_parts: list[str] = []

    for part in parts:
        if part is None:
            continue
        part_stripped = part.strip()
        if not part_stripped:
            continue


        if _COMBINED_PATTERN.fullmatch(part_stripped):

            if current_content_parts:
                content = "\n".join(current_content_parts).strip()
                if len(content) >= min_content_chars:
                    sections.append(Section(
                        title=current_title,
                        content=content,
                    ))
            current_title = part_stripped
            current_content_parts = []
        else:
            current_content_parts.append(part_stripped)


    if current_content_parts:
        content = "\n".join(current_content_parts).strip()
        if len(content) >= min_content_chars:
            sections.append(Section(title=current_title, content=content))

    return sections


class FiscalDocumentChunker:
    """
    Fragmenta documentos fiscales en 2 capas:

      1. Detección de secciones por regex de dominio (sin cambios).
      2. Agrupación dinámica por párrafos dentro de cada sección,
         con sub-división por oraciones solo para bloques excepcional-
         mente largos que ni siquiera caben fusionados.

    El tamaño de cada chunk resultante es VARIABLE — depende de cómo
    se agrupen los párrafos reales del documento, no de un chunk_size
    fijo aplicado uniformemente. Esto preserva la propiedad de
    "chunkeo dinámico" sin requerir embeddings durante el chunking.
    """

    def __init__(
        self,
        embed_model,
        breakpoint_threshold: int = 88,
        buffer_size: int = 2,
        min_section_length: int = 200,
        max_chunk_chars: int = 1200,
        min_chunk_chars: int = 300,
    ):
        """
        Args:
            embed_model: se conserva por compatibilidad con pipeline.py
                (que lo pasa al construir el chunker). Ya NO se usa para
                tomar decisiones de corte — el splitting es puramente
                estructural y no genera ninguna llamada de embedding.
            breakpoint_threshold: se conserva por compatibilidad con
                RAGConfig / .env existentes. Sin efecto en esta estrategia.
            buffer_size: se conserva por compatibilidad con RAGConfig.
                Sin efecto en esta estrategia.
            min_section_length: por debajo de este tamaño, la sección se
                conserva como un único chunk sin sub-dividir.
            max_chunk_chars: tamaño objetivo máximo de cada chunk agrupado
                por párrafos. Si fusionar el siguiente párrafo excede este
                límite, se cierra el chunk actual y se abre uno nuevo.
            min_chunk_chars: tamaño mínimo deseable antes de cerrar un
                chunk. Evita micro-chunks sin contexto suficiente —
                si el buffer actual es menor a este valor, se sigue
                fusionando aunque se exceda un poco max_chunk_chars.
        """
        self.min_section_length = min_section_length
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

        # Solo se usa como red de seguridad para párrafos individuales
        # que ya de por sí exceden max_chunk_chars (tablas largas,
        # listados extensos) — no participa en el flujo normal.
        self.fallback_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=40,
        )

    def chunk(self, document: Document) -> list[BaseNode]:
        sections = split_into_sections(document.text)

        if not sections:
            sections = [Section(
                title="documento_completo",
                content=document.text,
            )]

        all_chunks: list[BaseNode] = []

        for section in sections:
            section_chunks = self._process_section(section, document.metadata)
            all_chunks.extend(section_chunks)

        return all_chunks

    def _group_paragraphs_dynamically(self, text: str) -> list[str]:
        """
        Agrupa párrafos (separados por línea vacía) en bloques de tamaño
        variable, respetando los límites min/max configurados.

        No usa un tamaño fijo: el número de párrafos por chunk depende
        de cuán largos sean — un chunk puede tener 1 párrafo largo o
        5 párrafos cortos, lo que importa es el rango de caracteres.
        """
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        if not paragraphs:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        buffer = ""

        for para in paragraphs:
            candidate = f"{buffer}\n\n{para}".strip() if buffer else para

            if len(candidate) <= self.max_chunk_chars:
                buffer = candidate
                continue

            if len(buffer) >= self.min_chunk_chars:
                # El buffer ya tiene tamaño suficiente: se cierra como
                # chunk y el párrafo actual inicia el siguiente buffer.
                chunks.append(buffer)
                buffer = para
            else:
                # El buffer es muy pequeño todavía — se fusiona aunque
                # se exceda max_chunk_chars, para no generar un chunk
                # sin contexto suficiente.
                buffer = candidate

        if buffer:
            chunks.append(buffer)

        return chunks

    def _process_section(
        self,
        section: Section,
        base_metadata: dict,
    ) -> list[BaseNode]:
        section_metadata = {
            **base_metadata,
            "section": section.title,
            "section_length": section.char_count,
        }

        if section.char_count < self.min_section_length:
            return [TextNode(
                text=section.content,
                metadata={
                    **section_metadata,
                    "chunk_index": 0,
                    "chunks_in_section": 1,
                },
            )]

        grouped_texts = self._group_paragraphs_dynamically(section.content)

        if not grouped_texts:
            grouped_texts = [section.content]

        final_nodes: list[BaseNode] = []

        for text in grouped_texts:
            if len(text) > self.max_chunk_chars * 1.5:
                # Bloque excepcionalmente largo (p.ej. una tabla extensa
                # que no tiene saltos de párrafo internos): se sub-divide
                # por oraciones como red de seguridad. Esto NO llama al
                # embedder — SentenceSplitter trabaja por conteo de
                # tokens/oraciones, no por embeddings.
                section_doc = Document(text=text, metadata=section_metadata)
                try:
                    sub_nodes = self.fallback_splitter.get_nodes_from_documents(
                        [section_doc]
                    )
                    final_nodes.extend(sub_nodes)
                except Exception:
                    final_nodes.append(TextNode(text=text, metadata=dict(section_metadata)))
            else:
                final_nodes.append(TextNode(text=text, metadata=dict(section_metadata)))

        total = len(final_nodes)
        for i, node in enumerate(final_nodes):
            node.metadata["chunk_index"] = i
            node.metadata["chunks_in_section"] = total

        return final_nodes

    def describe_sections(self, document: Document) -> None:
        sections = split_into_sections(document.text)
        print(f"\n{'═'*60}")
        print(f"  Secciones detectadas: {len(sections)}")
        print(f"{'═'*60}")
        for i, s in enumerate(sections):
            split = s.char_count >= self.min_section_length
            indicator = "→ Agrupación dinámica" if split else "→ Chunk único"
            print(f"  [{i+1:02d}] {s.title[:55]:<55} {s.char_count:>5} chars  {indicator}")
        print(f"{'─'*60}\n")
