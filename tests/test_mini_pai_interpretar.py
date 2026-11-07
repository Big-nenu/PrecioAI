import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json
from copy import deepcopy

from openpyxl import Workbook

from mini_pai_interpretar import (inspeccionar_excel, validar, interpretar,
                                  validar_jerarquia, materializar)


class PruebasInterpretacion(unittest.TestCase):
    def test_cantidad_se_conserva_por_fila_y_rechaza_la_de_otro_concepto(self):
        origen = dict(hojas=[dict(nombre='Obra', filas=[
            dict(fila=19, celdas={'B19': 'X-001', 'C19': 'Trazo', 'E19': '1900.21'}),
            dict(fila=107, celdas={'B107': 'X-075', 'C107': 'Otro trabajo', 'E107': '133.17'})])])
        propuesta = dict(registros=[dict(tipo='concepto', hoja='Obra', fila=n, padre=None,
                                        motivo=None, evidencia=dict(clave=[f'B{n}'],
                                        descripcion=[f'C{n}'], unidad=[], cantidad=[f'E{n}']))
                                    for n in (19, 107)], dudas=[])
        datos = materializar(propuesta, origen)
        validar(datos, origen)
        self.assertEqual([r['cantidad'] for r in datos['registros']], ['1900.21', '133.17'])
        datos['registros'][0].update(cantidad='133.17')
        datos['registros'][0]['evidencia']['cantidad'] = ['E107']
        with self.assertRaisesRegex(ValueError, 'fila del registro'):
            validar(datos, origen)

    def test_alcance_parcial_y_rangos_invalidos_sin_consultar_ia(self):
        origen, datos = self.ejemplo()
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=deepcopy(origen)), patch(
                "mini_pai_interpretar.consultar_ia", return_value=json.dumps(self.propuesta(datos))):
            resultado = interpretar("sintetico.xlsx", hoja="Obra", fila_inicial=7, fila_final=8)
        self.assertEqual(resultado["alcance"], dict(hoja="Obra", fila_inicial=7, fila_final=8, parcial=True))
        self.assertEqual(resultado["registros"][0]["fila"], 7)
        for opciones in (dict(hoja="Inexistente"), dict(fila_inicial=0),
                         dict(fila_inicial=9, fila_final=3), dict(fila_inicial=100),
                         dict(tamano_bloque=0), dict(tamano_bloque=True)):
            with self.subTest(opciones=opciones), patch(
                    "mini_pai_interpretar.inspeccionar_excel", return_value=deepcopy(origen)), patch(
                    "mini_pai_interpretar.consultar_ia") as ia:
                with self.assertRaises(ValueError):
                    interpretar("sintetico.xlsx", **opciones)
                ia.assert_not_called()

    def test_filas_excluidas_explicitas_y_cobertura(self):
        origen, datos = self.ejemplo()
        origen["hojas"][0]["filas"].insert(0, {"fila": 1, "celdas": {"D1": "Portada"}})
        propuesta = self.propuesta(datos)
        with self.assertRaisesRegex(ValueError, "Filas sin interpretar"):
            materializar(propuesta, origen)
        exclusion = dict(tipo="omitir", hoja="Obra", fila=1, padre=None,
                         motivo="Portada del documento", evidencia=dict(clave=[], descripcion=[], unidad=[], cantidad=[]))
        propuesta["registros"].insert(0, exclusion)
        resultado = materializar(propuesta, origen)
        validar(resultado, origen)
        self.assertEqual(resultado["excluidas"], [dict(hoja="Obra", fila=1, motivo="Portada del documento")])
        for cambio in ("duplicada", "sin_motivo", "celda_inventada"):
            with self.subTest(cambio=cambio):
                incorrecta = deepcopy(propuesta)
                if cambio == "duplicada":
                    incorrecta["registros"].append(deepcopy(exclusion))
                elif cambio == "sin_motivo":
                    incorrecta["registros"][0]["motivo"] = ""
                else:
                    incorrecta["registros"][1]["evidencia"]["cantidad"] = ["XX100"]
                with self.assertRaises(ValueError):
                    materializar(incorrecta, origen)

    def test_materializa_padres_sin_clave_y_texto_original(self):
        origen = {"archivo": "sintetico.xlsx", "hojas": [{"nombre": "Obra", "filas": [
            {"fila": 2, "celdas": {"J2": "Grupo  sin clave\n"}},
            {"fila": 4, "celdas": {"M4": "Sección"}},
            {"fila": 8, "celdas": {"C8": "Trazo", "F8": "con equipo", "G8": "0"}}]}]}
        def evidencia(descripcion, cantidad=None):
            return dict(clave=[], descripcion=descripcion, unidad=[], cantidad=cantidad or [])
        propuesta = {"registros": [
            dict(tipo="partida", hoja="Obra", fila=2, padre=None, motivo=None, evidencia=evidencia(["J2"])),
            dict(tipo="subpartida", hoja="Obra", fila=4, padre=2, motivo=None, evidencia=evidencia(["M4"])),
            dict(tipo="concepto", hoja="Obra", fila=8, padre=4, motivo=None, evidencia=evidencia(["C8", "F8"], ["G8"]))],
            "dudas": []}
        datos = materializar(propuesta, origen)
        validar(datos, origen)
        self.assertEqual(datos["registros"][0]["descripcion"], "Grupo  sin clave\n")
        self.assertEqual(datos["registros"][2]["descripcion"], "Trazo con equipo")
        self.assertEqual(datos["registros"][2]["cantidad"], "0")
        self.assertEqual(datos["registros"][2]["padre"], 4)
        for padre in (2, 99, 8, True):
            with self.subTest(padre=padre):
                incorrecta = deepcopy(propuesta)
                incorrecta["registros"][2]["padre"] = padre
                with self.assertRaises(ValueError):
                    validar(materializar(incorrecta, origen), origen)

    def propuesta(self, datos):
        registros, encabezados = [], {}
        for r in datos["registros"]:
            clave_padre = r["subpartida"] or r["partida"]
            padre = encabezados.get((r["hoja"], clave_padre)) if clave_padre else None
            registros.append({k: r[k] for k in ("tipo", "hoja", "fila", "evidencia")})
            registros[-1]["padre"] = padre
            registros[-1]["motivo"] = None
            if r["tipo"] != "concepto":
                encabezados[r["hoja"], r["clave"]] = r["fila"]
        return {"registros": registros, "dudas": datos["dudas"]}

    def test_un_reintento_con_error_de_validacion_y_sin_aceptar_datos_inventados(self):
        origen, correcto = self.ejemplo()
        incorrecto = deepcopy(correcto)
        incorrecto["registros"][0]["evidencia"]["cantidad"] = ["Z7"]
        for respuestas, falla in (([incorrecto, correcto], False),
                                   ([incorrecto, incorrecto], True)):
            with self.subTest(falla=falla), patch(
                    "mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                    "mini_pai_interpretar.consultar_ia",
                    side_effect=[json.dumps(self.propuesta(r)) for r in respuestas]) as ia:
                if falla:
                    with self.assertRaisesRegex(ValueError, "Evidencia inválida"):
                        interpretar("sintetico.xlsx")
                else:
                    self.assertEqual(interpretar("sintetico.xlsx")["registros"][0]["cantidad"], "12.50")
                self.assertEqual(ia.call_count, 2)
                self.assertIn("Evidencia inválida", ia.call_args.args[0][-1]["content"])

    def jerarquia(self):
        return [
            dict(tipo="partida", hoja="Obra", fila=3, clave="Grupo", partida=None, subpartida=None),
            dict(tipo="subpartida", hoja="Obra", fila=6, clave="Seccion", partida="Grupo", subpartida=None),
            dict(tipo="concepto", hoja="Obra", fila=9, clave="X", partida="Grupo", subpartida="Seccion"),
            dict(tipo="partida", hoja="Obra", fila=13, clave="Otro", partida=None, subpartida=None),
            dict(tipo="concepto", hoja="Obra", fila=14, clave="X", partida="Otro", subpartida=None),
            dict(tipo="concepto", hoja="Otra hoja", fila=2, clave=None, partida=None, subpartida=None)]

    def test_jerarquia_cambio_partida_y_hoja_y_clave_repetida(self):
        validar_jerarquia(self.jerarquia())

    def test_rechaza_relaciones_inventadas_adelantadas_y_fuera_de_orden(self):
        for indice, campo, valor in ((2, "partida", "Inexistente"),
                                     (2, "partida", "Otro"),
                                     (4, "subpartida", "Seccion"),
                                     (5, "partida", "Otro"),
                                     (1, "subpartida", "Seccion"),
                                     (2, "fila", 6)):
            with self.subTest(indice=indice, campo=campo, valor=valor):
                registros = self.jerarquia()
                registros[indice][campo] = valor
                with self.assertRaises(ValueError):
                    validar_jerarquia(registros)

    def test_interpretar_agrupaciones_con_columnas_variables(self):
        origen = {"archivo": "sintetico.xlsx", "hojas": [{"nombre": "Obra", "filas": [
            {"fila": 3, "celdas": {"K3": "Grupo", "C3": "Obra exterior"}},
            {"fila": 6, "celdas": {"J6": "Seccion", "D6": "Preliminares"}},
            {"fila": 9, "celdas": {"G9": "Trazo", "C9": "12.50", "M9": "m2"}}]}]}
        registros = deepcopy(self.jerarquia()[:3])
        for registro, descripcion, evidencia in zip(registros,
                ("Obra exterior", "Preliminares", "Trazo"),
                ({"clave": ["K3"], "descripcion": ["C3"], "unidad": [], "cantidad": []},
                 {"clave": ["J6"], "descripcion": ["D6"], "unidad": [], "cantidad": []},
                 {"clave": [], "descripcion": ["G9"], "unidad": ["M9"], "cantidad": ["C9"]})):
            registro.update(descripcion=descripcion, unidad=None, cantidad=None, evidencia=evidencia)
        registros[2].update(clave=None, unidad="m2", cantidad="12.50")
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                "mini_pai_interpretar.consultar_ia", return_value=json.dumps(self.propuesta({"registros": registros, "dudas": []}))):
            resultado = interpretar("sintetico.xlsx")
        self.assertEqual([r["tipo"] for r in resultado["registros"]], ["partida", "subpartida", "concepto"])

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
                "mini_pai_interpretar.consultar_ia", return_value=json.dumps(self.propuesta(respuesta))) as ia:
            resultado = interpretar("sintetico.xlsx")
        self.assertEqual(resultado["archivo"], "sintetico.xlsx")
        self.assertEqual(resultado["registros"], [{**respuesta["registros"][0], "padre": None, "motivo": None}])
        self.assertIn("F7", ia.call_args.args[0][-1]["content"])
        self.assertEqual(ia.call_args.kwargs["esquema"]["required"], ["registros", "dudas"])

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
