import uuid

from app.schemas.conversacion_schema import ConsultaResponse, EmbeddingUsado, SaveConsulta
from app.schemas.user_schema import UsuarioActual


async def consultar_service(pregunta: str, user: UsuarioActual) -> ConsultaResponse:

    id_usuario = user.id
    id_organizacion = user.id_organizacion
    id_consulta = str(uuid.uuid4())
    """
    Datos mencionados por derek:
    Envio: consulta
    Recibo: id_conulta, Respuesta, Embeddings

    aqui ira el servicio de derek para consultas
    """

    respuesta_prueba = f"Esta seria una respuesta simulada para: {pregunta}"
    embedding_prueba = [
        EmbeddingUsado(id=str(uuid.uuid4()), texto="Ejemplo de embedding usado en la respuesta")
    ]

    SaveConsulta(
        id_consulta=id_consulta,
        respuesta=respuesta_prueba,
        id_usuario=id_usuario,
        id_organizacion=id_organizacion,
    )

    return ConsultaResponse(
        id_consulta=id_consulta,
        respuesta=respuesta_prueba,
        Embeddings_usados=embedding_prueba,
        distancia=None,
    )
