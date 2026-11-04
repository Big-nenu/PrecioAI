import unittest
from ranking_conceptos import ordenar_candidatos


def concepto(codigo, descripcion):
    return {"Codigo": codigo, "DescripcionLarga": descripcion}


class TestRanking(unittest.TestCase):
    def setUp(self):
        self.candidatos = [
            concepto("10301-001", "Trazo y nivelación manual"),
            concepto("10301-003", "Trazo y nivelación con equipo topográfico (Hasta 1000 m2)"),
            concepto("10301-004", "Trazo y nivelación con equipo topográfico (Mayor a 1000 m2)"),
            concepto("10301-006", "Trazo y nivelación con equipo topográfico, incluye elaboración de plano (Hasta 1000 m2)"),
        ]

    def test_sin_plano_prefiere_003(self):
        r = ordenar_candidatos("trazo y nivelación con equipo topográfico hasta 1000 m2", self.candidatos)
        self.assertEqual(r[0]["Codigo"], "10301-003")
        self.assertEqual(len(r), 4)

    def test_con_plano_prefiere_006(self):
        r = ordenar_candidatos("trazo y nivelación con equipo topográfico, elaboración de plano hasta 1000 m2", self.candidatos)
        self.assertEqual(r[0]["Codigo"], "10301-006")

    def test_no_modifica_originales(self):
        ordenar_candidatos("trazo", self.candidatos)
        self.assertNotIn("puntaje", self.candidatos[0])


if __name__ == "__main__":
    unittest.main()
