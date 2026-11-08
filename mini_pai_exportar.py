"""Primer Excel de revisión: conserva el cliente sin confirmar candidatos automáticamente."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from mini_pai_buscar import validar_entrada
from mini_pai_confirmar import seleccion_validada
from mini_pai_revision import resolver, reporte, indice


COLUMNAS = ("Partida", "Código", "Código auxiliar", "Descripción completa",
            "Descripción auxiliar", "Unidad", "Cantidad", "Tipo")
COPIAR = ("Partida", "Código", "Código auxiliar", "Descripción auxiliar", "Unidad", "Cantidad")


def cantidad_excel(valor):
    """Solo convierte decimales inequívocos; el texto original queda en Revisión."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError("La cantidad debe conservar el texto del JSON interpretado")
    texto = valor.strip()
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", texto):
        numero = Decimal(texto)
        if len(numero.as_tuple().digits) <= 15 and abs(numero) < Decimal("1e15"):
            convertido = int(numero) if numero == numero.to_integral_value() else float(numero)
            if Decimal(str(convertido)) == numero:
                return convertido
    return valor


def escribir(hoja, valores):
    """Evita fórmulas accidentales y truncamientos silenciosos de texto en Excel."""
    fila = hoja.max_row + 1 if hoja.cell(1, 1).value is not None else 1
    for columna, valor in enumerate(valores, 1):
        if isinstance(valor, str) and len(valor) > 32767:
            raise ValueError("Un campo supera los 32767 caracteres de una celda Excel; no se truncará")
        celda = hoja.cell(fila, columna, valor)
        if isinstance(valor, str):
            celda.data_type = "s"
            celda.number_format = "@"
        celda.font = Font(name="Arial", size=10)
        celda.alignment = Alignment(vertical="top", wrap_text=True)
    return fila


def crear_excel(datos, *, final=False):
    """No usa SQL ni IA: exporta el JSON revisable del PR #3 sin modificarlo."""
    validar_entrada(datos, {})
    indice(datos)  # Valida también las decisiones explícitas de conservar originales.
    if any(r["clave"] is not None and not isinstance(r["clave"], str) for r in datos["registros"]):
        raise ValueError("Las claves deben conservar el texto original")
    conceptos = {(r["hoja"], r["fila"]) for r in datos["registros"] if r["tipo"] == "concepto"}
    busquedas = {}
    seleccionadas = {}
    codigos = {}
    descripciones_finales = {}
    origenes = {(r["hoja"], r["fila"]): r for r in datos["registros"]}
    for b in datos.get("busquedas_construbase", []):
        identidad = (b["hoja"], b["fila"])
        if identidad not in conceptos or identidad in busquedas:
            raise ValueError("Búsqueda duplicada o ajena a los conceptos")
        seleccionadas[identidad] = seleccion_validada(origenes[identidad], b)
        seleccion = seleccionadas[identidad]
        if seleccion:
            firma = seleccion["DescripcionLarga"], seleccion["unidad_catalogo"]
            if seleccion["Codigo"] in codigos and codigos[seleccion["Codigo"]] != firma:
                raise ValueError("Código de ConstruBase con descripciones o unidades distintas; revisar conflicto")
            codigos[seleccion["Codigo"]] = firma
        busquedas[identidad] = b

    libro = Workbook()
    catalogo = libro.active
    catalogo.title = "Catálogo"
    copiar = libro.create_sheet("Copiar auxiliares")
    revision = libro.create_sheet("Revisión")
    escribir(catalogo, COLUMNAS)
    escribir(copiar, COPIAR)
    parcial = datos.get("alcance", {}).get("parcial", False)
    confirmadas = sum(s is not None for s in seleccionadas.values())
    escribir(revision, ["Alcance", "PARCIAL" if parcial else "Según JSON de entrada",
                       "Confirmadas", confirmadas, "Solo las confirmadas usan los datos de ConstruBase."])
    escribir(revision, ["Uso", "Copiado probado por el usuario en Neodata. Revisar los conceptos pendientes."])
    escribir(revision, ["Hoja origen", "Fila origen", "Fila Excel", "Tipo", "Padre (fila origen)",
                       "Partida original", "Subpartida original", "Estado", "Cantidad original",
                       "Observaciones", "Evidencia", "Unidad cliente", "IdCodigo confirmado",
                       "Revisor", "Motivo técnico", "Verificado SQL (UTC)"])
    # Se conservan los encabezados como filas y el parentesco por hoja/fila.
    rutas, etiquetas, estado, rutas_usadas = {}, {}, {}, {}
    for r in datos["registros"]:
        hoja, fila, tipo = r["hoja"], r["fila"], r["tipo"]
        partida, subpartida = estado.get(hoja, (None, None))
        padre_legado = None if tipo == "partida" else partida if tipo == "subpartida" else subpartida or partida
        padre = r.get("padre", padre_legado)
        observaciones = []
        if r.get('contexto_descripcion'):
            observaciones.append('Descripción común conservada en filas origen: '+', '.join(str(c['fila']) for c in r['contexto_descripcion']))
        seleccion = None
        catalogo_sql = None
        if tipo != "concepto":
            etiqueta = r["clave"] or r["descripcion"] or ""
            raiz = rutas.get((hoja, padre), "")
            # No duplicar A cuando el cliente ya proporcionó A.A01 (o A.01).
            etiqueta_padre = etiquetas.get((hoja,padre), "")
            sufijo = etiqueta[len(etiqueta_padre)+1:] if etiqueta_padre and etiqueta.startswith(etiqueta_padre+".") else etiqueta
            ruta = raiz + "." + sufijo if raiz else etiqueta
            etiquetas[hoja,fila] = etiqueta
            rutas[hoja, fila] = ruta
            if tipo == "partida":
                partida, subpartida = fila, None
            else:
                subpartida = fila
            estado[hoja] = partida, subpartida
            if not etiqueta:
                observaciones.append("Encabezado sin clave ni descripción; revisar jerarquía")
            if ruta in rutas_usadas:
                observaciones.append("Ruta de partida repetida; comprobar antes de copiar")
            rutas_usadas[ruta] = (hoja, fila)
            valores = [ruta, None, None, r["descripcion"], None, None, None, None]
            estado_revision = "Encabezado"
        else:
            ruta = rutas.get((hoja, padre), "")
            b = busquedas.get((hoja, fila))
            catalogo_sql = seleccionadas.get((hoja, fila))
            if catalogo_sql is not None:
                seleccion = b["seleccion"]
                estado_revision = ("Seleccionada por IA (SQL verificado)" if seleccion.get("origen") == "ia"
                                   else "Confirmada por revisión humana")
                observaciones.append("Unidad cliente: " + r["unidad"] + "; unidad ConstruBase: " + catalogo_sql["unidad_catalogo"])
            elif b is None:
                estado_revision = "Sin evaluar"
            elif b.get("candidatos"):
                estado_revision = "Dudosa: pendiente de confirmar"
            elif b.get("estado") == "sin_candidatos_en_busqueda":
                estado_revision = "No encontrada en esta búsqueda"
                observaciones.append("No demuestra ausencia de equivalencia en todo ConstruBase")
            else:
                estado_revision = "Sin evaluar"
            if b and (b.get("evaluacion_ia") or b.get("error_ia")) and catalogo_sql is None:
                estado_revision = "Pendiente de revisión: IA"
                observaciones.append(b.get("error_ia") or b["evaluacion_ia"]["motivo"])
            if b and b.get("limite_sql_alcanzado"):
                observaciones.append(f"Búsqueda limitada a {b.get('limite_recuperacion', 50)} resultados SQL")
            for campo in ("clave", "descripcion", "unidad", "cantidad"):
                if r[campo] is None or not str(r[campo]).strip():
                    observaciones.append("Falta " + campo + " del cliente")
            if not ruta:
                observaciones.append("Concepto sin partida; no se inventó un agrupador")
            if r["clave"] is not None and len(r["clave"]) > 20:
                observaciones.append("Código auxiliar supera 20 caracteres; no se recortó")
            cantidad = cantidad_excel(r["cantidad"])
            if isinstance(cantidad, str):
                observaciones.append("Cantidad conservada como texto; revisar formato numérico")
            codigo_salida = catalogo_sql["Codigo"] if catalogo_sql else None
            descripcion_salida = catalogo_sql["DescripcionLarga"] if catalogo_sql else None
            auxiliar = r["clave"]
            if final or (b and b.get("sin_matriz")):
                codigo_salida, descripcion_salida, categoria = resolver(r, b)
                if not catalogo_sql:
                    estado_revision = categoria
                    if not auxiliar or not auxiliar.strip():
                        auxiliar = codigo_salida  # Código proporcionado por el usuario, original intacto.
                    if b.get("sin_matriz"):
                        observaciones.append("Decisión: " + b["sin_matriz"]["motivo"])
            if final and (not ruta or not descripcion_salida or not descripcion_salida.strip()):
                raise ValueError(f"{hoja}:{fila}: faltan Partida o Descripción completa para el Excel final")
            if final:
                if (codigo_salida in descripciones_finales
                        and descripciones_finales[codigo_salida] != descripcion_salida):
                    raise ValueError(f"{hoja}:{fila}: Código {codigo_salida!r} con descripciones distintas; revisar conflicto")
                descripciones_finales[codigo_salida] = descripcion_salida
            valores = [ruta, codigo_salida, auxiliar,
                       descripcion_salida, r["descripcion"],
                       catalogo_sql["unidad_catalogo"] if catalogo_sql else r["unidad"], cantidad, 4]
            if catalogo_sql and len(catalogo_sql["Codigo"]) > 20:
                observaciones.append("Código de ConstruBase supera 20 caracteres; no se recortó")
        numero = escribir(catalogo, valores)
        # Seis columnas del manual; el nombre de un encabezado va en descripción auxiliar.
        escribir(copiar, [valores[0], valores[1], valores[2],
                          valores[4] if tipo == "concepto" else valores[3], valores[5], valores[6]])
        manual = b.get('sin_matriz') if tipo == 'concepto' and b else None
        escribir(revision, [hoja, fila, numero, tipo, r.get("padre", padre), r["partida"],
                            r["subpartida"], estado_revision, r["cantidad"],
                            "; ".join(observaciones), json.dumps(r.get("evidencia", {}), ensure_ascii=False),
                            r["unidad"], catalogo_sql["IdCodigo"] if catalogo_sql else None,
                            seleccion["revisor"] if seleccion else (manual['revisor'] if manual else None),
                            seleccion["motivo"] if seleccion else (manual['motivo'] if manual else (b.get("evaluacion_ia", {}).get("motivo") if tipo == "concepto" and b else None)),
                            seleccion["verificado_utc"] if seleccion else None])
        for h in (catalogo, copiar):
            if tipo != "concepto":
                for celda in h[numero]:
                    celda.fill = PatternFill("solid", fgColor="DCE6F1" if tipo == "partida" else "E8EDF2")
                    celda.font = Font(name="Arial", size=10, bold=True)
    for hoja, anchos, cabecera in (
            (catalogo, [22, 20, 22, 72, 72, 12, 16, 9], 1),
            (copiar, [22, 20, 22, 72, 12, 16], 1),
            (revision, [18, 12, 12, 14, 16, 20, 22, 35, 20, 65, 65, 16, 20, 24, 65, 30], 3)):
        hoja.sheet_view.showGridLines = False
        hoja.freeze_panes = f"D{cabecera + 1}"
        if hoja == revision:
            hoja.auto_filter.ref = f"A3:P{hoja.max_row}"
        for celda in hoja[cabecera]:
            celda.fill = PatternFill("solid", fgColor="284B63")
            celda.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        hoja.row_dimensions[cabecera].height = 32
        for c, ancho in enumerate(anchos, 1):
            hoja.column_dimensions[get_column_letter(c)].width = ancho
        for n in range(cabecera + 1, hoja.max_row + 1):
            lineas = max(sum(max(1, (len(t) + int(anchos[c - 1]) - 1) // int(anchos[c - 1]))
                             for t in str(hoja.cell(n, c).value or "").split("\n"))
                         for c in range(1, len(anchos) + 1))
            hoja.row_dimensions[n].height = min(409, max(24, lineas * 16 + 8))
        hoja.print_title_rows = f"1:{cabecera}"
    for coordenada in ("E1", "B2"):
        revision[coordenada].alignment = Alignment(vertical="center", wrap_text=False)
    revision.row_dimensions[1].height = 28
    revision.row_dimensions[2].height = 28
    return libro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presupuesto", help="JSON interpretado, opcionalmente con búsquedas")
    parser.add_argument("--salida", required=True, help="Archivo .xlsx nuevo")
    parser.add_argument("--final", action="store_true", help="Exige decisiones resueltas y códigos; conserva cliente cuando no hay matriz")
    args = parser.parse_args()
    origen, destino = Path(args.presupuesto), Path(args.salida)
    if destino.suffix.lower() != ".xlsx":
        parser.error("La salida debe ser .xlsx")
    # Una salida nueva impide reemplazar el Excel original o cualquier otro archivo.
    if destino.exists() or destino.is_symlink() or origen.resolve() == destino.resolve():
        parser.error("La salida debe ser un archivo nuevo; no se sobrescriben entradas ni resultados")
    informe = destino.with_suffix(".md")
    if informe.exists() or informe.is_symlink() or informe.resolve() == origen.resolve():
        parser.error("El reporte .md también debe ser nuevo y distinto de la entrada")
    datos = json.loads(origen.read_text(encoding="utf-8"))
    contenido = reporte(datos, final=args.final)
    libro = crear_excel(datos, final=args.final)
    confirmadas = libro["Revisión"]["D1"].value
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destino.open("xb") as archivo:
            libro.save(archivo)
    finally:
        libro.close()
    with informe.open("x", encoding="utf-8") as archivo:
        archivo.write(contenido)
    print(f"Excel y reporte generados; {confirmadas} selecciones verificadas (origen IA/humano en Revisión)")


if __name__ == "__main__":
    main()
