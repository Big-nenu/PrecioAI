"""Índice vectorial local reanudable; no escribe en ConstruBase ni selecciona matrices."""
import hashlib
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import numpy as np

from laboratorio_coincidencias import embeddings, prefijos


def firma(catalogo, modelo, digest):
    ids = [c["id"] for c in catalogo]
    if not ids or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Catálogo vacío o IDs inválidos/duplicados")
    if any(not isinstance(c.get("descripcion"), str) or not c["descripcion"].strip() for c in catalogo):
        raise ValueError("Falta descripción original")
    if not isinstance(digest, str) or not digest:
        raise ValueError("Se requiere digest del modelo para no mezclar vectores")
    contenido = json.dumps(sorted(catalogo, key=lambda c: c["id"]), ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
    return dict(version=1, catalogo_sha256=hashlib.sha256(contenido).hexdigest(),
                modelo=modelo, digest=digest, prefijos=list(prefijos(modelo)), documentos=len(ids))


def construir(ruta, catalogo, modelo, digest, *, base="http://127.0.0.1:11434", lote=32, progreso=None):
    if type(lote) is not int or lote < 1:
        raise ValueError("Lote inválido")
    identidad = firma(catalogo, modelo, digest)
    ruta = Path(ruta)
    if ruta.is_symlink():
        raise ValueError("El índice no puede ser un enlace")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(ruta)) as db:
        # Un archivo ajeno nunca se adopta ni sobrescribe como índice.
        tablas = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tablas and tablas != {"meta", "vectores"}:
            raise ValueError("El archivo no es un índice Mini-PAI")
        db.execute("CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS vectores (id TEXT PRIMARY KEY, documento TEXT NOT NULL, vector BLOB NOT NULL)")
        fila = db.execute("SELECT valor FROM meta WHERE clave='identidad'").fetchone()
        if fila and json.loads(fila[0]) != identidad:
            raise ValueError("Índice de otro catálogo/modelo/prefijo; usar una ruta nueva")
        if not fila:
            if db.execute("SELECT COUNT(*) FROM vectores").fetchone()[0]:
                raise ValueError("Índice sin identidad verificable")
            db.execute("INSERT INTO meta VALUES ('identidad',?)", (json.dumps(identidad),))
            db.commit()
        existentes = {r[0] for r in db.execute("SELECT id FROM vectores")}
        if not existentes <= {c["id"] for c in catalogo}:
            raise ValueError("El índice contiene documentos ajenos")
        dimension = db.execute("SELECT valor FROM meta WHERE clave='dimension'").fetchone()
        dimension = int(dimension[0]) if dimension else None
        pendientes = [c for c in catalogo if c["id"] not in existentes]
        _, prefijo = prefijos(modelo)
        for inicio in range(0, len(pendientes), lote):
            parte = pendientes[inicio:inicio + lote]
            matriz = embeddings(base, modelo, [prefijo + c["descripcion"] for c in parte], lote=lote)
            if dimension is not None and matriz.shape[1] != dimension:
                raise ValueError("El modelo cambió de dimensión")
            dimension = matriz.shape[1]
            with db:
                db.execute("INSERT OR REPLACE INTO meta VALUES ('dimension',?)", (str(dimension),))
                db.executemany("INSERT INTO vectores VALUES (?,?,?)", [
                    (c["id"], json.dumps(c, ensure_ascii=False), v.astype("<f4").tobytes()) for c, v in zip(parte, matriz)])
            if progreso:
                progreso(len(existentes) + min(inicio + lote, len(pendientes)), len(catalogo))
        return dict(nuevos=len(pendientes), reutilizados=len(existentes), dimension=dimension, documentos=len(catalogo))


def cargar(ruta, identidad):
    ruta = Path(ruta)
    with closing(sqlite3.connect(ruta.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        guardada = db.execute("SELECT valor FROM meta WHERE clave='identidad'").fetchone()
        if guardada is None or json.loads(guardada[0]) != identidad:
            raise ValueError("Identidad de índice distinta")
        dimension = db.execute("SELECT valor FROM meta WHERE clave='dimension'").fetchone()
        filas = db.execute("SELECT id,documento,vector FROM vectores ORDER BY id").fetchall()
    if dimension is None or len(filas) != identidad["documentos"]:
        raise ValueError("Índice incompleto; reanudar la construcción")
    dimension = int(dimension[0])
    documentos, vectores = [], []
    for identificador, documento, blob in filas:
        if len(blob) != dimension * 4:
            raise ValueError("Vector persistido corrupto")
        dato = json.loads(documento)
        if dato["id"] != identificador:
            raise ValueError("Documento y vector no corresponden")
        documentos.append(dato)
        vectores.append(np.frombuffer(blob, dtype="<f4"))
    matriz = np.asarray(vectores, dtype=np.float32)
    if not np.isfinite(matriz).all() or np.any(np.linalg.norm(matriz, axis=1) == 0):
        raise ValueError("Vectores persistidos inválidos")
    # Comprobar también los textos, no solo el número de filas.
    reconstruida = firma(sorted(documentos, key=lambda d: d["id"]), identidad["modelo"], identidad["digest"])
    if reconstruida != identidad:
        raise ValueError("Contenido del catálogo persistido distinto")
    return documentos, matriz
