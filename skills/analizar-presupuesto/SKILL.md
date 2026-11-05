# Skill: analizar-presupuesto

## Objetivo
Comprender presupuestos de obra heterogéneos (Excel o PDF) y preparar búsquedas de conceptos técnicamente compatibles en ConstruBase. No asumir columnas, claves ni partidas fijas.

## Procedimiento del agente
1. Inspeccionar el documento con las herramientas disponibles y detectar hojas, tablas, encabezados y estructura real.
2. Identificar descripciones, unidades y cantidades. Claves y partidas son opcionales; si faltan, dejar valores nulos, nunca inventarlos.
3. Mantener trazabilidad por archivo, hoja/página y fila o región. Conservar cada renglón aunque se repita una clave.
4. Señalar campos dudosos para revisión humana, sin detener los registros claros.
5. Para cada concepto, extraer características técnicas y buscar candidatos reales mediante herramientas SQL de solo lectura.
6. Comparar alcance, material, método, unidad y condiciones; mostrar hasta cinco candidatos válidos, sin rellenar ni fabricar coincidencias.
7. Esperar selección del usuario antes de asociar una matriz; nunca modificar ConstruBase.

## Herramientas previstas (aún no conectadas al agente)
- Inspección de Excel y PDF sin estructura fija.
- Búsqueda de conceptos en ConstruBase.
- Consulta de matrices y subanálisis.
- Exportación del presupuesto elegido.

## Estado
Esta skill es una especificación inicial, no un agente operativo. El módulo `proveedor_ia.py` permite probar el modelo local o remoto; aún faltan orquestación, llamadas a herramientas y pruebas con documentos diversos.
