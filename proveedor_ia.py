"""Proveedor de IA intercambiable: Ollama local o API compatible OpenAI."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def cargar_env(ruta=".env"):
    """Lee configuración local sin sobrescribir variables de entorno."""
    archivo = Path(ruta)
    if not archivo.is_file():
        return
    for linea in archivo.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def configuracion():
    cargar_env()
    proveedor = os.getenv("PRECIOAI_AI_PROVIDER", "ollama").lower()
    if proveedor not in ("ollama", "openai"):
        raise ValueError("PRECIOAI_AI_PROVIDER debe ser ollama u openai")
    base = os.getenv("PRECIOAI_AI_BASE_URL", "").rstrip("/")
    if not base:
        base = "http://127.0.0.1:11434/v1" if proveedor == "ollama" else "https://api.openai.com/v1"
    modelo = os.getenv("PRECIOAI_AI_MODEL", "")
    if not modelo:
        raise ValueError("Configura PRECIOAI_AI_MODEL en .env")
    clave = os.getenv("PRECIOAI_AI_API_KEY", "")
    if proveedor == "openai" and not clave:
        raise ValueError("Configura PRECIOAI_AI_API_KEY para la nube")
    return base, modelo, clave


def consultar_ia(mensajes, *, esquema=None):
    base, modelo, clave = configuracion()
    if not base.startswith(("http://", "https://")):
        raise ValueError("URL de proveedor inválida")
    solicitud = {"model": modelo, "messages": mensajes, "stream": False}
    nativo = (os.getenv("PRECIOAI_AI_PROVIDER", "ollama").lower() == "ollama"
              and bool(os.getenv("PRECIOAI_OLLAMA_NUM_CTX")))
    if nativo:
        contexto = int(os.environ["PRECIOAI_OLLAMA_NUM_CTX"])
        prediccion = int(os.getenv("PRECIOAI_OLLAMA_NUM_PREDICT", "2048"))
        pensamiento = os.getenv("PRECIOAI_OLLAMA_THINK", "").lower()
        if not 4096 <= contexto <= 32768 or not 256 <= prediccion <= 8192 or pensamiento not in ("", "true", "false"):
            raise ValueError("Configuración Ollama de contexto/generación inválida")
        solicitud.update(options=dict(num_ctx=contexto, num_predict=prediccion, temperature=0))
        if pensamiento:
            solicitud["think"] = pensamiento == "true"
        if esquema is not None:
            solicitud["format"] = esquema
    if esquema is not None and not nativo:
        solicitud["temperature"] = 0
        solicitud["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "interpretacion_presupuesto", "strict": True, "schema": esquema}}
    cuerpo = json.dumps(solicitud).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if clave:
        headers["Authorization"] = "Bearer " + clave
    url = base.removesuffix("/v1") + "/api/chat" if nativo else base + "/chat/completions"
    peticion = Request(url, data=cuerpo, headers=headers, method="POST")
    try:
        with urlopen(peticion, timeout=120) as respuesta:
            datos = json.load(respuesta)
    except HTTPError as exc:
        raise RuntimeError(f"El proveedor devolvió HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("No se pudo conectar al proveedor de IA") from exc
    try:
        if not isinstance(datos, dict):
            raise TypeError("El proveedor no devolvió un objeto")
        if nativo:
            if datos.get("done_reason") == "length":
                raise RuntimeError("La respuesta de IA quedó truncada; reducir el bloque de entrada")
            contenido = datos["message"]["content"]
            if not isinstance(contenido, str) or datos.get("done") is not True:
                raise TypeError("Respuesta nativa incompleta")
            return contenido
        opcion = datos["choices"][0]
        if not isinstance(opcion, dict):
            raise TypeError("La opción no es un objeto")
        if opcion.get("finish_reason") == "length":
            raise RuntimeError("La respuesta de IA quedó truncada; reducir el bloque de entrada")
        contenido = opcion["message"]["content"]
        if not isinstance(contenido, str):
            raise TypeError("El contenido no es texto")
        return contenido
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Respuesta inesperada del proveedor de IA") from exc


def main():
    parser = argparse.ArgumentParser(description="Probar conexión con IA local o nube")
    parser.add_argument("--probar", action="store_true", help="Enviar una prueba breve")
    args = parser.parse_args()
    if not args.probar:
        parser.print_help()
        return
    print(consultar_ia([{"role": "user", "content": "Responde solamente: PrecioAI listo"}]))


if __name__ == "__main__":
    main()
