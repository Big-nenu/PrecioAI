from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

import mini_pai_claves as claves
import mini_pai_buscar as buscador


class PruebasClavesIA(unittest.TestCase):
    def registro(self):
        return dict(tipo='concepto',hoja='Variable',fila=7,padre=None,clave='00017',
            descripcion="Concreto F'C=200 KG/CM2 hecho en obra, acabado aparente",
            unidad='M3 ',cantidad='300.00',partida=None,subpartida=None)

    def plan(self):
        return dict(actividad=dict(nombre='Concreto',evidencia='Concreto'),atributos=[
            dict(nombre='resistencia',valor='200',campo='descripcion',evidencia="F'C=200 KG/CM2"),
            dict(nombre='elaboración',valor='hecho en obra',campo='descripcion',evidencia='hecho en obra'),
            dict(nombre='terminación del cliente',valor='acabado aparente',campo='descripcion',evidencia='acabado aparente'),
            dict(nombre='unidad',valor='M3',campo='unidad',evidencia='M3 ')],
            consultas=['concreto 200 obra','concreto aparente','concreto'],dudas=[])

    def conexion(self):
        conexion=Mock()
        conexion.cursor.return_value.fetchall.return_value=[(11,'M3'),(12,'M2')]
        return conexion

    def test_atributos_abiertos_con_evidencia_y_sin_cantidad_en_el_prompt(self):
        r=self.registro()
        respuesta=self.plan();respuesta['actividad']['evidencia']='C0'
        for a in respuesta['atributos']:
            a['evidencia']='CU' if a.pop('campo')=='unidad' else 'C0'
        with patch.object(claves,'consultar_ia',return_value=json.dumps(respuesta)) as consultar:
            plan=claves.interpretar_claves(r,'Instrucciones de prueba')
        self.assertEqual(plan['consultas'],self.plan()['consultas'])
        self.assertEqual(plan['atributos'][0]['evidencia'],r['descripcion'])
        contenido=json.loads(consultar.call_args.args[0][1]['content'])
        self.assertEqual(set(contenido),{'descripcion','unidad','fragmentos'})
        self.assertNotIn('300.00',consultar.call_args.args[0][1]['content'])
        self.assertEqual(r,self.registro())

    def test_rechaza_resistencia_o_numero_no_mencionados_y_metodo_inventado(self):
        for caso in ('atributo','consulta','metodo'):
            plan=self.plan();r=self.registro()
            if caso=='atributo': plan['atributos'][0]['valor']='300'
            elif caso=='consulta': plan['consultas'][0]='concreto 300'
            else:
                r['descripcion']='Excavación por cualquier medio'
                plan['actividad']=dict(nombre='Excavación',evidencia='Excavación')
                plan['atributos']=[dict(nombre='método',valor='manual',campo='descripcion',evidencia='por cualquier medio')]
                plan['consultas']=['excavación']
            with self.subTest(caso=caso),self.assertRaises(ValueError): claves.validar_plan(plan,r)

    def test_consulta_no_es_descripcion_entera_ni_puede_superar_los_limites(self):
        for consultas in ([],['concreto hecho obra'],['concreto']*2,['uno dos tres cuatro cinco seis siete ocho nueve'],['x'*121]):
            plan=self.plan();plan['consultas']=consultas
            with self.assertRaises(ValueError): claves.validar_plan(plan,self.registro())

    def test_union_de_consultas_no_se_detiene_en_la_primera_y_respeta_unidad(self):
        datos=dict(registros=[self.registro()],dudas=['Original'])
        antes=deepcopy(datos)
        candidato=lambda n,u,desc:dict(IdCodigo=n,Codigo=f'CB-{n}',DescripcionLarga=desc,IdUnidad=u,IdTipo=4)
        especifico=candidato(2,11,'Concreto F\'c=200 hecho en obra')
        with patch.object(buscador,'buscar',side_effect=[
                [candidato(1,12,'Concreto'),especifico],[especifico,candidato(3,11,self.registro()['descripcion'])],[]]) as buscar:
            salida=buscador.buscar_presupuesto(datos,self.conexion(),consultas={'Variable:7':self.plan()['consultas']},ampliar=True)
        b=salida['busquedas_construbase'][0]
        self.assertEqual(buscar.call_count,3)
        self.assertEqual(b['recuperados_unicos'],3)
        self.assertEqual(b['candidatos'][0]['IdCodigo'],2)
        self.assertEqual(b['candidatos'][0]['consulta_origen'],'concreto 200 obra')
        self.assertEqual(b['origen_terminos'],'plan_ia')
        self.assertIsNone(b['seleccion'])
        self.assertEqual(datos,antes)
        self.assertEqual(salida['registros'],antes['registros'])

    def test_error_ia_no_recae_silenciosamente_en_dos_palabras(self):
        datos=dict(registros=[self.registro()])
        with patch.object(claves,'configuracion',return_value=('local','mismo-modelo','')),patch.object(
                claves,'interpretar_claves',side_effect=ValueError('Evidencia inválida')),patch.object(buscador,'buscar') as buscar:
            salida=claves.buscar_con_ia(datos,self.conexion())
        buscar.assert_not_called()
        self.assertEqual(salida['busquedas_construbase'][0]['estado'],'requiere_terminos')
        self.assertIn('error',salida['interpretacion_tecnica_ia']['Variable:7'])
        self.assertEqual(salida['registros'],datos['registros'])

    def test_integracion_interpreta_antes_de_consultar_sin_alterar_original(self):
        datos=dict(registros=[self.registro()]);antes=deepcopy(datos)
        secuencia=[]
        def interpretar(*args):
            secuencia.append('IA');return self.plan()
        def buscar(*args,**kwargs):
            secuencia.append('SQL');return []
        with patch.object(claves,'configuracion',return_value=('local','modelo-prueba','')),patch.object(
                claves,'interpretar_claves',side_effect=interpretar),patch.object(buscador,'buscar',side_effect=buscar):
            salida=claves.buscar_con_ia(datos,self.conexion())
        self.assertEqual(secuencia,['IA','SQL','SQL','SQL'])
        self.assertEqual(salida['interpretacion_tecnica_ia']['Variable:7']['plan'],self.plan())
        self.assertEqual(datos,antes)

    def test_unidad_no_es_subcadena_y_resistencia_no_es_subnumero(self):
        plan=self.plan();plan['atributos'][-1]['valor']='M'
        with self.assertRaises(ValueError): claves.validar_plan(plan,self.registro())
        r=self.registro();r['descripcion']=r['descripcion'].replace('200','2000')
        plan=self.plan();plan['atributos'][0]['evidencia']="F'C=2000 KG/CM2"
        with self.assertRaises(ValueError): claves.validar_plan(plan,r)

    def test_limpieza_no_exige_comillas_ni_punto_final_y_conserva_decimales(self):
        self.assertEqual(claves.limpiar_consulta('excavacion tipo "B" 2.00 M.'),'excavacion tipo B 2.00 M')
        self.assertEqual(claves.limpiar_consulta('concreto 200; espesor 0,05'),'concreto 200 espesor 0,05')

    def test_limpia_consultas_del_modelo_y_no_modifica_evidencia(self):
        respuesta=self.plan();respuesta['actividad']['evidencia']='C0'
        for a in respuesta['atributos']:
            a['evidencia']='CU' if a.pop('campo')=='unidad' else 'C0'
        respuesta['consultas']=['concreto "200" obra.', 'concreto']
        with patch.object(claves,'consultar_ia',return_value=json.dumps(respuesta)):
            plan=claves.interpretar_claves(self.registro(),'Prueba')
        self.assertEqual(plan['consultas'],['concreto 200 obra','concreto'])
        self.assertEqual(plan['actividad']['evidencia'],self.registro()['descripcion'])
        respuesta['consultas']='a'
        with patch.object(claves,'consultar_ia',return_value=json.dumps(respuesta)),self.assertRaises(ValueError):
            claves.interpretar_claves(self.registro(),'Prueba')
