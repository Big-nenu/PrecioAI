"""Cálculos aislados para validar reglas de importes de ConstruBase.

No presupone cuál política de redondeo utiliza Neodata.
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP


REDONDEOS = {"normal": ROUND_HALF_UP, "arriba": ROUND_UP}


def calcular_importe(costo, volumen, dividir=False, redondeo="normal"):
    """Devuelve importe con dos decimales, usando Decimal y sin flotantes."""
    if redondeo not in REDONDEOS:
        raise ValueError("Redondeo desconocido")
    costo = Decimal(str(costo))
    volumen = Decimal(str(volumen))
    if dividir and volumen == 0:
        raise ValueError("No se puede dividir entre cero")
    bruto = costo / volumen if dividir else costo * volumen
    return bruto.quantize(Decimal("0.01"), rounding=REDONDEOS[redondeo])
