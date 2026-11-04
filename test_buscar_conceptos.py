import unittest
from unittest.mock import Mock
from buscar_conceptos import buscar


class TestBusqueda(unittest.TestCase):
    def test_busqueda_parametrizada(self):
        cursor = Mock()
        cursor.description = [("Codigo",), ("DescripcionLarga",)]
        cursor.fetchall.return_value = [("10301-003", "Trazo hasta 1000 m2")]
        conexion = Mock()
        conexion.cursor.return_value = cursor
        resultado = buscar(conexion, "trazo 1000", 5)
        self.assertEqual(resultado[0]["Codigo"], "10301-003")
        sql, *params = cursor.execute.call_args.args
        self.assertIn("TOP (5)", sql)
        self.assertEqual(params, ["%trazo%", "%1000%"])

    def test_limites(self):
        with self.assertRaises(ValueError):
            buscar(Mock(), " ")
        with self.assertRaises(ValueError):
            buscar(Mock(), "trazo", 51)


if __name__ == "__main__":
    unittest.main()
