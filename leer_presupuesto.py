"""Lector inicial del catálogo de conceptos Excel. No modifica el archivo."""
import argparse
import json
import re
from decimal import Decimal, InvalidOperation


def normalizar_cantidad(valor):
    if valor is None or isinstance(valor, bool):
        return None
    texto = str(valor).strip().replace(' ', '')
    if not re.fullmatch(r'-?[0-9,.]+', texto):
        return None
    if ',' in texto and '.' in texto:
        texto = texto.replace(',', '')
    elif ',' in texto:
        partes = texto.split(',')
        texto = texto.replace(',', '') if len(partes[-1]) == 3 else texto.replace(',', '.')
    try:
        return str(Decimal(texto))
    except InvalidOperation:
        return None


def extraer_filas(filas):
    resultado = []
    partida = None
    for n, fila in enumerate(filas, 1):
        c = (list(fila) + [None] * 5)[:5]
        clave, descripcion = str(c[0] or '').strip(), str(c[1] or '').strip()
        unidad = str(c[3] or '').strip()
        cantidad = normalizar_cantidad(c[4])
        if not clave or not descripcion or clave.upper() == 'CLAVE':
            continue
        if unidad and cantidad is not None:
            resultado.append(dict(tipo='concepto', fila=n, clave=clave, descripcion=descripcion,
                                  unidad=unidad, cantidad=cantidad, partida=partida))
        elif not unidad and cantidad is None and re.fullmatch(r'[A-Z](?:\.\d+\([^)]*\))?', clave, re.I):
            partida = dict(clave=clave, descripcion=descripcion)
            resultado.append(dict(tipo='partida', fila=n, **partida))
    return resultado


def leer(ruta):
    from openpyxl import load_workbook
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        if 'Conceptos' not in libro.sheetnames:
            raise ValueError("El archivo no contiene una hoja llamada 'Conceptos'")
        hoja = libro['Conceptos']
        return extraer_filas(hoja.iter_rows(min_col=1, max_col=5, values_only=True))
    finally:
        libro.close()

def main():
    p = argparse.ArgumentParser(description='Extraer conceptos y partidas de Excel, sin modificarlo')
    p.add_argument('archivo')
    p.add_argument('--salida', help='JSON de salida (opcional)')
    args = p.parse_args()
    datos = leer(args.archivo)
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    if args.salida:
        from pathlib import Path
        Path(args.salida).write_text(texto, encoding='utf-8')
        print(f"{sum(d['tipo']=='concepto' for d in datos)} conceptos; {sum(d['tipo']=='partida' for d in datos)} partidas")
    else:
        print(texto)


if __name__ == '__main__':
    main()
