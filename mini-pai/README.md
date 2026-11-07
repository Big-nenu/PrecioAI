# Mini-PAI

Mini-PAI es el primer producto de [PrecioAI (PAI)](../README.md). Ahorra la captura y el acomodo manual de presupuestos: recibe un Excel de un cliente, identifica sus conceptos, busca matrices de ConstruBase y entrega un `.xlsx` para copiar y pegar manualmente en Neodata PU Win+, acompañado de un reporte `.md`.

**Experiencia objetivo:** «Analiza este presupuesto» → procesamiento → preguntas sobre casos dudosos → elecciones del usuario → Excel y reporte. El usuario no debe conocer Python, diseñar consultas SQL, acomodar columnas ni corregir al asistente por chat. Este es el comportamiento que debe alcanzarse; el prototipo todavía necesita validación de extremo a extremo.

## Qué debe hacer

1. **Inspeccionar el archivo completo.** Revisar todas las hojas y filas con datos, identificar el catálogo y declarar el alcance procesado. Separar conceptos, partidas, subpartidas, metadatos, notas y totales. Identificar explícitamente cualquier muestra o ejecución parcial.
2. **Interpretar estructuras variables mediante IA y herramientas.** Identificar celdas de código, descripción, unidad y cantidad sin exigir nombres, posiciones o vocabularios propios de un cliente. Python recupera los valores originales desde esa evidencia; el modelo no debe reescribir cantidades ni reconstruir descripciones.
3. **Conservar datos y jerarquía.** Mantener códigos, descripciones completas, unidades, cantidades y relaciones entre partidas y subpartidas. Rastrear cada registro hasta archivo, hoja, fila y celdas. Un agrupador no cuenta como concepto y un total no se convierte en cantidad.
4. **Buscar matrices reales.** La IA identifica actividad principal y atributos técnicos explícitos y prepara búsquedas de palabras clave y variantes. No buscar la descripción completa como una cadena exacta. Reutilizar el buscador SQL de ConstruBase exclusivamente en lectura.
5. **Comparar técnicamente.** Evaluar materiales, procedimientos, dimensiones, espesores, resistencias, alcances y unidades. Distinguir redacción equivalente, información no mencionada y diferencias reales. Similitud textual, misma unidad o confianza declarada no bastan para aprobar.
6. **Resolver lo justificable y preguntar las dudas.** Una equivalencia automática necesita motivo, evidencia y validaciones. En pendientes, presentar hasta tres candidatos pertinentes con código, descripción completa, unidad y diferencias, más la opción **4: Conservar concepto original — sin matriz de ConstruBase**. Esperar la elección real; las preguntas pueden reunirse al final.
7. **Verificar selecciones en SQL.** Recuperar nuevamente código real, descripción íntegra y unidad de cada matriz elegida. No inventar información de catálogo, resumirla ni modificar ConstruBase. Una unidad distinta no autoriza convertir cantidades automáticamente.
8. **Entregar Excel y reporte.** Conservar jerarquía y formato comprobado. Distinguir matrices seleccionadas por IA o usuario, conservación manual, búsquedas sin candidatos y errores. Un fallo de búsqueda no demuestra ausencia de matrices.

## Reglas de integridad del producto

- Mantener intactos el presupuesto original y ConstruBase; guardar resultados en rutas nuevas.
- Conservar unidos los campos de cada concepto: nunca asignar cantidades o importes de otro renglón por aparecer cerca en el documento o en un resumen.
- Informar conteos reales y exclusiones con evidencia; no reutilizar cifras ni decisiones de conversaciones anteriores.
- **Un código principal identifica una sola descripción completa en el catálogo entregado.** Si el mismo código aparece con descripciones distintas, señalar y resolver el conflicto antes de la entrega final. No renombrar códigos ni fusionar conceptos silenciosamente. Repetir código y descripción idénticos en distintas partidas no es por sí solo ese conflicto.
- Si falta código del cliente y se conserva sin matriz, solicitarlo y registrar la respuesta separadamente del original.
- No forzar equivalencias para aumentar las selecciones. Diferencias e información insuficiente requieren revisión.
- No presentar un borrador o una ejecución parcial como presupuesto final. No exportar si el usuario lo ha prohibido.

Son condiciones de aceptación, no una afirmación de que todas estén verificadas hoy. La guarda del exportador final también rechaza códigos con descripciones distintas entre originales conservados y matrices seleccionadas; permite repetir código y descripción idénticos. Cobertura completa y comportamiento autónomo siguen pendientes de validación.

## Formato de salida

**Se conserva el formato que el usuario ya probó al copiar y pegar en Neodata.** La hoja `Catálogo` contiene:

```text
Partida | Código | Código auxiliar | Descripción completa | Descripción auxiliar | Unidad | Cantidad | Tipo
```

| Campo | Con matriz seleccionada y verificada | Sin matriz tras búsqueda válida vacía o elección de conservar |
| --- | --- | --- |
| Partida | Ruta de la jerarquía original | Misma jerarquía |
| Código | Código real de ConstruBase | Código original del cliente, o proporcionado explícitamente si faltaba |
| Código auxiliar | Código original del cliente | Código original del cliente, cuando exista |
| Descripción completa | Texto íntegro y original de ConstruBase | Texto íntegro y original del cliente |
| Descripción auxiliar | Texto íntegro y original del cliente | Texto íntegro y original del cliente |
| Unidad | Unidad validada de la matriz; conservar y señalar la del cliente si difiere | Unidad original del cliente |
| Cantidad | Cantidad original del cliente, sin conversión automática | Cantidad original del cliente |
| Tipo | Convención del exportador existente; conceptos tipo 4 | Misma convención |

Los nombres de las partidas y subpartidas se conservan en sus filas de agrupación. La cantidad no se sustituye por precio unitario, importe, subtotal o IVA. Las cantidades ambiguas se señalan, sin adivinarlas.

Para el copiado indicado por el usuario son obligatorios **Partida, Código y Descripción completa**. Unidad, Cantidad y auxiliares también se conservan cuando existen. Un concepto final sin matriz no debe quedar con Código o Descripción completa vacíos. Esto no cambia el tratamiento de encabezados del formato probado.

El libro conserva además `Copiar auxiliares`, con `Partida | Código | Código auxiliar | Descripción auxiliar | Unidad | Cantidad`, y `Revisión`, con trazabilidad y advertencias. La referencia de seis columnas procede del Manual PUWIN+ citado en el historial; la de ocho, del catálogo de ejemplo y la prueba manual del usuario. No se intercambian códigos ni descripciones de cliente y catálogo.

El Markdown distingue:

- **Con matriz:** código real, procedencia de la elección y justificación disponible.
- **Conservados por elección:** el usuario decidió no utilizar ninguna matriz.
- **Sin candidatos en la búsqueda realizada:** original conservado; no prueba ausencia en todo ConstruBase.
- **Errores y pendientes:** no se ocultan como resultados resueltos o ausencia de coincidencias.

## Estado real

| Componente | Implementado | Límite actual |
| --- | --- | --- |
| Inspección | Lectura de hojas y celdas sin columnas fijas | Inspeccionar no equivale a identificar todos los conceptos |
| Interpretación | Ruta tabular comprobada en dos originales; bloques conservados; evidencia y jerarquía | Ruta tabular limitada a una tabla estable; otros formatos y bloques pendientes |
| Recuperación | Consultas propuestas por IA, SQL parametrizado y candidatos revisables | AND/LIKE y ranking limitado pueden dejar fuera matrices útiles |
| Comparación | Nemotron, evidencia técnica, validaciones y verificación SQL | Casos dudosos requieren revisión; no garantiza equivalencia universal |
| Revisión | Hasta tres candidatos admisibles y conservar original; decisiones auditadas | No existe todavía interfaz sencilla para el ingeniero |
| Entrega | Excel y Markdown con selecciones IA/humanas y originales | Copiado probado; conflictos de descripción protegidos; flujo autónomo pendiente |

En la revisión actual pasaron **172 pruebas automatizadas** mediante `python -m unittest discover -q`, sin IA ni SQL en vivo. No sustituyen las pruebas reales de extracción y decisiones.

La corrección de metadatos, clasificación por bloques y jerarquía sobre archivos originales se documenta en [ORIGINALES.md](ORIGINALES.md). Las pruebas funcionales conservan originales por elección del usuario y se distinguen de una aprobación técnica de matrices.

La [auditoría inicial](AUDITORIA-EXTRACCION.md) reprodujo fallos de clasificación y campos omitidos en la ruta por bloques. La nueva [extracción tabular](EXTRACCION-TABULAR.md), activada con `--por-tabla`, recuperó **78 conceptos, 15 agrupadores y 312 campos sin diferencias** respecto al Excel. Tardó **39.467 s** y tres llamadas con un reintento, solo interpretación, sin SQL ni exportación.

La IA identifica cabeceras y agrupadores; Python recupera los campos completos desde columnas identificadas para ese documento. No hay letras fijas ni vocabulario de un cliente. La ruta anterior permanece para no alterar otros formatos sin comprobarlos. El nuevo modo requiere una tabla estable, cabeceras de descripción/unidad/cantidad entre las primeras 20 filas no vacías y revisión en formatos nuevos. No está validado para continuaciones entre filas o cambios de columnas.

La skill instalada de Cline se sincronizó con la versionada. Su conversación completa todavía no se ha probado; los resultados anteriores proceden de ejecución nativa de los módulos.

### Mediciones anteriores

| Prueba con Nemotron local | Tiempo medido | Límite |
| --- | ---: | --- |
| Tres conceptos con candidatos guardados | Aproximadamente 88 s | Excluye interpretación y búsqueda desde cero |
| Primera muestra de veinte | 751.951 s, aproximadamente 12:32 | Incluye fallos; excluye espera por decisiones humanas |
| Comparación posterior de veinte | 349.760 s solo comparación | 17 conceptos con candidatos; no es un nuevo total ni prueba controlada de aceleración |

Pasadas, repeticiones y revalidaciones están en el [historial](historial/README-2026-11-06.md) y [CONTINUIDAD.md](CONTINUIDAD.md). Revalidar respuestas guardadas no cuenta como inferencia nueva; elecciones delegadas a Codex no cuentan como decisiones automáticas de Nemotron.

### Modelos

**Nemotron sigue como principal.** La [comparación real con Gemma](PRUEBA-MODELOS.md) ejecutada por el usuario favoreció a Nemotron en esta muestra: extracción completa frente a fallo, y menor tiempo técnico. Las propuestas todavía requieren validación semántica; no son equivalencias certificadas.

Los ensayos exploratorios de Nemotron, D1 y TEV1 están en [EVALUADORES.md](EVALUADORES.md); no justifican sustituirlo. Las herramientas del [laboratorio](LABORATORIO.md) permiten comparar recuperación y decisiones por separado.

Se ejecutaron [pruebas separadas de embeddings, índice persistente y D1/D3 frente a Nemotron](PRUEBA-RECUPERACION-DECISIONES.md). EmbeddingGemma 270m recuperó más referencias útiles que Qwen en la muestra de 20 conceptos contra 19,418 registros. La ruta [mini_pai_buscar.py --indice](BUSQUEDA.md) ya conecta ese índice al selector existente, conservando Nemotron y la revalidación SQL. Ver [prueba integrada y límites](INTEGRACION-INDICE.md). Las decisiones rápidas no sustituyen las guardas técnicas ni la revisión de dudas.

La [corrección de acción principal](ACCION-PRINCIPAL.md) hizo que Nemotron rechazara por sí mismo construir un cimiento frente a demolerlo. Cuatro controles de sinónimos/formulaciones compatibles conservaron selección; los diez negativos no se seleccionaron. Se alineó el esquema con las guardas existentes de procedimiento y alcance. El Excel revisado de la muestra conserva una propuesta SQL y 19 pendientes tras retirar también una propuesta de alcance limitado. Persisten inconsistencias de etiquetas e inclusiones; no se certifica la evaluación general.

## Desarrollo y uso actual

El [comando único mini_pai.py](FLUJO.md) coordina las etapas y permite continuar una sesión con decisiones parciales o conservar todos los originales, sin repetir etapas terminadas. Guarda estado y hashes en la carpeta de sesión. Es una herramienta local por terminal; los límites del intérprete y del selector siguen vigentes.

Para el catálogo tabular completo usar primero [la ruta --por-tabla](EXTRACCION-TABULAR.md). Los comandos por bloques de esta sección conservan el comportamiento anterior y no sustituyen la nueva comprobación.

Los módulos siguen en la raíz: [mapa del código](../docs/ESTRUCTURA.md). La [skill versionada](../skills/analizar-presupuesto/SKILL.md) forma parte de las instrucciones y contratos; no es un servidor MCP ni garantiza obediencia del asistente.

Desde la raíz, crear una carpeta nueva para cada ejecución y usar las etapas existentes:

```powershell
New-Item -ItemType Directory -Path salidas/ejecucion-001
python mini_pai_interpretar.py "ruta/al/presupuesto.xlsx" --salida salidas/ejecucion-001/interpretacion.json
python mini_pai_claves.py salidas/ejecucion-001/interpretacion.json --salida salidas/ejecucion-001/candidatos.json
python mini_pai_seleccionar.py salidas/ejecucion-001/candidatos.json --salida salidas/ejecucion-001/evaluacion.json
python mini_pai_revision.py salidas/ejecucion-001/evaluacion.json --salida salidas/ejecucion-001/opciones.md
```

Para la recuperación semántica, sustituir el comando `mini_pai_claves.py` por `mini_pai_buscar.py ... --indice ruta/al/indice.sqlite --salida ...`, usando la interpretación sin búsquedas previas. No ejecutar las dos rutas sobre la misma salida. La [guía de búsqueda](BUSQUEDA.md) explica creación y reutilización del índice.

Revisar alcance y salidas entre etapas. Después de recibir decisiones reales, usar `mini_pai_confirmar.py` según [GUIA-CLINE.md](GUIA-CLINE.md). Con el JSON resuelto:

```powershell
python mini_pai_exportar.py salidas/ejecucion-001/resuelto.json --final --salida salidas/ejecucion-001/presupuesto.xlsx
python -m unittest discover -v
```

El exportador entrega también `presupuesto.md`. Existe un coordinador reanudable, pero **el uso autónomo sobre presupuestos diversos todavía requiere validar la extracción y las decisiones**. La guía de Cline sirve para desarrollo y pruebas, no es la interfaz final. Ver [FLUJO.md](FLUJO.md).

Más detalle: [búsqueda SQL](BUSQUEDA.md), [guía de Cline](GUIA-CLINE.md), [continuidad y procedencia](CONTINUIDAD.md).

## Próximo trabajo, por orden

1. Mantener comprobaciones de extracción y jerarquía sobre los originales. Los resultados actuales y su alcance están en [ORIGINALES.md](ORIGINALES.md); nuevos formatos todavía requieren referencia.
2. Exponer el coordinador mediante un MCP mínimo para que distintos agentes lo utilicen sin depender de Cline. Sigue pendiente; no duplicar la lógica de los módulos existentes.
3. Mantener los controles de integridad y resolver las inconsistencias técnicas conocidas del selector antes de confiar en equivalencias automáticas generales. Conservar originales prueba el flujo, no certifica matrices.
4. Ampliar las referencias expertas y comprobar nuevas entregas y su pegado, conservando el modelo y las guardas actuales.
5. Cuando el flujo sea confiable, preparar la interfaz familiar; después abordar acceso web para otros usuarios y suscripciones.

## Fuera del trabajo inmediato

No controlar Neodata ni automatizar su importación. No modificar ConstruBase, construir matrices nuevas, procesar PDF, implementar cobros ni desarrollar PAI completo o infraestructura web ahora. Esas ampliaciones requieren definición y pruebas propias.

Los cambios continúan en el [PR #3](https://github.com/Big-nenu/PrecioAI/pull/3), para revisión y sin fusión automática.
