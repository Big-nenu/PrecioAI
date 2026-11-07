from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from openpyxl import load_workbook
import mini_pai_confirmar as confirmar
import mini_pai_exportar as exportar
from tests import test_mini_pai_exportar as ejemplos


class PruebasConfirmaciones(unittest.TestCase):
    def entrada(self):
        datos = ejemplos.PruebasExportar().entrada()
        datos["busquedas_construbase"][0]["candidatos"][0].update(
            Codigo="CB-001", DescripcionLarga="  Descripción íntegra ConstruBase\ncon especificaciones. ",
            IdUnidad=11, IdTipo=4, unidad_catalogo="M2")
        return datos

    def decisiones(self):
        return [dict(hoja="Obra", fila=3, IdCodigo=10, revisor="Revisor de prueba",
                     motivo="Prueba sintética de una decisión explícita, no equivalencia real")]

    def conexion(self, datos=None):
        c = Mock()
        candidato = (datos or self.entrada())["busquedas_construbase"][0]["candidatos"][0]
        c.cursor.return_value.fetchall.return_value = [tuple(candidato[k] for k in confirmar.CAMPOS_SQL)]
        return c

    def test_confirma_solo_id_existente_sin_mutar_origen_y_sql_parametrizado(self):
        datos = self.entrada()
        antes = deepcopy(datos)
        conexion = self.conexion()
        salida = confirmar.confirmar(datos, self.decisiones(), conexion)
        self.assertEqual(datos, antes)
        self.assertEqual(salida["registros"], antes["registros"])
        seleccion = salida["busquedas_construbase"][0]["seleccion"]
        self.assertEqual(seleccion["IdCodigo"], 10)
        self.assertEqual(seleccion["catalogo"]["Codigo"], "CB-001")
        self.assertEqual(conexion.cursor.return_value.execute.call_args.args[1:], (10,))
        self.assertTrue(conexion.cursor.return_value.execute.call_args.args[0].startswith("SELECT"))

    def test_exporta_datos_cb_y_cliente_sin_intercambiarlos(self):
        salida = confirmar.confirmar(self.entrada(), self.decisiones(), self.conexion())
        libro = exportar.crear_excel(salida)
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "prueba.xlsx"
            libro.save(destino)
            libro.close()
            b = load_workbook(destino)
            self.assertEqual([b["Catálogo"].cell(4,c).value for c in range(2,9)],
                ["CB-001", "001.00", "  Descripción íntegra ConstruBase\ncon especificaciones. ",
                 "  Cliente\ncompleto ", "M2", 12.5, 4])
            self.assertEqual(b["Copiar auxiliares"]["B4"].value, "CB-001")
            self.assertEqual(b["Copiar auxiliares"]["D4"].value, "  Cliente\ncompleto ")
            self.assertEqual(b["Revisión"]["D1"].value, 1)
            self.assertEqual(b["Revisión"]["H6"].value, "Confirmada por revisión humana")
            self.assertEqual(b["Revisión"]["L6"].value, "M2 ")
            self.assertEqual(b["Revisión"]["M6"].value, 10)
            b.close()

    def test_unidad_distinta_sin_datos_y_decision_ambigua_no_consultan_sql(self):
        for caso in ("unidad", "faltante", "motivo", "id", "duplicada"):
            with self.subTest(caso=caso):
                datos, decisiones, conexion = self.entrada(), self.decisiones(), self.conexion()
                if caso == "unidad":
                    datos["registros"][2]["unidad"] = "M3"
                elif caso == "faltante":
                    datos["registros"][2]["unidad"] = None
                elif caso == "motivo":
                    decisiones[0]["motivo"] = " "
                elif caso == "id":
                    decisiones[0]["IdCodigo"] = 999
                else:
                    decisiones *= 2
                with self.assertRaises(ValueError):
                    confirmar.confirmar(datos, decisiones, conexion)
                conexion.cursor.assert_not_called()

    def test_catalogo_cambiado_o_id_ausente_rechaza_sin_confirmar(self):
        for filas in ([], [(10,"CAMBIADO","Descripción distinta",11,4,"M2")]):
            datos, conexion = self.entrada(), self.conexion()
            conexion.cursor.return_value.fetchall.return_value = filas
            with self.assertRaises(ValueError):
                confirmar.confirmar(datos,self.decisiones(),conexion)
            self.assertIsNone(datos["busquedas_construbase"][0]["seleccion"])

    def test_rechaza_modificaciones_posteriores_y_reemplazo_de_decision(self):
        original = confirmar.confirmar(self.entrada(), self.decisiones(), self.conexion())
        for caso in ("cliente", "candidato", "auditoria", "reemplazo"):
            with self.subTest(caso=caso):
                datos = deepcopy(original)
                if caso == "cliente":
                    datos["registros"][2]["cantidad"] = "999"
                elif caso == "candidato":
                    datos["busquedas_construbase"][0]["candidatos"][0]["Codigo"] = "OTRO"
                elif caso == "auditoria":
                    datos["busquedas_construbase"][0]["seleccion"]["motivo"] = ""
                with self.assertRaises(ValueError):
                    if caso == "reemplazo":
                        confirmar.confirmar(datos,self.decisiones(),self.conexion())
                    else:
                        exportar.crear_excel(datos)

    def test_confirmar_un_concepto_no_selecciona_los_demas(self):
        datos = self.entrada()
        segundo = deepcopy(datos["registros"][2])
        segundo.update(fila=4, clave="OTRO")
        datos["registros"].append(segundo)
        busqueda = deepcopy(datos["busquedas_construbase"][0])
        busqueda["fila"] = 4
        datos["busquedas_construbase"].append(busqueda)
        salida = confirmar.confirmar(datos,self.decisiones(),self.conexion())
        self.assertIsNone(salida["busquedas_construbase"][1]["seleccion"])
        libro = exportar.crear_excel(salida)
        self.assertEqual(libro["Revisión"]["D1"].value,1)
        self.assertIsNone(libro["Catálogo"]["B5"].value)
        self.assertEqual(libro["Revisión"]["H7"].value,"Dudosa: pendiente de confirmar")
        libro.close()

    def test_codigo_repetido_con_descripcion_distinta_bloquea_exportacion(self):
        datos = self.entrada()
        segundo = deepcopy(datos["registros"][2])
        segundo.update(fila=4, clave="OTRO")
        datos["registros"].append(segundo)
        busqueda = deepcopy(datos["busquedas_construbase"][0])
        busqueda["fila"] = 4
        busqueda["candidatos"][0].update(IdCodigo=11,DescripcionLarga="Otro concepto con el mismo código")
        datos["busquedas_construbase"].append(busqueda)
        decisiones=self.decisiones()+[dict(self.decisiones()[0],fila=4,IdCodigo=11)]
        conexion=self.conexion()
        conexion.cursor.return_value.fetchall.side_effect=[
            [tuple(b["candidatos"][0][k] for k in confirmar.CAMPOS_SQL)] for b in datos["busquedas_construbase"]]
        salida=confirmar.confirmar(datos,decisiones,conexion)
        with self.assertRaisesRegex(ValueError,"revisar conflicto"):
            exportar.crear_excel(salida)

    def test_cli_no_sobrescribe_y_rechaza_decisiones_antes_de_abrir_sql(self):
        with tempfile.TemporaryDirectory() as carpeta:
            presupuesto = Path(carpeta)/"entrada.json"
            decisiones = Path(carpeta)/"decisiones.json"
            salida = Path(carpeta)/"seleccion.json"
            presupuesto.write_text(json.dumps(self.entrada()),encoding="utf-8")
            decisiones.write_text(json.dumps(self.decisiones()),encoding="utf-8")
            with patch("sys.argv",["confirmar",str(presupuesto),str(decisiones),"--salida",str(salida)]), patch.object(confirmar,"conectar_sql") as conectar, patch("sys.stdout",new_callable=io.StringIO):
                conectar.return_value.__enter__.return_value = self.conexion()
                confirmar.main()
            self.assertEqual(json.loads(salida.read_text(encoding="utf-8"))["registros"],self.entrada()["registros"])
            for destino in (presupuesto,decisiones,salida):
                antes=destino.read_bytes()
                with patch("sys.argv",["confirmar",str(presupuesto),str(decisiones),"--salida",str(destino)]), patch.object(confirmar,"conectar_sql") as conectar, patch("sys.stderr",new_callable=io.StringIO):
                    with self.assertRaises(SystemExit):
                        confirmar.main()
                    conectar.assert_not_called()
                self.assertEqual(destino.read_bytes(),antes)
