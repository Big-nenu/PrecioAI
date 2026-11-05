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

## Interpretación de catálogo en Mini-PAI (etapa 1)
- Conservar cada encabezado de agrupación como partida o subpartida, aunque no
  tenga unidad ni cantidad. Distinguirlo de portada, títulos, totales y notas.
- Identificar el padre por hoja y fila original, incluso cuando no haya clave
  o se repitan claves. No invertir los niveles ni arrastrar una subpartida al
  cambiar de partida. Reportar jerarquías más profundas o ambiguas.
- Seleccionar celdas como evidencia; las herramientas recuperan el texto y
  cantidades originales. No volver a escribir o normalizar sus valores.
- Explicar cada fila excluida; no convertir metadatos en conceptos para cubrir
  todas las filas. Usar el contrato de salida indicado por la herramienta.
- Durante esta etapa no ejecutar los pasos 5–7 de búsqueda y selección SQL.

## Herramientas previstas (aún no conectadas al agente)
- Inspección de Excel y PDF sin estructura fija.
- Búsqueda de conceptos en ConstruBase.
- Consulta de matrices y subanálisis.
- Exportación del presupuesto elegido.

## Estado
`mini_pai_interpretar.py` usa esta skill y `proveedor_ia.py` para una interpretación
revisable de Excel con evidencia y validación determinista. No hay agente con
llamadas autónomas a herramientas; siguen pendientes la integración SQL, el
procesamiento de libros completos por bloques y pruebas con documentos diversos.
