import unittest
from decimal import Decimal

from calculo_importes import calcular_importe


class TestCalculoImportes(unittest.TestCase):
    def test_multiplicacion_material(self):
        self.assertEqual(calcular_importe("3600", "0.0002"), Decimal("0.72"))

    def test_division_cuadrilla(self):
        self.assertEqual(calcular_importe("2916.60", "400", dividir=True), Decimal("7.29"))

    def test_division_topografo_ejemplo(self):
        self.assertEqual(calcular_importe("778.55", "600", dividir=True), Decimal("1.30"))

    def test_redondeos_diferentes(self):
        self.assertEqual(calcular_importe("1.29123", "1"), Decimal("1.29"))
        self.assertEqual(calcular_importe("1.29123", "1", redondeo="arriba"), Decimal("1.30"))

    def test_division_cero(self):
        with self.assertRaises(ValueError):
            calcular_importe("10", "0", dividir=True)

    def test_redondeo_desconocido(self):
        with self.assertRaises(ValueError):
            calcular_importe("10", "1", redondeo="otro")


if __name__ == "__main__":
    unittest.main()
