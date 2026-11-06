"""Búsqueda de conceptos en ConstruBase (solo lectura)."""
import argparse
import getpass
import json
import os
import socket
import sys


def buscar(conexion, texto, limite=10, *, tipo=None):
    """Devuelve coincidencias de la descripción completa, sin modificar la BD."""
    if not 1 <= limite <= 50:
        raise ValueError("El límite debe estar entre 1 y 50")
    if tipo is not None and (type(tipo) is not int or not 1 <= tipo <= 5):
        raise ValueError("Tipo de insumo inválido")
    palabras = [p for p in texto.strip().split() if p]
    if not palabras:
        raise ValueError("Indica palabras para buscar")
    descripcion = "COALESCE(NULLIF(DescripcionLarga, N''), Descripcion) COLLATE Latin1_General_100_CI_AI"
    filtros = " AND ".join(f"{descripcion} LIKE ?" for _ in palabras)
    parametros = [f"%{p}%" for p in palabras]
    if tipo is not None:
        filtros = "IdTipo = ? AND " + filtros
        parametros.insert(0, tipo)
    sql = f"""SELECT TOP ({limite}) IdCodigo, Codigo, Descripcion, DescripcionLarga, IdUnidad, IdTipo
FROM dbo.PuCatalogo
WHERE {filtros}
ORDER BY Codigo, IdCodigo"""
    cursor = conexion.cursor()
    cursor.execute(sql, *parametros)
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


def conectar_sql(ruta_env=".env", *, pedir_clave=False):
    """Abre la misma fuente SQL en modo lectura, sin registrar credenciales."""
    import pyodbc
    cargar_env(ruta_env)
    servidor = os.getenv("PRECIOAI_SQL_SERVER") or rf"{socket.gethostname()}\PUWPS2022"
    base = os.getenv("PRECIOAI_SQL_DATABASE", "CONSTRUBASE_OCTUBRE_2026")
    usuario = os.getenv("PRECIOAI_SQL_USER", "sa")
    clave = os.getenv("PRECIOAI_SQL_PASSWORD")
    if not clave and pedir_clave:
        clave = getpass.getpass("Contraseña de SQL Server: ")
    if not clave:
        raise ValueError("Configura PRECIOAI_SQL_PASSWORD en el entorno o en un .env local")
    driver = os.getenv("PRECIOAI_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    cadena = (f"DRIVER={{{driver}}};SERVER={servidor};DATABASE={base};"
              f"UID={usuario};PWD={clave};Encrypt=yes;TrustServerCertificate=yes;"
              "ApplicationIntent=ReadOnly;")
    return pyodbc.connect(cadena, timeout=8, readonly=True)


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
    try:
        with conectar_sql(pedir_clave=True) as conexion:
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
