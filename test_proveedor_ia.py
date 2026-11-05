import os
import unittest
from unittest.mock import patch
import proveedor_ia


class TestProveedorIA(unittest.TestCase):
    def test_ollama_por_defecto(self):
        with patch.dict(os.environ, {"PRECIOAI_AI_PROVIDER": "ollama", "PRECIOAI_AI_MODEL": "modelo-prueba", "PRECIOAI_AI_BASE_URL": ""}, clear=True):
            self.assertEqual(proveedor_ia.configuracion()[:2], ("http://127.0.0.1:11434/v1", "modelo-prueba"))

    def test_nube_exige_clave(self):
        with patch.dict(os.environ, {"PRECIOAI_AI_PROVIDER": "openai", "PRECIOAI_AI_MODEL": "modelo-prueba"}, clear=True):
            with self.assertRaisesRegex(ValueError, "API_KEY"):
                proveedor_ia.configuracion()


if __name__ == "__main__":
    unittest.main()
