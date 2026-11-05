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
    if esquema is not None:
        solicitud["temperature"] = 0
        solicitud["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "interpretacion_presupuesto", "strict": True, "schema": esquema}}
    cuerpo = json.dumps(solicitud).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if clave:
        headers["Authorization"] = "Bearer " + clave
    peticion = Request(base + "/chat/completions", data=cuerpo, headers=headers, method="POST")
    try:
        with urlopen(peticion, timeout=120) as respuesta:
            datos = json.load(respuesta)
    except HTTPError as exc:
        raise RuntimeError(f"El proveedor devolvió HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("No se pudo conectar al proveedor de IA") from exc
    try:
        if datos["choices"][0].get("finish_reason") == "length":
            raise RuntimeError("La respuesta de IA quedó truncada; reducir el bloque de entrada")
        return datos["choices"][0]["message"]["content"]
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
