from contextlib import ExitStack
from copy import deepcopy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    import numpy as np
except ImportError:
    np = None
if np is not None:
    import indice_local as idx
    import laboratorio_coincidencias as lab
    import mini_pai_buscar as mini
    from tests import test_mini_pai_buscar as existentes


@unittest.skipIf(np is None, 'Instalar requirements-laboratorio.txt para probar recuperación con índice')
class BusquedaIndiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / 'indice.sqlite'
        self.entrada = existentes.PruebasBusquedaPresupuesto().entrada()
        self.conexion = Mock()
        self.conexion.cursor.return_value.fetchall.return_value = [
            (1, 'REAL1', 'Descripción SQL íntegra M2', 11, 4, 'M2'),
            (2, 'REAL2', 'Descripción SQL íntegra M3', 12, 4, 'M3')]
        self.stack = self.enterContext(ExitStack())
        self.stack.enter_context(patch.object(lab, 'entorno_modelos', return_value=dict(modelos=[dict(digest='digest')])) )
        self.descarga = self.stack.enter_context(patch.object(lab, 'post', return_value={}))
        self.documentos = self.stack.enter_context(patch.object(idx, 'embeddings', return_value=np.eye(2, dtype=np.float32)))
        self.consultas = self.stack.enter_context(patch.object(lab, 'embeddings', side_effect=lambda b,m,t,**kw: np.array([[0,1]] * len(t), dtype=np.float32)))

    def buscar(self):
        return mini.buscar_con_indice(self.entrada, self.conexion, self.ruta)

    def test_contrato_conserva_fuentes_reutiliza_cache_y_descarga_modelo(self):
        copia = deepcopy(self.entrada)
        primera = self.buscar()
        segunda = self.buscar()
        self.assertEqual(copia, self.entrada)
        self.assertEqual(primera['registros'], copia['registros'])
        self.assertEqual(segunda['recuperacion_indice']['construccion']['nuevos'], 0)
        self.assertEqual(self.documentos.call_count, 1)
        self.assertEqual(self.consultas.call_count, 2)
        self.assertEqual(self.descarga.call_count, 2)
        for b in segunda['busquedas_construbase']:
            self.assertIsNone(b['seleccion'])
            self.assertTrue(b['requiere_revision'])
            self.assertEqual(b['estado'], 'candidatos_por_revisar')
            self.assertEqual([c['IdCodigo'] for c in b['candidatos']], [1,2])
            self.assertEqual(b['candidatos'][0]['DescripcionLarga'], 'Descripción SQL íntegra M2')
            self.assertEqual(b['candidatos'][1]['comparacion_unidad'], 'diferente')
        self.assertTrue(all(c.args[0].lstrip().startswith('SELECT') for c in self.conexion.cursor.return_value.execute.call_args_list))

    def test_sin_descripcion_no_es_busqueda_vacia(self):
        for r in self.entrada['registros']:
            if r['tipo']=='concepto':r['descripcion']=None
        salida = self.buscar()
        self.consultas.assert_not_called()
        self.assertTrue(all(b['estado']=='requiere_descripcion' and not b['candidatos'] for b in salida['busquedas_construbase']))

    def test_cache_incompatible_falla_sin_degradar_a_sin_coincidencias(self):
        self.buscar()
        with patch.object(lab, 'entorno_modelos', return_value=dict(modelos=[dict(digest='cambiado')])):
            with self.assertRaisesRegex(ValueError, 'otro catálogo'):
                self.buscar()
        self.assertEqual(self.documentos.call_count, 1)

    def test_no_reemplaza_decisiones_existentes(self):
        self.entrada['busquedas_construbase']=[dict(seleccion=dict(IdCodigo=1))]
        with self.assertRaisesRegex(ValueError, 'no reemplazar'):
            self.buscar()
        self.conexion.cursor.assert_not_called()

    def test_cli_rechaza_salida_igual_al_indice(self):
        with patch('sys.argv', ['buscar','entrada.json','--salida',str(self.ruta),'--indice',str(self.ruta)]), patch('sys.stderr',new_callable=io.StringIO):
            with self.assertRaises(SystemExit):mini.main()
        self.assertFalse(self.ruta.exists())

    def test_embedding_recibe_contexto_compartido_sin_cambiar_cliente(self):
        from tests import test_contextos_compartidos as compartidos
        self.entrada=compartidos.ContextosCompartidos().datos()
        copia=deepcopy(self.entrada)
        self.buscar()
        textos=self.consultas.call_args.args[2]
        self.assertIn('Suministro de panel de madera',textos[0])
        self.assertIn('De 0.70 x 0.60 m',textos[0])
        self.assertNotIn('panel de madera',textos[-1])
        self.assertEqual(self.entrada,copia)
