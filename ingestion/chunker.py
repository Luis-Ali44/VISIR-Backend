import re
from dataclasses import dataclass

from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter
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

    def __init__(
        self,
        embed_model,
        breakpoint_threshold: int = 88,
        buffer_size: int = 2,
        min_section_length: int = 200,
    ):
        self.min_section_length = min_section_length

        self.semantic_splitter = SemanticSplitterNodeParser(
            embed_model=embed_model,
            breakpoint_percentile_threshold=breakpoint_threshold,
            buffer_size=buffer_size,
        )

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

        section_doc = Document(
            text=section.content,
            metadata=section_metadata,
        )

        try:
            semantic_chunks = self.semantic_splitter.get_nodes_from_documents(
                [section_doc]
            )
        except Exception:

            semantic_chunks = self.fallback_splitter.get_nodes_from_documents(
                [section_doc]
            )

        total = len(semantic_chunks)
        for i, chunk in enumerate(semantic_chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunks_in_section"] = total

        return semantic_chunks

    def describe_sections(self, document: Document) -> None:
        sections = split_into_sections(document.text)
        print(f"\n{'═'*60}")
        print(f"  Secciones detectadas: {len(sections)}")
        print(f"{'═'*60}")
        for i, s in enumerate(sections):
            split = s.char_count >= self.min_section_length
            indicator = "→ SemanticSplit" if split else "→ Chunk único"
            print(f"  [{i+1:02d}] {s.title[:55]:<55} {s.char_count:>5} chars  {indicator}")
        print(f"{'─'*60}\n")
