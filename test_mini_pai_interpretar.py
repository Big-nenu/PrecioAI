import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from mini_pai_interpretar import inspeccionar_excel, validar


class PruebasInterpretacion(unittest.TestCase):
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
