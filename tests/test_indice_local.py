import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError:
    np = None
if np is not None:
    import indice_local as idx


@unittest.skipIf(np is None, 'Instalar requirements-laboratorio.txt para probar el índice')
class IndiceLocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / 'indice.sqlite'
        self.docs = [dict(id=str(i), descripcion=f'Concepto original {i}', unidad='m2') for i in range(3)]
        self.modelo = 'embeddinggemma-2:270m'
        self.firma = idx.firma(self.docs, self.modelo, 'digest')

    def construir(self, **kw):
        return idx.construir(self.ruta, self.docs, self.modelo, 'digest', **kw)

    @staticmethod
    def vectores(base, modelo, textos, **kw):
        return np.array([[1, i + 1] for i, _ in enumerate(textos)], dtype=np.float32)

    def test_persistir_reabrir_sin_recalcular_y_orden_independiente(self):
        with patch.object(idx, 'embeddings', side_effect=self.vectores) as mock:
            self.assertEqual(self.construir()['nuevos'], 3)
            self.assertEqual(self.construir()['reutilizados'], 3)
            self.assertEqual(mock.call_count, 1)
        docs, vec = idx.cargar(self.ruta, self.firma)
        self.assertEqual(docs, self.docs)
        np.testing.assert_array_equal(vec, [[1, 1], [1, 2], [1, 3]])
        self.assertEqual(idx.firma(self.docs[::-1], self.modelo, 'digest'), self.firma)

    def test_interrupcion_reanuda_solo_pendientes(self):
        with patch.object(idx, 'embeddings', side_effect=[np.array([[1, 2]], dtype=np.float32), RuntimeError('interrumpido')]):
            with self.assertRaises(RuntimeError):
                self.construir(lote=1)
        with self.assertRaisesRegex(ValueError, 'incompleto'):
            idx.cargar(self.ruta, self.firma)
        with patch.object(idx, 'embeddings', side_effect=self.vectores) as mock:
            self.assertEqual(self.construir()['nuevos'], 2)
            self.assertEqual(len(mock.call_args.args[2]), 2)
        self.assertEqual(len(idx.cargar(self.ruta, self.firma)[0]), 3)

    def test_identidad_distinta_rechazada(self):
        with patch.object(idx, 'embeddings', side_effect=self.vectores):
            self.construir()
        for docs, digest in [(self.docs, 'otro'), ([dict(d, descripcion='alterado') for d in self.docs], 'digest')]:
            with self.assertRaisesRegex(ValueError, 'otro catálogo'):
                idx.construir(self.ruta, docs, self.modelo, digest)
        with patch.object(idx, 'prefijos', return_value=('otra consulta', 'otro documento')):
            with self.assertRaisesRegex(ValueError, 'otro catálogo'):
                self.construir()
        self.assertEqual(idx.cargar(self.ruta, self.firma)[0], self.docs)

    def test_no_adopta_base_ajena(self):
        with closing(sqlite3.connect(self.ruta)) as db, db:
            db.execute('CREATE TABLE original (valor TEXT)')
            db.execute("INSERT INTO original VALUES ('intacto')")
        with self.assertRaisesRegex(ValueError, 'no es un índice'):
            self.construir()
        with closing(sqlite3.connect(self.ruta)) as db:
            self.assertEqual(db.execute('SELECT valor FROM original').fetchone()[0], 'intacto')

    def test_vector_y_texto_corruptos_rechazados(self):
        for caso in ('longitud', 'nan', 'cero', 'texto'):
            with self.subTest(caso=caso):
                ruta = Path(self.tmp.name) / f'{caso}.sqlite'
                with patch.object(idx, 'embeddings', side_effect=self.vectores):
                    idx.construir(ruta, self.docs, self.modelo, 'digest')
                with closing(sqlite3.connect(ruta)) as db, db:
                    if caso == 'texto':
                        db.execute('UPDATE vectores SET documento=? WHERE id=?', (json.dumps(dict(self.docs[0], descripcion='cambiado')), '0'))
                    else:
                        blob = b'x' if caso == 'longitud' else np.array([float('nan'), 1] if caso == 'nan' else [0, 0], dtype='<f4').tobytes()
                        db.execute('UPDATE vectores SET vector=? WHERE id=?', (blob, '0'))
                with self.assertRaises(ValueError):
                    idx.cargar(ruta, self.firma)

    def test_prefijo_qwen_solo_consulta(self):
        consulta, documento = idx.prefijos('qwen3-embedding:0.6b')
        self.assertTrue(consulta.startswith('Instruct: '))
        self.assertTrue(consulta.endswith('\nQuery: '))
        self.assertEqual(documento, '')
