"""Diagnóstico de relaciones PuCatalogo/PuMatrices; no modifica ConstruBase."""
import json
import sys

from buscar_conceptos import cargar_env


def diagnosticar(conexion, codigo):
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME IN ('PuCatalogo', 'PuExpIns', 'PuMatrices')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """)
    esquema = {}
    for tabla, columna, tipo in cursor.fetchall():
        esquema.setdefault(tabla, []).append({"columna": columna, "tipo": tipo})
    cursor.execute("""
        SELECT TOP (1) IdCodigo, Codigo, DescripcionLarga, IdTipo
        FROM dbo.PuCatalogo WHERE Codigo = ?
    """, codigo)
    fila = cursor.fetchone()
    concepto = None if fila is None else {
        "IdCodigo": str(fila[0]), "Codigo": fila[1],
        "DescripcionLarga": fila[2], "IdTipo": fila[3]
    }
    relaciones = {}
    if concepto:
        cursor.execute("""
            SELECT e.IdExpIns, e.IdPresupuesto, COUNT(m.IdMatriz) AS Renglones
            FROM dbo.PuExpIns AS e
            LEFT JOIN dbo.PuMatrices AS m ON m.IdCodigoMatriz = e.IdExpIns
            WHERE e.IdCodigo = ?
            GROUP BY e.IdExpIns, e.IdPresupuesto
            ORDER BY Renglones DESC, e.IdExpIns
        """, fila[0])
        relaciones["matrices_del_concepto"] = [
            {"IdExpIns": r[0], "IdPresupuesto": r[1], "Renglones": r[2]}
            for r in cursor.fetchall()
        ]
    return {"esquema": esquema, "concepto": concepto, "relaciones": relaciones,
            "nota": "Diagnóstico por relación verificada; no se recuperan costos ni subanálisis."}


def main():
    import argparse
    import getpass
    import os
    import socket
    parser = argparse.ArgumentParser()
    parser.add_argument("codigo", nargs="?", default="10301-003")
    args = parser.parse_args()
    try:
        import pyodbc
    except ImportError:
        print("Instala pyodbc: python -m pip install pyodbc", file=sys.stderr)
        return 1
    cargar_env()
    servidor = os.getenv("PRECIOAI_SQL_SERVER") or rf"{socket.gethostname()}\PUWPS2022"
    clave = os.getenv("PRECIOAI_SQL_PASSWORD") or getpass.getpass("Contraseña SQL Server: ")
    cadena = (f"DRIVER={{{os.getenv('PRECIOAI_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')}}};"
              f"SERVER={servidor};DATABASE={os.getenv('PRECIOAI_SQL_DATABASE', 'CONSTRUBASE_OCTUBRE_2026')};"
              f"UID={os.getenv('PRECIOAI_SQL_USER', 'sa')};PWD={clave};"
              "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;")
    try:
        with pyodbc.connect(cadena, timeout=8) as conexion:
            resultado = diagnosticar(conexion, args.codigo)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))
        return 0
    except pyodbc.Error as error:
        print(f"Error SQL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
