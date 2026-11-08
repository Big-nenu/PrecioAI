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
        self.assertIn("IdCodigo", sql)
        self.assertIn("COLLATE Latin1_General_100_CI_AI", sql)
        self.assertIn("COALESCE(NULLIF(DescripcionLarga, N''), Descripcion)", sql)
        self.assertEqual(params, ["%trazo%", "%1000%"])

    def test_tipo_parametrizado_opcional(self):
        cursor = Mock(description=[("IdCodigo",)])
        cursor.fetchall.return_value = [(28,)]
        conexion = Mock()
        conexion.cursor.return_value = cursor
        self.assertEqual(buscar(conexion, "trazo", tipo=4), [{"IdCodigo": 28}])
        sql, *params = cursor.execute.call_args.args
        self.assertIn("IdTipo = ?", sql)
        self.assertEqual(params, [4, "%trazo%"])
        with self.assertRaises(ValueError):
            buscar(conexion, "trazo", tipo=True)

    def test_limites(self):
        with self.assertRaises(ValueError):
            buscar(Mock(), " ")
        with self.assertRaises(ValueError):
            buscar(Mock(), "trazo", 51)


if __name__ == "__main__":
    unittest.main()
