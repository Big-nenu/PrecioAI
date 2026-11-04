"""Búsqueda de conceptos en ConstruBase (solo lectura)."""
import argparse
import getpass
import json
import os
import sys


def buscar(conexion, texto, limite=10):
    """Devuelve coincidencias de la descripción completa, sin modificar la BD."""
    if not 1 <= limite <= 50:
        raise ValueError("El límite debe estar entre 1 y 50")
    palabras = [p for p in texto.strip().split() if p]
    if not palabras:
        raise ValueError("Indica palabras para buscar")
    filtros = " AND ".join("DescripcionLarga LIKE ?" for _ in palabras)
    sql = f"""SELECT TOP ({limite}) Codigo, Descripcion, DescripcionLarga, IdUnidad, IdTipo
FROM dbo.PuCatalogo
WHERE {filtros}
ORDER BY Codigo"""
    cursor = conexion.cursor()
    cursor.execute(sql, *(f"%{p}%" for p in palabras))
    columnas = [col[0] for col in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def cargar_env(ruta=".env"):
    """Carga variables locales sin sobrescribir las del entorno."""
    from pathlib import Path
    archivo = Path(__file__).resolve().parent / ruta
    if not archivo.is_file():
        return
    for linea in archivo.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave = clave.strip()
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("\u0027", "\u0022"):
            valor = valor[1:-1]
        if clave.startswith("PRECIOAI_SQL_"):
            os.environ.setdefault(clave, valor)


def main():
    parser = argparse.ArgumentParser(description="Buscar conceptos de ConstruBase")
    parser.add_argument("texto", help="Palabras a buscar en la descripción completa")
    parser.add_argument("--limite", type=int, default=10)
    parser.add_argument("--ordenar", action="store_true", help="Priorizar coincidencias con reglas explicables")
    args = parser.parse_args()
    try:
        import pyodbc
    except ImportError:
        print("Falta pyodbc. Instala con: python -m pip install pyodbc", file=sys.stderr)
        return 1
    cargar_env()
    servidor = os.getenv("PRECIOAI_SQL_SERVER", r"LUIS-PC\PUWPS2022")
    base = os.getenv("PRECIOAI_SQL_DATABASE", "CONSTRUBASE_OCTUBRE_2026")
    usuario = os.getenv("PRECIOAI_SQL_USER", "sa")
    clave = os.getenv("PRECIOAI_SQL_PASSWORD") or getpass.getpass("Contraseña de SQL Server: ")
    driver = os.getenv("PRECIOAI_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    cadena = (f"DRIVER={{{driver}}};SERVER={servidor};DATABASE={base};"
              f"UID={usuario};PWD={clave};Encrypt=yes;TrustServerCertificate=yes;"
              "ApplicationIntent=ReadOnly;")
    try:
        with pyodbc.connect(cadena, timeout=8) as conexion:
            datos = buscar(conexion, args.texto, args.limite)
        if args.ordenar:
            from ranking_conceptos import ordenar_candidatos
            datos = ordenar_candidatos(args.texto, datos)
        print(json.dumps(datos, ensure_ascii=False, indent=2, default=str))
        return 0
    except (pyodbc.Error, ValueError) as exc:
        print(f"Error de búsqueda: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
