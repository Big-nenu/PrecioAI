"""Registra decisiones humanas explícitas sobre candidatos verificados en SQL (solo lectura)."""
import argparse
from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path

from buscar_conceptos import conectar_sql
from mini_pai_buscar import validar_entrada
from ranking_conceptos import normalizar
from numeros_tecnicos import numeros
from mini_pai_interpretar import descripciones_cliente, descripcion_tecnica


CAMPOS_SQL = ("IdCodigo", "Codigo", "DescripcionLarga", "IdUnidad", "IdTipo", "unidad_catalogo")
ASPECTOS = ("materiales", "procedimiento", "dimensiones", "espesor", "resistencia", "alcance", "unidad")


def validar_evaluacion_ia(registro, busqueda, evaluacion):
    """Comprueba IDs, cobertura y citas; no es una prueba de corrección semántica."""
    if (not isinstance(evaluacion, dict) or set(evaluacion) != {"seleccion_id", "motivo", "candidatos", "comprobaciones"}
            or not isinstance(evaluacion["motivo"], str) or not evaluacion["motivo"].strip()
            or not isinstance(evaluacion["candidatos"], list) or not isinstance(evaluacion["comprobaciones"], list)):
        raise ValueError("Evaluación IA incompleta")
    fuentes = {c["IdCodigo"]: c for c in busqueda["candidatos"]}
    vistos = set()
    def cita(texto, fuente):
        return isinstance(texto, str) and " ".join(normalizar(texto).split()) in " ".join(normalizar(fuente or "").split())
    def cita_cliente(texto):
        return any(cita(texto,fuente) for fuente in descripciones_cliente(registro))
    for item in evaluacion["candidatos"]:
        if (not isinstance(item, dict) or set(item) != {"IdCodigo", "dictamen", "motivo", "cliente", "catalogo"}
                or type(item["IdCodigo"]) is not int or item["IdCodigo"] not in fuentes or item["IdCodigo"] in vistos
                or item["dictamen"] not in ("equivalente", "incompatible", "insuficiente")
                or not isinstance(item["motivo"], str) or not item["motivo"].strip()):
            raise ValueError("Dictamen con ID ajeno, duplicado o incompleto")
        vistos.add(item["IdCodigo"])
        c = fuentes[item["IdCodigo"]]
        if (not (cita_cliente(item["cliente"]) or cita(item["cliente"], registro["unidad"]))
                or not (cita(item["catalogo"], c["DescripcionLarga"]) or cita(item["catalogo"], c.get("unidad_catalogo")))):
            raise ValueError("Cita de evidencia ajena al texto original")
        if item["dictamen"] == "incompatible" and (not item["cliente"].strip() or not item["catalogo"].strip()):
            raise ValueError("Incompatibilidad sin evidencia de ambos textos")
    if vistos != set(fuentes):
        raise ValueError("La IA no evaluó todos los candidatos")
    elegido = evaluacion["seleccion_id"]
    if elegido is None:
        if any(i["dictamen"] == "equivalente" for i in evaluacion["candidatos"]):
            raise ValueError("Dictamen equivalente sin selección: si existe duda, clasificarlo insuficiente")
        if evaluacion["comprobaciones"]:
            raise ValueError("Sin selección no debe haber comprobaciones de un candidato elegido")
        return
    c = candidato_elegido(busqueda, elegido)
    if len(evaluacion["motivo"].strip()) < 30:
        raise ValueError("La selección necesita una justificación técnica, no una etiqueta")
    if not any(i["IdCodigo"] == elegido and i["dictamen"] == "equivalente" for i in evaluacion["candidatos"]):
        raise ValueError("Selección sin dictamen equivalente")
    validar_unidad(registro, c)
    aspectos = set()
    for p in evaluacion["comprobaciones"]:
        if (not isinstance(p, dict) or set(p) != {"aspecto", "estado", "cliente", "catalogo", "motivo"}
                or p["aspecto"] not in ASPECTOS or p["aspecto"] in aspectos
                or p["estado"] not in ("compatible", "no_aplica")
                or not isinstance(p["motivo"], str) or not p["motivo"].strip()):
            raise ValueError("Selección con diferencias, incertidumbre o comprobaciones incompletas")
        aspectos.add(p["aspecto"])
        if p["estado"] == "no_aplica":
            if p["aspecto"] in ("procedimiento", "alcance", "unidad"):
                raise ValueError("No_aplica no puede ocultar un requisito esencial")
            if not cita_cliente(p['cliente']) or not cita(p['catalogo'], c['DescripcionLarga']):
                raise ValueError('No_aplica contiene citas ajenas al concepto o candidato')
            t = normalizar(descripcion_tecnica(registro))
            if ((p["aspecto"] == "espesor" and "espesor" in t)
                    or (p["aspecto"] == "resistencia" and re.search(r"f\s*['’]?\s*c|kg\s*/\s*cm", t))
                    or (p["aspecto"] == "dimensiones" and re.search(r"\d\s*(?:cm|mm|m)\b", t))):
                raise ValueError("No_aplica oculta una especificación dimensional o de resistencia")
        else:
            origen = registro["unidad"] if p["aspecto"] == "unidad" else registro["descripcion"]
            destino = c["unidad_catalogo"] if p["aspecto"] == "unidad" else c["DescripcionLarga"]
            if (not isinstance(p["cliente"], str) or not p["cliente"].strip()
                    or not isinstance(p["catalogo"], str) or not p["catalogo"].strip()
                    or not (cita(p["cliente"], origen) if p["aspecto"] == "unidad" else cita_cliente(p["cliente"])) or not cita(p["catalogo"], destino)):
                raise ValueError("Comprobación sin citas verificables")
            if p["aspecto"] in ("dimensiones", "espesor", "resistencia"):
                if numeros(p["cliente"]) != numeros(p["catalogo"]):
                    raise ValueError("Valores técnicos distintos en las citas; no se infieren conversiones")
            if p["aspecto"] == "materiales":
                def tipos(texto):
                    return set(re.findall(r"\btipo\s*[\"']?([abc])\b", normalizar(texto)))
                a, b = tipos(p["cliente"]), tipos(p["catalogo"])
                if a and b and a != b:
                    raise ValueError("Tipos de material explícitos distintos")
    if aspectos != set(ASPECTOS):
        raise ValueError("Falta evaluar algún aspecto técnico")


def huella(registro):
    return hashlib.sha256(json.dumps(registro, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode("utf-8")).hexdigest()


def candidato_elegido(busqueda, identificador):
    if type(identificador) is not int or identificador < 1:
        raise ValueError("IdCodigo debe ser un entero SQL positivo")
    candidatos = [c for c in busqueda.get("candidatos", []) if c.get("IdCodigo") == identificador]
    if len(candidatos) != 1:
        raise ValueError("El IdCodigo debe identificar un único candidato de esta búsqueda")
    candidato = candidatos[0]
    if (any(not isinstance(candidato.get(c), str) or not candidato[c].strip()
            for c in ("Codigo", "DescripcionLarga", "unidad_catalogo"))
            or candidato.get("IdTipo") != 4 or type(candidato.get("IdUnidad")) is not int):
        raise ValueError("Candidato sin código, descripción completa, unidad o tipo 4 verificables")
    return candidato


def validar_unidad(registro, candidato):
    unidad = registro.get("unidad")
    if not unidad or normalizar(unidad).strip() != normalizar(candidato["unidad_catalogo"]).strip():
        raise ValueError("Unidad distinta o faltante: resolver antes de confirmar; no se convierten cantidades")


def seleccion_validada(registro, busqueda):
    """Valida la auditoría y devuelve la instantánea SQL; no acredita la decisión técnica."""
    seleccion = busqueda.get("seleccion")
    if seleccion is None:
        return None
    base = {"IdCodigo", "revisor", "motivo", "concepto_sha256", "catalogo", "verificado_utc"}
    if (not isinstance(seleccion, dict)
            or set(seleccion) not in (base, base | {"origen", "modelo", "evaluacion_sha256"})
            or any(not isinstance(seleccion.get(c), str) or not seleccion[c].strip()
                   for c in ("revisor", "motivo", "verificado_utc"))):
        raise ValueError("La selección requiere una confirmación explícita con auditoría")
    candidato = candidato_elegido(busqueda, seleccion["IdCodigo"])
    if seleccion["concepto_sha256"] != huella(registro):
        raise ValueError("El concepto cambió después de la confirmación; revisar nuevamente")
    if seleccion["catalogo"] != {c: candidato[c] for c in CAMPOS_SQL}:
        raise ValueError("Los datos del candidato cambiaron después de la confirmación")
    validar_unidad(registro, candidato)
    if "origen" in seleccion:
        if seleccion["origen"] != "ia" or not isinstance(seleccion["modelo"], str) or not seleccion["modelo"].strip():
            raise ValueError("Origen de selección inválido")
        evaluacion = busqueda.get("evaluacion_ia")
        if seleccion["evaluacion_sha256"] != huella(evaluacion):
            raise ValueError("La evidencia IA cambió tras seleccionar")
        validar_evaluacion_ia(registro, busqueda, evaluacion)
        if evaluacion["seleccion_id"] != seleccion["IdCodigo"] or evaluacion["motivo"] != seleccion["motivo"]:
            raise ValueError("Selección y evaluación IA no coinciden")
    return seleccion["catalogo"]


def sin_matriz_validada(registro, busqueda):
    decision = busqueda.get("sin_matriz")
    if decision is None:
        return None
    campos = {"revisor", "motivo", "concepto_sha256", "codigo", "registrado_utc"}
    if (not isinstance(decision, dict) or set(decision) != campos
            or busqueda.get("seleccion") is not None
            or any(not isinstance(decision[k], str) or not decision[k].strip() for k in campos)
            or decision["concepto_sha256"] != huella(registro)
            or (registro["clave"] and registro["clave"].strip() and decision["codigo"] != registro["clave"])):
        raise ValueError("Decisión sin matriz inválida o concepto modificado; revisar nuevamente")
    return decision


def preparar(datos, decisiones):
    validar_entrada(datos, {})
    if any(r['clave'] is not None and not isinstance(r['clave'], str) for r in datos['registros']):
        raise ValueError('Las claves deben conservar texto del cliente')
    conceptos = {(r["hoja"], r["fila"]): r for r in datos["registros"] if r["tipo"] == "concepto"}
    busquedas = {}
    for b in datos.get("busquedas_construbase", []):
        identidad = b["hoja"], b["fila"]
        if identidad not in conceptos or identidad in busquedas:
            raise ValueError("Búsqueda duplicada o ajena a los conceptos")
        seleccion_validada(conceptos[identidad], b)
        sin_matriz_validada(conceptos[identidad], b)
        busquedas[identidad] = b
    if not isinstance(decisiones, list) or not decisiones:
        raise ValueError("Se requiere una lista no vacía de decisiones humanas")
    vistos, preparados = set(), []
    for d in decisiones:
        if (not isinstance(d, dict) or set(d) not in ({"hoja", "fila", "IdCodigo", "revisor", "motivo"},
                                               {"hoja", "fila", "IdCodigo", "revisor", "motivo", "codigo"})
                or not isinstance(d["hoja"], str) or type(d["fila"]) is not int
                or any(not isinstance(d[c], str) or not d[c].strip() for c in ("revisor", "motivo"))):
            raise ValueError("Cada decisión requiere hoja, fila, IdCodigo, revisor y motivo técnico")
        identidad = d["hoja"], d["fila"]
        if identidad in vistos or identidad not in busquedas:
            raise ValueError("Decisión duplicada o sin búsqueda de origen")
        vistos.add(identidad)
        b = busquedas[identidad]
        if b.get("seleccion") is not None or b.get("sin_matriz") is not None:
            raise ValueError("Ya existe una selección; no se reemplaza silenciosamente")
        if d["IdCodigo"] is None:
            registro = conceptos[identidad]
            codigo = registro["clave"] if registro["clave"] and registro["clave"].strip() else d.get("codigo")
            if (not isinstance(codigo, str) or not codigo.strip()
                    or ("codigo" in d and d["codigo"] != codigo)):
                raise ValueError("Falta código del cliente: solicitar uno al usuario sin modificar el original")
            preparados.append((d, registro, None))
            continue
        if "codigo" in d:
            raise ValueError("No se puede alterar el código del cliente al seleccionar una matriz")
        candidato = candidato_elegido(b, d["IdCodigo"])
        validar_unidad(conceptos[identidad], candidato)
        preparados.append((d, conceptos[identidad], candidato))
    return preparados


def consultar_candidato(conexion, identificador):
    if type(identificador) is not int or identificador < 1:
        raise ValueError("IdCodigo debe ser un entero SQL positivo")
    cursor = conexion.cursor()
    cursor.execute("""SELECT c.IdCodigo, c.Codigo, c.DescripcionLarga, c.IdUnidad, c.IdTipo,
u.Unidad AS unidad_catalogo FROM dbo.PuCatalogo AS c
LEFT JOIN dbo.PuUnidades AS u ON u.IdUnidad = c.IdUnidad
WHERE c.IdCodigo = ? AND c.IdTipo = 4""", identificador)
    filas = cursor.fetchall()
    if len(filas) != 1:
        raise ValueError("El candidato no corresponde a un único concepto tipo 4 en ConstruBase")
    return dict(zip(CAMPOS_SQL, filas[0]))


def confirmar(datos, decisiones, conexion):
    preparados = preparar(datos, decisiones)
    salida = deepcopy(datos)
    busquedas = {(b["hoja"], b["fila"]): b for b in salida["busquedas_construbase"]}
    for decision, registro, candidato in preparados:
        if candidato is None:
            b = busquedas[decision["hoja"], decision["fila"]]
            codigo = registro["clave"] if registro["clave"] and registro["clave"].strip() else decision["codigo"]
            b["sin_matriz"] = dict(revisor=decision["revisor"], motivo=decision["motivo"],
                concepto_sha256=huella(registro), codigo=codigo,
                registrado_utc=datetime.now(timezone.utc).isoformat())
            sin_matriz_validada(registro, b)
            b.update(estado="sin_matriz_por_usuario", requiere_revision=False)
            continue
        actual = consultar_candidato(conexion, decision["IdCodigo"])
        if actual != {c: candidato[c] for c in CAMPOS_SQL}:
            raise ValueError("ConstruBase difiere de la búsqueda guardada; volver a buscar y revisar")
        b = busquedas[decision["hoja"], decision["fila"]]
        b["seleccion"] = dict(IdCodigo=decision["IdCodigo"], revisor=decision["revisor"],
            motivo=decision["motivo"], concepto_sha256=huella(registro), catalogo=actual,
            verificado_utc=datetime.now(timezone.utc).isoformat())
        seleccion_validada(registro, b)
        b["estado"] = "confirmada_por_revision_humana"
        b["requiere_revision"] = False
    return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presupuesto")
    parser.add_argument("decisiones")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--salida", required=True, help="JSON nuevo con confirmaciones")
    args = parser.parse_args()
    destino = Path(args.salida)
    ruta_env = Path(args.env)
    if not ruta_env.is_absolute():
        ruta_env = Path(__file__).resolve().parent / ruta_env
    if destino.exists() or destino.is_symlink() or any(
            Path(p).resolve() == destino.resolve() for p in (args.presupuesto, args.decisiones, ruta_env)):
        parser.error("La salida debe ser nueva y distinta de entradas/configuración")
    datos = json.loads(Path(args.presupuesto).read_text(encoding="utf-8"))
    decisiones = json.loads(Path(args.decisiones).read_text(encoding="utf-8"))
    preparar(datos, decisiones)  # Antes de abrir SQL, también en el CLI.
    with (conectar_sql(ruta_env) if any(d['IdCodigo'] is not None for d in decisiones) else nullcontext(None)) as conexion:
        salida = confirmar(datos, decisiones, conexion)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"{len(decisiones)} decisiones humanas registradas; matrices elegidas verificadas en SQL")


if __name__ == "__main__":
    main()
