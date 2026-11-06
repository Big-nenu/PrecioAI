"""Conecta el JSON interpretado con candidatos SQL revisables, sin asociar matrices."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

from buscar_conceptos import buscar, conectar_sql
from mini_pai_interpretar import validar_jerarquia
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
    validar_jerarquia(presupuesto["registros"])


def buscar_presupuesto(presupuesto, conexion, *, terminos=None):
    """Preserva la entrada y añade búsquedas separadas. Ningún candidato se confirma."""
    terminos = {} if terminos is None else terminos
    validar_entrada(presupuesto, terminos)
    cursor = conexion.cursor()
    cursor.execute("SELECT IdUnidad, Unidad FROM dbo.PuUnidades")
    unidades = dict(cursor.fetchall())
    salida = deepcopy(presupuesto)
    busquedas, cache = [], {}
    for registro in presupuesto["registros"]:
        if registro["tipo"] != "concepto":
            continue
        identificador = f"{registro['hoja']}:{registro['fila']}"
        consulta = terminos.get(identificador, proponer_terminos(registro["descripcion"]))
        resultado = dict(hoja=registro["hoja"], fila=registro["fila"], terminos=consulta,
                         origen_terminos="indicados" if identificador in terminos else "propuesta_reglas",
                         intentos=[], candidatos=[], requiere_revision=True, seleccion=None,
                         observaciones_origen=[f"Falta {campo} en el JSON interpretado; revisar el Excel"
                             for campo in ("descripcion", "unidad", "cantidad")
                             if registro[campo] is None or not str(registro[campo]).strip()])
        if not consulta:
            resultado["estado"] = "requiere_terminos"
            busquedas.append(resultado)
            continue
        consultas = [consulta]
        # Si la propuesta compuesta no recupera nada, probar su primer término.
        # Los términos indicados por el usuario nunca se amplían automáticamente.
        if identificador not in terminos and len(consulta.split()) > 1:
            consultas.append(consulta.split()[0])
        recuperados = []
        for texto in consultas:
            if texto not in cache:
                cache[texto] = buscar(conexion, texto, 50, tipo=4)
            recuperados = cache[texto]
            resultado["intentos"].append(dict(terminos=texto, recuperados=len(recuperados)))
            if recuperados:
                break
        resultado["recuperados"] = len(recuperados)
        resultado["limite_sql_alcanzado"] = len(recuperados) == 50
        # IdCodigo identifica los conceptos; no fusionar por código o descripción.
        unicos = {}
        for candidato in recuperados:
            identificador_sql = candidato.get("IdCodigo")
            if identificador_sql is None:
                raise ValueError("ConstruBase devolvió un candidato sin IdCodigo")
            unicos.setdefault(identificador_sql, candidato)
        ordenados = ordenar_candidatos(registro["descripcion"] or consulta, list(unicos.values()))
        principal = proponer_terminos(registro["descripcion"] or consulta).split()[:1]
        for candidato in ordenados:
            inicio = proponer_terminos(candidato.get("DescripcionLarga") or candidato.get("Descripcion")).split()[:1]
            candidato["coincide_inicio_actividad"] = bool(principal and inicio == principal)
            if candidato["coincide_inicio_actividad"]:
                candidato["razones"].append("Coincide el primer término de actividad: " + principal[0])
        # Conserva el ranking existente dentro de cada grupo. Evita que una obra
        # distinta suba solo por mencionar la actividad entre sus inclusiones.
        ordenados.sort(key=lambda c: not c["coincide_inicio_actividad"])
        for candidato in ordenados[:5]:
            unidad = unidades.get(candidato.get("IdUnidad"))
            a, b = normalizar(registro["unidad"] or "").strip(), normalizar(unidad or "").strip()
            comparacion = "sin_datos" if not a or not b else "igual" if a == b else "diferente"
            candidato["unidad_catalogo"] = unidad
            candidato["comparacion_unidad"] = comparacion
            candidato["requiere_revision"] = True
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
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presupuesto", help="JSON generado por mini_pai_interpretar")
    parser.add_argument("--salida", required=True)
    parser.add_argument("--env", default=".env", help="Configuración SQL local")
    parser.add_argument("--terminos", help="JSON opcional: mapa hoja:fila a términos de búsqueda")
    args = parser.parse_args()
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
    presupuesto = json.loads(Path(args.presupuesto).read_text(encoding="utf-8"))
    terminos = json.loads(Path(args.terminos).read_text(encoding="utf-8")) if args.terminos else {}
    validar_entrada(presupuesto, terminos)
    with conectar_sql(ruta_env) as conexion:
        datos = buscar_presupuesto(presupuesto, conexion, terminos=terminos)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"{len(datos['busquedas_construbase'])} conceptos consultados; candidatos pendientes de revisión")


if __name__ == "__main__":
    main()
