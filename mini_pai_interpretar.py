"""Etapa 1 Mini-PAI: inspección flexible y clasificación asistida por IA."""
import argparse
import json
from pathlib import Path

from proveedor_ia import consultar_ia


def inspeccionar_excel(ruta):
    """Devuelve celdas no vacías con coordenadas, sin inferir columnas."""
    from openpyxl import load_workbook

    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        hojas = []
        for hoja in libro:
            filas = []
            for numero, valores in enumerate(hoja.iter_rows(values_only=True), 1):
                celdas = {}
                for columna, valor in enumerate(valores, 1):
                    if valor is not None and str(valor).strip():
                        from openpyxl.utils import get_column_letter
                        celdas[f"{get_column_letter(columna)}{numero}"] = str(valor)
                if celdas:
                    filas.append({"fila": numero, "celdas": celdas})
            hojas.append({"nombre": hoja.title, "filas": filas})
        return {"archivo": Path(ruta).name, "hojas": hojas}
    finally:
        libro.close()


def interpretar(ruta, skill=None):
    skill = skill or Path(__file__).resolve().parent / "skills/analizar-presupuesto/SKILL.md"
    instrucciones = Path(skill).read_text(encoding="utf-8")
    inspeccion = inspeccionar_excel(ruta)
    respuesta = consultar_ia([
        {"role": "system", "content": instrucciones + """
Para esta tarea SOLO clasifica las filas del Excel. Devuelve exclusivamente JSON válido,
sin markdown, con objeto {"registros": [...], "dudas": [...]}.
Cada registro debe tener: tipo (partida, subpartida o concepto), hoja,
fila, clave, descripcion, unidad, cantidad, partida, subpartida.
Los campos ausentes son null. partida y subpartida son referencias textuales
a las claves originales de sus encabezados, o null.
No inventes datos ni clasifiques como concepto una fila sin evidencia.
Conserva las filas de origen y reporta ambigüedades en dudas.
No busques matrices ni hagas consultas SQL."""},
        {"role": "user", "content": json.dumps(inspeccion, ensure_ascii=False)},
    ])
    try:
        datos = json.loads(respuesta)
    except json.JSONDecodeError as exc:
        raise ValueError("La IA no devolvió JSON válido; revisar la respuesta") from exc
    validar(datos, inspeccion)
    return datos


def validar(datos, inspeccion):
    """Rechaza referencias inventadas y tipos fuera del contrato."""
    if not isinstance(datos, dict) or not isinstance(datos.get("registros"), list) or not isinstance(datos.get("dudas"), list):
        raise ValueError("La respuesta no cumple la estructura requerida")
    origen = {(h["nombre"], f["fila"]) for h in inspeccion["hojas"] for f in h["filas"]}
    campos = {"tipo", "hoja", "fila", "clave", "descripcion", "unidad", "cantidad", "partida", "subpartida"}
    for registro in datos["registros"]:
        if not isinstance(registro, dict) or not campos.issubset(registro):
            raise ValueError("Registro incompleto")
        if registro["tipo"] not in ("partida", "subpartida", "concepto"):
            raise ValueError("Tipo de registro inválido")
        if (registro["hoja"], registro["fila"]) not in origen:
            raise ValueError("La IA citó una fila que no existe en el Excel")


def main():
    parser = argparse.ArgumentParser(description="Interpretar presupuesto Excel con IA y skill")
    parser.add_argument("archivo")
    parser.add_argument("--salida", help="Archivo JSON de salida")
    args = parser.parse_args()
    datos = interpretar(args.archivo)
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
        print(f"Guardados {len(datos['registros'])} registros; {len(datos['dudas'])} dudas")
    else:
        print(texto)


if __name__ == "__main__":
    main()
