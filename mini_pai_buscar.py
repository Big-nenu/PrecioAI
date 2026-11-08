"""Conecta el JSON interpretado con candidatos SQL revisables, sin asociar matrices."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import time

from buscar_conceptos import buscar, conectar_sql
from mini_pai_interpretar import validar_jerarquia, contextos_por_concepto, descripcion_tecnica
from ranking_conceptos import normalizar, ordenar_candidatos


VACIAS = {"de", "del", "la", "las", "el", "los", "con", "sin", "por", "para", "una", "uno", "unos",
          "unas", "en", "que", "cualquier", "medio", "medios", "elemento", "elementos",
          "suministro", "colocacion", "instalacion", "incluye"}


def proponer_terminos(descripcion):
    """Propuesta sencilla y visible; no pretende interpretar equivalencia técnica."""
    principal = re.split(r"\bincluye\b", normalizar(descripcion or ""), maxsplit=1)[0]
    palabras = list(dict.fromkeys(p for p in re.findall(r"[a-z]{3,}", principal) if p not in VACIAS))
    return " ".join(palabras[:2])


def validar_entrada(presupuesto, terminos):
    if (not isinstance(presupuesto, dict) or not isinstance(presupuesto.get("registros"), list)
            or not isinstance(terminos, dict)):
        raise ValueError("Se requiere el objeto JSON de mini_pai_interpretar y un mapa de términos")
    claves, conceptos = set(), set()
    requeridos = {"tipo", "hoja", "fila", "clave", "descripcion", "unidad", "cantidad", "partida", "subpartida"}
    for registro in presupuesto["registros"]:
        if (not isinstance(registro, dict) or not requeridos.issubset(registro)
                or registro["tipo"] not in ("partida", "subpartida", "concepto")
                or not isinstance(registro["hoja"], str) or not registro["hoja"]
                or type(registro["fila"]) is not int or registro["fila"] < 1
                or any(registro[c] is not None and not isinstance(registro[c], str)
                       for c in ("descripcion", "unidad"))):
            raise ValueError("Registro de presupuesto inválido o incompleto")
        clave = f"{registro['hoja']}:{registro['fila']}"
        if clave in claves:
            raise ValueError("Hoja/fila duplicada en el presupuesto")
        claves.add(clave)
        if registro["tipo"] == "concepto":
            conceptos.add(clave)
    if any(not isinstance(k, str) or k not in conceptos or not isinstance(v, str) or not v.strip()
           for k, v in terminos.items()):
        raise ValueError("Los términos deben referir a conceptos existentes mediante hoja:fila")
    contextos=contextos_por_concepto(presupuesto['registros'])
    for r in presupuesto['registros']:
        if r.get('contexto_descripcion',[]) != contextos.get((r['hoja'],r['fila']),[]):
            raise ValueError('Contexto de descripción alterado o incompleto')


def buscar_presupuesto(presupuesto, conexion, *, terminos=None, ampliar=False, consultas=None):
    """Preserva la entrada y añade búsquedas separadas. Ningún candidato se confirma."""
    terminos = {} if terminos is None else terminos
    validar_entrada(presupuesto, terminos)
    consultas = {} if consultas is None else consultas
    claves = {f"{r['hoja']}:{r['fila']}" for r in presupuesto['registros'] if r['tipo']=='concepto'}
    if (not isinstance(consultas, dict) or terminos and consultas
            or any(k not in claves or not isinstance(v, list) or len(v)>3
                   or any(not isinstance(t, str) or not t.strip() or len(t)>120 for t in v)
                   for k,v in consultas.items())):
        raise ValueError("Consultas inválidas o combinadas con términos explícitos")
    cursor = conexion.cursor()
    cursor.execute("SELECT IdUnidad, Unidad FROM dbo.PuUnidades")
    unidades = dict(cursor.fetchall())
    salida = deepcopy(presupuesto)
    busquedas, cache = [], {}
    for registro in presupuesto["registros"]:
        if registro["tipo"] != "concepto":
            continue
        identificador = f"{registro['hoja']}:{registro['fila']}"
        consulta = terminos.get(identificador, proponer_terminos(descripcion_tecnica(registro)))
        plan = consultas.get(identificador)
        if plan is not None:
            consulta = plan[0] if plan else ""
        resultado = dict(hoja=registro["hoja"], fila=registro["fila"], terminos=consulta,
                         origen_terminos="indicados" if identificador in terminos else "propuesta_reglas",
                         intentos=[], candidatos=[], requiere_revision=True, seleccion=None,
                         observaciones_origen=[f"Falta {campo} en el JSON interpretado; revisar el Excel"
                             for campo in ("descripcion", "unidad", "cantidad")
                             if registro[campo] is None or not str(registro[campo]).strip()])
        if plan is not None:
            resultado["origen_terminos"] = "plan_ia"
        if not consulta:
            resultado["estado"] = "requiere_terminos"
            busquedas.append(resultado)
            continue
        intentos = list(plan) if plan is not None else [consulta]
        # Si la propuesta compuesta no recupera nada, probar su primer término.
        # Los términos indicados por el usuario nunca se amplían automáticamente.
        if plan is None and identificador not in terminos and len(consulta.split()) > 1:
            intentos.append(consulta.split()[0])
        recuperados = []
        prioridad = {}
        tope_alcanzado = False
        for posicion,texto in enumerate(intentos):
            if texto not in cache:
                cache[texto] = buscar(conexion, texto, 50, tipo=4)
                if ampliar:
                    while cache[texto] and len(cache[texto]) % 50 == 0 and len(cache[texto]) < 500:
                        pagina = buscar(conexion, texto, 50, tipo=4, desplazamiento=len(cache[texto]))
                        cache[texto] += pagina
                        if len(pagina) < 50:
                            break
            pagina = cache[texto]
            resultado["intentos"].append(dict(terminos=texto, recuperados=len(pagina)))
            if plan is not None:
                recuperados.extend(pagina)
                for c in pagina:
                    prioridad.setdefault(c["IdCodigo"],posicion)
            else:
                recuperados = pagina
            tope_alcanzado |= len(pagina)==(500 if ampliar else 50)
            if recuperados and plan is None:
                break
        resultado["recuperados"] = len(recuperados)
        resultado["limite_sql_alcanzado"] = tope_alcanzado
        if ampliar:
            resultado["limite_recuperacion"] = 500
        # IdCodigo identifica los conceptos; no fusionar por código o descripción.
        unicos = {}
        for candidato in recuperados:
            identificador_sql = candidato.get("IdCodigo")
            if identificador_sql is None:
                raise ValueError("ConstruBase devolvió un candidato sin IdCodigo")
            unicos.setdefault(identificador_sql, candidato)
        ordenados = ordenar_candidatos(descripcion_tecnica(registro) or consulta, list(unicos.values()))
        principal = proponer_terminos(descripcion_tecnica(registro) or consulta).split()[:1]
        for candidato in ordenados:
            inicio = proponer_terminos(candidato.get("DescripcionLarga") or candidato.get("Descripcion")).split()[:1]
            candidato["coincide_inicio_actividad"] = bool(principal and inicio == principal)
            if candidato["coincide_inicio_actividad"]:
                candidato["razones"].append("Coincide el primer término de actividad: " + principal[0])
        # Conserva el ranking existente dentro de cada grupo. Evita que una obra
        # distinta suba solo por mencionar la actividad entre sus inclusiones.
        ordenados.sort(key=lambda c: not c["coincide_inicio_actividad"])
        if plan is not None:
            # La IA ordena consultas específicas primero; las amplias recuperan
            # alternativas sin reemplazar por relevancia léxica los hallazgos específicos.
            ordenados.sort(key=lambda c: prioridad[c["IdCodigo"]])
            resultado["recuperados_unicos"] = len(unicos)
        if ampliar:
            # Recuperación: prioriza unidad coincidente sin afirmar equivalencia.
            unidad_cliente = normalizar(registro["unidad"] or "").strip()
            ordenados.sort(key=lambda c: not (unidad_cliente and unidad_cliente ==
                normalizar(unidades.get(c.get("IdUnidad")) or "").strip()))
        for candidato in ordenados[:5]:
            unidad = unidades.get(candidato.get("IdUnidad"))
            a, b = normalizar(registro["unidad"] or "").strip(), normalizar(unidad or "").strip()
            comparacion = "sin_datos" if not a or not b else "igual" if a == b else "diferente"
            candidato["unidad_catalogo"] = unidad
            candidato["comparacion_unidad"] = comparacion
            candidato["requiere_revision"] = True
            if plan is not None:
                candidato["consulta_origen"] = intentos[prioridad[candidato["IdCodigo"]]]
            candidato["advertencias"].append("Equivalencia técnica pendiente de revisión humana")
            if comparacion == "diferente":
                candidato["advertencias"].append("Unidad distinta; no se ha comprobado conversión o compatibilidad")
            elif comparacion == "sin_datos":
                candidato["advertencias"].append("No se pudo comparar la unidad")
            resultado["candidatos"].append(candidato)
        resultado["estado"] = "candidatos_por_revisar" if resultado["candidatos"] else "sin_candidatos_en_busqueda"
        busquedas.append(resultado)
    salida["busquedas_construbase"] = busquedas
    salida["aviso_busqueda"] = ("Búsqueda inicial por términos revisables; prioriza coincidencia del primer término de "
        "actividad y después el ranking existente. Hasta 50 resultados SQL por intento y "
        "hasta 5 candidatos mostrados por concepto. No equivale a buscar todo el catálogo por relevancia ni "
        "a confirmar equivalencias. Los conceptos originales permanecen intactos. No se recuperan matrices ni costos.")
    if ampliar:
        salida["aviso_busqueda"] = ("Recuperación ampliada: páginas de 50 hasta 500 por intento; "
            "prioriza unidad coincidente y ranking existente, muestra hasta cinco. "
            "La unidad y el ranking no prueban equivalencia técnica. No se buscan matrices ni costos.")
    return salida


def buscar_con_indice(presupuesto, conexion, ruta, *, base="http://127.0.0.1:11434"):
    """Recupera vecinos del catálogo vigente; conserva el contrato del selector."""
    import indice_local
    from laboratorio_coincidencias import (comparar_unidad, embeddings, entorno_modelos,
                                           post, prefijos, similitudes)
    validar_entrada(presupuesto, {})
    if presupuesto.get('busquedas_construbase'):
        raise ValueError('Usar la interpretación sin búsquedas previas; no reemplazar decisiones')
    modelo = 'embeddinggemma-2:270m'
    entorno = entorno_modelos(base, [modelo])
    disponibles = entorno.get('modelos', [])
    if not disponibles:
        raise ValueError('EmbeddingGemma 270m no disponible en Ollama: ' + entorno.get('error', modelo))
    digest = disponibles[0]['digest']
    inicio = time.perf_counter()
    cursor = conexion.cursor()
    cursor.execute("""SELECT c.IdCodigo,c.Codigo,
COALESCE(NULLIF(c.DescripcionLarga,N''),c.Descripcion),c.IdUnidad,c.IdTipo,u.Unidad
FROM dbo.PuCatalogo c LEFT JOIN dbo.PuUnidades u ON u.IdUnidad=c.IdUnidad
WHERE c.IdTipo=4 ORDER BY c.IdCodigo""")
    catalogo = [dict(id=str(r[0]), codigo=r[1], descripcion=r[2], IdUnidad=r[3],
                     IdTipo=r[4], unidad=r[5]) for r in cursor.fetchall()]
    tiempos = dict(segundos_sql=time.perf_counter() - inicio)
    identidad = indice_local.firma(catalogo, modelo, digest)
    salida = deepcopy(presupuesto)
    conceptos = [r for r in salida['registros'] if r['tipo'] == 'concepto']
    validos = [r for r in conceptos if descripcion_tecnica(r).strip()]
    try:
        inicio = time.perf_counter()
        construccion = indice_local.construir(ruta, catalogo, modelo, digest, base=base)
        documentos, vectores = indice_local.cargar(ruta, identidad)
        tiempos['segundos_indice'] = time.perf_counter() - inicio
        inicio = time.perf_counter()
        resultados = {}
        if validos:
            qp, _ = prefijos(modelo)
            preguntas = embeddings(base, modelo, [qp + descripcion_tecnica(r) for r in validos], lote=32)
            for r, puntos in zip(validos, similitudes(vectores, preguntas)):
                orden = sorted(range(len(documentos)), key=lambda j: (
                    comparar_unidad(r['unidad'], documentos[j]['unidad']) != 'igual',
                    -float(puntos[j]), documentos[j]['id']))
                candidatos = []
                for j in orden[:5]:
                    d = documentos[j]
                    comparacion = comparar_unidad(r['unidad'], d['unidad'])
                    candidatos.append(dict(IdCodigo=int(d['id']), Codigo=d['codigo'],
                        DescripcionLarga=d['descripcion'], IdUnidad=d['IdUnidad'], IdTipo=d['IdTipo'],
                        unidad_catalogo=d['unidad'], comparacion_unidad=comparacion,
                        similitud_coseno=float(puntos[j]), requiere_revision=True,
                        advertencias=['Vecino semántico, no equivalencia confirmada'] +
                            ([] if comparacion == 'igual' else ['Unidad distinta o no acreditada; no se convierten cantidades'])))
                resultados[r['hoja'], r['fila']] = candidatos
        salida['busquedas_construbase'] = [dict(hoja=r['hoja'], fila=r['fila'],
            candidatos=resultados.get((r['hoja'], r['fila']), []), seleccion=None, requiere_revision=True,
            origen_terminos='indice_semantico', recuperados=len(catalogo),
            estado='candidatos_por_revisar' if (r['hoja'], r['fila']) in resultados else 'requiere_descripcion')
            for r in conceptos]
        tiempos['segundos_consultas'] = time.perf_counter() - inicio
        salida['recuperacion_indice'] = dict(modelo=modelo, digest=digest, identidad=identidad,
            indice=str(Path(ruta).resolve()), construccion=construccion, **tiempos)
        salida['aviso_busqueda'] = ('Índice del catálogo SQL vigente, coseno y unidad coincidente primero; '
            'hasta cinco vecinos por concepto. No hay umbral de ausencia calibrado: candidatos no implican '
            'equivalencia ni autorizan selecciones. Sin descripción queda pendiente, no sin coincidencias.')
    finally:
        # Liberar VRAM antes de llamar al evaluador principal.
        post(base, '/api/embed', dict(model=modelo, input=[], keep_alive=0))
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presupuesto", help="JSON generado por mini_pai_interpretar")
    parser.add_argument("--salida", required=True)
    parser.add_argument("--env", default=".env", help="Configuración SQL local")
    parser.add_argument("--terminos", help="JSON opcional: mapa hoja:fila a términos de búsqueda")
    parser.add_argument("--ampliar", action="store_true", help="Recuperar hasta 500 por intento antes de ordenar")
    parser.add_argument("--indice", help="SQLite local de EmbeddingGemma 270m; usa catálogo SQL vigente en lectura")
    args = parser.parse_args()
    if args.indice and (args.terminos or args.ampliar):
        parser.error('--indice no se combina con --terminos ni --ampliar')
    destino = Path(args.salida)
    ruta_env = Path(args.env)
    if not ruta_env.is_absolute():
        ruta_env = Path(__file__).resolve().parent / ruta_env
    for entrada in (args.presupuesto, args.terminos, ruta_env):
        if entrada:
            origen = Path(entrada)
            if (origen.resolve() == destino.resolve()
                    or origen.exists() and destino.exists() and origen.samefile(destino)):
                parser.error("La salida debe ser distinta de los archivos de entrada/configuración")
    if args.indice:
        ruta_indice = Path(args.indice)
        if (destino.exists() or destino.is_symlink() or ruta_indice.suffix.lower() != '.sqlite'
                or any(ruta_indice.resolve() == Path(p).resolve()
                       for p in (args.presupuesto, ruta_env, destino))):
            parser.error('Usar salida nueva e índice .sqlite distinto de entradas, configuración y salida')
    presupuesto = json.loads(Path(args.presupuesto).read_text(encoding="utf-8"))
    terminos = json.loads(Path(args.terminos).read_text(encoding="utf-8")) if args.terminos else {}
    validar_entrada(presupuesto, terminos)
    with conectar_sql(ruta_env) as conexion:
        datos = (buscar_con_indice(presupuesto, conexion, args.indice) if args.indice else
                 buscar_presupuesto(presupuesto, conexion, terminos=terminos, ampliar=args.ampliar))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"{len(datos['busquedas_construbase'])} conceptos consultados; candidatos pendientes de revisión")


if __name__ == "__main__":
    main()
