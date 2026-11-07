import json
import io
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import mini_pai_tabla as tabla
import mini_pai_interpretar as interpretar


class PruebasTabla(unittest.TestCase):
    def ejemplo(self):
        origen = dict(archivo="sintetico.xlsx", hojas=[dict(nombre="Obra", filas=[
            dict(fila=1, celdas={"K1": "Portada"}),
            dict(fila=2, celdas={"C2": "Referencia", "K2": "Trabajo", "H2": "Medida", "Q2": "Volumen"}),
            dict(fila=3, celdas={"C3": "Z", "K3": "Grupo"}),
            dict(fila=4, celdas={"C4": "001", "K4": "Descripción\n íntegra " + "x" * 200, "H4": "M3/KM", "Q4": "1900.21"}),
            dict(fila=5, celdas={"C5": "S", "K5": "Sección"}),
            dict(fila=6, celdas={"C6": "002", "K6": "Otro trabajo", "H6": "M2", "Q6": "133.17"}),
            dict(fila=7, celdas={"K7": "Resumen"}),
            dict(fila=8, celdas={"C8": "Z", "K8": "Grupo", "R8": "Total"})])])
        estructura = dict(hoja="Obra", encabezado=2,
                          columnas=dict(clave="C2", descripcion="K2", unidad="H2", cantidad="Q2"))
        plan = dict(resumen_desde=7, filas={
            "3": dict(tipo="partida", padre=None, motivo=None),
            "5": dict(tipo="subpartida", padre=3, motivo=None)}, dudas=[])
        return origen, estructura, plan

    def test_campos_completos_y_padres_sin_columnas_fijas(self):
        origen, estructura, plan = self.ejemplo()
        antes = deepcopy((origen, estructura, plan))
        datos = tabla.materializar_tabla(origen, estructura, plan)
        conceptos = [r for r in datos["registros"] if r["tipo"] == "concepto"]
        self.assertEqual([r["cantidad"] for r in conceptos], ["1900.21", "133.17"])
        self.assertEqual(conceptos[0]["descripcion"], origen["hojas"][0]["filas"][3]["celdas"]["K4"])
        self.assertEqual(conceptos[0]["unidad"], "M3/KM")
        self.assertEqual(conceptos[0]["evidencia"]["cantidad"], ["Q4"])
        self.assertEqual([r["padre"] for r in conceptos], [3, 5])
        self.assertEqual([r["fila"] for r in datos["excluidas"]], [1, 2, 7, 8])
        self.assertFalse(datos["alcance"]["parcial"])
        self.assertEqual((origen, estructura, plan), antes)

    def test_rechaza_columnas_inventadas_duplicadas_y_cabecera_falsa(self):
        for cambio in ("celda", "duplicada", "fila", "bool", "sin_unidad"):
            with self.subTest(cambio=cambio):
                origen, estructura, plan = self.ejemplo()
                if cambio == "celda": estructura["columnas"]["cantidad"] = "Q999"
                elif cambio == "duplicada": estructura["columnas"]["cantidad"] = "H2"
                elif cambio == "fila": estructura["columnas"]["cantidad"] = "Q4"
                elif cambio == "bool": estructura["encabezado"] = True
                else: estructura["columnas"]["unidad"] = None
                with self.assertRaises(ValueError):
                    tabla.materializar_tabla(origen, estructura, plan)

    def test_rechaza_resumen_que_perderia_conceptos_y_plan_incompleto(self):
        for cambio in ("corte", "fila_ajena", "sin_fila", "padre", "sin_motivo"):
            with self.subTest(cambio=cambio):
                origen, estructura, plan = self.ejemplo()
                if cambio == "corte": plan["resumen_desde"] = 5
                elif cambio == "fila_ajena": plan["filas"]["99"] = plan["filas"]["3"]
                elif cambio == "sin_fila": del plan["filas"]["5"]
                elif cambio == "padre": plan["filas"]["5"]["padre"] = 99
                else: plan["filas"]["5"] = dict(tipo="omitir", padre=None, motivo=None)
                with self.assertRaises(ValueError):
                    tabla.materializar_tabla(origen, estructura, plan)

    def test_rechaza_grupos_sin_conceptos_y_no_inventa_ausentes(self):
        origen, estructura, plan = self.ejemplo()
        plan["resumen_desde"] = None
        plan["filas"].update({"7": dict(tipo="omitir", padre=None, motivo="Resumen"),
                              "8": dict(tipo="partida", padre=None, motivo=None)})
        with self.assertRaisesRegex(ValueError, "Agrupadores sin conceptos"):
            tabla.materializar_tabla(origen, estructura, plan)
        origen, estructura, plan = self.ejemplo()
        del origen["hojas"][0]["filas"][5]["celdas"]["H6"]
        plan["filas"]["6"] = dict(tipo="concepto", padre=5, motivo=None)
        datos = tabla.materializar_tabla(origen, estructura, plan)
        self.assertIsNone(datos["registros"][-1]["unidad"])
        self.assertEqual(datos["registros"][-1]["cantidad"], "133.17")

    def test_otra_hoja_se_declara_parcial_sin_mutar_el_plan(self):
        origen, estructura, plan = self.ejemplo()
        origen["hojas"].append(dict(nombre="Otra", filas=[dict(fila=1, celdas={"A1": "Datos"})]))
        datos = tabla.materializar_tabla(origen, estructura, plan)
        self.assertTrue(datos["alcance"]["parcial"])
        self.assertIn("Otra", datos["dudas"][0])
        self.assertEqual(plan["dudas"], [])

    def test_rechaza_metadato_de_portada_como_concepto_sin_medicion(self):
        origen, estructura, plan = self.ejemplo()
        origen["hojas"][0]["filas"][2]["celdas"]["K3"] = "Portada"
        plan["filas"]["3"] = dict(tipo="concepto", padre=None, motivo=None)
        plan["filas"]["5"] = dict(tipo="partida", padre=None, motivo=None)
        with self.assertRaisesRegex(ValueError, "portada"):
            tabla.materializar_tabla(origen, estructura, plan)

    def test_proveedor_y_reintento_conservan_datos_reales(self):
        origen, estructura, plan = self.ejemplo()
        incompleto = deepcopy(plan)
        del incompleto["filas"]["5"]
        with patch.object(tabla, "inspeccionar_excel", return_value=origen), patch.object(
                tabla, "consultar_ia", side_effect=[json.dumps(x) for x in (estructura, incompleto, plan)]) as ia:
            resultado = tabla.interpretar_tabla("sintetico.xlsx")
        self.assertEqual(ia.call_count, 3)
        self.assertIn("Faltan filas", ia.call_args.args[0][-1]["content"])
        self.assertEqual(resultado["registros"][1]["cantidad"], "1900.21")

    def test_cli_selecciona_ruta_tabular_y_rechaza_rangos(self):
        origen, estructura, plan = self.ejemplo()
        resultado = tabla.materializar_tabla(origen, estructura, plan)
        with tempfile.TemporaryDirectory() as carpeta:
            entrada, salida = Path(carpeta)/"original.xlsx", Path(carpeta)/"datos.json"
            entrada.write_bytes(b"Original intacto")
            argumentos = ["interpretar", str(entrada), "--por-tabla", "--salida", str(salida)]
            with patch("sys.argv", argumentos), patch.object(tabla, "interpretar_tabla", return_value=resultado) as ia:
                interpretar.main()
                ia.assert_called_once_with(str(entrada))
            self.assertEqual(json.loads(salida.read_text(encoding="utf-8")), resultado)
            self.assertEqual(entrada.read_bytes(), b"Original intacto")
            for extra in (["--hoja", "Obra"], ["--fila-inicial", "2"], ["--fila-final", "6"]):
                with patch("sys.argv", argumentos + extra), patch.object(tabla, "interpretar_tabla") as ia, patch(
                        "sys.stderr", new_callable=io.StringIO):
                    with self.assertRaises(SystemExit):
                        interpretar.main()
                    ia.assert_not_called()
