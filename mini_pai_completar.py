"""Completa campos omitidos con celdas explícitas, conservando trazabilidad."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from mini_pai_interpretar import inspeccionar_excel, validar


def completar(datos, inspeccion, cambios, sha256):
    validar(datos, inspeccion)
    if 'busquedas_construbase' in datos:
        raise ValueError('Completa la interpretación antes de buscar; vuelve a consultar después')
    if not isinstance(cambios, list) or not cambios:
        raise ValueError('Se requiere una lista de campos omitidos y sus celdas')
    salida = deepcopy(datos)
    registros = {(r['hoja'], r['fila']): r for r in salida['registros']}
    celdas = {(h['nombre'], c): v for h in inspeccion['hojas'] for f in h['filas'] for c, v in f['celdas'].items()}
    vistos, auditoria = set(), []
    for cambio in cambios:
        if not isinstance(cambio, dict) or set(cambio) != {'hoja', 'fila', 'campo', 'celdas'}:
            raise ValueError('Corrección inválida')
        hoja, fila, campo, refs = (cambio[k] for k in ('hoja', 'fila', 'campo', 'celdas'))
        if not isinstance(hoja, str) or type(fila) is not int or campo not in ('clave', 'descripcion', 'unidad', 'cantidad'):
            raise ValueError('Identidad o campo inválido')
        registro = registros.get((hoja, fila))
        if registro is None or registro['tipo'] != 'concepto':
            raise ValueError('La corrección debe referir a un concepto existente')
        if (hoja, fila, campo) in vistos or registro[campo] is not None or registro['evidencia'][campo] != []:
            raise ValueError('Solo se completan campos omitidos, una vez por campo')
        vistos.add((hoja, fila, campo))
        if not isinstance(refs, list) or not refs or any(not isinstance(c, str) for c in refs):
            raise ValueError('Indica celdas de evidencia')
        try:
            valor = ' '.join(celdas[hoja, c] for c in refs)
        except KeyError as exc:
            raise ValueError('La celda no existe o está vacía') from exc
        registro[campo], registro['evidencia'][campo] = valor, list(refs)
        auditoria.append(dict(cambio, anterior=None, valor=valor, origen='revision_explicita', excel_sha256=sha256))
    validar(salida, inspeccion)
    salida.setdefault('completados', []).extend(auditoria)
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('presupuesto')
    parser.add_argument('excel')
    parser.add_argument('cambios', help='JSON con hoja, fila, campo y celdas por cambio')
    parser.add_argument('--salida', required=True)
    args = parser.parse_args()
    destino = Path(args.salida)
    for ruta in (args.presupuesto, args.excel, args.cambios):
        origen = Path(ruta)
        if origen.resolve() == destino.resolve() or destino.exists() and origen.samefile(destino):
            parser.error('La salida debe ser distinta de las entradas')
    excel = Path(args.excel)
    huella = hashlib.sha256(excel.read_bytes()).hexdigest()
    inspeccion = inspeccionar_excel(excel)
    if huella != hashlib.sha256(excel.read_bytes()).hexdigest():
        raise ValueError('El Excel cambió durante la inspección')
    datos = json.loads(Path(args.presupuesto).read_text(encoding='utf-8'))
    cambios = json.loads(Path(args.cambios).read_text(encoding='utf-8'))
    salida = completar(datos, inspeccion, cambios, huella)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(f'{len(cambios)} campos completados con evidencia; ejecutar nuevamente la búsqueda')


if __name__ == '__main__':
    main()
