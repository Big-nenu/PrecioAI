from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook
import mini_pai_exportar as exportar


class PruebasExportar(unittest.TestCase):
    def entrada(self):
        base = dict(hoja="Obra", unidad=None, cantidad=None, partida=None, subpartida=None)
        return dict(alcance=dict(parcial=True), registros=[
            dict(base, tipo="partida", fila=1, padre=None, clave="A", descripcion="Obra original"),
            dict(base, tipo="subpartida", fila=2, padre=1, clave="A.A01", descripcion="Trabajos", partida="A"),
            dict(base, tipo="concepto", fila=3, padre=2, clave="001.00", descripcion="  Cliente\ncompleto ",
                 partida="A", subpartida="A.A01", unidad="M2 ", cantidad="0012.5000")],
            busquedas_construbase=[dict(hoja="Obra", fila=3, seleccion=None, candidatos=[
                dict(IdCodigo=10, Codigo="NO-SELECCIONADO", DescripcionLarga="Texto de ConstruBase")])])

    def test_columnas_exactas_origen_y_jerarquia_sin_confirmar_candidato(self):
        datos = self.entrada()
        antes = deepcopy(datos)
        libro = exportar.crear_excel(datos)
        self.addCleanup(libro.close)
        self.assertEqual(datos, antes)
        c, seis, rev = libro.worksheets
        self.assertEqual(tuple(x.value for x in c[1]), exportar.COLUMNAS)
        self.assertEqual(tuple(x.value for x in seis[1]), exportar.COPIAR)
        self.assertEqual([c.cell(f, 1).value for f in (2, 3, 4)], ["A", "A.A01", "A.A01"])
        self.assertEqual([c.cell(4, col).value for col in range(2, 9)],
                         [None, "001.00", None, "  Cliente\ncompleto ", "M2 ", 12.5, 4])
        self.assertEqual(seis["D3"].value, "Trabajos")
        self.assertEqual(rev["B1"].value, "PARCIAL")
        self.assertEqual(rev["D1"].value, 0)
        self.assertEqual(rev["H6"].value, "Dudosa: pendiente de confirmar")
        self.assertEqual(rev["I6"].value, "0012.5000")

    def test_estados_sin_inventar_no_encontrada_global(self):
        for busqueda, esperado in ((None, "Sin evaluar"),
                (dict(hoja="Obra",fila=3,seleccion=None,candidatos=[],estado="sin_candidatos_en_busqueda"),
                 "No encontrada en esta búsqueda")):
            with self.subTest(esperado=esperado):
                datos = self.entrada()
                datos["busquedas_construbase"] = [] if busqueda is None else [busqueda]
                libro = exportar.crear_excel(datos)
                self.assertEqual(libro["Revisión"]["H6"].value, esperado)
                self.assertIsNone(libro["Catálogo"]["B4"].value)
                libro.close()

    def test_rechaza_seleccion_no_soportada_y_relaciones_invalidas(self):
        for caso in ("seleccion", "padre", "busqueda"):
            datos = self.entrada()
            if caso == "seleccion":
                datos["busquedas_construbase"][0]["seleccion"] = 10
            elif caso == "padre":
                datos["registros"][2]["padre"] = 99
            else:
                datos["busquedas_construbase"] *= 2
            with self.subTest(caso=caso), self.assertRaises(ValueError):
                exportar.crear_excel(datos)

    def test_cantidad_cero_ambigua_precisa_y_no_truncamiento(self):
        self.assertEqual(exportar.cantidad_excel("0"), 0)
        self.assertEqual(exportar.cantidad_excel("1,234"), "1,234")
        self.assertEqual(exportar.cantidad_excel("1234567890123456"), "1234567890123456")
        self.assertEqual(exportar.cantidad_excel("0." + "0" * 400 + "1"), "0." + "0" * 400 + "1")
        datos = self.entrada()
        datos["registros"][2]["descripcion"] = "x" * 32768
        with self.assertRaisesRegex(ValueError, "no se truncará"):
            exportar.crear_excel(datos)

    def test_hojas_padres_sin_clave_y_repetidos_no_se_fusionan(self):
        datos = self.entrada()
        datos["registros"][0].update(clave=None, descripcion="Obra por nombre")
        datos["registros"][1].update(clave="01", partida=None)
        datos["registros"][2].update(partida=None, subpartida="01")
        otros = deepcopy(datos["registros"])
        for r in otros:
            r["hoja"] = "Otra hoja"
        datos["registros"].extend(otros)
        libro = exportar.crear_excel(datos)
        self.addCleanup(libro.close)
        self.assertEqual(libro["Catálogo"]["A4"].value, "Obra por nombre.01")
        self.assertEqual(libro["Catálogo"]["A7"].value, "Obra por nombre.01")
        self.assertEqual(libro["Revisión"].max_row, 9)

    def test_cli_archivo_real_texto_literal_y_proteccion_de_entradas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            origen, salida = Path(carpeta) / "entrada.json", Path(carpeta) / "salida.xlsx"
            datos = self.entrada()
            datos["registros"][2]["descripcion"] = '=HYPERLINK("no-ejecutar")'
            origen.write_text(json.dumps(datos), encoding="utf-8")
            huella = origen.read_bytes()
            with patch("sys.argv", ["exportar", str(origen), "--salida", str(salida)]), patch("sys.stdout", new_callable=io.StringIO):
                exportar.main()
            libro = load_workbook(salida)
            self.assertEqual(libro["Catálogo"]["E4"].value, datos["registros"][2]["descripcion"])
            self.assertEqual(libro["Catálogo"]["E4"].data_type, "s")
            self.assertEqual(libro["Catálogo"]["C4"].value, "001.00")
            self.assertEqual(libro["Copiar auxiliares"]["F4"].data_type, "n")
            libro.close()
            anterior = salida.read_bytes()
            with patch("sys.argv", ["exportar", str(origen), "--salida", str(salida)]), patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    exportar.main()
            self.assertEqual(salida.read_bytes(), anterior)
            self.assertEqual(origen.read_bytes(), huella)
