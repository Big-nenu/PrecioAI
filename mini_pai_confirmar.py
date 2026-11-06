"""Registra decisiones humanas explícitas sobre candidatos verificados en SQL (solo lectura)."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from buscar_conceptos import conectar_sql
from mini_pai_buscar import validar_entrada
from ranking_conceptos import normalizar


CAMPOS_SQL = ("IdCodigo", "Codigo", "DescripcionLarga", "IdUnidad", "IdTipo", "unidad_catalogo")


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
    if (not isinstance(seleccion, dict)
            or set(seleccion) != {"IdCodigo", "revisor", "motivo", "concepto_sha256", "catalogo", "verificado_utc"}
            or any(not isinstance(seleccion.get(c), str) or not seleccion[c].strip()
                   for c in ("revisor", "motivo", "verificado_utc"))):
        raise ValueError("La selección requiere una confirmación explícita con auditoría")
    candidato = candidato_elegido(busqueda, seleccion["IdCodigo"])
    if seleccion["concepto_sha256"] != huella(registro):
        raise ValueError("El concepto cambió después de la confirmación; revisar nuevamente")
    if seleccion["catalogo"] != {c: candidato[c] for c in CAMPOS_SQL}:
        raise ValueError("Los datos del candidato cambiaron después de la confirmación")
    validar_unidad(registro, candidato)
    return seleccion["catalogo"]


def preparar(datos, decisiones):
    validar_entrada(datos, {})
    conceptos = {(r["hoja"], r["fila"]): r for r in datos["registros"] if r["tipo"] == "concepto"}
    busquedas = {}
    for b in datos.get("busquedas_construbase", []):
        identidad = b["hoja"], b["fila"]
        if identidad not in conceptos or identidad in busquedas:
            raise ValueError("Búsqueda duplicada o ajena a los conceptos")
        seleccion_validada(conceptos[identidad], b)
        busquedas[identidad] = b
    if not isinstance(decisiones, list) or not decisiones:
        raise ValueError("Se requiere una lista no vacía de decisiones humanas")
    vistos, preparados = set(), []
    for d in decisiones:
        if (not isinstance(d, dict) or set(d) != {"hoja", "fila", "IdCodigo", "revisor", "motivo"}
                or not isinstance(d["hoja"], str) or type(d["fila"]) is not int
                or any(not isinstance(d[c], str) or not d[c].strip() for c in ("revisor", "motivo"))):
            raise ValueError("Cada decisión requiere hoja, fila, IdCodigo, revisor y motivo técnico")
        identidad = d["hoja"], d["fila"]
        if identidad in vistos or identidad not in busquedas:
            raise ValueError("Decisión duplicada o sin búsqueda de origen")
        vistos.add(identidad)
        b = busquedas[identidad]
        if b.get("seleccion") is not None:
            raise ValueError("Ya existe una selección; no se reemplaza silenciosamente")
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
    with conectar_sql(ruta_env) as conexion:
        salida = confirmar(datos, decisiones, conexion)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"{len(decisiones)} decisiones humanas verificadas en SQL; ninguna selección automática")


if __name__ == "__main__":
    main()
