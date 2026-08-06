from app.services.routing_logic import analizar_lexico


class TestAnalisisLexico:
    def test_pregunta_vacia_devuelve_normativa_sin_confianza(self):
        result = analizar_lexico("")
        assert result["ruta_seleccionada"] == "NORMATIVA"
        assert result["confianza_lexica"] == 0.0

    def test_palabras_normativa_devuelve_normativa(self):
        result = analizar_lexico("¿Cuál es la ley del SAT?")
        assert result["ruta_seleccionada"] == "NORMATIVA"
        assert result["confianza_lexica"] == 0.90
        assert "ley" in result["palabras_clave_detectadas"]
        assert "sat" in result["palabras_clave_detectadas"]

    def test_palabras_cfdi_devuelve_cfdi(self):
        result = analizar_lexico("¿Cuánto gasto en facturas este mes?")
        assert result["ruta_seleccionada"] == "CFDI_PROPIOS"
        assert result["confianza_lexica"] == 0.70
        assert "gasto" in result["palabras_clave_detectadas"]

    def test_mixto_devuelve_hibrido(self):
        result = analizar_lexico("¿Puedo deducir mis gastos de facturas según la ley?")
        assert result["ruta_seleccionada"] == "HIBRIDO"
        assert result["confianza_lexica"] == 0.70

    def test_sin_palabras_clave_devuelve_normativa(self):
        result = analizar_lexico("Hola mundo")
        assert result["ruta_seleccionada"] == "NORMATIVA"
        assert result["confianza_lexica"] == 0.0

    def test_no_afecta_mayusculas_acentos(self):
        result = analizar_lexico("RÉGIMEN E IMPUESTO")
        assert result["ruta_seleccionada"] == "NORMATIVA"
        assert "regimen" in result["palabras_clave_detectadas"]
        assert "impuesto" in result["palabras_clave_detectadas"]

    def test_palabra_gasto_gastos_normalizada(self):
        result = analizar_lexico("¿Cuánto me gasté?")
        r2 = analizar_lexico("¿Cuánto me gastes?")
        assert result["ruta_seleccionada"] == r2["ruta_seleccionada"]

    def test_palabra_proveedor(self):
        result = analizar_lexico("¿Quién es mi proveedor?")
        assert result["ruta_seleccionada"] == "CFDI_PROPIOS"
        assert "proveedor" in result["palabras_clave_detectadas"]
