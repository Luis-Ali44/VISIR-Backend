from pathlib import Path

import pymupdf 
import pymupdf4llm
from llama_index.core import Document


def load_pdf(
    pdf_path: str,
    doc_id: str,
    doc_hash: str,
    importance: int = 3,
    extra_metadata: dict | None = None,
) -> Document:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    
    md_text = pymupdf4llm.to_markdown(
        str(path),
        show_progress=False,
    )

    pdf_doc = pymupdf.open(str(path))
    pdf_metadata = pdf_doc.metadata or {}
    total_pages = pdf_doc.page_count
    pdf_doc.close()

    metadata = {
        
        "doc_id":       doc_id,
        "source":       str(path.resolve()),
        "filename":     path.name,
        "doc_hash":     doc_hash,

        
        "importance":        importance,
        "importance_weight": round(importance / 5.0, 2),

    
        "total_pages": total_pages,
        "pdf_title":   pdf_metadata.get("title", path.stem),
        "pdf_author":  pdf_metadata.get("author", ""),

        
        **(extra_metadata or {}),
    }

    return Document(text=md_text, metadata=metadata)

"""
def load_pdf_by_pages(
    pdf_path: str,
    doc_id: str,
    doc_hash: str,
    importance: int = 3,
    extra_metadata: dict | None = None,
) -> list[Document]:
    path = Path(pdf_path)
    pdf_doc = pymupdf.open(str(path))
    total_pages = pdf_doc.page_count
    pdf_doc.close()

    documents = []

    for page_num in range(total_pages):
       
        page_md = pymupdf4llm.to_markdown(
            str(path),
            pages=[page_num],
            show_progress=False,
        )

        if not page_md.strip():
            continue  

        metadata = {
            "doc_id":            doc_id,
            "source":            str(path.resolve()),
            "filename":          path.name,
            "doc_hash":          doc_hash,
            "page_number":       page_num + 1,  
            "total_pages":       total_pages,
            "importance":        importance,
            "importance_weight": round(importance / 5.0, 2),
            **(extra_metadata or {}),
        }

        documents.append(Document(text=page_md, metadata=metadata))

    return documents

"""
def load_pdf_by_pages(
    pdf_path: str,
    doc_id: str,
    doc_hash: str,
    importance: int = 3,
    extra_metadata: dict | None = None,
) -> list[Document]:
    path = Path(pdf_path)
    
    # 1. Extraer TODO el documento a Markdown en UNA SOLA llamada
    # Esto es mucho más eficiente que abrir el PDF página por página
    full_md_text = pymupdf4llm.to_markdown(str(path), show_progress=False)
    
    # 2. Dividir por el separador de página que usa pymupdf4llm
    # Por defecto, pymupdf4llm usa un salto de página consistente
    pages_text = full_md_text.split("\n\n---") 
    
    total_pages = len(pages_text)
    documents = []

    for page_num, page_md in enumerate(pages_text):
        if not page_md.strip():
            continue  

        metadata = {
            "doc_id":            doc_id,
            "source":            str(path.resolve()),
            "filename":          path.name,
            "doc_hash":          doc_hash,
            "page_number":       page_num + 1,  
            "total_pages":       total_pages,
            "importance":        importance,
            "importance_weight": round(importance / 5.0, 2),
            **(extra_metadata or {}),
        }

        documents.append(Document(text=page_md, metadata=metadata))

    return documents

def load_markdown(
    md_path: str,
    doc_id: str,
    doc_hash: str,
    importance: int = 3,
    extra_metadata: dict | None = None,
) -> list[Document]:
    path = Path(md_path)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {md_path}")

    text = path.read_text(encoding="utf-8")

    metadata = {
        "doc_id": doc_id,
        "source": str(path.resolve()),
        "filename": path.name,
        "doc_hash": doc_hash,
        "importance": importance,
        "importance_weight": round(importance / 5.0, 2),
        **(extra_metadata or {}),
    }

    return [Document(text=text, metadata=metadata)]


def load_document(
    file_path: str,
    doc_id: str,
    doc_hash: str,
    importance: int = 3,
    extra_metadata: dict | None = None,
) -> list[Document]:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return load_pdf_by_pages(
            pdf_path=file_path,
            doc_id=doc_id,
            doc_hash=doc_hash,
            importance=importance,
            extra_metadata=extra_metadata,
        )

    if ext in {".md", ".markdown", ".txt"}:
        return load_markdown(
            md_path=file_path,
            doc_id=doc_id,
            doc_hash=doc_hash,
            importance=importance,
            extra_metadata=extra_metadata,
        )

    raise ValueError(f"Unsupported file extension: {ext}")
