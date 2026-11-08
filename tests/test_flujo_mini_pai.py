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
        for etapa in (self.interpretar,self.buscar,self.evaluar):self.assertEqual(etapa.call_count,1)
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
            with self.assertRaisesRegex(ValueError,'cambió en SQL'):self.iniciar()
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
