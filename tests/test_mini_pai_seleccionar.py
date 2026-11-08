from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

import mini_pai_seleccionar as ia
from mini_pai_confirmar import ASPECTOS, validar_evaluacion_ia, seleccion_validada
from mini_pai_exportar import crear_excel
from tests import test_mini_pai_confirmar as ejemplos
import mini_pai_buscar as busqueda


class PruebasSeleccionIA(unittest.TestCase):
    def test_esquema_respeta_requisitos_esenciales_y_no_aplica(self):
        datos = self.datos()
        r, b = datos['registros'][2], datos['busquedas_construbase'][0]
        esquema = ia.esquema(b, ia.fragmentos(r, b))
        pruebas = esquema['properties']['comprobaciones']['items']['anyOf']
        por_aspecto = {p['properties']['aspecto']['enum'][0]: p['properties']['estado']['enum'] for p in pruebas}
        self.assertEqual(por_aspecto['unidad'], ['compatible'])
        for aspecto in ('procedimiento', 'alcance'):
            self.assertEqual(set(por_aspecto[aspecto]), {'compatible','diferente','insuficiente'})
        for aspecto in ('materiales','dimensiones','espesor','resistencia'):
            self.assertIn('no_aplica', por_aspecto[aspecto])

    def datos(self):
        datos = ejemplos.PruebasConfirmaciones().entrada()
        r = datos["registros"][2]
        r["descripcion"] = "Trazo con equipo topográfico; incluye ejes y bancos."
        b = datos["busquedas_construbase"][0]
        b["candidatos"][0]["DescripcionLarga"] = r["descripcion"]
        return datos

    def evaluacion(self):
        pruebas=[]
        for aspecto in ASPECTOS:
            texto = {"procedimiento":"equipo topográfico","alcance":"ejes y bancos","unidad":"M2"}.get(aspecto,"")
            pruebas.append(dict(aspecto=aspecto,estado="compatible" if texto else "no_aplica",
                cliente=texto,catalogo=texto,motivo="Coincide la evidencia" if texto else "No exigido en este trabajo"))
        return dict(seleccion_id=10,motivo="Misma actividad, procedimiento, alcance y unidad acreditados",
            candidatos=[dict(IdCodigo=10,dictamen="equivalente",motivo="Actividad y alcance iguales",
                cliente="ejes y bancos",catalogo="ejes y bancos")],comprobaciones=pruebas)

    def respuesta(self, evaluacion=None):
        e=deepcopy(evaluacion or self.evaluacion())
        e['orden_revision'] = {f'puesto_{n}':c['IdCodigo'] for n,c in enumerate(e['candidatos'],1)}
        for p in e["candidatos"]+e["comprobaciones"]:
            if p["cliente"]: p["cliente"]="CU" if p.get("aspecto")=="unidad" else "C0"
            if p["catalogo"]: p["catalogo"]="KU10" if p.get("aspecto")=="unidad" else "K10_0"
        return json.dumps(e)

    def test_flujo_ia_sql_exporta_sin_cambiar_columnas_ni_auxiliares(self):
        datos=self.datos(); antes=deepcopy(datos)
        conexion=ejemplos.PruebasConfirmaciones().conexion(datos)
        with patch.object(ia,"configuracion",return_value=("local","modelo-prueba","")), patch.object(
                ia,"consultar_ia",return_value=self.respuesta()) as consultar:
            salida=ia.seleccionar(datos,conexion)
        instrucciones=consultar.call_args.args[0][0]["content"]
        self.assertIn("REDACCION_EQUIVALENTE",instrucciones)
        self.assertNotIn("Seleccionar celdas como evidencia",instrucciones)
        self.assertEqual(datos,antes)
        self.assertEqual(salida["resumen_ia"]["seleccionados_ia"],1)
        b=salida["busquedas_construbase"][0]
        self.assertEqual(b["seleccion"]["origen"],"ia")
        seleccion_validada(salida["registros"][2],b)
        libro=crear_excel(salida)
        self.assertEqual(libro["Catálogo"]["B4"].value,"CB-001")
        self.assertEqual(libro["Catálogo"]["D4"].value,datos["registros"][2]["descripcion"])
        self.assertEqual(libro["Catálogo"]["C4"].value,"001.00")
        self.assertEqual(libro["Catálogo"]["G4"].value,12.5)
        self.assertEqual(libro["Catálogo"].max_column,8)
        self.assertEqual(libro["Copiar auxiliares"].max_column,6)
        self.assertIn("Seleccionada por IA",libro["Revisión"]["H6"].value)
        libro.close()

    def test_id_ajeno_citas_inventadas_o_cobertura_incompleta_se_rechazan(self):
        datos=self.datos();r=datos["registros"][2];b=datos["busquedas_construbase"][0]
        for caso in ("id","cita","aspecto","candidato","sin_evidencia"):
            e=self.evaluacion()
            if caso=="id": e["seleccion_id"]=999
            elif caso=="cita": e["candidatos"][0]["catalogo"]="texto inventado"
            elif caso=="aspecto": e["comprobaciones"].pop()
            elif caso=="candidato": e["candidatos"]=[]
            else: e["comprobaciones"][1]["cliente"]=" "
            with self.subTest(caso=caso),self.assertRaises(ValueError):
                validar_evaluacion_ia(r,b,e)

    def test_misma_unidad_no_permite_espesores_o_resistencias_distintas(self):
        for aspecto,a,b in (("espesor","6.00 cm de espesor","5 cm de espesor"),
                            ("resistencia","F'c=250 kg/cm2","F'c=150 kg/cm2")):
            datos=self.datos();r=datos["registros"][2];bus=datos["busquedas_construbase"][0]
            r["descripcion"]+=" "+a
            bus["candidatos"][0]["DescripcionLarga"]+=" "+b
            e=self.evaluacion()
            p=next(p for p in e["comprobaciones"] if p["aspecto"]==aspecto)
            p.update(estado="compatible",cliente=a,catalogo=b)
            with self.subTest(aspecto=aspecto),self.assertRaises(ValueError):
                validar_evaluacion_ia(r,bus,e)
            p.update(estado="no_aplica",cliente="",catalogo="")
            with self.assertRaises(ValueError): validar_evaluacion_ia(r,bus,e)

    def test_tipo_b_no_equivale_a_tipo_c_aunque_unidad_sea_igual(self):
        datos=self.datos();r=datos["registros"][2];b=datos["busquedas_construbase"][0]
        r["descripcion"]+=" Material tipo B."
        b["candidatos"][0]["DescripcionLarga"]+=" Material tipo C."
        e=self.evaluacion();p=e["comprobaciones"][0]
        p.update(estado="compatible",cliente="Material tipo B",catalogo="Material tipo C")
        with self.assertRaises(ValueError): validar_evaluacion_ia(r,b,e)

    def test_descripciones_distintas_pueden_sustentar_equivalencia_semantica(self):
        datos=self.datos();r=datos["registros"][2];b=datos["busquedas_construbase"][0]
        r["descripcion"]="Localización de ejes y bancos con tránsito y nivel."
        b["candidatos"][0]["DescripcionLarga"]="Trazo de ejes y bancos con equipo topográfico."
        e=self.evaluacion()
        e["comprobaciones"][1].update(cliente="tránsito y nivel",catalogo="equipo topográfico")
        validar_evaluacion_ia(r,b,e)

    def test_insuficiente_o_error_no_selecciona_ni_verifica_sql(self):
        e=self.evaluacion();e.update(seleccion_id=None,comprobaciones=[])
        e["candidatos"][0]["dictamen"]="insuficiente"
        for respuesta in (self.respuesta(e),"JSON inválido"):
            conexion=Mock()
            with patch.object(ia,"configuracion",return_value=("local","modelo-prueba","")),patch.object(
                    ia,"consultar_ia",return_value=respuesta):
                salida=ia.seleccionar(self.datos(),conexion)
            self.assertEqual(salida["resumen_ia"]["pendientes"],1)
            self.assertIsNone(salida["busquedas_construbase"][0]["seleccion"])
            conexion.cursor.assert_not_called()

    def test_sql_modificado_o_evidencia_posterior_no_se_aceptan(self):
        conexion=ejemplos.PruebasConfirmaciones().conexion(self.datos())
        conexion.cursor.return_value.fetchall.return_value=[]
        with patch.object(ia,"configuracion",return_value=("local","modelo-prueba","")),patch.object(
                ia,"consultar_ia",return_value=self.respuesta()):
            salida=ia.seleccionar(self.datos(),conexion)
        self.assertEqual(salida["resumen_ia"]["errores"],1)
        self.assertIsNone(salida["busquedas_construbase"][0]["seleccion"])

    def test_modificar_evidencia_ia_bloquea_exportacion(self):
        conexion=ejemplos.PruebasConfirmaciones().conexion(self.datos())
        with patch.object(ia,"configuracion",return_value=("local","modelo-prueba","")),patch.object(
                ia,"consultar_ia",return_value=self.respuesta()):
            salida=ia.seleccionar(self.datos(),conexion)
        salida["busquedas_construbase"][0]["evaluacion_ia"]["motivo"]="Motivo alterado"
        with self.assertRaises(ValueError): crear_excel(salida)

    def test_no_acepta_equivalente_sin_elegir_ni_fragmento_inventado(self):
        datos=self.datos();e=self.evaluacion();e.update(seleccion_id=None,comprobaciones=[])
        with self.assertRaises(ValueError):
            validar_evaluacion_ia(datos["registros"][2],datos["busquedas_construbase"][0],e)
        respuesta=json.loads(self.respuesta());respuesta["candidatos"][0]["cliente"]="C999"
        with patch.object(ia,"consultar_ia",return_value=json.dumps(respuesta)):
            with self.assertRaises(ValueError):
                ia.comparar(datos["registros"][2],datos["busquedas_construbase"][0],"Instrucciones")

    def test_compatibilidad_parcial_no_aprueba_y_preserva_propuesta(self):
        datos=self.datos();e=self.evaluacion()
        e["comprobaciones"][5].update(estado="insuficiente",motivo="Falta acreditar una prestación expresa")
        antes=deepcopy(e)
        pendiente,propuesta=ia.resolver_incertidumbre(e)
        self.assertEqual(e,antes)
        self.assertEqual(propuesta,antes)
        self.assertIsNone(pendiente["seleccion_id"])
        self.assertEqual(pendiente["candidatos"][0]["dictamen"],"insuficiente")
        validar_evaluacion_ia(datos["registros"][2],datos["busquedas_construbase"][0],pendiente)
        conexion=Mock()
        with patch.object(ia,"configuracion",return_value=("local","modelo-prueba","")),patch.object(
                ia,"consultar_ia",return_value=self.respuesta(e)):
            salida=ia.seleccionar(datos,conexion)
        self.assertEqual(salida["resumen_ia"]["seleccionados_ia"],0)
        self.assertEqual(salida["resumen_ia"]["errores"],0)
        self.assertIsNone(salida["busquedas_construbase"][0]["seleccion"])
        self.assertEqual(salida["busquedas_construbase"][0]["evaluacion_ia_propuesta"]["seleccion_id"],10)
        conexion.cursor.assert_not_called()

    def test_resolucion_no_promueve_ni_altera_decision_completa(self):
        e=self.evaluacion();antes=deepcopy(e)
        resultado,propuesta=ia.resolver_incertidumbre(e)
        self.assertEqual(resultado,antes)
        self.assertIsNone(propuesta)
        e.update(seleccion_id=None,comprobaciones=[])
        e["candidatos"][0]["dictamen"]="insuficiente"
        resultado,propuesta=ia.resolver_incertidumbre(e)
        self.assertIsNone(resultado["seleccion_id"])
        self.assertIsNone(propuesta)

    def test_paginacion_sql_parametriza_el_desplazamiento(self):
        from buscar_conceptos import buscar
        con=Mock();cursor=con.cursor.return_value
        cursor.description=[("IdCodigo",)];cursor.fetchall.return_value=[]
        buscar(con,"demolicion",50,tipo=4,desplazamiento=50)
        args=cursor.execute.call_args.args
        self.assertIn("OFFSET ? ROWS",args[0])
        self.assertEqual(args[1:],(4,"%demolicion%",50))

    def test_recuperacion_ampliada_recoge_paginas_antes_de_priorizar_unidad(self):
        datos=self.datos();datos.pop("busquedas_construbase")
        ejemplo=ejemplos.PruebasConfirmaciones()
        primero=[dict(IdCodigo=n,Codigo=str(n),DescripcionLarga="Trazo con equipo topográfico",
                       IdUnidad=12,IdTipo=4) for n in range(50)]
        ultimo=[dict(IdCodigo=99,Codigo="fuera-del-primer-lote",DescripcionLarga="Trazo con equipo topográfico",
                       IdUnidad=11,IdTipo=4)]
        con=Mock();con.cursor.return_value.fetchall.return_value=[(11,"M2"),(12,"M3")]
        with patch.object(busqueda,"buscar",side_effect=[primero,ultimo]) as buscar:
            salida=busqueda.buscar_presupuesto(datos,con,ampliar=True)
        b=salida["busquedas_construbase"][0]
        self.assertEqual(b["recuperados"],51)
        self.assertEqual(b["candidatos"][0]["IdCodigo"],99)
        self.assertEqual(buscar.call_args.kwargs["desplazamiento"],50)
