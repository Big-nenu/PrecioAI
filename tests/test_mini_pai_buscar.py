import io
import json
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import buscar_conceptos as sql
import mini_pai_buscar as mini


class PruebasBusquedaPresupuesto(unittest.TestCase):
    def test_prioriza_actividad_sobre_mencion_en_otro_trabajo_y_marca_faltantes(self):
        entrada = self.entrada()
        entrada["registros"] = entrada["registros"][:2]
        entrada["registros"][1].update(descripcion="Plantilla de concreto", unidad=None, cantidad=None)
        candidatos = [dict(IdCodigo=1, Codigo="muro", DescripcionLarga="Muro con plantilla de concreto",
                           IdUnidad=12, IdTipo=4),
                      dict(IdCodigo=2, Codigo="plantilla", DescripcionLarga="Plantilla de concreto",
                           IdUnidad=11, IdTipo=4)]
        with patch.object(mini, "buscar", return_value=candidatos):
            resultado = mini.buscar_presupuesto(entrada, self.conexion())["busquedas_construbase"][0]
        self.assertEqual(resultado["candidatos"][0]["IdCodigo"], 2)
        self.assertTrue(resultado["candidatos"][0]["coincide_inicio_actividad"])
        self.assertEqual(len(resultado["observaciones_origen"]), 2)

    def entrada(self):
        registros = [dict(tipo="partida", hoja="Obra", fila=2, clave="A", descripcion="Grupo",
                          unidad=None, cantidad=None, partida=None, subpartida=None, padre=None)]
        for fila in (3, 4):
            registros.append(dict(tipo="concepto", hoja="Obra", fila=fila, clave="REPETIDA",
                descripcion="Trazo y nivelación con equipo topográfico. Incluye materiales.",
                unidad="M2", cantidad="12.00", partida="A", subpartida=None, padre=2,
                evidencia=dict(clave=[f"A{fila}"], descripcion=[f"D{fila}"], unidad=[f"H{fila}"], cantidad=[f"J{fila}"])))
        return dict(archivo="ejemplo.xlsx", alcance=dict(parcial=True), registros=registros,
                    dudas=["Revisar el alcance"], excluidas=[dict(hoja="Obra", fila=1, motivo="Portada")])

    def conexion(self):
        conexion = Mock()
        conexion.cursor.return_value.fetchall.return_value = [(11, "M2"), (12, "M3")]
        return conexion

    def candidatos(self):
        return [dict(IdCodigo=n, Codigo=f"codigo-{n}", DescripcionLarga="Trazo y nivelación topográfico",
                     Descripcion="Trazo", IdUnidad=11 if n % 2 else 12, IdTipo=4) for n in range(1, 8)]

    def test_preserva_origen_jerarquia_repetidos_y_no_asocia_matrices(self):
        entrada = self.entrada()
        copia = deepcopy(entrada)
        candidatos = self.candidatos()
        with patch.object(mini, "buscar", return_value=candidatos) as buscar:
            salida = mini.buscar_presupuesto(entrada, self.conexion())
        self.assertEqual(entrada, copia)
        self.assertEqual(salida["registros"], entrada["registros"])
        self.assertEqual(salida["excluidas"], entrada["excluidas"])
        self.assertEqual(salida["alcance"], entrada["alcance"])
        self.assertEqual(buscar.call_count, 1)  # Caché por consulta, no por clave del cliente.
        busquedas = salida["busquedas_construbase"]
        self.assertEqual([b["fila"] for b in busquedas], [3, 4])
        self.assertTrue(all(len(b["candidatos"]) == 5 and b["seleccion"] is None for b in busquedas))
        self.assertTrue(any(c["comparacion_unidad"] == "diferente" for c in busquedas[0]["candidatos"]))
        self.assertNotIn("advertencias", candidatos[0])

    def test_ampliacion_visible_y_terminos_explicitos_no_se_amplian(self):
        entrada = self.entrada()
        entrada["registros"] = entrada["registros"][:2]
        with patch.object(mini, "buscar", side_effect=[[], self.candidatos()]) as buscar:
            resultado = mini.buscar_presupuesto(entrada, self.conexion())["busquedas_construbase"][0]
        self.assertEqual([c.args[1] for c in buscar.call_args_list], ["trazo nivelacion", "trazo"])
        self.assertEqual(len(resultado["intentos"]), 2)
        with patch.object(mini, "buscar", return_value=[]) as buscar:
            resultado = mini.buscar_presupuesto(entrada, self.conexion(), terminos={"Obra:3": "trazo manual"})["busquedas_construbase"][0]
        self.assertEqual(buscar.call_count, 1)
        self.assertEqual(resultado["estado"], "sin_candidatos_en_busqueda")

    def test_sin_descripcion_pide_terminos_y_no_inventa(self):
        entrada = self.entrada()
        for r in entrada["registros"][1:]:
            r["descripcion"] = None
        with patch.object(mini, "buscar") as buscar:
            salida = mini.buscar_presupuesto(entrada, self.conexion())
        buscar.assert_not_called()
        self.assertTrue(all(b["estado"] == "requiere_terminos" for b in salida["busquedas_construbase"]))

    def test_limite_y_duplicados_sql_por_identidad(self):
        candidatos = self.candidatos()
        with patch.object(mini, "buscar", return_value=[candidatos[0]] * 50):
            busqueda = mini.buscar_presupuesto(self.entrada(), self.conexion())["busquedas_construbase"][0]
        self.assertTrue(busqueda["limite_sql_alcanzado"])
        self.assertEqual(len(busqueda["candidatos"]), 1)

    def test_rechaza_entradas_invalidas_antes_de_consultar(self):
        for cambio in ("duplicado", "terminos", "padre"):
            with self.subTest(cambio=cambio):
                entrada, terminos = self.entrada(), {}
                if cambio == "duplicado":
                    entrada["registros"][2]["fila"] = 3
                elif cambio == "terminos":
                    terminos = {"Obra:99": "trazo"}
                else:
                    entrada["registros"][1]["padre"] = 99
                conexion = self.conexion()
                with self.assertRaises(ValueError):
                    mini.buscar_presupuesto(entrada, conexion, terminos=terminos)
                conexion.cursor.assert_not_called()

    def test_cli_no_sobrescribe_entrada_y_genera_json_revisable(self):
        with tempfile.TemporaryDirectory() as carpeta:
            entrada = Path(carpeta) / "presupuesto.json"
            entrada.write_text(json.dumps(self.entrada()), encoding="utf-8")
            inicial = entrada.read_bytes()
            with patch("sys.argv", ["mini", str(entrada), "--salida", str(entrada)]), patch(
                    "sys.stderr", new_callable=io.StringIO), patch.object(mini, "conectar_sql") as conectar:
                with self.assertRaises(SystemExit):
                    mini.main()
                conectar.assert_not_called()
            self.assertEqual(entrada.read_bytes(), inicial)
            salida = Path(carpeta) / "resultados" / "revision.json"
            conexion = self.conexion()
            with patch("sys.argv", ["mini", str(entrada), "--salida", str(salida)]), patch.object(
                    mini, "conectar_sql") as conectar, patch.object(mini, "buscar", return_value=self.candidatos()):
                conectar.return_value.__enter__.return_value = conexion
                mini.main()
            self.assertEqual(json.loads(salida.read_text(encoding="utf-8"))["registros"], self.entrada()["registros"])
            self.assertEqual(entrada.read_bytes(), inicial)


class PruebasConexionSQL(unittest.TestCase):
    def test_conexion_lectura_y_credenciales_existentes(self):
        with patch.dict(os.environ, {"PRECIOAI_SQL_SERVER": "local", "PRECIOAI_SQL_DATABASE": "base",
                "PRECIOAI_SQL_USER": "usuario", "PRECIOAI_SQL_PASSWORD": "prueba"}, clear=True), patch.object(
                sql, "cargar_env"), patch("pyodbc.connect") as conectar:
            sql.conectar_sql()
        self.assertTrue(conectar.call_args.kwargs["readonly"])
        self.assertIn("ApplicationIntent=ReadOnly", conectar.call_args.args[0])

    def test_sin_clave_no_pregunta_en_flujo_no_interactivo(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sql, "cargar_env"), patch.object(
                sql.getpass, "getpass") as preguntar, patch("pyodbc.connect") as conectar:
            with self.assertRaises(ValueError):
                sql.conectar_sql()
            preguntar.assert_not_called()
            conectar.assert_not_called()

    def test_consulta_anterior_conserva_opcion_de_clave_interactiva(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sql, "cargar_env"), patch.object(
                sql.getpass, "getpass", return_value="prueba") as preguntar, patch("pyodbc.connect"):
            sql.conectar_sql(pedir_clave=True)
            preguntar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
