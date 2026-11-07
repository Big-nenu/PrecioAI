import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from mini_pai_interpretar import interpretar


class PruebasBloques(unittest.TestCase):
    def escenario(self):
        filas = [dict(fila=n, celdas={f"C{n}": f"Texto {n}"})
                 for n in (1, 4, 7, 8, 12, 15, 18, 22, 23)]
        # La clave se repite: las relaciones deben depender de la fila.
        for fila in filas:
            if fila["fila"] in (1, 15):
                fila["celdas"][f"J{fila['fila']}"] = "Repetida"
        origen = dict(archivo="sintetico.xlsx", hojas=[
            dict(nombre="Obra", filas=filas),
            dict(nombre="Otra", filas=[dict(fila=1, celdas={"F1": "Otro concepto"})])])

        def registro(tipo, fila, padre=None, hoja="Obra"):
            return dict(tipo=tipo, hoja=hoja, fila=fila, padre=padre, motivo=None,
                        evidencia=dict(clave=[], descripcion=[f"C{fila}"], unidad=[], cantidad=[]))

        primero = [registro("partida", 1), registro("subpartida", 4, 1), registro("concepto", 7, 4)]
        primero[0]["evidencia"]["clave"] = ["J1"]
        primero[2]["evidencia"]["descripcion"].append("C8")
        segundo = [registro("concepto", 12, 4), registro("partida", 15), registro("concepto", 18, 15)]
        segundo[1]["evidencia"]["clave"] = ["J15"]
        tercero = [registro("subpartida", 22, 15), registro("concepto", 23, 22)]
        otra = [registro("concepto", 1, hoja="Otra")]
        otra[0]["evidencia"]["descripcion"] = ["F1"]
        respuestas = [dict(registros=r, dudas=[]) for r in (primero, segundo, tercero, otra)]
        return origen, respuestas

    def ejecutar(self, origen, respuestas):
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                "mini_pai_interpretar.consultar_ia",
                side_effect=[json.dumps(r) for r in respuestas]) as ia:
            resultado = interpretar("sintetico.xlsx", tamano_bloque=3)
        return resultado, ia

    def test_continuacion_cambio_partida_y_aislamiento_entre_hojas(self):
        origen, respuestas = self.escenario()
        resultado, ia = self.ejecutar(origen, respuestas)
        self.assertEqual(ia.call_count, 4)
        self.assertEqual(len(resultado["registros"]), 9)
        self.assertEqual(resultado["registros"][2]["descripcion"], "Texto 7 Texto 8")
        self.assertEqual(resultado["bloques"][0]["filas_continuacion"], [8])
        self.assertEqual(resultado["bloques"][1]["filas_objetivo"], [12, 15, 18])
        self.assertEqual(resultado["registros"][3]["padre"], 4)
        self.assertIsNone(resultado["registros"][5]["subpartida"])
        self.assertIsNone(resultado["registros"][-1]["padre"])
        contextos = [json.loads(c.args[0][-1]["content"])["encabezados_vigentes"]
                     for c in ia.call_args_list]
        self.assertEqual([[r["fila"] for r in c] for c in contextos], [[], [1, 4], [15], []])
        self.assertEqual(len({(r["hoja"], r["fila"]) for r in resultado["registros"]}), 9)
        for llamada in ia.call_args_list:
            entrada = json.loads(llamada.args[0][-1]["content"])
            esquema = llamada.kwargs["esquema"]["properties"]["registros"]["items"]["properties"]
            self.assertEqual(esquema["fila"]["enum"], entrada["filas_objetivo"])
            self.assertEqual(llamada.kwargs["esquema"]["properties"]["registros"]["maxItems"],
                             len(entrada["filas_objetivo"]))
            self.assertTrue(all(f["fila"] not in esquema["fila"]["enum"]
                                for f in entrada["anticipacion"]))
            self.assertTrue(all(r["fila"] in esquema["padre"]["enum"]
                                for r in entrada["encabezados_vigentes"]))

    def test_rechaza_reemision_de_contexto_y_la_corrige_sin_duplicados(self):
        origen, respuestas = self.escenario()
        incorrecta = deepcopy(respuestas[1])
        incorrecta["registros"].insert(0, deepcopy(respuestas[0]["registros"][0]))
        resultado, ia = self.ejecutar(origen, [respuestas[0], incorrecta, *respuestas[1:]])
        self.assertEqual(ia.call_count, 5)
        self.assertEqual(len(resultado["registros"]), 9)

    def test_falla_identifica_bloque_y_no_continua_con_estado_invalido(self):
        origen, respuestas = self.escenario()
        incorrecta = deepcopy(respuestas[1])
        incorrecta["registros"][0]["padre"] = 99
        with patch("mini_pai_interpretar.inspeccionar_excel", return_value=origen), patch(
                "mini_pai_interpretar.consultar_ia", side_effect=[
                    json.dumps(r) for r in (respuestas[0], incorrecta, incorrecta)]) as ia:
            with self.assertRaisesRegex(ValueError, "Falló bloque de Obra, filas 12–18"):
                interpretar("sintetico.xlsx", tamano_bloque=3)
        self.assertEqual(ia.call_count, 3)


if __name__ == "__main__":
    unittest.main()
