"""Ordena candidatos de ConstruBase sin modificar la base de datos.

Reglas conservadoras: nunca se inventan precios ni se descartan resultados.
"""
import re
import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def caracteristicas(texto):
    t = normalizar(texto)
    plano = bool(re.search(r"\b(planos?|elaboracion de plano)\b", t))
    topografia = bool(re.search(r"\btopograf\w*|\bequipo top\b", t))
    manual = bool(re.search(r"\bmanual\b", t))
    hasta = re.search(r"\bhasta\s+([\d,.]+)\s*m\s*(?:2|²|cuadrados)?", t)
    mayor = re.search(r"\b(?:mayor a|mas de|superior a|>\s*)\s*([\d,.]+)\s*m\s*(?:2|²|cuadrados)?", t)
    def numero(m):
        return float(m.group(1).replace(",", "")) if m else None
    return dict(plano=plano, topografia=topografia, manual=manual,
                hasta=numero(hasta), mayor=numero(mayor))


def ordenar_candidatos(consulta, candidatos):
    """Devuelve copias ordenadas, con puntaje y advertencias explicables."""
    pedido = caracteristicas(consulta)
    palabras = set(re.findall(r"[a-z0-9]+", normalizar(consulta)))
    palabras -= {"de", "y", "con", "para", "en", "el", "la", "los", "las", "hasta", "m2", "equipo"}
    salida = []
    for candidato in candidatos:
        item = dict(candidato)
        descripcion = item.get("DescripcionLarga") or item.get("Descripcion") or ""
        encontrado = caracteristicas(descripcion)
        vocabulario = set(re.findall(r"[a-z0-9]+", normalizar(descripcion)))
        puntos = len(palabras & vocabulario)
        razones = []
        advertencias = []
        for atributo, etiqueta in (("topografia", "equipo topográfico"), ("manual", "trabajo manual")):
            if pedido[atributo]:
                if encontrado[atributo]:
                    puntos += 5
                    razones.append("Coincide: " + etiqueta)
                else:
                    puntos -= 5
                    advertencias.append("No menciona " + etiqueta)
        if pedido["plano"]:
            if encontrado["plano"]:
                puntos += 5
                razones.append("Incluye elaboración de plano")
            else:
                puntos -= 5
                advertencias.append("No menciona elaboración de plano")
        elif encontrado["plano"]:
            puntos -= 2
            advertencias.append("Incluye plano, aunque no se solicitó")
        if pedido["hasta"] is not None:
            if encontrado["hasta"] == pedido["hasta"]:
                puntos += 8
                razones.append("Coincide límite de superficie")
            elif encontrado["mayor"] is not None and encontrado["mayor"] >= pedido["hasta"]:
                puntos -= 8
                advertencias.append("Indica superficie mayor, no hasta el límite solicitado")
            elif encontrado["hasta"] is not None:
                puntos -= 3
                advertencias.append("Límite de superficie diferente")
            else:
                advertencias.append("Sin límite de superficie explícito")
        item["puntaje"] = puntos
        item["razones"] = razones
        item["advertencias"] = advertencias
        salida.append(item)
    return sorted(salida, key=lambda x: (-x["puntaje"], str(x.get("Codigo", ""))))
