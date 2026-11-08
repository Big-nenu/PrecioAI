import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

import probar_modelos_mini_pai as prueba
from tests import test_mini_pai_tabla as ejemplos_tabla
from tests import test_mini_pai_confirmar as ejemplos_confirmar
from mini_pai_tabla import materializar_tabla


class PruebasReportesModelos(unittest.TestCase):
    def muestra(self, carpeta):
        origen, estructura, plan = ejemplos_tabla.PruebasTabla().ejemplo()
        referencia = materializar_tabla(origen, estructura, plan)
        archivos = {"presupuesto": ("entrada.xlsx", b"Original intacto"),
            "referencia": ("referencia.json", json.dumps(referencia).encode()),
            "candidatos": ("candidatos.json", json.dumps(ejemplos_confirmar.PruebasConfirmaciones().entrada()).encode())}
        manifest = dict(archivos={}, controles=[dict(hoja="Obra", fila=3, ids_incompatibles=[10], motivo="Control sintético")],
                        nota="Muestra sintética; no son resultados de modelos reales")
        for nombre, (ruta, contenido) in archivos.items():
            (carpeta/ruta).write_bytes(contenido)
            manifest["archivos"][nombre] = dict(ruta=ruta, sha256=prueba.sha(contenido))
        ruta = carpeta/"muestra.json"
        ruta.write_text(json.dumps(manifest), encoding="utf-8")
        return prueba.cargar_muestra(ruta)

    def evaluacion(self):
        return dict(seleccion_id=None, motivo="Información insuficiente en el ensayo sintético",
            candidatos=[dict(IdCodigo=10, dictamen="insuficiente", motivo="Falta evidencia", cliente="", catalogo="")],
            comprobaciones=[])

    def test_cotejo_detecta_cantidad_ajena_y_cambio_de_jerarquia(self):
        with tempfile.TemporaryDirectory() as temporal:
            muestra = self.muestra(Path(temporal))
            ref = muestra["referencia"]
            actual = json.loads(json.dumps(ref))
            self.assertTrue(prueba.cotejar(actual, ref)["correcta"])
            actual["registros"][1]["cantidad"] = "133.17"
            actual["registros"][2]["padre"] = None
            resultado = prueba.cotejar(actual, ref)
            self.assertFalse(resultado["correcta"])
            self.assertEqual({d["campo"] for d in resultado["diferencias"]}, {"cantidad", "padre"})

    def test_muestra_modificada_se_rechaza_antes_de_llamar_al_modelo(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            self.muestra(carpeta)
            (carpeta/"entrada.xlsx").write_bytes(b"Cambiada")
            with self.assertRaisesRegex(ValueError, "muestra cambió"):
                prueba.cargar_muestra(carpeta/"muestra.json")

    def test_control_detecta_propuesta_indebida_aunque_guardas_la_bloqueen(self):
        caso = dict(hoja="Obra", fila=3, evaluacion=self.evaluacion(),
                    propuesta=dict(seleccion_id=10, candidatos=[dict(IdCodigo=10, dictamen="equivalente")]))
        controles = [dict(hoja="Obra", fila=3, ids_incompatibles=[10], motivo="Material distinto")]
        self.assertIn("ALERTA", prueba.control_tecnico(caso, controles))
        caso = dict(hoja="Obra", fila=3, error="JSON inválido", respuesta_rechazada="no es json")
        self.assertIn("no evaluable", prueba.control_tecnico(caso, controles))
        caso["respuesta_rechazada"] = json.dumps(dict(seleccion_id=[], candidatos=None))
        self.assertIn("no evaluable", prueba.control_tecnico(caso, controles))

    def test_reporte_env_restaurado_entradas_intactas_y_sin_sql(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            muestra = self.muestra(carpeta)
            def extraer(_):
                self.assertEqual(os.environ["PRECIOAI_AI_MODEL"], "modelo-prueba")
                return muestra["referencia"]
            with patch.dict(os.environ, {"PRECIOAI_AI_MODEL": "principal", "PRECIOAI_SQL_PASSWORD": "NO_PUBLICAR"}), patch.object(
                    prueba, "interpretar_tabla", side_effect=extraer), patch.object(prueba, "http"), patch.object(
                    prueba.selector, "comparar", return_value=(self.evaluacion(), None)), patch.object(prueba.selector, "conectar_sql") as sql:
                resultado = prueba.ejecutar("modelo-prueba", muestra, carpeta/"salida", {"digest": "prueba"}, {"simulado": True})
                self.assertEqual(os.environ["PRECIOAI_AI_MODEL"], "principal")
                sql.assert_not_called()
            self.assertTrue(resultado["extraccion"]["correcta"])
            self.assertTrue(resultado["entradas_intactas"])
            md = (carpeta/"salida"/resultado["archivo_reporte"]).read_text(encoding="utf-8")
            self.assertNotIn("NO_PUBLICAR", md)
            self.assertIn("sin verificación SQL", md)
            resultado["llamadas"] = [dict(fase="extraccion", segundos=0, respuesta={"load_duration": None})]
            self.assertIn("Tokens entrada", prueba.markdown(resultado))
            self.assertEqual((carpeta/"entrada.xlsx").read_bytes(), b"Original intacto")
            with self.assertRaises(FileExistsError):
                prueba.ejecutar("modelo-prueba", muestra, carpeta/"salida", None, {})

    def test_fallo_extraccion_no_impide_reporte_tecnico(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            muestra = self.muestra(carpeta)
            with patch.object(prueba, "interpretar_tabla", side_effect=ValueError("Fallo de formato")), patch.object(
                    prueba, "http"), patch.object(prueba.selector, "comparar", return_value=(self.evaluacion(), None)):
                resultado = prueba.ejecutar("modelo", muestra, carpeta/"salida", {}, {})
            self.assertFalse(resultado["extraccion"]["correcta"])
            self.assertEqual(len(resultado["tecnica"]), 1)
            self.assertTrue((carpeta/"salida"/resultado["archivo_reporte"]).is_file())

    def test_interrupcion_conserva_markdown_parcial(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            muestra = self.muestra(carpeta)
            with patch.object(prueba, "interpretar_tabla", side_effect=KeyboardInterrupt), patch.object(prueba, "http"):
                with self.assertRaises(KeyboardInterrupt):
                    prueba.ejecutar("modelo", muestra, carpeta/"salida", {}, {})
            guardado = json.loads((carpeta/"salida/resultados.json").read_text(encoding="utf-8"))
            self.assertEqual(guardado["estado"], "interrumpido")
            self.assertIn("interrumpido", (carpeta/"salida/reporte-modelo.md").read_text(encoding="utf-8"))

    def test_modelo_no_disponible_no_inventa_resultados(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            muestra = self.muestra(carpeta)
            with patch.object(prueba, "interpretar_tabla") as ia, patch.object(prueba, "http") as red:
                resultado = prueba.ejecutar("ausente", muestra, carpeta/"salida", None, {})
                ia.assert_not_called()
                red.assert_not_called()
            self.assertEqual(resultado["estado"], "no_ejecutado")
            self.assertNotIn("extraccion", resultado)
            self.assertEqual(resultado["llamadas"], [])

    def test_instrumentacion_conserva_respuesta_y_mide_sin_guardar_headers(self):
        resultado = dict(modelo="modelo", fase="extraccion", llamadas=[])
        original = dict(done=True, message=dict(content="{}"), prompt_eval_count=10, eval_count=5)
        respuesta = io.BytesIO(json.dumps(original).encode())
        peticion = Request(prueba.BASE + "/api/chat", data=json.dumps(dict(model="modelo")).encode(),
                           headers={"Authorization": "NO_GUARDAR"})
        with patch.object(prueba.proveedor_ia, "urlopen", return_value=respuesta), patch.object(
                prueba, "http", return_value={"models": [{"name": "modelo", "size_vram": 1024}]}):
            with prueba.instrumentar(resultado):
                with prueba.proveedor_ia.urlopen(peticion) as r:
                    self.assertEqual(json.load(r), original)
        self.assertEqual(resultado["llamadas"][0]["vram_residente_bytes"], 1024)
        self.assertNotIn("NO_GUARDAR", json.dumps(resultado))
