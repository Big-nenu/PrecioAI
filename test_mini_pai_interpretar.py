import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json

from openpyxl import Workbook

from mini_pai_interpretar import inspeccionar_excel, validar, interpretar


class PruebasInterpretacion(unittest.TestCase):
    def ejemplo(self):
        origen = {"archivo": "sintetico.xlsx", "hojas": [{"nombre": "Obra", "filas": [
            {"fila": 7, "celdas": {"F7": "Trazo", "J7": "12.50", "C7": "m2"}},
            {"fila": 8, "celdas": {"F8": "con equipo"}}]}]}
        registro = dict(tipo="concepto", hoja="Obra", fila=7, clave=None,
                        descripcion="Trazo con equipo", unidad="m2", cantidad="12.50",
                        partida=None, subpartida=None, evidencia={"clave": [],
                        "descripcion": ["F7", "F8"], "unidad": ["C7"], "cantidad": ["J7"]})
        return origen, {"registros": [registro], "dudas": []}

    def test_interpretar_con_proveedor_simulado(self):
        origen, respuesta = self.ejemplo()
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                "mini_pai_interpretar.consultar_ia", return_value=json.dumps(respuesta)) as ia:
            resultado = interpretar("sintetico.xlsx")
        self.assertEqual(resultado["archivo"], "sintetico.xlsx")
        self.assertEqual(resultado["registros"], respuesta["registros"])
        self.assertIn("F7", ia.call_args.args[0][1]["content"])

    def test_rechaza_valor_inventado_y_celda_ajena(self):
        for cambio in ("valor", "celda", "fila", "sin_evidencia", "tipo_fila"):
            with self.subTest(cambio=cambio):
                origen, datos = self.ejemplo()
                registro = datos["registros"][0]
                if cambio == "valor":
                    registro["cantidad"] = "999"
                elif cambio == "celda":
                    registro["evidencia"]["cantidad"] = ["Z7"]
                elif cambio == "fila":
                    registro["evidencia"]["descripcion"] = ["F8"]
                elif cambio == "tipo_fila":
                    registro["fila"] = True
                else:
                    del registro["evidencia"]
                with self.assertRaises(ValueError):
                    validar(datos, origen)

    def test_rechaza_json_invalido(self):
        origen, _ = self.ejemplo()
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                "mini_pai_interpretar.consultar_ia", return_value="No es JSON"):
            with self.assertRaisesRegex(ValueError, "JSON válido"):
                interpretar("sintetico.xlsx")

    def test_inspeccion_sin_columnas_fijas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "ejemplo.xlsx"
            libro = Workbook()
            hoja = libro.active
            hoja.title = "Presupuesto"
            hoja["C4"] = "PRELIMINARES"
            hoja["F9"] = "TRAZO"
            hoja["J9"] = 12.5
            libro.save(ruta)
            datos = inspeccionar_excel(ruta)
            filas = datos["hojas"][0]["filas"]
            self.assertEqual(filas[0], {"fila": 4, "celdas": {"C4": "PRELIMINARES"}})
            self.assertEqual(filas[1]["celdas"]["J9"], "12.5")

    def test_rechaza_fila_inventada(self):
        origen = {"hojas": [{"nombre": "Hoja", "filas": [{"fila": 2, "celdas": {"A2": "X"}}]}]}
        registro = dict(tipo="concepto", hoja="Hoja", fila=3, clave=None,
                        descripcion="X", unidad=None, cantidad=None,
                        partida=None, subpartida=None)
        with self.assertRaisesRegex(ValueError, "no existe"):
            validar({"registros": [registro], "dudas": []}, origen)


if __name__ == "__main__":
    unittest.main()
