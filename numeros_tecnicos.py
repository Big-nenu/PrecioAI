"""Lectura numérica para evidencia técnica; nunca reescribe datos ni convierte unidades."""
from decimal import Decimal
from fractions import Fraction
import re


def numeros(texto):
    valores = set()
    patron = r'\d+(?:[.,]\d+)*(?:/\d+)?'
    for token in re.findall(patron, texto or ''):
        if '/' in token:
            try:
                valor = Fraction(token)
            except (ValueError, ZeroDivisionError) as exc:
                raise ValueError('Fracción técnica no interpretable; requiere revisión') from exc
        else:
            # Convención del presupuesto: comas agrupadas de miles, punto decimal.
            # Se admite coma decimal no agrupada y 0,xxx. No se interpreta punto de miles.
            if re.fullmatch(r'[1-9]\d{0,2}(?:,\d{3})+(?:\.\d+)?', token):
                token = token.replace(',', '')
            elif ',' in token:
                if token.count(',') != 1 or '.' in token:
                    raise ValueError('Formato numérico ambiguo; requiere revisión')
                token = token.replace(',', '.')
            try:
                valor = Fraction(Decimal(token))
            except ArithmeticError as exc:
                raise ValueError('Formato numérico no interpretable; requiere revisión') from exc
        valores.add(valor)
    return valores
