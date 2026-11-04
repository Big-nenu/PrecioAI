"""Consulta los renglones de una matriz de ConstruBase (solo lectura)."""
import argparse
import getpass
import json
import os
import socket
import sys

from buscar_conceptos import cargar_env


def obtener_renglones(conexion, id_expins, profundidad=0, visitados=None):
    if not 0 <= profundidad <= 3:
        raise ValueError("La profundidad debe estar entre 0 y 3")
    visitados = set() if visitados is None else visitados
    if id_expins in visitados:
        return {"IdExpIns": id_expins, "advertencia": "Referencia circular detectada"}
    visitados = visitados | {id_expins}
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.IdExpIns, e.IdPresupuesto, c.Codigo, c.DescripcionLarga
        FROM dbo.PuExpIns AS e
        JOIN dbo.PuCatalogo AS c ON c.IdCodigo = e.IdCodigo
        WHERE e.IdExpIns = ?
    """, id_expins)
    encabezado = cursor.fetchone()
    if encabezado is None:
        raise ValueError("No existe la instancia de matriz solicitada")
    cursor.execute("""
        SELECT m.Renglon, m.IdCodigoInsumo AS IdExpInsInsumo,
               c.Codigo, c.DescripcionLarga, c.IdTipo,
               m.Volumen, m.Dividir, m.Expresion
        FROM dbo.PuMatrices AS m
        JOIN dbo.PuExpIns AS e ON e.IdExpIns = m.IdCodigoInsumo
        JOIN dbo.PuCatalogo AS c ON c.IdCodigo = e.IdCodigo
        WHERE m.IdCodigoMatriz = ?
        ORDER BY m.Renglon, m.IdMatriz
    """, id_expins)
    columnas = [col[0] for col in cursor.description]
    renglones = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    if profundidad:
        for renglon in renglones:
            if renglon["IdTipo"] == 4:
                renglon["subanalisis"] = obtener_renglones(
                    conexion, renglon["IdExpInsInsumo"], profundidad - 1, visitados)
    return {"matriz": {"IdExpIns": encabezado[0],
                       "IdPresupuesto": encabezado[1],
                       "Codigo": encabezado[2],
                       "DescripcionLarga": encabezado[3]},
            "renglones": renglones,
            "nota": "Cantidades originales; no se calculan precios. Subanálisis limitados a la profundidad solicitada."}


def main():
    parser = argparse.ArgumentParser(description="Consultar renglones de una matriz")
    parser.add_argument("id_expins", type=int, help="IdExpIns de la matriz, no IdCodigo")
    parser.add_argument("--profundidad", type=int, default=0, choices=range(4),
                        help="Niveles de subanálisis a consultar (0-3)")
    args = parser.parse_args()
    cargar_env()
    try:
        import pyodbc
    except ImportError:
        print("Falta pyodbc: python -m pip install pyodbc", file=sys.stderr)
        return 1
    servidor = os.getenv("PRECIOAI_SQL_SERVER") or rf"{socket.gethostname()}\PUWPS2022"
    clave = os.getenv("PRECIOAI_SQL_PASSWORD") or getpass.getpass("Contraseña SQL Server: ")
    cadena = (f"DRIVER={{{os.getenv('PRECIOAI_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')}}};"
              f"SERVER={servidor};DATABASE={os.getenv('PRECIOAI_SQL_DATABASE', 'CONSTRUBASE_OCTUBRE_2026')};"
              f"UID={os.getenv('PRECIOAI_SQL_USER', 'sa')};PWD={clave};"
              "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;")
    try:
        with pyodbc.connect(cadena, timeout=8) as conexion:
            resultado = obtener_renglones(conexion, args.id_expins, args.profundidad)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
        return 0
    except (pyodbc.Error, ValueError) as error:
        print(f"Error al consultar matriz: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
