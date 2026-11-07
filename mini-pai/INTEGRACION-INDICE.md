# Mini-PAI: recuperación con índice conectada al flujo existente

Prueba real del 7 de noviembre de 2026. Se conectó EmbeddingGemma 270m mediante `mini_pai_buscar.py --indice` al contrato del selector existente. Se conservó Nemotron, la verificación SQL, los originales y el formato Excel. No hay cambio de arquitectura ni dependencias nuevas.

## Alcance y mediciones

Se reutilizó la interpretación de los mismos **20 conceptos y cuatro agrupadores**, hoja Conceptos, filas 18–41 de la muestra anterior. Se inspeccionaron todas las hojas del original y se cotejaron nuevamente 80 campos por sus celdas, sin diferencias. Es un alcance parcial del presupuesto; no se procesó el archivo completo ni se midió otra extracción IA.

| Etapa | Segundos |
| --- | --- |
| inspeccion_y_cotejo_s | 0.273 |
| recuperacion_total_s | 4.399 |
| seleccion_s | 430.901 |
| reverificacion_sql_s | 0.108 |
| exportacion_s | 0.074 |

Hubo 20 llamadas a Nemotron para los 20 conceptos. El índice reutilizó **19,418 documentos y generó cero vectores nuevos de catálogo**. Se consultó el catálogo SQL vigente; se vectorizaron realmente las descripciones del cliente y se descargó EmbeddingGemma antes de evaluar. El tiempo de recuperación incluye carga del modelo, SQL, validación del índice y ranking; no es comparable directamente con una consulta caliente del laboratorio.

## Resultados y revisión

Nemotron propuso 5 selecciones que pasaron las guardas y SQL. La revisión retiró una: había elegido una matriz para construir un cimiento de piedra frente a una petición de demolerlo. El texto de ConstruBase no acredita demolición. La respuesta original y su selección se conservaron sin cambios en el archivo de ejecución; el resultado revisado documenta explícitamente la intervención de Codex.

El Excel de revisión contiene **4 propuestas IA vigentes con SQL revalidado y 16 conceptos pendientes**, sin elecciones humanas inventadas. Las cuatro propuestas de acero coinciden en diámetro, resistencia y unidad; la revisión del usuario sigue siendo necesaria para confirmar alcance e inclusiones, especialmente la interpretación funcional de amarres/alambre. No se mide exactitud técnica general. Los controles piedra/concreto y plantilla de 6 cm frente a otros espesores no quedaron seleccionados en la entrega revisada.

Se prepararon hasta tres opciones según el orden técnico y la alternativa de conservar el original. Los incompatibles se excluyen de esas opciones; puede haber menos de tres o ninguna. Los errores de evaluación, si los hay, permanecen pendientes y visibles, nunca como ausencia de matrices. El índice siempre devuelve vecinos: cero búsquedas vacías no significa veinte equivalencias.

**El archivo es un borrador de revisión, no el Excel final para copiar completo.** Los conceptos pendientes conservan código y descripción originales en auxiliares; sus campos principales quedan vacíos según el exportador existente. No se marcaron como sin matriz ni se respondió por el usuario. Al elegir conservar el original, el flujo final coloca sus datos en principales y auxiliares. La exportación final sigue bloqueada hasta resolver las dudas.

## Qué se comprobó

- Las ocho columnas de Catálogo, las seis de Copiar auxiliares y la estructura existente de Revisión permanecen iguales.
- Se reabrió el Excel y se comprobaron los 20 conceptos, cuatro agrupadores, padres, auxiliares, cantidades originales, código/descripción/unidad de las cuatro selecciones y campos vacíos de los pendientes.
- Las cuatro matrices vigentes se consultaron otra vez en SQL Server; coincidieron íntegramente con las instantáneas guardadas.
- Se comprobaron hashes del presupuesto, muestra y `.env`; no se alteraron. SQL se usó solo por SELECT.
- Pasaron 156 pruebas automatizadas, cinco nuevas de contrato del índice, reutilización, conservación, fallos y protección de salida.

## Reproducir y continuar

Desde la raíz del repositorio, usar una salida nueva y una interpretación sin búsquedas:

```powershell
python mini_pai_buscar.py ruta/interpretacion.json --indice datos_privados/indices/embeddinggemma-2_270m-3fbdf26b6f5797d8.sqlite --salida salidas/nueva/candidatos.json
python mini_pai_seleccionar.py salidas/nueva/candidatos.json --salida salidas/nueva/evaluacion.json
python mini_pai_revision.py salidas/nueva/evaluacion.json --salida salidas/nueva/opciones.md
python mini_pai_exportar.py salidas/nueva/evaluacion.json --salida salidas/nueva/revision.xlsx
```

La ruta del índice corresponde a esta computadora y a esta versión del catálogo/modelo. En otra instalación, usar una ruta nueva para construirlo; no se publica el índice ni los documentos de catálogo. Si cambia la identidad se rechaza su reutilización, sin sobrescribirlo.

Evidencia privada en `salidas/integracion-indice-20-2026-11-07/`: interpretación reutilizada, candidatos, respuestas completas, evaluación sin auditar, evaluación revisada, mediciones y Excel/Markdown. `ejecutar.py` y `finalizar.py` conservan el ensayo exacto; este último incluye la auditoría específica de la demolición y no es una regla del selector de producción.

**Límite pendiente:** el selector automático todavía puede confundir construir y demoler si ambos textos mencionan el mismo objeto y material. Este incremento no corrigió sus criterios ni convierte la auditoría específica de la muestra en una guarda general. Requiere corregir y probar la evaluación de la actividad principal antes de dar por seguro el uso automático. La comparación técnica sigue dominando el tiempo; estos resultados no acreditan aceleración del presupuesto completo. No se volvió a probar el pegado en Neodata, no se generó un Excel final y el PR #3 permanece sin fusionar.
