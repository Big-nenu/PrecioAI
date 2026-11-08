import argparse
from copy import deepcopy
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from openpyxl import load_workbook
import mini_pai as flujo
import mini_pai_confirmar as confirmaciones
from tests import test_mini_pai_buscar as ejemplos
from tests import test_mini_pai_confirmar as matrices


class FlujoMiniPaiTests(unittest.TestCase):
    def test_ayuda_admite_salida_redirigida_de_windows(self):
        buffer = io.BytesIO()
        salida = io.TextIOWrapper(buffer, encoding='cp1252')
        try:
            with patch('sys.argv',['mini_pai.py','--help']), patch('sys.stdout',salida):
                with self.assertRaises(SystemExit) as exc:flujo.main()
            self.assertEqual(exc.exception.code,0)
            salida.flush()
            self.assertIn(b'--sesion',buffer.getvalue())
        finally:salida.close()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.original = self.raiz / 'original.xlsx'
        self.original.write_bytes(b'Entrada protegida; lector simulado')
        self.sesion = self.raiz / 'sesion'
        self.datos = ejemplos.PruebasBusquedaPresupuesto().entrada()
        self.candidatos = deepcopy(self.datos)
        self.candidatos['busquedas_construbase'] = [dict(hoja=r['hoja'],fila=r['fila'],seleccion=None,
            estado='candidatos_por_revisar',candidatos=[dict(IdCodigo=10,Codigo='REAL',
                DescripcionLarga=r['descripcion'],unidad_catalogo='M2',IdUnidad=11,IdTipo=4)])
            for r in self.datos['registros'] if r['tipo']=='concepto']
        self.interpretar = self.enterContext(patch.object(flujo,'interpretar',return_value=self.datos))
        self.buscar = self.enterContext(patch.object(flujo,'buscar_con_indice',return_value=self.candidatos))
        self.evaluar = self.enterContext(patch.object(flujo,'seleccionar',return_value=self.candidatos))
        self.sql = self.enterContext(patch.object(flujo,'conectar_sql',return_value=Mock()))
        self.enterContext(patch.object(flujo,'cargar_env'))
        self.enterContext(patch.object(flujo,'codigo_actual',return_value='codigo-prueba'))

    def args(self, **cambios):
        valores=dict(archivo=None,sesion=str(self.sesion),indice=None,env=None,por_tabla=None,
                     hoja=None,fila_inicial=None,fila_final=None,decisiones=None,
                     conservar_originales=False,revisor=None)
        valores.update(cambios)
        return argparse.Namespace(**valores)

    def iniciar(self):
        return flujo.ejecutar(self.args(archivo=str(self.original),indice=str(self.raiz/'indice.sqlite')))

    def test_preguntas_reanudacion_originales_y_final_idempotente_sin_sql_ni_ia(self):
        self.assertEqual(self.iniciar()['estado'],'esperando_decisiones')
        self.assertEqual(flujo.ejecutar(self.args())['pendientes'],2)
        llamadas_sql=self.sql.call_count
        resultado=flujo.ejecutar(self.args(conservar_originales=True,revisor='Usuario de prueba'))
        self.assertEqual(resultado['estado'],'terminado')
        self.assertEqual(self.sql.call_count,llamadas_sql)
        for etapa in (self.interpretar,self.buscar):self.assertEqual(etapa.call_count,1)
        self.evaluar.assert_not_called()
        excel=self.sesion/'presupuesto.xlsx';digest=flujo.sha(excel)
        flujo.ejecutar(self.args())
        self.assertEqual(flujo.sha(excel),digest)
        libro=load_workbook(excel,read_only=True)
        try:
            self.assertEqual(libro['Catálogo']['B3'].value,'REPETIDA')
            self.assertEqual(libro['Catálogo']['C3'].value,'REPETIDA')
            self.assertEqual(libro['Catálogo']['D3'].value,self.datos['registros'][1]['descripcion'])
            self.assertEqual(libro['Catálogo'].max_column,8)
        finally:libro.close()
        self.assertFalse((self.sesion/'sesion.lock').exists())

    def test_muestra_limita_solo_etapas_posteriores_y_conserva_ancestros(self):
        antes = deepcopy(self.datos)
        acotado = flujo.muestra(self.datos,1)
        self.assertEqual(self.datos,antes)
        self.assertEqual([r['fila'] for r in acotado['registros']],[2,3])
        self.assertTrue(acotado['alcance']['parcial'])
        self.assertEqual(acotado['alcance']['conceptos_interpretados'],2)
        self.assertEqual(acotado['alcance']['conceptos_procesados'],1)
        for limite in (0,-1,True):
            with self.assertRaises(ValueError):flujo.muestra(self.datos,limite)

    def test_fallo_repite_solo_la_etapa_no_terminada(self):
        self.buscar.side_effect=[RuntimeError('Sin SQL'),self.candidatos]
        with self.assertRaisesRegex(RuntimeError,'Sin SQL'):self.iniciar()
        self.assertTrue((self.sesion/'interpretacion.json').exists())
        self.assertFalse((self.sesion/'sesion.lock').exists())
        self.assertEqual(flujo.ejecutar(self.args())['estado'],'esperando_decisiones')
        self.assertEqual(self.interpretar.call_count,1)
        self.assertEqual(self.buscar.call_count,2)

    def test_decisiones_parciales_se_guardan_y_no_se_reaplican(self):
        self.iniciar()
        def decision(fila):return [dict(hoja='Obra',fila=fila,IdCodigo=None,revisor='Usuario',motivo='Conservar original')]
        archivo=self.raiz/'decisiones.json';archivo.write_text(json.dumps(decision(3)),encoding='utf-8')
        args=self.args(decisiones=str(archivo))
        estado=flujo.ejecutar(args)
        self.assertEqual(estado['pendientes'],1)
        self.assertEqual(len(flujo.ejecutar(args)['resoluciones']),1)
        archivo.write_text(json.dumps(decision(4)),encoding='utf-8')
        estado=flujo.ejecutar(args)
        self.assertEqual(estado['estado'],'terminado')
        self.assertEqual(len(estado['resoluciones']),2)
        self.assertTrue((self.sesion/'resolucion-001.json').exists())

    def test_cambios_en_original_checkpoint_o_codigo_bloquean_reutilizacion(self):
        self.iniciar()
        self.original.write_bytes(b'Otro original')
        with self.assertRaisesRegex(ValueError,'original cambió'):flujo.ejecutar(self.args())
        self.original.write_bytes(b'Entrada protegida; lector simulado')
        with patch.object(flujo,'codigo_actual',return_value='otra-version'):
            with self.assertRaisesRegex(ValueError,'versión'):flujo.ejecutar(self.args())
        (self.sesion/'interpretacion.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'modificado'):flujo.ejecutar(self.args())
        self.assertEqual(self.interpretar.call_count,1)
        self.assertFalse((self.sesion/'presupuesto.xlsx').exists())

    def test_no_adopta_carpeta_ajena_ni_elimina_bloqueo_de_otro_proceso(self):
        self.sesion.mkdir();ajeno=self.sesion/'dato.txt';ajeno.write_text('intacto',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'carpeta nueva'):self.iniciar()
        self.assertEqual(ajeno.read_text(encoding='utf-8'),'intacto')
        bloqueo=self.sesion/'sesion.lock';bloqueo.write_text('otro proceso',encoding='utf-8')
        with self.assertRaises(FileExistsError):self.iniciar()
        self.assertTrue(bloqueo.exists())
        self.interpretar.assert_not_called()

    def test_decisiones_invalidas_no_abren_sql_ni_sobrescriben_estado(self):
        self.iniciar();conteo=self.sql.call_count
        archivo=self.raiz/'decisiones.json';archivo.write_text('[{}]',encoding='utf-8')
        with self.assertRaises(ValueError):flujo.ejecutar(self.args(decisiones=str(archivo)))
        self.assertEqual(self.sql.call_count,conteo)
        self.assertFalse((self.sesion/'resolucion-001.json').exists())

    def test_matriz_cambiada_en_sql_impide_excel_y_se_puede_reverificar(self):
        ejemplo=matrices.PruebasConfirmaciones();datos=ejemplo.entrada()
        seleccionados=confirmaciones.confirmar(datos,ejemplo.decisiones(),ejemplo.conexion(datos))
        self.interpretar.return_value=datos;self.buscar.return_value=datos;self.evaluar.return_value=seleccionados
        with patch.object(flujo,'consultar_candidato',return_value={'Codigo':'CAMBIADO'}):
            with self.assertRaisesRegex(ValueError,'cambió en SQL'):
                flujo.ejecutar(self.args(archivo=str(self.original),indice=str(self.raiz/'indice.sqlite'),evaluar_tecnicamente=True))
        self.assertFalse((self.sesion/'presupuesto.xlsx').exists())
        catalogo=seleccionados['busquedas_construbase'][0]['seleccion']['catalogo']
        with patch.object(flujo,'consultar_candidato',return_value=catalogo):
            self.assertEqual(flujo.ejecutar(self.args())['estado'],'terminado')
        self.assertEqual(self.evaluar.call_count,1)

    def test_revision_estructural_se_transmite_y_se_protege_al_reanudar(self):
        archivo=self.raiz/'estructura.json';archivo.write_text('{}',encoding='utf-8')
        with patch.object(flujo,'interpretar_tabla',return_value=self.datos) as lector:
            estado=flujo.ejecutar(self.args(archivo=str(self.original),indice=str(self.raiz/'indice.sqlite'),
                por_tabla=True,revision_estructura=str(archivo)))
        lector.assert_called_once_with(str(self.original.resolve()),revision=str(archivo.resolve()))
        self.assertEqual(estado['parametros']['revision_estructura_sha256'],flujo.sha(archivo))
        archivo.write_text('{"cambio":true}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'revisión estructural cambió'):
            flujo.ejecutar(self.args())

    def test_revision_sin_ruta_tabular_no_se_ignora(self):
        archivo=self.raiz/'estructura.json';archivo.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'requiere --por-tabla'):
            flujo.ejecutar(self.args(archivo=str(self.original),indice=str(self.raiz/'indice.sqlite'),revision_estructura=str(archivo)))
        self.interpretar.assert_not_called()

    def test_por_defecto_muestra_tres_opciones_sin_evaluar_y_protege_el_modo(self):
        for b in self.candidatos['busquedas_construbase']:
            base=b['candidatos'][0]
            b['candidatos']=[dict(base,IdCodigo=n,Codigo=f'REAL-{n}') for n in range(10,15)]
        estado=self.iniciar()
        self.assertFalse(estado['parametros']['evaluar_tecnicamente'])
        self.assertNotIn('evaluacion',estado['etapas'])
        self.assertFalse((self.sesion/'evaluacion.json').exists())
        self.evaluar.assert_not_called()
        preguntas=(self.sesion/estado['preguntas']).read_text(encoding='utf-8')
        self.assertIn('REAL-10',preguntas)
        self.assertIn('REAL-12',preguntas)
        self.assertNotIn('REAL-13',preguntas)
        self.assertIn('Conservar',preguntas)
        self.assertFalse((self.sesion/'presupuesto.xlsx').exists())
        with self.assertRaisesRegex(ValueError,'No cambiar parámetros'):
            flujo.ejecutar(self.args(evaluar_tecnicamente=True))

    def test_seleccion_humana_sin_evaluacion_revalida_sql_y_conserva_auxiliares(self):
        self.iniciar()
        decisiones=[dict(hoja='Obra',fila=3,IdCodigo=10,revisor='Usuario de prueba',motivo='Matriz elegida'),
                    dict(hoja='Obra',fila=4,IdCodigo=None,revisor='Usuario de prueba',motivo='Conservar original')]
        archivo=self.raiz/'decisiones.json';archivo.write_text(json.dumps(decisiones),encoding='utf-8')
        candidato=self.candidatos['busquedas_construbase'][0]['candidatos'][0]
        catalogo={k:candidato[k] for k in confirmaciones.CAMPOS_SQL}
        with patch.object(confirmaciones,'consultar_candidato',return_value=catalogo) as confirmar_sql, \
                patch.object(flujo,'consultar_candidato',return_value=catalogo) as exportar_sql:
            estado=flujo.ejecutar(self.args(decisiones=str(archivo)))
        self.assertEqual(estado['estado'],'terminado')
        confirmar_sql.assert_called_once();exportar_sql.assert_called_once()
        self.evaluar.assert_not_called()
        libro=load_workbook(self.sesion/'presupuesto.xlsx',read_only=True)
        try:
            hoja=libro['Catálogo']
            self.assertEqual(hoja['B3'].value,'REAL')
            self.assertEqual(hoja['C3'].value,self.datos['registros'][1]['clave'])
            self.assertEqual(hoja['D3'].value,catalogo['DescripcionLarga'])
            self.assertEqual(hoja['E3'].value,self.datos['registros'][1]['descripcion'])
            self.assertEqual(hoja.max_column,8)
        finally:libro.close()

    def test_busqueda_vacia_exporta_originales_sin_evaluar(self):
        for b in self.candidatos['busquedas_construbase']:
            b.update(candidatos=[],estado='sin_candidatos_en_busqueda')
        estado=self.iniciar()
        self.assertEqual(estado['estado'],'terminado')
        self.evaluar.assert_not_called()
        self.assertNotIn('evaluacion',estado['etapas'])
        self.assertIn('Sin candidatos encontrados (2)',(self.sesion/'presupuesto.md').read_text(encoding='utf-8'))
        libro=load_workbook(self.sesion/'presupuesto.xlsx',read_only=True)
        try:
            for fila,r in zip((3,4),[r for r in self.datos['registros'] if r['tipo']=='concepto']):
                self.assertEqual(libro['Catálogo'].cell(fila,2).value,r['clave'])
                self.assertEqual(libro['Catálogo'].cell(fila,4).value,r['descripcion'])
                self.assertEqual(libro['Catálogo'].cell(fila,5).value,r['descripcion'])
        finally:libro.close()
