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

Son condiciones de aceptación, no una afirmación de que todas estén verificadas hoy. La guarda existente detecta códigos de matrices seleccionadas con distinta descripción o unidad; falta comprobar el conflicto general incluyendo originales conservados. Cobertura completa y comportamiento autónomo siguen pendientes de validación.

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
| Interpretación | IA por bloques, evidencia, materialización y validación de jerarquía | Falta comprobar presupuestos completos y formatos diversos |
| Recuperación | Consultas propuestas por IA, SQL parametrizado y candidatos revisables | AND/LIKE y ranking limitado pueden dejar fuera matrices útiles |
| Comparación | Nemotron, evidencia técnica, validaciones y verificación SQL | Casos dudosos requieren revisión; no garantiza equivalencia universal |
| Revisión | Hasta tres candidatos admisibles y conservar original; decisiones auditadas | No existe todavía interfaz sencilla para el ingeniero |
| Entrega | Excel y Markdown con selecciones IA/humanas y originales | Copiado probado; flujo autónomo y conflictos pendientes |

Tras esta reorganización pasaron las mismas **127 pruebas automatizadas** mediante `python -m unittest discover -q`, sin IA ni SQL en vivo. No sustituyen las pruebas reales de extracción y decisiones.

En la prueba asistida del presupuesto de **78 conceptos**, el resumen de Cline atribuyó a un concepto la cantidad e importe de otro. Falta cotejar sus resultados estructurados para ubicar el error. **No está demostrado que la mezcla provenga del extractor Python**, ni basta cambiar el prompt para considerarla resuelta.

### Mediciones anteriores

| Prueba con Nemotron local | Tiempo medido | Límite |
| --- | ---: | --- |
| Tres conceptos con candidatos guardados | Aproximadamente 88 s | Excluye interpretación y búsqueda desde cero |
| Primera muestra de veinte | 751.951 s, aproximadamente 12:32 | Incluye fallos; excluye espera por decisiones humanas |
| Comparación posterior de veinte | 349.760 s solo comparación | 17 conceptos con candidatos; no es un nuevo total ni prueba controlada de aceleración |

Pasadas, repeticiones y revalidaciones están en el [historial](historial/README-2026-11-06.md) y [CONTINUIDAD.md](CONTINUIDAD.md). Revalidar respuestas guardadas no cuenta como inferencia nueva; elecciones delegadas a Codex no cuentan como decisiones automáticas de Nemotron.

### Modelos

**Nemotron sigue como principal.** Los ensayos exploratorios de Nemotron, D1 y TEV1 están en [EVALUADORES.md](EVALUADORES.md); no justifican sustituirlo. Las herramientas del [laboratorio](LABORATORIO.md) permiten comparar recuperación y decisiones por separado.

Falta evaluar la combinación propuesta de embeddings, D1/D3 y Nemotron sobre los mismos conceptos y candidatos, midiendo calidad, tiempo y memoria. Tener modelos descargados no equivale a tenerlos integrados o probados en este flujo. Cambiar modelos no sustituye corregir errores de integridad.

## Desarrollo y uso actual

Los módulos siguen en la raíz: [mapa del código](../docs/ESTRUCTURA.md). La [skill versionada](../skills/analizar-presupuesto/SKILL.md) forma parte de las instrucciones y contratos; no es un servidor MCP ni garantiza obediencia del asistente.

Desde la raíz, crear una carpeta nueva para cada ejecución y usar las etapas existentes:

```powershell
New-Item -ItemType Directory -Path salidas/ejecucion-001
python mini_pai_interpretar.py "ruta/al/presupuesto.xlsx" --salida salidas/ejecucion-001/interpretacion.json
python mini_pai_claves.py salidas/ejecucion-001/interpretacion.json --salida salidas/ejecucion-001/candidatos.json
python mini_pai_seleccionar.py salidas/ejecucion-001/candidatos.json --salida salidas/ejecucion-001/evaluacion.json
python mini_pai_revision.py salidas/ejecucion-001/evaluacion.json --salida salidas/ejecucion-001/opciones.md
```

Revisar alcance y salidas entre etapas. Después de recibir decisiones reales, usar `mini_pai_confirmar.py` según [GUIA-CLINE.md](GUIA-CLINE.md). Con el JSON resuelto:

```powershell
python mini_pai_exportar.py salidas/ejecucion-001/resuelto.json --final --salida salidas/ejecucion-001/presupuesto.xlsx
python -m unittest discover -v
```

El exportador entrega también `presupuesto.md`. **No existe todavía una orquestación única validada** que complete el proceso sin supervisión técnica. La guía de Cline sirve para desarrollo y pruebas, no es la interfaz final.

Más detalle: [búsqueda SQL](BUSQUEDA.md), [guía de Cline](GUIA-CLINE.md), [continuidad y procedencia](CONTINUIDAD.md).

## Próximo trabajo, por orden

1. Auditar inspección → interpretación → datos guardados en el presupuesto actual. Comprobar cobertura, jerarquía y correspondencia de celdas; localizar y corregir la mezcla antes de confiar en búsquedas posteriores.
2. Comprobar las reglas de integridad pendientes, especialmente códigos con descripciones distintas, e implementar únicamente las validaciones que falten.
3. Ejecutar una prueba completa reproducible con decisiones humanas reales, Excel y reporte; medir cada etapa y revisar el pegado.
4. Comparar los modelos pendientes sin sustituir Nemotron hasta demostrar mejora; conservar controles de incompatibilidades reales.
5. Cuando el flujo sea confiable, preparar la interfaz familiar; después abordar acceso web para otros usuarios y suscripciones.

## Fuera del trabajo inmediato

No controlar Neodata ni automatizar su importación. No modificar ConstruBase, construir matrices nuevas, procesar PDF, implementar cobros ni desarrollar PAI completo o infraestructura web ahora. Esas ampliaciones requieren definición y pruebas propias.

Los cambios continúan en el [PR #3](https://github.com/Big-nenu/PrecioAI/pull/3), para revisión y sin fusión automática.
