"""Prueba local reproducible de extracción y comparación; genera Markdown, sin SQL."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import time
from unittest.mock import patch
from urllib.request import Request, urlopen

import mini_pai_seleccionar as selector
from mini_pai_tabla import interpretar_tabla
from mini_pai_revision import texto
import proveedor_ia


RAIZ = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:11434"
CONFIG = dict(PRECIOAI_AI_PROVIDER="ollama", PRECIOAI_AI_BASE_URL=BASE + "/v1",
              PRECIOAI_AI_API_KEY="", PRECIOAI_OLLAMA_NUM_CTX="12288",
              PRECIOAI_OLLAMA_NUM_PREDICT="6144", PRECIOAI_OLLAMA_THINK="true")


def sha(datos):
    return hashlib.sha256(datos).hexdigest()


def http(ruta, datos=None):
    req = Request(BASE + ruta, data=json.dumps(datos).encode() if datos is not None else None,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=15) as respuesta:
        return json.load(respuesta)


def cargar_muestra(ruta):
    manifest = json.loads(ruta.read_text(encoding="utf-8"))
    archivos = {}
    for nombre in ("presupuesto", "referencia", "candidatos"):
        entrada = manifest["archivos"][nombre]
        archivo = ruta.parent / entrada["ruta"]
        if sha(archivo.read_bytes()) != entrada["sha256"]:
            raise ValueError(f"La muestra cambió: {nombre}. No comparar resultados de entradas distintas")
        archivos[nombre] = archivo
    manifest["presupuesto"] = archivos["presupuesto"]
    manifest["rutas"] = archivos
    for nombre in ("referencia", "candidatos"):
        manifest[nombre] = json.loads(archivos[nombre].read_text(encoding="utf-8"))
    manifest["muestra_sha256"] = sha(ruta.read_bytes())
    selector.validar_entrada(manifest["candidatos"], {})
    return manifest


def cotejar(actual, referencia):
    identidad = lambda r: (r["hoja"], r["fila"])
    esperados = {identidad(r): r for r in referencia["registros"]}
    if len(esperados) != len(referencia["registros"]):
        raise ValueError("La referencia tiene filas duplicadas")
    obtenidos = {identidad(r): r for r in actual["registros"]}
    diferencias = []
    campos = ("tipo", "padre", "clave", "descripcion", "unidad", "cantidad", "partida", "subpartida", "evidencia")
    if len(obtenidos) != len(actual["registros"]):
        diferencias.append(dict(campo="filas duplicadas"))
    for clave in sorted(set(esperados) | set(obtenidos)):
        if clave not in esperados or clave not in obtenidos:
            diferencias.append(dict(hoja=clave[0], fila=clave[1], campo="registro faltante o adicional"))
            continue
        for campo in campos:
            if esperados[clave].get(campo) != obtenidos[clave].get(campo):
                diferencias.append(dict(hoja=clave[0], fila=clave[1], campo=campo,
                                        esperado=esperados[clave].get(campo), obtenido=obtenidos[clave].get(campo)))
    if ({identidad(r) for r in referencia["excluidas"]} != {identidad(r) for r in actual["excluidas"]}
            or actual["alcance"] != referencia["alcance"]):
        diferencias.append(dict(campo="exclusiones o alcance distintos"))
    conceptos = [r for r in actual["registros"] if r["tipo"] == "concepto"]
    return dict(correcta=not diferencias, conceptos=len(conceptos),
                conceptos_esperados=sum(r["tipo"] == "concepto" for r in esperados.values()),
                agrupadores=len(actual["registros"]) - len(conceptos), diferencias=diferencias)


def control_tecnico(caso, controles):
    control = next((c for c in controles if (c["hoja"], c["fila"]) == (caso["hoja"], caso["fila"])), None)
    if control is None:
        return "Sin etiqueta técnica de referencia"
    evaluacion = caso.get("propuesta") or caso.get("evaluacion")
    if evaluacion is None and caso.get("respuesta_rechazada"):
        try:
            evaluacion = json.loads(caso["respuesta_rechazada"])
        except (ValueError, TypeError):
            pass
    if not isinstance(evaluacion, dict):
        return "Control no evaluable: " + control["motivo"]
    prohibidos = set(control["ids_incompatibles"])
    candidatos = evaluacion.get("candidatos", [])
    if not isinstance(candidatos, list):
        candidatos = []
    elegido = evaluacion.get("seleccion_id")
    if ((type(elegido) is int and elegido in prohibidos) or any(
            type(c.get("IdCodigo")) is int and c["IdCodigo"] in prohibidos and c.get("dictamen") == "equivalente"
            for c in candidatos if isinstance(c, dict))):
        return "ALERTA: propuso equivalencia incompatible; " + control["motivo"]
    if caso.get("error"):
        return "Control no evaluable por error: " + control["motivo"]
    return "No propuso equivalencia incompatible; revisar clasificación: " + control["motivo"]


@contextmanager
def instrumentar(resultado):
    abrir = proveedor_ia.urlopen

    def medir(req, **kwargs):
        inicio = time.perf_counter()
        registro = dict(fase=resultado["fase"], caso=resultado.get("caso"),
                        solicitud=json.loads(req.data))
        try:
            with abrir(req, **kwargs) as respuesta:
                raw = respuesta.read()
            datos = json.loads(raw)
            registro["respuesta"] = datos
            return io.BytesIO(raw)
        except Exception as exc:
            registro["error"] = str(exc)
            raise
        finally:
            registro["segundos"] = time.perf_counter() - inicio
            try:
                residentes = http("/api/ps")["models"]
                registro["vram_residente_bytes"] = next((m["size_vram"] for m in residentes
                    if m.get("name", m.get("model")) == resultado["modelo"]), None)
                if type(registro["vram_residente_bytes"]) not in (int, float):
                    registro["vram_residente_bytes"] = None
                registro["otros_modelos_gpu"] = [m.get("name", m.get("model")) for m in residentes
                    if isinstance(m.get("name", m.get("model")), str)
                    and m.get("name", m.get("model")) != resultado["modelo"] and m.get("size_vram", 0) > 0]
            except Exception:
                registro["vram_residente_bytes"] = None
            resultado["llamadas"].append(registro)

    with patch.object(proveedor_ia, "urlopen", medir):
        yield


def markdown(r):
    lineas = [f"# Prueba Mini-PAI — {texto(r['modelo'])}", "", f"Estado: **{texto(r['estado'])}**. Fecha UTC: {r['fecha']}.", "",
        f"Muestra SHA256: `{r['muestra_sha256']}`", "", f"Nota de procedencia: {texto(r['nota'])}", "",
        "Contexto 12288; máximo de salida 6144; razonamiento activado; temperatura 0. Ollama local.", "",
        "El modelo se libera de memoria antes y después de su prueba, sin borrar ni descargar archivos. Los tiempos incluyen carga inicial, reintentos e instrumentación.", "",
        "Esta prueba usa funciones Python: no mide elección autónoma de herramientas, MCP o Cline.", "",
        "## Extracción", ""]
    e = r.get("extraccion", {})
    lineas += [f"- Correcta contra referencia cotejada: **{texto(e.get('correcta', 'No evaluable'))}**.",
        f"- Conceptos: {e.get('conceptos', '—')}/{e.get('conceptos_esperados', '—')}; agrupadores: {e.get('agrupadores', '—')}; segundos: {e.get('segundos', 0):.3f}.",
        f"- Error: {texto(e.get('error', 'Ninguno'))}.", ""]
    for d in e.get("diferencias", []):
        lineas.append(f"- {texto(json.dumps(d, ensure_ascii=False))}")
    if e.get("estructura") is not None:
        lineas += ["", "Estructura detectada: " + texto(json.dumps(e["estructura"], ensure_ascii=False))]
    for duda in e.get("dudas", []):
        lineas.append("- Duda de extracción: " + texto(duda))
    lineas += ["", "## Comparación técnica con candidatos fijos", "",
        f"Casos con evaluación válida: {sum('evaluacion' in c for c in r['tecnica'])}; "
        f"errores de evaluación: {sum('error' in c for c in r['tecnica'])}; "
        f"sin candidatos en la muestra: {sum(not c['candidatos'] for c in r['tecnica'])}; "
        f"propuestas tras guardas locales: {sum(c.get('evaluacion', {}).get('seleccion_id') is not None for c in r['tecnica'])}. "
        f"Suma de tiempos de casos técnicos: {sum(c.get('segundos', 0) for c in r['tecnica']):.3f} s.", "",
        "Los resultados son propuestas con validaciones locales, **sin verificación SQL ni selección confirmada**. Una salida válida no demuestra exactitud técnica.", "",
        "| Caso | Candidatos | Segundos | ID propuesto | ID tras guardas locales | Resultado/control |",
        "| --- | ---: | ---: | --- | --- | --- |"]
    for c in r["tecnica"]:
        base = c.get("propuesta") or c.get("evaluacion") or {}
        lineas.append(f"| {texto(c['hoja'])}:{c['fila']} | {len(c['candidatos'])} | {c.get('segundos', 0):.3f} | "
            f"{base.get('seleccion_id')} | {c.get('evaluacion', {}).get('seleccion_id')} | "
            f"{texto(c['control'] + ('; Error: ' + c['error'] if c.get('error') else ''))} |")
    for c in r["tecnica"]:
        lineas += ["", f"### {texto(c['hoja'])}:{c['fila']} — {texto(c['codigo_cliente'])}", "",
            f"Cliente: {texto(c['descripcion_cliente'])}", "", f"Control: {texto(c['control'])}", ""]
        if c.get("error"):
            lineas.append("Error: " + texto(c["error"]))
        e = c.get("evaluacion", {})
        lineas.append("Motivo global: " + texto(e.get("motivo", "Sin evaluación válida")))
        lineas.append("Orden técnico validado: " + (", ".join(str(x["IdCodigo"]) for x in e.get("candidatos", [])) or "No disponible"))
        propuesta = c.get("propuesta") or e
        dictamenes = {x["IdCodigo"]: x for x in e.get("candidatos", [])}
        for candidato in c["candidatos"]:
            d = dictamenes.get(candidato["IdCodigo"], {})
            lineas += ["", f"- **{texto(candidato['Codigo'])} / ID {candidato['IdCodigo']} / {texto(candidato['unidad_catalogo'])}**: "
                + texto(candidato["DescripcionLarga"]),
                f"  Dictamen tras guardas: {texto(d.get('dictamen', 'Sin evaluación'))}. {texto(d.get('motivo', ''))}",
                f"  Evidencia cliente: {texto(d.get('cliente', ''))}; catálogo: {texto(d.get('catalogo', ''))}."]
        if c.get("propuesta"):
            lineas += ["", "Propuesta degradada por las guardas: " + texto(json.dumps(propuesta, ensure_ascii=False))]
        for prueba in e.get("comprobaciones", []):
            lineas.append("- Comprobación: " + texto(json.dumps(prueba, ensure_ascii=False)))
    lineas += ["", "## Llamadas y entorno", "", "| Fase/caso | Segundos HTTP | Tokens entrada | Tokens salida | Carga modelo (s) |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for c in r["llamadas"]:
        d = c.get("respuesta", {})
        if not isinstance(d, dict):
            d = {}
        carga = f"{d['load_duration']/1e9:.3f}" if type(d.get("load_duration")) in (int, float) else "—"
        lineas.append(f"| {texto(c['fase'])}/{texto(c.get('caso'))} | {c['segundos']:.3f} | {d.get('prompt_eval_count', '—')} | "
            f"{d.get('eval_count', '—')} | {carga} |")
    memoria = [c["vram_residente_bytes"] for c in r["llamadas"] if c.get("vram_residente_bytes") is not None]
    otros = sorted({m for c in r["llamadas"] for m in c.get("otros_modelos_gpu", [])})
    lineas += ["", f"VRAM residente máxima observada entre llamadas: {max(memoria)/1024**2:.1f} MiB." if memoria else "VRAM residente: no disponible.",
        "Esta lectura no es el pico de memoria de la GPU ni incluye toda la memoria del sistema.", "",
        "Otros modelos residentes en GPU durante la prueba: " + texto(", ".join(otros) if otros else "No observados") + ".", "",
        f"Tiempo total: {r.get('segundos', 0):.3f} s. Entorno: {texto(r['entorno'])}.", "",
        "Modelo instalado: " + texto(json.dumps(r["modelo_info"], ensure_ascii=False)), "",
        "Entradas intactas al finalizar: " + texto(r.get("entradas_intactas", "Prueba en curso")) + ".", "",
        "Código SHA256: " + texto(json.dumps(r["codigo_sha256"], ensure_ascii=False)), "",
        "No se mide recuperación SQL ni calidad técnica general. Los dos controles negativos no bastan para declarar ganador.",
        "Los reportes contienen descripciones privadas del presupuesto y catálogo; no publicarlos en GitHub."]
    if r.get("error"):
        lineas += ["", "Error de ejecución: " + texto(r["error"])]
    return "\n".join(lineas) + "\n"


def guardar(carpeta, resultado):
    for nombre, contenido in ((resultado["archivo_reporte"], markdown(resultado)),
                              ("resultados.json", json.dumps(resultado, ensure_ascii=False, indent=2))):
        temporal = carpeta / (nombre + ".tmp")
        temporal.write_text(contenido, encoding="utf-8")
        temporal.replace(carpeta / nombre)


def ejecutar(modelo, muestra, carpeta, info, entorno):
    r = dict(modelo=modelo, estado="en_curso", fecha=datetime.now(timezone.utc).isoformat(), fase="preparacion",
        archivo_reporte="reporte-" + re.sub(r"[^A-Za-z0-9_.-]", "_", modelo).strip(".") + ".md",
        muestra_sha256=muestra["muestra_sha256"], nota=muestra["nota"], entorno=entorno, modelo_info=info,
        codigo_sha256={n: sha((RAIZ/n).read_bytes()) for n in (
            "probar_modelos_mini_pai.py", "mini_pai_interpretar.py", "mini_pai_tabla.py", "mini_pai_seleccionar.py",
            "mini_pai_confirmar.py", "numeros_tecnicos.py", "ranking_conceptos.py", "proveedor_ia.py", "skills/analizar-presupuesto/SKILL.md")},
        tecnica=[], llamadas=[])
    carpeta.mkdir()
    inicio = time.perf_counter()
    guardar(carpeta, r)
    try:
        if info is None:
            r.update(estado="no_ejecutado", error="Modelo no disponible o no se pudo consultar Ollama; no hay resultados inventados")
            return r
        http("/api/generate", dict(model=modelo, keep_alive=0))
        with patch.dict(os.environ, dict(CONFIG, PRECIOAI_AI_MODEL=modelo)), instrumentar(r):
            r["fase"] = "extraccion"
            print(f"{modelo}: extrayendo presupuesto", flush=True)
            inicio_fase = time.perf_counter()
            try:
                actual = interpretar_tabla(str(muestra["presupuesto"]))
                r["extraccion"] = cotejar(actual, muestra["referencia"])
                r["extraccion"].update(estructura=actual.get("estructura_tabla_ia"), dudas=actual.get("dudas", []))
                (carpeta/"interpretacion.json").write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                r["extraccion"] = dict(correcta=False, error=str(exc))
            r["extraccion"]["segundos"] = time.perf_counter() - inicio_fase
            guardar(carpeta, r)
            skill = (RAIZ/"skills/analizar-presupuesto/SKILL.md").read_text(encoding="utf-8")
            instrucciones = skill.split("## Criterio de comparación técnica (etapa 2)", 1)[1].split("\n## ", 1)[0]
            registros = {(x["hoja"], x["fila"]): x for x in muestra["candidatos"]["registros"] if x["tipo"] == "concepto"}
            r["fase"] = "tecnica"
            for n, b in enumerate(muestra["candidatos"]["busquedas_construbase"], 1):
                registro = registros[b["hoja"], b["fila"]]
                caso = dict(hoja=b["hoja"], fila=b["fila"], codigo_cliente=registro["clave"],
                    descripcion_cliente=registro["descripcion"], candidatos=b["candidatos"])
                r["caso"] = f"{b['hoja']}:{b['fila']}"
                print(f"{modelo}: comparación {n}/{len(registros)} — {r['caso']}", flush=True)
                inicio_fase = time.perf_counter()
                try:
                    if b["candidatos"]:
                        caso["evaluacion"], caso["propuesta"] = selector.comparar(registro, b, instrucciones)
                    else:
                        caso["estado"] = "sin_candidatos_en_muestra"
                except Exception as exc:
                    caso["error"] = str(exc)
                    if hasattr(exc, "respuesta_ia"):
                        caso["respuesta_rechazada"] = exc.respuesta_ia
                caso["segundos"] = time.perf_counter() - inicio_fase
                caso["control"] = ("No evaluado: sin candidatos en la muestra" if not b["candidatos"]
                                   else control_tecnico(caso, muestra["controles"]))
                r["tecnica"].append(caso)
                guardar(carpeta, r)
        r["estado"] = "terminado"
    except KeyboardInterrupt:
        r["estado"] = "interrumpido"
        raise
    except Exception as exc:
        r.update(estado="error", error=str(exc))
    finally:
        if info is not None:
            try:
                http("/api/generate", dict(model=modelo, keep_alive=0))
            except Exception:
                pass
        try:
            r["entradas_intactas"] = all(sha(p.read_bytes()) == muestra["archivos"][n]["sha256"] for n, p in muestra["rutas"].items())
        except OSError:
            r["entradas_intactas"] = False
        if not r["entradas_intactas"]:
            r.update(estado="muestra_modificada", error="Las entradas cambiaron durante la prueba; no comparar resultados")
        r["segundos"] = time.perf_counter() - inicio
        guardar(carpeta, r)
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelos", nargs="+", default=["nemotron-3.5-bolt:e4b", "gemma4:e4b-it-qat"])
    parser.add_argument("--muestra", type=Path, default=RAIZ/"datos_privados/prueba-modelos/muestra.json")
    parser.add_argument("--salida", type=Path, default=RAIZ/"salidas"/("prueba-modelos-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")))
    args = parser.parse_args()
    try:
        muestra = cargar_muestra(args.muestra)
        args.salida.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    try:
        disponibles = {m["name"]: m for m in http("/api/tags")["models"]}
        version = http("/api/version")
    except Exception as exc:
        disponibles, version = {}, dict(error=str(exc))
    entorno = dict(python=platform.python_version(), plataforma=platform.platform(), ollama=version)
    print("Reportes en:", args.salida, flush=True)
    try:
        for n, modelo in enumerate(args.modelos, 1):
            nombre = f"{n:02}-" + re.sub(r"[^A-Za-z0-9_.-]", "_", modelo).strip(".")
            resultado = ejecutar(modelo, muestra, args.salida/nombre, disponibles.get(modelo), entorno)
            print(f"Reporte guardado ({resultado['estado']}):", args.salida/nombre/resultado["archivo_reporte"], flush=True)
    except KeyboardInterrupt:
        print("Prueba interrumpida. Los reportes parciales están guardados.")
        return 130
    print("Prueba terminada. Revisa los reportes: terminar no significa que el modelo haya pasado los controles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
