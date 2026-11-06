# Skill: analizar-presupuesto

## Objetivo
Comprender presupuestos de obra heterogéneos (Excel o PDF) y preparar búsquedas de conceptos técnicamente compatibles en ConstruBase. No asumir columnas, claves ni partidas fijas.

## Procedimiento del agente
1. Inspeccionar el documento con las herramientas disponibles y detectar hojas, tablas, encabezados y estructura real.
2. Identificar descripciones, unidades y cantidades. Claves y partidas son opcionales; si faltan, dejar valores nulos, nunca inventarlos.
3. Mantener trazabilidad por archivo, hoja/página y fila o región. Conservar cada renglón aunque se repita una clave.
4. Señalar campos dudosos para revisión humana, sin detener los registros claros.
5. Para cada concepto, extraer características técnicas y buscar candidatos reales mediante herramientas SQL de solo lectura.
6. Comparar alcance, material, método, dimensiones, espesor, resistencia, unidad y
   condiciones de hasta cinco candidatos recuperados. Separar compatibles,
   incompatibles e insuficientes; no rellenar ni fabricar coincidencias.
7. En la selección inteligente de Mini-PAI, elegir mediante IA solo equivalencias
   técnicamente justificadas con evidencia y verificación SQL. Reservar la revisión
   humana para diferencias, dudas o información insuficiente. Nunca modificar ConstruBase.

## Interpretación técnica para búsqueda
- Antes de consultar ConstruBase, identificar la actividad principal y los atributos
  relevantes que realmente aparecen en la descripción/unidad. Sus nombres son
  abiertos: no depender de columnas, vocabularios o filtros específicos de un cliente.
- Respaldar cada atributo con una cita de su campo. Un número debe conservar su
  contexto: resistencia, espesor, dimensión u otro significado; no convertir una
  cantidad de presupuesto en una especificación técnica. Ausente significa desconocido.
- Proponer consultas breves de palabras clave y variantes semánticas. Priorizar
  las específicas con atributos explícitos y conservar una alternativa amplia
  de actividad. No buscar la descripción completa ni exigir todas sus inclusiones.
- Comparar la unidad por separado; no asumir que está escrita en la descripción
  del catálogo. No inventar métodos: «por cualquier medio» no significa «manual».
- Estas consultas recuperan candidatos a matriz base, no certifican equivalencia
  ni garantizan inclusiones. No cambiar los códigos o descripciones originales.

## Criterio de comparación técnica (etapa 2)
- Separar tres situaciones en el motivo: REDACCION_EQUIVALENTE, NO_MENCIONADO y
  DIFERENCIA_REAL. No mezclar ausencia de información con contradicción.
- REDACCION_EQUIVALENTE: dos expresiones acreditan la misma función técnica.
  Si ambos textos son de trazo y nivelación con equipo topográfico, «cuadrilla de
  topografía» acredita la función de «personal técnico calificado» de ese trabajo,
  y establecer ejes de referencia acredita la función de localizar entre ejes.
  No listar esas funciones como ausentes solo por la redacción.
  Explicar la correspondencia apoyada en ambos textos, sin exigir palabras idénticas.
- Una formulación permisiva no exige todos los procedimientos: «por cualquier
  medio» admite un método manual o con maquinaria compatible con el resto del trabajo.
- NO_MENCIONADO: el texto no acredita una inclusión concreta. No afirmar que está
  excluida, ni garantizar que está incluida. Una referencia general a materiales
  no demuestra por sí sola estacas o mojoneras, ni excavar demuestra por sí solo
  afine de taludes, traspaleos o acarreos. Si esa prestación expresa es necesaria
  para la sustitución y no está acreditada, dejar insuficiente y nombrar la duda.
- Tener recursos no acredita ejecutar una prestación: «mano de obra, maquinaria
  y equipo» no demuestra afine, traspaleos, movimientos o acarreos. La comparación
  del alcance debe cubrir también las actividades expresas adicionales al trabajo
  principal; no basta acreditar solo ese trabajo principal.
- Una lista parcial de recursos tampoco acredita los que faltan: mencionar fletes,
  equipo o herramienta no garantiza materiales de consumo expresamente solicitados.
  No sustituir esa comprobación por «incluye los recursos necesarios».
- DIFERENCIA_REAL: ambos textos acreditan especificaciones contradictorias que
  impiden la sustitución, como piedra frente a concreto armado o espesores de
  6 frente a 5 cm. No compensarlas con misma unidad, similitud o confianza.
- Una actividad expresada semánticamente de otra manera no es una inclusión
  omitida: justificar su correspondencia. Esto no acredita otras prestaciones,
  materiales, certificaciones, costos o recursos que no aparecen en los textos.

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
- En bloques, emitir solo las filas objetivo. Reutilizar los encabezados vigentes
  como padres de solo lectura, sin duplicarlos. La anticipación solo aporta
  evidencia de continuaciones; no emitir sus filas como registros independientes.

## Herramientas previstas (aún no conectadas al agente)
- Inspección de Excel y PDF sin estructura fija.
- Búsqueda de conceptos en ConstruBase.
- Consulta de matrices y subanálisis.
- Exportación del presupuesto elegido.

## Estado
`mini_pai_interpretar.py` usa esta skill y `proveedor_ia.py` para una interpretación
revisable de Excel con evidencia y validación determinista. No hay agente con
llamadas autónomas a herramientas. Existe procesamiento por bloques con contexto
de padres; siguen pendientes su validación sobre libros completos y documentos diversos.
`mini_pai_seleccionar.py` reutiliza esta skill y herramientas deterministas para
comparar candidatos completos, recuperar evidencia por fragmentos y comprobar en
SQL las selecciones IA. No cambia el formato Excel ya comprobado por el usuario.
