# Pruebas de recuperación, índice y decisiones — 7 de noviembre de 2026

Se ejecutaron las tres pruebas localmente y por fases, liberando cada modelo antes del siguiente. Nemotron conserva su configuración de producción; no se aplicaron selecciones ni se generó un Excel nuevo. ConstruBase se consultó exclusivamente por SELECT.

## Recuperación real y velocidad

Se buscaron los mismos 20 conceptos de la muestra anterior en los **19,418 registros tipo 4 (conceptos/básicos)** de ConstruBase. Se utilizaron descripciones completas sin truncar, IDs, códigos y unidades reales. Doce consultas tienen referencias de matrices útiles procedentes de revisiones previas o del diámetro/resistencia explícitos del acero 5/16; ocho no tienen etiqueta. Estas referencias no certifican equivalencia completa. No es una prueba independiente de precisión.

La tabla muestra coseno con la misma unidad textual primero. Se midió también sin esa prioridad y con centrado, reutilizando vectores. La unidad solo ordena: nunca aprueba ni convierte cantidades.

| Modelo | Referencia en top 1 | En top 3 | En top 5 | Construcción inicial | 20 consultas con índice | Índice | VRAM residente observada |
| --- | --- | --- | --- | --- | --- | --- | --- |
| embeddinggemma-2:270m | 7/12 | 10/12 | 11/12 | 309.70 s | 0.617 s | 76.3 MiB | 362.9 MiB |
| qwen3-embedding:0.6b | 6/12 | 6/12 | 8/12 | 233.44 s | 0.626 s | 85.7 MiB | 4419.9 MiB |

Medición adicional de recuperación completa, ahora incluyendo ordenar los 19,418 candidatos de cada consulta y obtener los cinco primeros:

- embeddinggemma-2:270m: **1.706 s para 20 consultas** con el modelo cargado. La primera consulta tras descargar los otros modelos tardó 2.378 s, carga incluida, y se midió aparte. El ranking coincidió con la primera ejecución.
- qwen3-embedding:0.6b: **1.692 s para 20 consultas** con el modelo cargado. La primera consulta tras descargar los otros modelos tardó 2.271 s, carga incluida, y se midió aparte. El ranking coincidió con la primera ejecución.

La columna de consultas de la tabla (0.617/0.626 s) incluye cargar el índice, generar vectores nuevos para las 20 descripciones y calcular cosenos; excluye ordenar la lista. La medición adicional (1.706/1.692 s) sí incluye ese ordenamiento. Ambas excluyen interpretación, decisiones técnicas y exportación. La VRAM es una lectura de `/api/ps`, no el pico de toda la ejecución ni una promesa de memoria. Son mediciones locales únicas, no promedios ni una proyección a todos los presupuestos.

Con centrado y prioridad de unidad, Qwen llegó a 7/12 en top 3; Gemma mantuvo 10/12. Sin prioridad de unidad, Gemma obtuvo 9/12 y Qwen 4/12 (5/12 centrado). En esta muestra gana **EmbeddingGemma 270m para recuperar candidatos**. La referencia de demolición de concreto quedó quinta y la referencia previa de cimbra no apareció entre cinco; puede haber otras matrices útiles no etiquetadas. El acero 5/16, antes sin candidatos, sí recuperó una referencia útil.

Se escogió para las decisiones Gemma sin centrado con unidad primero, según mayor cobertura top 3, luego top 5, top 1 y menor tiempo de consultas. La elección es exploratoria sobre esta misma muestra; falta validarla en otra. Un ranking siempre devuelve vecinos, incluso cuando ninguno sirve: no hay umbral validado de ausencia de equivalencia.

## Índice persistente

`indice_local.py` guarda documentos originales y vectores float32 en SQLite local. La identidad incluye SHA256 del catálogo, digest del modelo y prefijos; rechaza reutilización incompatible. Guarda cada lote y reanuda los pendientes. La carga es de solo lectura y comprueba integridad de textos y vectores. No usa SQLite como copia editable de ConstruBase.

Ambos índices se reabrieron con **19,418 documentos reutilizados y cero vectores de catálogo nuevos**. En esa comprobación la función de embeddings se sustituyó por una que falla si se invoca; las consultas nuevas sí se vectorizaron realmente después. Los índices completos quedan en `datos_privados/indices/`, ignorados por Git. La siguiente actualización de catálogo/modelo exige otra identidad/ruta.

Es una capacidad del laboratorio, todavía no conectada al buscador del producto. No se cambió SQL, selector ni Excel. No se añadió ninguna dependencia: usa SQLite de Python y NumPy ya instalado para el laboratorio.

## D1, D3 y Nemotron sobre los mismos pares

Se compararon 71 pares idénticos por modelo: 60 pares de los tres vecinos de cada concepto, controles incompatibles adicionales sin duplicarlos y cuatro positivos idénticos controlados. Se incluyó además la cimbra con inclusiones no acreditadas. Todos recibieron descripciones completas, unidades y la misma rúbrica de cuatro clases; cada par tiene SHA256. D1/D3 usan el endpoint de decisiones existente y Nemotron el proveedor existente. No se evaluó uso autónomo de herramientas ni el contrato completo del selector de producción.

| Modelo | Tiempo total | Mediana por par | Controles incompatibles bien clasificados | Incompatibles llamados equivalentes | Positivos idénticos bien clasificados | Errores API/contrato |
| --- | --- | --- | --- | --- | --- | --- |
| d1:3b | 12.44 s | 0.105 s | 5/10 | 4/10 | 4/4 | 0 |
| d3:2b | 10.83 s | 0.091 s | 0/10 | 0/10 | 4/4 | 0 |
| nemotron-3.5-bolt:e4b | 529.23 s | 7.300 s | 9/10 | 0/10 | 4/4 | 0 |

Los diez negativos son cinco matrices de concreto armado frente a demolición de piedra, y cinco plantillas de 3/4/5 cm frente a los 6 cm del cliente. Los cuatro positivos repiten exactamente descripción y unidad de matrices reales: comprueban una condición sencilla, no la comprensión de presupuestos nuevos. No se calcula exactitud general de los otros pares porque no tienen dictamen experto. El tiempo total incluye la primera llamada y carga; las medianas reducen su efecto, pero la generación de una explicación por Nemotron tiene trabajo distinto al clasificador de D1/D3.

| Modelo | Equivalente | Compatible con diferencias | Incompatible | Información insuficiente |
| --- | --- | --- | --- | --- |
| d1:3b | 45 | 12 | 14 | 0 |
| d3:2b | 26 | 37 | 0 | 8 |
| nemotron-3.5-bolt:e4b | 13 | 28 | 30 | 0 |

Nemotron también tuvo un foco claro: en la cimbra general del cliente trató como equivalentes matrices específicas de zapatas y muros, aunque el texto del cliente no demuestra esa geometría ni todas las inclusiones. Son propuestas dudosas, no selecciones justificadas; esos pares permanecen para revisión en el reporte privado. Además, llamó compatible con diferencias a una plantilla de 5 cm bombeada frente a los 6 cm requeridos: reconoció la diferencia, pero su etiqueta contradice la rúbrica. No se aplicó como selección.

Comprobación adicional del orden de categorías (mismos cuatro negativos y un positivo, solo se invierte el orden de las etiquetas):

- d1:3b: 1/5 decisiones cambiaron; 0 errores. Es un foco diagnóstico pequeño, no otra medición general.
- d3:2b: 1/5 decisiones cambiaron; 0 errores. Es un foco diagnóstico pequeño, no otra medición general.

## Qué conviene hacer después

Usar EmbeddingGemma 270m con índice como siguiente integración mínima de recuperación, manteniendo la verificación SQL de las matrices elegidas y la revisión de dudas. D1 y D3 son rápidos, pero los controles no justifican darles autoridad para seleccionar matrices: hay falsas equivalencias o diferencias explícitas clasificadas como simples adaptaciones/insuficiencia. Nemotron permanece como referencia y también requiere revisión de sus decisiones y validaciones; cantidad de respuestas equivalentes no equivale a cantidad de selecciones correctas.

Esta prueba no demuestra cuánto tardará un presupuesto completo: no se ensambló el flujo de interpretación → recuperación → decisión → revisión humana → Excel. El índice resuelve el recálculo del catálogo, no el costo de las decisiones de Nemotron. No se implementó memoria de decisiones, MCP, interfaz ni cambio automático de modelo.

## Evidencia y reproducción

La evidencia privada está en `salidas/tres-pruebas-2026-11-07/`: `recuperacion.json`, `consultas.json`, `pares-decision.json`, `decisiones.json`, `estadisticas.json`, `procedencia.json` y `reporte.md`. Incluye respuestas originales, estados por par, tiempos, variantes, digests y hashes. Los drivers locales `ejecutar_recuperacion.py`, `ejecutar_decisiones.py` y `generar_reporte.py` conservan la preparación exacta del experimento; requieren las entradas privadas de esta computadora. No se publican catálogos ni presupuestos.

Se volvió a consultar por SELECT el catálogo completo: sus 19,418 documentos, códigos y unidades coincidieron con la instantánea del índice. Se comprobó el SHA256 del Excel original. Las entradas previas de las pruebas se conservaron.

Pasaron **151 pruebas automatizadas**, incluidas seis nuevas de persistencia, reutilización sin embeddings, reanudación, identidad, corrupción y prefijo Qwen. No sustituyen una prueba completa del producto.

Para reutilizar el índice desde Python, con una instantánea vigente y el digest real de Ollama:

```python
from indice_local import construir, cargar, firma
identidad = firma(catalogo, modelo, digest)
construir(ruta_local, catalogo, modelo, digest)  # solo los documentos pendientes
documentos, vectores = cargar(ruta_local, identidad)
```

Los prefijos de consulta para Qwen siguen su [ficha oficial](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B). D3 se probó mediante la [API de decisiones documentada por Ollama](https://ollama.com/library/d3:2b).
