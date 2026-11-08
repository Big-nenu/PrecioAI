# Presupuestos originales: estructura y flujo — 7 de noviembre de 2026

## Corrección

La clasificación tabular ahora separa el título global de la obra de sus agrupadores, y el anuncio del resumen final de los trabajos. Clasifica las filas sin medición en bloques de diez con esquema JSON, grupos vigentes, ejemplos anteriores, estilos originales de las celdas, trabajos vecinos y dos encabezados de anticipación. Una nueva subpartida puede reemplazar a la anterior sin convertirse en su hija o en un concepto. El estado anterior es contexto, no una agrupación congelada.

La IA devuelve tipo y motivo por fila. Python asigna los padres por la secuencia de grupos: partida sin padre, subpartida bajo la partida vigente y concepto bajo el último grupo activo. No se pide al modelo que decida un padre que el validador ya impone. Los estilos se usan como indicios visuales, sin imponer que negrita signifique partida. La lectura con formatos carga el libro en memoria; la inspección sin formatos conserva su lectura por streaming. Python sigue recuperando los campos completos desde las celdas originales. Cada bloque pasa por el materializador y los validadores existentes. Solo el grupo vigente puede quedar temporalmente sin descendientes mientras llega el siguiente bloque; la entrega completa sigue rechazando cualquier agrupador vacío. No se cambiaron modelo, búsqueda SQL, formato Excel ni dependencias.

Se añadió `--limite-conceptos` al coordinador para comprobar el flujo sobre archivos originales: interpreta todo el catálogo y guarda el checkpoint completo, pero acota las etapas posteriores y la entrega. El alcance parcial queda explícito. No prepara ni recorta el archivo de entrada.

## Resultado comprobado

| Archivo original | Conceptos medidos | Agrupadores | Campos originales de conceptos cotejados |
| --- | ---: | ---: | ---: |
| E2, hoja CATALOGO | 78 | 15 | 312 |
| Propuesta pepe, hoja Conceptos | 438 | 115 | 1,752 |

Los cotejos comprueban también tipos, padres y secuencia de partidas/subpartidas. El E2 se compara con la referencia completa ya validada. Propuesta se coteja contra sus celdas y una referencia de jerarquía auditada para ese libro; el patrón de claves de esa referencia privada no se incorpora como regla al producto. Su hoja Resumen queda declarada no procesada por la ruta de una tabla.

El recorrido funcional parte de ambos Excel originales, sin preparar copias. La interpretación es completa para el catálogo; búsqueda, comparación y entrega se acotan a veinte conceptos y cuatro agrupadores por archivo. Cada entrega final conserva los veinte originales por elección explícita del usuario, con cero matrices exportadas. Se reabrieron los libros y se cotejaron columnas, códigos/descripciones principales y auxiliares, unidades, cantidades, filas y parentescos de Revisión.

| Etapa medida | E2 | Propuesta pepe |
| --- | ---: | ---: |
| Interpretación completa y cotejo antes de buscar | 43.012 s | 264.657 s |
| Recuperación real con índice | 5.846 s | 6.444 s |
| Evaluación real Nemotron de veinte conceptos | 370.139 s | 411.023 s |
| Resolver conservando originales y exportar, proceso cargado | 0.115 s | 0.113 s |
| Reabrir sesión terminada por CLI, proceso nuevo | 0.497 s | 0.508 s |

Estas son mediciones de una ejecución, no un benchmark. La búsqueda reutilizó los 19,418 vectores existentes: cero documentos recalculados. El E2 terminó con veinte pendientes; Propuesta propuso tres matrices y dejó diecisiete pendientes. Son resultados del selector existente, no equivalencias certificadas ni una mejora atribuible a esta corrección. Se conservaron originales incluso donde había propuestas IA.

Durante la resolución se sustituyeron por errores las funciones de interpretación, recuperación, evaluación y conexión SQL: ninguna se llamó. Los tres checkpoints conservaron sus hashes. Reabrir la sesión terminada no regeneró el Excel. Pasaron **172 pruebas automatizadas** (`python -m unittest discover -q`) y `git diff --check`.

Las entregas están en `salidas/flujo-originales-2026-11-07/01-sesion/` (E2) y `06-sesion/` (Propuesta): `presupuesto.xlsx` y `presupuesto.md`. Los JSON de cotejo, llamadas, tiempos y comprobaciones de entrega están en la misma carpeta de pruebas; no se publican datos del cliente.

La prueba funcional del E2 se cerró antes del último ajuste de clasificación. Con el código definitivo se repitió su extracción completa: **51.588 s, cuatro llamadas**, cotejo completo sin diferencias y los mismos veinte registros de la entrega. No se repitieron búsqueda ni evaluación, cuyos módulos no cambiaron. Esa sesión cerrada registra la versión anterior; la protección de versión exige otra carpeta para continuar con código diferente. Propuesta completó todo el recorrido con el código definitivo.

## Evidencia y límites

Los archivos, respuestas nativas y cotejos permanecen privados bajo `salidas/flujo-originales-2026-11-07/`. El control final del E2 está en `salidas/extraccion-originales-2026-11-07/pasada-final/`. Los originales conservaron sus SHA256; ConstruBase se consultó mediante las herramientas existentes de solo lectura.

La prueba inicial de bloques corrigió un cambio de edificio en un corte, pero otra pasada todavía confundió encabezados con conceptos. La referencia independiente lo detectó y bloqueó esa prueba antes de buscar o exportar. Esos intentos no se cuentan como éxitos. También se corrigió un error del comprobador privado de reanudación (`DEFAULT`); no fue un fallo del coordinador y se continuó desde sus checkpoints, sin repetir inferencias.

Las entregas conservan originales por autorización explícita del usuario para estas pruebas. No certifican equivalencias técnicas ni representan ausencia de matrices. El catálogo tabular sigue limitado a una hoja con columnas estables y cabeceras reconocibles; otras hojas se declaran pendientes. La ruta por bloques para estructuras diferentes mantiene sus límites anteriores.

No se repitió el pegado en Neodata ni se implementaron MCP o interfaz. La comparación técnica sigue dominando el tiempo de las muestras; esta corrección no es una prueba de aceleración ni de precisión general. No se evaluaron matrices para los presupuestos completos. El siguiente incremento previsto es exponer el flujo existente mediante un MCP mínimo, sin duplicar sus etapas, antes de la interfaz familiar.
