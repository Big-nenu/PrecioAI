import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook
import mini_pai_interpretar as mini


class PruebasIntegridad(unittest.TestCase):
    def test_cli_preserva_excel_si_salida_es_origen_o_enlace(self):
        with tempfile.TemporaryDirectory() as carpeta:
            origen = Path(carpeta) / "origen.xlsx"
            libro = Workbook()
            libro.active["A1"] = "No sobrescribir"
            libro.save(origen)
            inicial = origen.read_bytes()
            enlace = Path(carpeta) / "salida.json"
            enlace.write_bytes(inicial)
            for destino in (origen, enlace):
                origen.write_bytes(inicial)
                with self.subTest(destino=destino), patch("sys.argv", [
                        "mini", str(origen), "--salida", str(destino)]), patch(
                        "sys.stderr", new_callable=io.StringIO), patch.object(
                        mini, "interpretar", return_value=dict(registros=[], dudas=[])) as interpretar, patch.object(
                        Path, "samefile", return_value=True):
                    with self.assertRaises(SystemExit) as salida:
                        mini.main()
                    self.assertEqual(salida.exception.code, 2)
                    interpretar.assert_not_called()
                    self.assertEqual(origen.read_bytes(), inicial)

    def escenario(self):
        inspeccion = dict(hojas=[dict(nombre="Obra", filas=[
            dict(fila=1, celdas={"C1": "Primera"}), dict(fila=2, celdas={"C2": "Segunda"})])])
        registro = dict(tipo="concepto", hoja="Obra", fila=1, padre=None, motivo=None,
                        evidencia=dict(clave=[], descripcion=["C1", "C2"], unidad=[], cantidad=[]))
        return inspeccion, registro

    def test_rechaza_claves_extra_en_evidencia(self):
        inspeccion, registro = self.escenario()
        registro["evidencia"]["otra"] = ["C99"]
        with self.assertRaisesRegex(ValueError, "evidencia|Evidencia"):
            mini.materializar(dict(registros=[registro], dudas=[]), inspeccion)

    def test_fila_no_puede_excluirse_y_usarse_como_continuacion(self):
        inspeccion, registro = self.escenario()
        exclusion = dict(tipo="omitir", hoja="Obra", fila=2, padre=None, motivo="Nota",
                         evidencia=dict(clave=[], descripcion=[], unidad=[], cantidad=[]))
        with self.assertRaisesRegex(ValueError, "continuación"):
            mini.materializar(dict(registros=[registro, exclusion], dudas=[]), inspeccion)


if __name__ == "__main__":
    unittest.main()
