import os
import io
import json
import unittest
from unittest.mock import patch
import proveedor_ia


class TestProveedorIA(unittest.TestCase):
    def test_ollama_contexto_acotado_mismo_modelo_y_esquema_nativo(self):
        with patch.dict(os.environ,{"PRECIOAI_AI_PROVIDER":"ollama","PRECIOAI_OLLAMA_NUM_CTX":"8192",
                "PRECIOAI_OLLAMA_THINK":"false"},clear=True),patch("proveedor_ia.configuracion",return_value=(
                "http://127.0.0.1:11434/v1","mismo-modelo","")),patch("proveedor_ia.urlopen") as abrir:
            abrir.return_value.__enter__.return_value=io.StringIO(json.dumps({
                "done":True,"done_reason":"stop","message":{"content":"{}"}}))
            self.assertEqual(proveedor_ia.consultar_ia([],esquema={"type":"object"}),"{}")
            peticion=abrir.call_args.args[0];cuerpo=json.loads(peticion.data)
            self.assertEqual(peticion.full_url,"http://127.0.0.1:11434/api/chat")
            self.assertEqual(cuerpo["model"],"mismo-modelo")
            self.assertEqual(cuerpo["keep_alive"], 0)
            self.assertEqual(cuerpo["options"]["num_ctx"],8192)
            self.assertFalse(cuerpo["think"])
            self.assertEqual(cuerpo["format"],{"type":"object"})

    def test_ollama_nativo_rechaza_respuesta_incompleta_o_truncada(self):
        for respuesta in ({"done":False,"message":{"content":"{}"}},
                          {"done":True,"done_reason":"length","message":{"content":"{}"}}):
            with self.subTest(respuesta=respuesta),patch.dict(os.environ,{
                    "PRECIOAI_OLLAMA_NUM_CTX":"8192"},clear=True),patch("proveedor_ia.configuracion",return_value=(
                    "http://local/v1","modelo","")),patch("proveedor_ia.urlopen") as abrir:
                abrir.return_value.__enter__.return_value=io.StringIO(json.dumps(respuesta))
                with self.assertRaises(RuntimeError): proveedor_ia.consultar_ia([])

    def test_respuesta_malformada_se_reporta_como_error_de_proveedor(self):
        for opcion in (None, "texto", [], {"message": {"content": None}},
                       {"message": {"content": {"objeto": True}}}):
            with self.subTest(opcion=opcion), patch("proveedor_ia.configuracion", return_value=(
                    "http://localhost/v1", "modelo", "")), patch("proveedor_ia.urlopen") as abrir:
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps({"choices": [opcion]}))
                with self.assertRaisesRegex(RuntimeError, "Respuesta inesperada"):
                    proveedor_ia.consultar_ia([])

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
