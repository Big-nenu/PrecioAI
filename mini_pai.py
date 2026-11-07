"""Flujo local reanudable: Excel -> candidatos -> preguntas -> Excel y Markdown."""
import argparse
from contextlib import closing, nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import time

from buscar_conceptos import conectar_sql
from mini_pai_interpretar import interpretar
from mini_pai_tabla import interpretar_tabla
from mini_pai_buscar import buscar_con_indice
from mini_pai_seleccionar import seleccionar
from mini_pai_confirmar import confirmar, consultar_candidato, preparar, seleccion_validada
from mini_pai_revision import indice, resolver, reporte
from mini_pai_exportar import crear_excel
from proveedor_ia import cargar_env

ROOT = Path(__file__).resolve().parent


def sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def codigo_actual():
    archivos = ['mini_pai.py', 'mini_pai_interpretar.py', 'mini_pai_tabla.py', 'mini_pai_buscar.py',
        'mini_pai_seleccionar.py', 'mini_pai_confirmar.py', 'mini_pai_revision.py', 'mini_pai_exportar.py',
        'proveedor_ia.py', 'indice_local.py', 'laboratorio_coincidencias.py', 'buscar_conceptos.py',
        'ranking_conceptos.py', 'numeros_tecnicos.py', 'skills/analizar-presupuesto/SKILL.md']
    return hashlib.sha256(json.dumps({p: sha(ROOT / p) for p in archivos}, sort_keys=True).encode()).hexdigest()


def escribir(ruta, contenido):
    temporal = ruta.with_name(ruta.name + '.tmp')
    temporal.write_text(contenido, encoding='utf-8')
    temporal.replace(ruta)


def guardar(estado, sesion):
    escribir(sesion / 'sesion.json', json.dumps(estado, ensure_ascii=False, indent=2, allow_nan=False))


def registrar(estado, sesion, nombre):
    estado['archivos'][nombre] = sha(sesion / nombre)


def verificar(estado, sesion):
    if estado.get('version') != 1 or estado['codigo'] != codigo_actual():
        raise ValueError('La versión del flujo cambió; usar el mismo código o una sesión nueva')
    if sha(estado['entrada']) != estado['entrada_sha256']:
        raise ValueError('El Excel original cambió; no se reutilizan sus resultados')
    for nombre, digest in estado['archivos'].items():
        if Path(nombre).name != nombre or sha(sesion / nombre) != digest:
            raise ValueError('Archivo de sesión modificado o inválido: ' + nombre)
    for etapa in estado['etapas']:
        if etapa not in ('interpretacion', 'candidatos', 'evaluacion') or etapa + '.json' not in estado['archivos']:
            raise ValueError('Etapa de sesión sin archivo verificado')
    if any(r['resultado'] not in estado['archivos'] for r in estado['resoluciones']):
        raise ValueError('Resolución sin archivo verificado')


def pendientes(datos):
    registros, busquedas = indice(datos)
    faltan = []
    for clave, r in registros.items():
        try:
            resolver(r, busquedas.get(clave))
        except ValueError:
            faltan.append(clave)
    return faltan


def muestra(datos, limite):
    """Acota búsqueda y evaluación, conservando íntegro el checkpoint de extracción."""
    if limite is None:
        return datos
    if type(limite) is not int or limite < 1:
        raise ValueError('El límite de conceptos debe ser un entero positivo')
    conceptos = [i for i,r in enumerate(datos['registros']) if r['tipo']=='concepto']
    salida = deepcopy(datos)
    if len(conceptos) > limite:
        salida['registros'] = salida['registros'][:conceptos[limite-1]+1]
        salida['alcance']['parcial'] = True
    salida['alcance'].update(limite_conceptos=limite,conceptos_interpretados=len(conceptos),
                            conceptos_procesados=min(limite,len(conceptos)))
    return salida


def ejecutar(args):
    sesion = Path(args.sesion).resolve()
    sesion.mkdir(parents=True, exist_ok=True)
    # Un bloqueo abandonado se retira manualmente solo tras comprobar que el proceso terminó.
    bloqueo = sesion / 'sesion.lock'
    with bloqueo.open('x', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    try:
        return continuar(args, sesion)
    finally:
        bloqueo.unlink()


def continuar(args, sesion):
    ruta_estado = sesion / 'sesion.json'
    if ruta_estado.exists():
        estado = json.loads(ruta_estado.read_text(encoding='utf-8'))
        verificar(estado, sesion)
        if args.archivo and str(Path(args.archivo).resolve()) != estado['entrada']:
            raise ValueError('La sesión corresponde a otro Excel')
        for campo in ('indice', 'env', 'hoja', 'fila_inicial', 'fila_final', 'por_tabla', 'limite_conceptos'):
            valor = getattr(args, campo, None)
            if valor is not None:
                if campo in ('indice', 'env'):
                    valor = str(Path(valor).resolve())
                if valor != estado['parametros'].get(campo):
                    raise ValueError('No cambiar parámetros de una sesión existente: ' + campo)
    else:
        if any(p.name != 'sesion.lock' for p in sesion.iterdir()):
            raise ValueError('La carpeta no es una sesión Mini-PAI; usar una carpeta nueva')
        if not args.archivo or not args.indice:
            raise ValueError('Una sesión nueva requiere Excel e --indice archivo.sqlite')
        parametros = dict(indice=str(Path(args.indice).resolve()),
            env=str(Path(args.env).resolve()) if args.env else str(ROOT / '.env'),
            hoja=args.hoja, fila_inicial=args.fila_inicial or 1, fila_final=args.fila_final,
            por_tabla=bool(args.por_tabla),limite_conceptos=getattr(args,'limite_conceptos',None))
        if parametros['por_tabla'] and (args.hoja or args.fila_inicial is not None or args.fila_final is not None):
            raise ValueError('--por-tabla no admite hoja ni rangos')
        entrada = str(Path(args.archivo).resolve())
        estado = dict(version=1, entrada=entrada, entrada_sha256=sha(entrada), codigo=codigo_actual(),
            parametros=parametros, archivos={}, etapas={}, resoluciones=[], estado='procesando')
        guardar(estado, sesion)
    if estado['estado'] == 'terminado':
        print('Sesión terminada: ' + str(sesion / 'presupuesto.xlsx'))
        return estado
    parametros = estado['parametros']
    cargar_env(parametros['env'])

    def etapa(nombre, funcion):
        if nombre not in estado['etapas']:
            archivo = sesion / (nombre + '.json')
            if archivo.exists():
                raise ValueError('Resultado sin registro de etapa; conservarlo y usar otra sesión: ' + archivo.name)
            print('Etapa: ' + nombre, flush=True)
            inicio = time.monotonic()
            datos = funcion()
            verificar(estado, sesion)
            escribir(archivo, json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False))
            registrar(estado, sesion, archivo.name)
            estado['etapas'][nombre] = dict(segundos=round(time.monotonic() - inicio, 3))
            guardar(estado, sesion)
        return json.loads((sesion / (nombre + '.json')).read_text(encoding='utf-8'))

    interpretacion = etapa('interpretacion', lambda: interpretar_tabla(estado['entrada']) if parametros['por_tabla']
        else interpretar(estado['entrada'], hoja=parametros['hoja'], fila_inicial=parametros['fila_inicial'],
                         fila_final=parametros['fila_final']))
    interpretacion = muestra(interpretacion, parametros.get('limite_conceptos'))

    def recuperar():
        with closing(conectar_sql(parametros['env'])) as conexion:
            return buscar_con_indice(interpretacion, conexion, parametros['indice'])

    candidatos = etapa('candidatos', recuperar)

    def evaluar():
        with closing(conectar_sql(parametros['env'])) as conexion:
            return seleccionar(candidatos, conexion)

    evaluacion = etapa('evaluacion', evaluar)
    datos = (json.loads((sesion / estado['resoluciones'][-1]['resultado']).read_text(encoding='utf-8'))
             if estado['resoluciones'] else evaluacion)
    decisiones = None
    if args.conservar_originales:
        # La elección global es explícita; las propuestas y decisiones previas quedan archivadas.
        decisiones = [dict(hoja=r['hoja'], fila=r['fila'], IdCodigo=None, revisor=args.revisor,
            motivo='Conservar todos los originales por elección explícita del usuario.')
            for r in candidatos['registros'] if r['tipo'] == 'concepto']
    elif args.decisiones:
        decisiones = json.loads(Path(args.decisiones).read_text(encoding='utf-8'))
    if decisiones is not None:
        huella = hashlib.sha256(json.dumps(decisiones, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not any(r['decisiones_sha256'] == huella for r in estado['resoluciones']):
            inicio = time.monotonic()
            base = candidatos if args.conservar_originales else datos
            preparados = preparar(base, decisiones)
            with (closing(conectar_sql(parametros['env'])) if any(c is not None for _, _, c in preparados)
                  else nullcontext(None)) as conexion:
                datos = confirmar(base, decisiones, conexion)
            numero = len(estado['resoluciones']) + 1
            decision_nombre, resultado = f'decisiones-{numero:03}.json', f'resolucion-{numero:03}.json'
            if any((sesion / n).exists() for n in (decision_nombre, resultado)):
                raise ValueError('Resolución sin registro; conservar archivos y usar otra sesión')
            for nombre, valor in ((decision_nombre, decisiones), (resultado, datos)):
                escribir(sesion / nombre, json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False))
                registrar(estado, sesion, nombre)
            estado['resoluciones'].append(dict(decisiones_sha256=huella, resultado=resultado,
                segundos=round(time.monotonic() - inicio, 3)))
            guardar(estado, sesion)
    faltan = pendientes(datos)
    estado['pendientes'] = len(faltan)
    if faltan:
        nombre = f'preguntas-{len(estado["resoluciones"]):03}.md'
        if nombre not in estado['archivos']:
            if (sesion / nombre).exists():
                raise ValueError('No se sobrescriben preguntas ajenas a la sesión')
            escribir(sesion / nombre, reporte(datos))
            registrar(estado, sesion, nombre)
        estado.update(estado='esperando_decisiones', preguntas=nombre)
        guardar(estado, sesion)
        print(f'{len(faltan)} pendientes. Opciones: {sesion / nombre}')
        print('Continuar con --sesion y --decisiones archivo.json; o --conservar-originales --revisor nombre.')
        return estado
    verificar(estado, sesion)
    registros, busquedas = indice(datos)
    selecciones = [seleccion_validada(r, busquedas.get(clave, {})) for clave, r in registros.items()]
    if any(selecciones):
        with closing(conectar_sql(parametros['env'])) as conexion:
            for seleccion in selecciones:
                if seleccion and consultar_candidato(conexion, seleccion['IdCodigo']) != seleccion:
                    raise ValueError('La matriz cambió en SQL; revisar en una sesión nueva')
    informe = reporte(datos, final=True)
    if any((sesion / n).exists() for n in ('presupuesto.xlsx', 'presupuesto.md')):
        raise ValueError('Entrega sin registro final; conservarla y usar otra sesión')
    inicio = time.monotonic()
    libro = crear_excel(datos, final=True)
    temporal = sesion / 'presupuesto.xlsx.tmp'
    try:
        with temporal.open('wb') as f:
            libro.save(f)
        temporal.replace(sesion / 'presupuesto.xlsx')
    finally:
        libro.close()
    escribir(sesion / 'presupuesto.md', informe)
    for nombre in ('presupuesto.xlsx', 'presupuesto.md'):
        registrar(estado, sesion, nombre)
    estado.update(estado='terminado', pendientes=0, segundos_exportacion=round(time.monotonic() - inicio, 3))
    guardar(estado, sesion)
    print('Excel y reporte: ' + str(sesion / 'presupuesto.xlsx'))
    return estado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', nargs='?')
    parser.add_argument('--sesion', required=True, help='Carpeta nueva al iniciar; misma carpeta al continuar')
    parser.add_argument('--indice')
    parser.add_argument('--env')
    parser.add_argument('--por-tabla', action='store_true', default=None)
    parser.add_argument('--hoja')
    parser.add_argument('--fila-inicial', type=int)
    parser.add_argument('--fila-final', type=int)
    parser.add_argument('--limite-conceptos', type=int, help='Interpreta el original completo; limita solo búsqueda/evaluación')
    decision = parser.add_mutually_exclusive_group()
    decision.add_argument('--decisiones', help='JSON existente con elecciones reales de usuario')
    decision.add_argument('--conservar-originales', action='store_true', help='Conservar TODOS, incluso propuestas IA')
    parser.add_argument('--revisor')
    args = parser.parse_args()
    if args.limite_conceptos is not None and args.limite_conceptos < 1:
        parser.error('--limite-conceptos debe ser positivo')
    if args.conservar_originales and (not args.revisor or not args.revisor.strip()):
        parser.error('--conservar-originales requiere --revisor')
    try:
        ejecutar(args)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, 'Mini-PAI: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
