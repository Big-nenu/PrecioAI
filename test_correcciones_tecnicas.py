from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from numeros_tecnicos import numeros
import mini_pai_claves as claves
import mini_pai_revision as revision
import mini_pai_seleccionar as selector
from mini_pai_confirmar import validar_evaluacion_ia
import test_mini_pai_claves as ejemplos_claves
import test_mini_pai_seleccionar as ejemplos_selector


class PruebasCorreccionesTecnicas(unittest.TestCase):
    def test_miles_decimales_y_fracciones_sin_conversion_de_unidades(self):
        self.assertEqual(numeros('Fy=4,200 kg/cm2'), numeros('Fy=4200 kg/cm2'))
        self.assertEqual(numeros('Fy=2,530'), numeros('Fy=2530'))
        self.assertEqual(numeros('0,05 0,005 2.00'), numeros('0.05 0.005 2'))
        self.assertNotEqual(numeros('1/2'), numeros('2/1'))
        self.assertNotEqual(numeros('5/16'), numeros('3/8'))
        self.assertEqual(numeros('1/4'), numeros('0.25'))
        self.assertEqual(numeros('4200 5/16'), numeros('4200 kg/cm2 5/16') - numeros('2'))
        self.assertNotEqual(numeros('0.14'), numeros('14'))
        with self.assertRaises(ValueError): numeros('1.234,56')
        with self.assertRaises(ValueError): numeros('5/0')
        self.assertNotEqual(numeros('4,200'), numeros('4,2'))

    def test_plan_con_resistencia_agrupada_y_actividad_compuesta(self):
        ejemplo = ejemplos_claves.PruebasClavesIA()
        r = ejemplo.registro()
        r['descripcion'] = 'Acero de refuerzo Fy=4,200 KG/CM2 de 5/16 en cimentación'
        p = dict(actividad=dict(nombre='Acero de refuerzo', evidencia='Acero de refuerzo'),
            atributos=[dict(nombre='resistencia', valor='4200', campo='descripcion', evidencia='Fy=4,200 KG/CM2')],
            consultas=['acero 4200 5/16', 'acero de refuerzo'], dudas=[])
        claves.validar_plan(p, r)
        p['atributos'][0]['valor'] = '6000'
        with self.assertRaises(ValueError): claves.validar_plan(p, r)

    def test_guardia_acepta_formato_de_fy_pero_rechaza_valor_distinto(self):
        ejemplo = ejemplos_selector.PruebasSeleccionIA()
        datos = ejemplo.datos(); r = datos['registros'][2]; b = datos['busquedas_construbase'][0]
        r['descripcion'] += ' Fy=4,200 kg/cm2.'
        b['candidatos'][0]['DescripcionLarga'] += ' Fy=4200 kg/cm2.'
        e = ejemplo.evaluacion()
        p = next(p for p in e['comprobaciones'] if p['aspecto'] == 'resistencia')
        p.update(estado='compatible', cliente='Fy=4,200 kg/cm2', catalogo='Fy=4200 kg/cm2')
        validar_evaluacion_ia(r, b, e)
        b['candidatos'][0]['DescripcionLarga'] = b['candidatos'][0]['DescripcionLarga'].replace('4200','6000')
        p['catalogo'] = 'Fy=6000 kg/cm2'
        with self.assertRaises(ValueError): validar_evaluacion_ia(r, b, e)

    def test_seleccion_con_dictamen_insuficiente_se_degrada_sin_sql(self):
        ejemplo = ejemplos_selector.PruebasSeleccionIA()
        e = ejemplo.evaluacion(); e['candidatos'][0]['dictamen'] = 'insuficiente'
        conexion = ejemplo.datos()
        with patch.object(selector, 'configuracion', return_value=('local','modelo','')), patch.object(
                selector, 'consultar_ia', return_value=ejemplo.respuesta(e)), patch.object(selector,'consultar_candidato') as sql:
            salida = selector.seleccionar(conexion, None)
        b = salida['busquedas_construbase'][0]
        self.assertIsNone(b['seleccion'])
        self.assertIn('evaluacion_ia_propuesta', b)
        self.assertEqual(salida['resumen_ia']['errores'], 0)
        sql.assert_not_called()

    def test_equivalente_sin_seleccion_no_se_aprueba_y_audita_original(self):
        e = ejemplos_selector.PruebasSeleccionIA().evaluacion()
        e.update(seleccion_id=None, comprobaciones=[])
        antes = deepcopy(e)
        resultado, propuesta = selector.resolver_incertidumbre(e)
        self.assertEqual(e, antes)
        self.assertEqual(propuesta, antes)
        self.assertIsNone(resultado['seleccion_id'])
        self.assertEqual(resultado['candidatos'][0]['dictamen'], 'insuficiente')

    def test_tres_opciones_siguen_orden_tecnico_y_no_orden_de_recuperacion(self):
        candidatos = [dict(IdCodigo=n) for n in range(1,6)]
        e = dict(candidatos=[dict(IdCodigo=n, dictamen='insuficiente') for n in (5,4,2,1,3)])
        b = dict(candidatos=candidatos, evaluacion_ia=e)
        self.assertEqual([c['IdCodigo'] for c,_ in revision.opciones(b)], [5,4,2])
        b['error_ia'] = 'No validada'
        self.assertEqual([c['IdCodigo'] for c,_ in revision.opciones(b)], [1,2,3])
        del b['error_ia']; e['candidatos'][0]['dictamen'] = 'incompatible'
        self.assertEqual([c['IdCodigo'] for c,_ in revision.opciones(b)], [4,2,1])

    def test_seleccion_sin_pruebas_esenciales_no_se_completa_automaticamente(self):
        ejemplo = ejemplos_selector.PruebasSeleccionIA()
        for caso in ('incompleta', 'unidad_no_aplica', 'id_ajeno'):
            e = ejemplo.evaluacion()
            if caso == 'incompleta': e['comprobaciones'].pop()
            elif caso == 'unidad_no_aplica': e['comprobaciones'][-1].update(estado='no_aplica',cliente='',catalogo='')
            else: e['seleccion_id'] = 999
            resultado, propuesta = selector.resolver_incertidumbre(e)
            if caso == 'id_ajeno':
                with self.assertRaises(ValueError): validar_evaluacion_ia(ejemplo.datos()['registros'][2],ejemplo.datos()['busquedas_construbase'][0],resultado)
            else:
                self.assertIsNone(resultado['seleccion_id'])
                self.assertIsNotNone(propuesta)
                self.assertEqual(resultado['comprobaciones'], [])

    def test_orden_explicito_se_materializa_y_rechaza_duplicados(self):
        ejemplo = ejemplos_selector.PruebasSeleccionIA(); datos = ejemplo.datos()
        r = datos['registros'][2]; b = datos['busquedas_construbase'][0]
        base = b['candidatos'][0]
        b['candidatos'] = [dict(base, IdCodigo=n, Codigo=f'CB-{n}') for n in range(10,15)]
        wire = dict(seleccion_id=None, motivo='Requiere revisión humana de las inclusiones no acreditadas',
            orden_revision={f'puesto_{n}':i for n,i in enumerate((14,13,12,11,10),1)}, comprobaciones=[], candidatos=[
                dict(IdCodigo=n,dictamen='insuficiente',motivo='Falta detalle de alcance',cliente='C0',catalogo=f'K{n}_0')
                for n in range(10,15)])
        with patch.object(selector,'consultar_ia',return_value=json.dumps(wire)):
            e,_ = selector.comparar(r,b,'Prueba')
        self.assertEqual([c['IdCodigo'] for c in e['candidatos']],[14,13,12,11,10])
        b['evaluacion_ia']=e
        self.assertEqual([c['IdCodigo'] for c,_ in revision.opciones(b)],[14,13,12])
        wire['orden_revision']={f'puesto_{n}':10 for n in range(1,6)}
        with patch.object(selector,'consultar_ia',return_value=json.dumps(wire)),self.assertRaisesRegex(ValueError,'Orden técnico'):
            selector.comparar(r,b,'Prueba')

    def test_prueba_con_espesor_distinto_se_audita_sin_aprobar_ni_consultar_sql(self):
        ejemplo = ejemplos_selector.PruebasSeleccionIA(); datos = ejemplo.datos()
        datos['registros'][2]['descripcion'] += ' Espesor de 6 cm.'
        datos['busquedas_construbase'][0]['candidatos'][0]['DescripcionLarga'] += ' Espesor de 5 cm.'
        e = ejemplo.evaluacion()
        next(p for p in e['comprobaciones'] if p['aspecto']=='espesor').update(
            estado='compatible',cliente='6 cm',catalogo='5 cm')
        with patch.object(selector,'configuracion',return_value=('local','modelo','')), patch.object(
                selector,'consultar_ia',return_value=ejemplo.respuesta(e)), patch.object(selector,'consultar_candidato') as sql:
            salida=selector.seleccionar(datos,None)
        b=salida['busquedas_construbase'][0]
        self.assertIsNone(b['seleccion'])
        self.assertEqual(b['evaluacion_ia_propuesta']['seleccion_id'],10)
        self.assertEqual(salida['resumen_ia']['errores'],0)
        sql.assert_not_called()

    def test_no_aplica_permite_cita_real_pero_no_inventada_ni_requisito_explicito(self):
        ejemplo=ejemplos_selector.PruebasSeleccionIA(); datos=ejemplo.datos()
        r=datos['registros'][2]; b=datos['busquedas_construbase'][0]; e=ejemplo.evaluacion()
        p=next(p for p in e['comprobaciones'] if p['aspecto']=='espesor')
        p.update(cliente='equipo topográfico',catalogo='equipo topográfico')
        validar_evaluacion_ia(r,b,e)
        p['catalogo']='cita inventada'
        with self.assertRaises(ValueError): validar_evaluacion_ia(r,b,e)
        p['catalogo']='equipo topográfico'
        r['descripcion']+=' espesor de 6 cm'
        with self.assertRaises(ValueError): validar_evaluacion_ia(r,b,e)
