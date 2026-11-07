import io
import unittest
from unittest.mock import patch

try:
    import numpy
except ImportError:
    numpy = None
if numpy is not None:
    import laboratorio_coincidencias as lab


@unittest.skipIf(numpy is None, "Requiere las dependencias del laboratorio")
class PruebasRevisionLaboratorio(unittest.TestCase):
    def test_muestra_malformada_falla_con_error_de_validacion(self):
        for campo, valor in (("candidatos", [None]), ("pares", {}),
                             ("pares", [{"consulta_id": [], "candidato_id": "a"}])):
            with self.subTest(campo=campo, valor=valor):
                muestra = self.muestra()
                muestra[campo] = valor
                with self.assertRaises(ValueError):
                    lab.validar_muestra(muestra)

    def muestra(self):
        return dict(candidatos=[dict(id="a", descripcion="Texto")],
                    consultas=[dict(id="q", descripcion="Consulta", esperados=None)],
                    pares=[dict(consulta_id="q", candidato_id="a", esperado=None)])

    def test_respuesta_http_con_json_no_objeto_se_rechaza(self):
        with patch.object(lab, "urlopen") as abrir:
            abrir.return_value.__enter__.return_value = io.StringIO("[]")
            with self.assertRaises(ValueError):
                lab.post("http://local", "/api/embed", {})

    def test_errores_json_tambien_al_descargar_no_interrumpen_el_reporte(self):
        with patch.object(lab, "urlopen") as abrir:
            abrir.return_value.__enter__.side_effect = lambda: io.StringIO("[]")
            reporte = lab.ejecutar(self.muestra(), "http://local", ["embeddinggemma-2:270m"])
        self.assertEqual(reporte["recuperacion"][0]["estado"], "error")
        self.assertIn("errores_descarga", reporte)

    def test_estructura_tev1_malformada_queda_no_evaluada(self):
        for answers in (None, [], {"compatibilidad": None}, {"compatibilidad": []}):
            with self.subTest(answers=answers), patch.object(lab, "post", return_value={"answers": answers}), patch.object(
                    lab, "memoria_observada", return_value=None):
                reporte = lab.ejecutar(self.muestra(), "http://local", [], tev1="tev1:0.8b")
                self.assertEqual(reporte["pares"][0]["estado"], "no_evaluado")
                self.assertNotIn("decision", reporte["pares"][0])

    def test_telemetria_malformada_no_rompe_la_evaluacion(self):
        with patch.object(lab, "urlopen") as abrir:
            abrir.return_value.__enter__.side_effect = lambda: io.StringIO('{"models": [null]}')
            self.assertIsNone(lab.memoria_observada("http://local", "modelo"))


if __name__ == "__main__":
    unittest.main()
