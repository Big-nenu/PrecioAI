import unittest
import io
from unittest.mock import patch

try:
    import numpy as np
    import laboratorio_coincidencias as lab
except ImportError:
    np = None


@unittest.skipIf(np is None, "Instalar requirements-laboratorio.txt para evaluar el laboratorio")
class PruebasLaboratorio(unittest.TestCase):
    def test_cli_no_sobrescribe_la_muestra(self):
        with patch("sys.argv", ["laboratorio", "muestra.json", "--salida", "muestra.json"]), patch(
                "sys.stderr", new_callable=io.StringIO), patch.object(lab, "ejecutar") as ejecutar:
            with self.assertRaises(SystemExit) as salida:
                lab.main()
        self.assertEqual(salida.exception.code, 2)
        ejecutar.assert_not_called()

    def muestra(self):
        return dict(candidatos=[dict(id="a", descripcion="Trazo manual", unidad="M2"),
                                dict(id="b", descripcion="Excavación", unidad="M3")],
                    consultas=[dict(id="q", descripcion="Trazo", unidad="m²", esperados=["a"])],
                    pares=[dict(consulta_id="q", candidato_id="b", esperado="incompatible")])

    def test_prefijos_separados_y_unidades(self):
        self.assertEqual(lab.prefijos("nomic-embed-text:latest"), ("search_query: ", "search_document: "))
        self.assertNotEqual(*lab.prefijos("embeddinggemma-2:270m"))
        self.assertEqual(lab.comparar_unidad("M2 ", "m²"), "igual")
        self.assertEqual(lab.comparar_unidad(None, "m²"), "sin_datos")
        self.assertEqual(lab.comparar_unidad("M2", "M3"), "diferente")

    def test_etiquetas_fuera_de_muestra_y_ids_duplicados(self):
        lab.validar_muestra(self.muestra())
        for tipo in ("id", "etiqueta", "par"):
            with self.subTest(tipo=tipo):
                datos = self.muestra()
                if tipo == "id":
                    datos["candidatos"][1]["id"] = "a"
                elif tipo == "etiqueta":
                    datos["consultas"][0]["esperados"] = ["inexistente"]
                else:
                    datos["pares"][0]["esperado"] = "si"
                with self.assertRaises(ValueError):
                    lab.validar_muestra(datos)

    def test_coseno_y_centrado_no_modifican_vectores(self):
        docs = np.array([[1., 0.], [0., 1.]], dtype=np.float32)
        copia = docs.copy()
        consultas = np.array([[1., 0.]], dtype=np.float32)
        np.testing.assert_allclose(lab.similitudes(docs, consultas), [[1, 0]])
        np.testing.assert_allclose(lab.similitudes(docs, consultas, True), [[1, -1]], atol=1e-6)
        np.testing.assert_array_equal(docs, copia)
        with self.assertRaises(ValueError):
            lab.similitudes(docs, np.array([[1, 0, 0]]))

    def test_embeddings_en_lotes_sin_truncamiento(self):
        with patch.object(lab, "post", side_effect=[dict(embeddings=[[1, 0], [0, 1]]),
                                                    dict(embeddings=[[1, 1]])]) as api:
            matriz = lab.embeddings("http://local", "modelo", ["a", "b", "c"], lote=2)
        self.assertEqual(matriz.shape, (3, 2))
        self.assertFalse(api.call_args_list[0].args[2]["truncate"])
        self.assertEqual(api.call_args_list[1].args[2]["input"], ["c"])

    def test_rechaza_embeddings_rotos_y_no_finitos(self):
        for vectores in ([[1, 0]], [[0, 0], [0, 0]], [[1, 0], [1]], [[float("nan"), 1], [1, 0]]):
            with self.subTest(vectores=vectores), patch.object(lab, "post", return_value=dict(embeddings=vectores)):
                with self.assertRaises(ValueError):
                    lab.embeddings("http://local", "modelo", ["a", "b"])

    def test_metricas_no_convierten_consultas_sin_etiqueta_en_aciertos(self):
        datos = self.muestra()
        datos["consultas"].extend([dict(id="sin_etiqueta", esperados=None), dict(id="sin_respuesta", esperados=[])])
        resultado = lab.resumir_ranking(datos, [[1, 0], [1, 0], [1, 0]])
        self.assertEqual(resultado["etiquetadas_positivas"], 1)
        self.assertEqual(resultado["hit_1"], 1)
        self.assertEqual(resultado["sin_respuesta_etiquetadas"], 1)
        datos["consultas"] = [dict(id="sin_etiqueta", esperados=None)]
        self.assertIsNone(lab.resumir_ranking(datos, [[1, 0]])["hit_1"])

    def test_tev1_tipo_invalido_no_se_acepta(self):
        datos = self.muestra()
        with patch.object(lab, "post", return_value=dict(answers=dict(compatibilidad=dict(choice="otro")))):
            with self.assertRaises(ValueError):
                lab.evaluar_par("http://local", "tev1", datos["consultas"][0], datos["candidatos"][1])

    def test_error_de_tev1_queda_no_evaluado_no_como_compatible(self):
        with patch.object(lab, "post", side_effect=RuntimeError("Sin conexión")), patch.object(
                lab, "memoria_observada", return_value=None):
            reporte = lab.ejecutar(self.muestra(), "http://local", [], tev1="tev1")
        self.assertEqual(reporte["pares"][0]["estado"], "no_evaluado")
        self.assertNotIn("decision", reporte["pares"][0])
        self.assertEqual(reporte["evaluacion_tev1"]["correctos"], 0)
        self.assertEqual(reporte["evaluacion_tev1"]["errores"], 1)


if __name__ == "__main__":
    unittest.main()
