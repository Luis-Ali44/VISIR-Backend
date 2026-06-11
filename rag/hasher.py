import hashlib
from pathlib import Path


def compute_file_hash(pdf_path: str) -> str:
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:

        for block in iter(lambda: f.read(8192), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compute_chunk_hash(text: str) -> str:
    normalized = text.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def short_hash(full_hash: str, length: int = 12) -> str:
    return full_hash[:length]


def compute_doc_id(pdf_path: str) -> str:
    file_name = Path(pdf_path).stem
    file_hash = compute_file_hash(pdf_path)
    return f"{file_name}__{short_hash(file_hash)}"
