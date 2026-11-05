import os
import io
import json
import unittest
from unittest.mock import patch
import proveedor_ia


class TestProveedorIA(unittest.TestCase):
    def test_esquema_opcional_y_respuesta_truncada(self):
        for esquema in (None, {"type": "object"}):
            with self.subTest(esquema=esquema), patch(
                    "proveedor_ia.configuracion", return_value=("http://localhost/v1", "modelo", "")), patch(
                    "proveedor_ia.urlopen") as abrir:
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps({
                    "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}))
                self.assertEqual(proveedor_ia.consultar_ia([], esquema=esquema), "{}")
                cuerpo = json.loads(abrir.call_args.args[0].data)
                if esquema is None:
                    self.assertNotIn("response_format", cuerpo)
                else:
                    self.assertEqual(cuerpo["response_format"]["json_schema"]["schema"], esquema)
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps({
                    "choices": [{"message": {"content": "{}"}, "finish_reason": "length"}]}))
                with self.assertRaisesRegex(RuntimeError, "truncada"):
                    proveedor_ia.consultar_ia([], esquema=esquema)

    def test_ollama_por_defecto(self):
        with patch.dict(os.environ, {"PRECIOAI_AI_PROVIDER": "ollama", "PRECIOAI_AI_MODEL": "modelo-prueba", "PRECIOAI_AI_BASE_URL": ""}, clear=True):
            self.assertEqual(proveedor_ia.configuracion()[:2], ("http://127.0.0.1:11434/v1", "modelo-prueba"))

    def test_nube_exige_clave(self):
        with patch.dict(os.environ, {"PRECIOAI_AI_PROVIDER": "openai", "PRECIOAI_AI_MODEL": "modelo-prueba"}, clear=True):
            with self.assertRaisesRegex(ValueError, "API_KEY"):
                proveedor_ia.configuracion()


if __name__ == "__main__":
    unittest.main()
