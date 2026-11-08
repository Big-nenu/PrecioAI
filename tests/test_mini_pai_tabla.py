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

    def test_un_grupo_pendiente_solo_se_admite_durante_la_planificacion(self):
        origen, estructura, plan = self.ejemplo()
        origen['hojas'][0]['filas'] = origen['hojas'][0]['filas'][:5]
        plan['resumen_desde'] = None
        temporal = tabla.materializar_tabla(origen, estructura, plan, _en_curso=True)
        self.assertTrue(temporal['alcance']['parcial'])
        with self.assertRaisesRegex(ValueError, 'Agrupadores sin conceptos'):
            tabla.materializar_tabla(origen, estructura, plan)

    def test_grupo_cerrado_vacio_no_se_admite_en_planificacion(self):
        origen, estructura, plan = self.ejemplo()
        plan['filas']['3']['tipo'] = 'partida'
        plan['filas']['5'] = dict(tipo='partida',padre=None,motivo=None)
        origen['hojas'][0]['filas'] = [r for r in origen['hojas'][0]['filas'] if r['fila'] != 4]
        with self.assertRaisesRegex(ValueError, 'Agrupadores sin conceptos'):
            tabla.materializar_tabla(origen, estructura, plan, _en_curso=True)

    def test_clasificacion_recibe_contexto_y_contrato_cerrado(self):
        origen, estructura, plan = self.ejemplo()
        origen['hojas'][0]['filas'][2]['formatos']={'K3':dict(estilo=7,negrita=True)}
        wire = dict(filas=deepcopy(plan['filas']),dudas=[])
        wire['filas'].update({str(n):dict(tipo='omitir',padre=None,motivo='Resumen final') for n in (7,8)})
        wire['filas']['7']['tipo']='resumen'
        with patch.object(tabla,'consultar_ia',return_value=json.dumps(wire)) as ia:
            salida = tabla.clasificar_tabla(origen,estructura)
        cuerpo=json.loads(ia.call_args.args[0][1]['content'])
        self.assertEqual({r['fila'] for r in cuerpo['trabajos_cercanos']},{4,6})
        self.assertEqual(cuerpo['filas_sin_medicion'][0]['formato']['descripcion'],dict(estilo=7,negrita=True))
        esquema=ia.call_args.kwargs['esquema']
        self.assertEqual(set(esquema['properties']['filas']['required']),{'3','5','7','8'})
        tipos = lambda n: set(esquema['properties']['filas']['properties'][n]['properties']['tipo']['enum'])
        self.assertNotIn('resumen',tipos('3'))
        self.assertIn('resumen',tipos('7'))
        self.assertEqual([r['fila'] for r in salida['registros']],[3,4,5,6])

    def test_documento_no_se_convierte_en_partida_y_no_pierde_sus_grupos(self):
        origen, estructura, _ = self.ejemplo()
        origen['hojas'][0]['filas'] = [origen['hojas'][0]['filas'][1],
            dict(fila=3,celdas={'C3':'OBRA','K3':'Descripción global del contrato'}),
            dict(fila=4,celdas={'C4':'A','K4':'Grupo de trabajos'}),
            dict(fila=5,celdas={'C5':'001','K5':'Trabajo concreto','H5':'M2','Q5':'2'}),
            dict(fila=6,celdas={'C6':'A.1','K6':'Sección de trabajos'}),
            dict(fila=7,celdas={'C7':'002','K7':'Otro trabajo','H7':'M2','Q7':'3'})]
        wire=dict(dudas=[],filas={
            '3':dict(tipo='documento',padre=None,motivo='Título general de la obra'),
            '4':dict(tipo='partida',padre=None,motivo=None),
            '6':dict(tipo='subpartida',padre=4,motivo=None)})
        wire['filas']=dict(reversed(list(wire['filas'].items())))
        with patch.object(tabla,'consultar_ia',return_value=json.dumps(wire)):
            resultado=tabla.clasificar_tabla(origen,estructura)
        self.assertEqual([(r['fila'],r['tipo'],r['padre']) for r in resultado['registros']],
                         [(4,'partida',None),(5,'concepto',4),(6,'subpartida',4),(7,'concepto',6)])
        self.assertIn(3,[r['fila'] for r in resultado['excluidas']])

    def test_bloques_conservan_partida_vigente_y_todos_los_trabajos(self):
        origen, estructura, _ = self.ejemplo()
        filas=[origen['hojas'][0]['filas'][1]]
        for i in range(23):
            n=3+2*i
            filas += [dict(fila=n,celdas={f'C{n}':f'S{i}',f'K{n}':'Grupo'}),
                      dict(fila=n+1,celdas={f'C{n+1}':f'P{i}',f'K{n+1}':'Trabajo',f'H{n+1}':'M2',f'Q{n+1}':'1'})]
        origen['hojas'][0]['filas']=filas
        def responder(mensajes,**kw):
            datos=json.loads(mensajes[1]['content'])
            return json.dumps(dict(dudas=[],filas={str(r['fila']):dict(
                tipo='partida' if r['fila']==3 else 'subpartida',padre=None if r['fila']==3 else 3,motivo=None)
                for r in datos['filas_sin_medicion']}))
        with patch.object(tabla,'consultar_ia',side_effect=responder) as ia:
            resultado=tabla.clasificar_tabla(origen,estructura)
        self.assertEqual(ia.call_count,3)
        primero=json.loads(ia.call_args_list[0].args[0][1]['content'])
        self.assertEqual([r['fila'] for r in primero['anticipacion']],[23,25])
        self.assertNotIn('23',ia.call_args_list[0].kwargs['esquema']['properties']['filas']['properties'])
        self.assertEqual(sum(r['tipo']=='concepto' for r in resultado['registros']),23)
        segundo=json.loads(ia.call_args_list[1].args[0][1]['content'])
        self.assertEqual(segundo['encabezados_vigentes'][0]['fila'],3)
        self.assertEqual([r['tipo'] for r in segundo['ejemplos_anteriores']],['partida','subpartida','subpartida'])
        self.assertFalse(resultado['alcance']['parcial'])

    def test_formato_original_es_contexto_opcional_sin_cambiar_valores(self):
        from openpyxl import Workbook
        from openpyxl.styles import Font
        with tempfile.TemporaryDirectory() as carpeta:
            ruta=Path(carpeta)/'original.xlsx'
            libro=Workbook();libro.active['C1']='Grupo';libro.active['C1'].font=Font(bold=True)
            libro.active['C2']='Trabajo';libro.save(ruta);libro.close()
            original=ruta.read_bytes()
            simple=interpretar.inspeccionar_excel(ruta)
            con_formato=interpretar.inspeccionar_excel(ruta,formatos=True)
            self.assertEqual(simple['hojas'][0]['filas'][0]['celdas'],con_formato['hojas'][0]['filas'][0]['celdas'])
            self.assertNotIn('formatos',simple['hojas'][0]['filas'][0])
            self.assertTrue(con_formato['hojas'][0]['filas'][0]['formatos']['C1']['negrita'])
            self.assertFalse(con_formato['hojas'][0]['filas'][1]['formatos']['C2']['negrita'])
            self.assertEqual(original,ruta.read_bytes())

    def test_rechaza_columnas_inventadas_duplicadas_y_cabecera_falsa(self):
        for cambio in ("celda", "duplicada", "bool", "sin_unidad"):
            with self.subTest(cambio=cambio):
                origen, estructura, plan = self.ejemplo()
                if cambio == "celda": estructura["columnas"]["cantidad"] = "Q999"
                elif cambio == "duplicada": estructura["columnas"]["cantidad"] = "H2"
                elif cambio == "bool": estructura["encabezado"] = True
                else: estructura["columnas"]["unidad"] = None
                with self.assertRaises(ValueError):
                    tabla.materializar_tabla(origen, estructura, plan)

    def test_columnas_con_rotulos_en_varias_filas_y_descripcion_sin_rotulo(self):
        origen,estructura,plan=self.ejemplo()
        origen['hojas'][0]['filas'][0]=dict(fila=1,celdas={'H1':'Unidad'})
        del origen['hojas'][0]['filas'][1]['celdas']['K2']
        estructura['columnas'].update(descripcion='K4',unidad='H1',cantidad='Q4')
        datos=tabla.materializar_tabla(origen,estructura,plan)
        self.assertEqual([r['cantidad'] for r in datos['registros'] if r['tipo']=='concepto'],['1900.21','133.17'])
        # Un ancla de datos no puede hacer desaparecer trabajos repetidos.
        origen['hojas'][0]['filas'][5]['celdas'].update(K6=origen['hojas'][0]['filas'][3]['celdas']['K4'],H6='M3/KM',Q6='1900.21')
        datos=tabla.materializar_tabla(origen,estructura,plan)
        self.assertEqual(sum(r['tipo']=='concepto' for r in datos['registros']),2)

    def test_cabecera_inferida_no_puede_ocultar_trabajos_medidos(self):
        origen,estructura,plan=self.ejemplo()
        estructura['encabezado']=4
        with self.assertRaisesRegex(ValueError,'cabecera excluiría'):
            tabla.materializar_tabla(origen,estructura,plan)

    def test_rotulo_posterior_no_se_acepta_como_ancla_de_datos(self):
        origen,estructura,plan=self.ejemplo()
        origen['hojas'][0]['filas'][4]['celdas'].update(H5='Unidad',Q5='Cantidad')
        estructura['columnas']['descripcion']='K5'
        with self.assertRaisesRegex(ValueError,'no pertenece a un trabajo medido'):
            tabla.materializar_tabla(origen,estructura,plan)

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
        plan = dict(filas=deepcopy(plan['filas']),dudas=[])
        plan['filas'].update({'7':dict(tipo='resumen',padre=None,motivo='Resumen final'),
                              '8':dict(tipo='omitir',padre=None,motivo='Resumen final')})
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
