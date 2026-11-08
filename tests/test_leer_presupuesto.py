import unittest
from leer_presupuesto import extraer_filas, normalizar_cantidad


class Pruebas(unittest.TestCase):
    def test_cantidad(self):
        self.assertEqual(normalizar_cantidad('1,599.0000'), '1599.0000')

    def test_estructura(self):
        filas = [['CLAVE', 'DESCRIPCION', None, 'UNIDAD', 'CANTIDAD'],
                 ['TRABAJO : 123', 'Encabezado', None, None, None],
                 ['A.02(150)', 'PRELIMINARES', None, None, None],
                 ['150110', 'TRAZO', None, 'M2', '386.30']]
        r = extraer_filas(filas)
        self.assertEqual([x['tipo'] for x in r], ['partida', 'concepto'])
        self.assertEqual(r[1]['partida']['clave'], 'A.02(150)')
        self.assertEqual(r[1]['fila'], 4)


if __name__ == '__main__':
    unittest.main()
