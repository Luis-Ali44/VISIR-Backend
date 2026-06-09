from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── POST /v1/documentos/cargar ────────────────────────────────


def test_cargar_documento_pdf_valido(tmp_path):
    archivo = tmp_path / "test.pdf"
    archivo.write_bytes(b"%PDF-1.4 test content")
    with open(archivo, "rb") as f:
        response = client.post(
            "/v1/documentos/cargar",
            files={"file": ("test.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200


def test_cargar_documento_tipo_invalido(tmp_path):
    archivo = tmp_path / "test.txt"
    archivo.write_bytes(b"contenido de texto")
    with open(archivo, "rb") as f:
        response = client.post(
            "/v1/documentos/cargar",
            files={"file": ("test.txt", f, "text/plain")},
        )
    assert response.status_code == 400
    assert "no permitido" in response.json()["detail"]


def test_cargar_documento_muy_grande(tmp_path):
    archivo = tmp_path / "grande.pdf"
    archivo.write_bytes(b"%PDF" + b"0" * (6 * 1024 * 1024))  # 6MB
    with open(archivo, "rb") as f:
        response = client.post(
            "/v1/documentos/cargar",
            files={"file": ("grande.pdf", f, "application/pdf")},
        )
    assert response.status_code == 400
    assert "grande" in response.json()["detail"]


# ── GET /v1/documentos ────────────────────────────────────────


def test_listar_documentos():
    response = client.get("/v1/documentos")
    assert response.status_code == 200
    assert "data" in response.json()
    assert "next_cursor" in response.json()


def test_listar_documentos_limit_invalido():
    response = client.get("/v1/documentos?limit=0")
    assert response.status_code == 422


# ── GET /v1/documentos/id ─────────────────────────────────────


def test_get_documento_no_encontrado():
    response = client.get("/v1/documentos/id?document_id=00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
