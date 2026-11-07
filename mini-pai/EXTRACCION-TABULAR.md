# Extracción tabular de Mini-PAI

## Qué cambia

La ruta `--por-tabla` evita pedir a la IA que vuelva a elegir cuatro celdas para cada concepto en bloques independientes:

1. Nemotron identifica la hoja y las celdas de encabezado que corresponden a código, descripción, unidad y cantidad.
2. Python comprueba que esas referencias existan en la cabecera y correspondan a columnas distintas. No hay letras de columna fijadas en el código.
3. Las filas con descripción, unidad y cantidad se recuperan desde sus propias celdas. La IA clasifica las filas restantes, incluyendo conceptos con campos ausentes, partidas, subpartidas, portada y notas. Recibe el contexto del documento y una vista compacta de la secuencia.
4. La IA identifica el comienzo del resumen final. Python exige una fila real posterior a todos los trabajos medidos y registra las exclusiones con esa evidencia.
5. Se reutilizan `materializar`, `validar` y la validación de jerarquía del intérprete existente. Todos los valores finales se recuperan del Excel original, completos.

No se cambian búsqueda SQL, comparación técnica, modelo, formato Excel ni columnas de salida. No hay dependencias nuevas. La skill de Cline indica cuándo utilizar esta ruta; las llamadas internas de cabeceras y grupos usan los contratos del módulo `mini_pai_tabla.py` y el proveedor existente.

## Resultado real comprobado

La ejecución nativa con `nemotron-3.5-bolt:e4b`, configuración local existente y el presupuesto de CATALOGO produjo:

| Comprobación | Resultado |
| --- | --- |
| Conceptos | **78**, los mismos que en el Excel |
| Partidas y subpartidas | **15**, con tipos y padres cotejados |
| Código, descripción, unidad y cantidad | **312 campos cotejados, cero diferencias** |
| Filas excluidas | **28**, con motivo; portada, cabecera, rótulo general y resumen/totales |
| Alcance | Hoja única completa; sin pérdida de conceptos |
| Original | SHA256 intacto |
| Tiempo de interpretación | **39.467 s**, tres llamadas, incluido un reintento |

Los padres de los 78 conceptos también se cotejaron contra los encabezados del archivo. Se conservaron las unidades compuestas, todas las cantidades y las descripciones completas. El reintento rechazó un rótulo general tratado como agrupador sin conceptos descendientes; no se inventaron trabajos para hacerlo pasar.

La medición corresponde a una ejecución de interpretación. **No incluye SQL, evaluación de matrices, decisiones humanas ni exportación** y no es una garantía de rendimiento. La ejecución anterior por bloques falló tras 285.779 s: no se presenta como una comparación entre dos ejecuciones completas exitosas.

Tras la medición se añadió una guarda específica para un texto de portada repetido como concepto sin medición y se volvió a validar el resultado guardado; esa revalidación no es inferencia nueva ni se contabiliza como tiempo de generación.

Pasaron **137 pruebas automatizadas**. Las ocho pruebas nuevas cubren campos íntegros en columnas reordenadas, cantidades de filas distintas, unidades compuestas, referencias falsas, columnas duplicadas, cortes que perderían conceptos medidos, cobertura de filas, padres inexistentes, agrupadores sin descendientes, metadatos de portada, campos realmente ausentes, otras hojas como alcance parcial, reintento y entrada por CLI. No sustituyen la prueba de más libros reales. El JSON real también pasó la validación de entrada del buscador y la creación del libro en memoria: 78 conceptos y las mismas ocho columnas, sin SQL ni escritura de un Excel nuevo.

## Uso

Desde la raíz, con una carpeta nueva:

```powershell
New-Item -ItemType Directory -Path salidas/tabla-001
python mini_pai_interpretar.py "ruta/al/presupuesto.xlsx" --por-tabla --salida salidas/tabla-001/interpretacion.json
```

El JSON conserva el contrato utilizado por `mini_pai_claves.py`, revisión, confirmación y exportación. Añade `estructura_tabla_ia` con las referencias de encabezado y el comienzo del resumen. No se ejecutan búsquedas ni se genera un Excel con este comando.

La ruta anterior por bloques conserva sus comandos y pruebas. El nuevo modo es explícito para no cambiar el comportamiento de las muestras y formatos anteriores sin validarlos.

## Límites

- Una tabla de columnas estables, con cabecera entre las primeras **20 filas no vacías** de la hoja.
- Deben poder reconocerse las columnas de descripción, unidad y cantidad. Algunos conceptos pueden carecer de esos valores; se conservan ausentes y se clasifican mediante IA. No se inventa un código faltante.
- No está validada para cambios de columnas, varias tablas en una hoja o descripciones repartidas entre varias filas; no debe darse por correcta en esos casos. Los saltos de línea dentro de una celda sí se conservan.
- Otras hojas con datos se declaran no procesadas y el alcance se marca parcial.
- Un agrupador sin conceptos descendientes o una ambigüedad que no se resuelva tras el reintento detiene la extracción; no se descarta silenciosamente.
- Los encabezados seleccionados por IA y las exclusiones requieren revisión en formatos nuevos. La existencia de una referencia no prueba por sí sola que su significado sea correcto.

## Evidencia y ensayos descartados

La evidencia privada está en `salidas/estructura-tablas-2026-11-07/ejecucion-02/`: respuestas por llamada, tiempos, `interpretacion.json` y `cotejo.json`. La ejecución 01 y los planes exploratorios del directorio padre conservan fallos de contrato; no son resultados finales. La prueba completa de conversación en Cline sigue pendiente; la skill instalada se sincronizó con la versionada.

Enviar la inspección completa en un solo JSON no funcionó: los logs locales de Ollama registraron entradas de aproximadamente 14 mil tokens recortadas a 6,147. La nueva ejecución compacta registró 1,736, 4,094 y 4,490 tokens de entrada por llamada. El [código de Ollama](https://github.com/ollama/ollama/blob/main/llm/llama_server.go) documenta ese recorte de entradas que exceden el contexto. **No se ha demostrado que explique los errores anteriores por bloques**, que también ocurrieron con entradas más pequeñas.

También se descartaron planes globales demasiado amplios y contratos que mezclaban clasificación con valores por concepto. No se atribuye la mejora a un único ajuste de prompt ni se afirma que desactivar la salida estructurada mejore otros pasos: las cabeceras usan esquema; la respuesta de grupos se valida estrictamente en Python.

## Siguiente paso

Usar esta interpretación cotejada como entrada para probar recuperación y selección de matrices. Mantener la revisión humana para dudas técnicas y conservar el Excel de salida que ya funciona. Comparar otros modelos solo con entradas fiables. Todavía no se ha generado el Excel final de este presupuesto ni se han comprobado nuevas matrices.
