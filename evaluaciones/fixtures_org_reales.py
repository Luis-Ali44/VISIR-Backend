from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

ID_ORGANIZACION_PRUEBA = "11111111-1111-1111-1111-111111111111"

CFDIS_REALES: list[dict] = [
    {
        "archivo": "cfdi_v33_egreso_restaurante_045",
        "rubro": "restaurante",
        "tipo": "EGRESO",
        "fecha": "2026-03-07",
        "total": "11,641.74",
        "folio_fiscal": "92F6C6FD-5A5E-41D9-8ABF-6EE31DA33084",
        "emisor_nombre": "PULIDO-CORTÉS IAP",
        "emisor_rfc": "ZME981109SO5",
        "receptor_rfc": "ZBJ221212PL3",
        "concepto": "Servicios de hospedaje y/o restaurantes y catering",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v33_egreso_restaurante_047",
        "rubro": "restaurante",
        "tipo": "EGRESO",
        "fecha": "2026-01-23",
        "total": "7,688.65",
        "folio_fiscal": "77BDAEFD-A8EE-4E77-97CA-5BF06E57F119",
        "emisor_nombre": "INDUSTRIAS OLIVO TOVAR Y MURO IAP",
        "emisor_rfc": "XOK970330AM3",
        "receptor_rfc": "FYU200407ZV8",
        "concepto": "Servicios de hospedaje y/o restaurantes y catering",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v33_egreso_salud_048",
        "rubro": "salud",
        "tipo": "EGRESO",
        "fecha": "2025-12-12",
        "total": "21,875.01",
        "folio_fiscal": "DAFFFA7B-5860-4DCF-9634-0B1BBA21B9A1",
        "emisor_nombre": "VILLANUEVA GALARZA ELVIRA SAS DE CV",
        "emisor_rfc": "LCNZ690415GV5",
        "receptor_rfc": "KOPS831213YR2",
        "concepto": "Servicios médicos, de enfermería y/o medicamentos",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v33_ingreso_comercio_minorista_038",
        "rubro": "comercio_minorista",
        "tipo": "INGRESO",
        "fecha": "2025-12-21",
        "total": "69,475.38",
        "folio_fiscal": "E4EAFF52-67FC-46F8-B20A-DE1A9ED00DEC",
        "emisor_nombre": "PROYECTOS OTERO Y VILLALOBOS AC",
        "emisor_rfc": "VXV130612FG7",
        "receptor_rfc": "FDX180502VE8",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "03 - TRANSFERENCIA ELECTRO",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v33_ingreso_comercio_minorista_039",
        "rubro": "comercio_minorista",
        "tipo": "INGRESO",
        "fecha": "2025-12-30",
        "total": "219,674.83",
        "folio_fiscal": "8E180676-DDB8-442A-9B73-291CDD01A1BD",
        "emisor_nombre": "ALEJANDRO-RINCÓN E HIJOS IAP",
        "emisor_rfc": "RJK081113RT1",
        "receptor_rfc": "WJN171210MT3",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "03 - TRANSFERENCIA ELECTRO",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v33_ingreso_salud_031",
        "rubro": "salud",
        "tipo": "INGRESO",
        "fecha": "2026-01-01",
        "total": "7,715.22",
        "folio_fiscal": "2FA04A39-9266-434D-A9F9-BDBDD48FFBAE",
        "emisor_nombre": "MUÑIZ SOLÍS ALMA SAS DE CV",
        "emisor_rfc": "ERYL640525EC6",
        "receptor_rfc": "ILMD650218ZX5",
        "concepto": "Servicios médicos, de enfermería y/o medicamentos",
        "forma_pago": "04 - TARJETA DE CRE",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v33_ingreso_salud_032",
        "rubro": "salud",
        "tipo": "INGRESO",
        "fecha": "2026-01-03",
        "total": "2,186.00",
        "folio_fiscal": "EBB219E6-32C6-4827-A9EC-76CCE1F47E14",
        "emisor_nombre": "FLÓREZ RENTERÍA ESPERANZA AC",
        "emisor_rfc": "LYHV820908GI6",
        "receptor_rfc": "RYXT941216QU7",
        "concepto": "Servicios médicos, de enfermería y/o medicamentos",
        "forma_pago": "28 - TARJETA DE DE",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v40_egreso_comercio_minorista_0211",
        "rubro": "comercio_minorista",
        "tipo": "EGRESO",
        "fecha": "2025-12-09",
        "total": "1,183.22",
        "folio_fiscal": "32C71474-881B-4B8C-8640-DC089F4617A4",
        "emisor_nombre": "ROBLES-JUÁREZ E HIJOS S DE RL DE CV",
        "emisor_rfc": "BUH230514EL3",
        "receptor_rfc": "KNS170205JU2",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_comercio_minorista_022",
        "rubro": "comercio_minorista",
        "tipo": "EGRESO",
        "fecha": "2026-04-18",
        "total": "7,690.34",
        "folio_fiscal": "81E25336-29A9-43B2-A7A9-D1501136C606",
        "emisor_nombre": "RODRÍGEZ Y ASOCIADOS SA DE CV",
        "emisor_rfc": "WTG080118JN7",
        "receptor_rfc": "KPC191203VE6",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PPD",
    },
    {
        "archivo": "cfdi_v40_egreso_comercio_minorista_024",
        "rubro": "comercio_minorista",
        "tipo": "EGRESO",
        "fecha": "2026-05-18",
        "total": "216,262.19",
        "folio_fiscal": "06EF02C1-C5CF-48A9-B5B6-1EC94C0A38ED",
        "emisor_nombre": "INDUSTRIAS MURO-VILLARREAL SA DE CV",
        "emisor_rfc": "ZJG200124TB9",
        "receptor_rfc": "SHV160605VJ1",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_comercio_minorista_025",
        "rubro": "comercio_minorista",
        "tipo": "EGRESO",
        "fecha": "2026-02-08",
        "total": "105,181.12",
        "folio_fiscal": "46B66112-6313-4239-8CD8-4FDE1A6E8A97",
        "emisor_nombre": "CARRIÓN-ESTÉVEZ S RL DE CV SAS DE CV",
        "emisor_rfc": "GHO080621UB8",
        "receptor_rfc": "WPT240201OM2",
        "concepto": "Artículos de papelería, equipo de cómputo y/o mercancía general",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_construccion_026",
        "rubro": "construccion",
        "tipo": "EGRESO",
        "fecha": "2026-01-01",
        "total": "163,472.16",
        "folio_fiscal": "D49CA2D3-0564-4117-9AEE-EA60A9604415",
        "emisor_nombre": "INDUSTRIAS TELLO Y GRACIA S DE RL DE CV",
        "emisor_rfc": "IAA150205ZP9",
        "receptor_rfc": "BVO990812HE5",
        "concepto": "Servicios de construcción, remodelación y/o materiales (cemento)",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_construccion_027",
        "rubro": "construccion",
        "tipo": "EGRESO",
        "fecha": "2026-03-25",
        "total": "367,565.98",
        "folio_fiscal": "C02A8A77-CDE5-4B7B-8D54-C2D9609A572E",
        "emisor_nombre": "DOMÍNGUEZ VILLA Y ALONZO S DE RL DE CV",
        "emisor_rfc": "ZOP090921IE3",
        "receptor_rfc": "XXE130405HH9",
        "concepto": "Servicios de construcción, remodelación y/o materiales (cemento)",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_construccion_028",
        "rubro": "construccion",
        "tipo": "EGRESO",
        "fecha": "2026-05-02",
        "total": "793,587.90",
        "folio_fiscal": "08FE59D3-75EC-4245-AEC3-BFB22667A1F1",
        "emisor_nombre": "INDUSTRIAS CORNEJO BAEZA Y VELÁSQUEZ SAS",
        "emisor_rfc": "HMP191209QF0",
        "receptor_rfc": "IZJ030218JP1",
        "concepto": "Servicios de construcción, remodelación y/o materiales (cemento)",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
    {
        "archivo": "cfdi_v40_egreso_construccion_029",
        "rubro": "construccion",
        "tipo": "EGRESO",
        "fecha": "2025-11-29",
        "total": "917,948.81",
        "folio_fiscal": "6DEFA9CE-F3FA-43FF-9ACB-35755214DFE8",
        "emisor_nombre": "CORPORACIN VILLASEÑOR-HOLGUÍN IAP",
        "emisor_rfc": "RVX220428XG0",
        "receptor_rfc": "WQQ210720RZ7",
        "concepto": "Servicios de construcción, remodelación y/o materiales (cemento)",
        "forma_pago": "01 - EFECTIVO",
        "metodo_pago": "PUE",
    },
]


def _a_extraccion(c: dict) -> dict:
    total = float(c["total"].replace(",", ""))
    iva = round(total - (total / 1.16), 2)
    subtotal = round(total - iva, 2)
    descripcion = c["concepto"] + " (" + c["rubro"] + ", " + c["tipo"] + ")"
    return {
        "folio_fiscal": c["folio_fiscal"],
        "fecha_emision": c["fecha"],
        "emisor": {"nombre": c["emisor_nombre"], "RFC": c["emisor_rfc"]},
        "receptor": {"nombre": None, "RFC": c["receptor_rfc"]},
        "metodo_pago": c["metodo_pago"],
        "forma_pago": c["forma_pago"],
        "moneda": "MXN",
        "subtotal": subtotal,
        "iva": iva,
        "retenciones": 0,
        "total": total,
        "conceptos": [{"descripcion": descripcion}],
    }


def indexar_fixtures() -> None:
    import os

    from app.services.org_ingestion_service import ingestar_cfdi_organizacion
    from rag.config import load_config_from_env
    from rag.store import FiscalChromaStore

    config = load_config_from_env(os.getenv("CHROMA_PATH", "./chroma_db"))
    store = FiscalChromaStore(
        chroma_path=config.chroma_path,
        collection_name=os.getenv("CHROMA_ORG_COLLECTION", "documentos_organizacion"),
    )

    stats_antes = store.stats_by_org(ID_ORGANIZACION_PRUEBA)
    chunks_antes = stats_antes.get("total_chunks", 0)

    for c in CFDIS_REALES:
        extraccion = _a_extraccion(c)
        filename = c["archivo"] + ".md"
        ingestar_cfdi_organizacion(
            extraccion=extraccion,
            id_organizacion=ID_ORGANIZACION_PRUEBA,
            id_documento=c["folio_fiscal"],
            id_usuario="eval",
            extra_metadata={"filename": filename},
        )
        print("  [OK] " + filename + " indexado ($" + c["total"] + " MXN, " + c["rubro"] + ")")

    stats_despues = store.stats_by_org(ID_ORGANIZACION_PRUEBA)
    chunks_despues = stats_despues.get("total_chunks", 0)
    chunks_nuevos = chunks_despues - chunks_antes

    if chunks_nuevos <= 0:
        raise RuntimeError(
            f"[ERROR] No se indexó ningún chunk nuevo (antes={chunks_antes}, "
            f"después={chunks_despues}). Revisa que Ollama/embeddings estén disponibles."
        )

    metadatas = store.collection.get(
        where={"id_organizacion": {"$eq": ID_ORGANIZACION_PRUEBA}},
        include=["metadatas"],
    )["metadatas"]
    filenames_indexados = {m.get("filename") for m in metadatas}
    esperados = {c["archivo"] + ".md" for c in CFDIS_REALES}
    faltantes = esperados - filenames_indexados
    if faltantes:
        raise RuntimeError(f"[ERROR] Estos filenames no quedaron indexados: {faltantes}")

    print(
        "\n[OK] "
        + str(len(CFDIS_REALES))
        + " CFDIs reales indexados en '"
        + ID_ORGANIZACION_PRUEBA
        + "' ("
        + str(chunks_nuevos)
        + " chunks nuevos)."
    )


if __name__ == "__main__":
    indexar_fixtures()
