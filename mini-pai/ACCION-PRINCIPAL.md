# Evaluación de la acción principal — 7 de noviembre de 2026

Se corrigieron las instrucciones de comparación de la skill y del selector. Primero se comprueba qué trabajo se realiza sobre qué objeto; después se comparan materiales, dimensiones, alcance y unidad. Construir un elemento no acredita demolerlo. Las acciones nominales y los sinónimos siguen siendo válidos si el contexto los acredita; una acción ambigua queda insuficiente. Se alinearon las opciones de estado del esquema con la validación existente: procedimiento y alcance ya no pueden generarse como no_aplica. No se cambiaron campos, validadores, modelo, búsqueda SQL o formato Excel; no hay listas de palabras para filtrar clientes.

## Prueba nativa con Nemotron

Se reevaluaron nueve conceptos de los veinte anteriores, con exactamente los mismos candidatos y textos completos; todos los códigos, descripciones y unidades se cotejaron en SQL antes de inferir. Se incluyeron todas las propuestas automáticas vigentes. Los otros once conceptos, que ya estaban pendientes, se conservaron sin nueva inferencia. Nemotron mantuvo contexto 12288, máximo de salida 6144, razonamiento y temperatura 0.

| Fila | Actividad | Antes | Ahora | Propuesta del selector |
| --- | --- | --- | --- | --- |
| 20 | Demolición de cimiento | E1/I3/S1 | I5 | Pendiente |
| 25 | Trazo y nivelación | S5 | I1/S4 | Pendiente |
| 26 | Excavación en cepas | I3/S2 | I3/S2 | Pendiente |
| 28 | Carga y acarreo | S5 | S5 | Pendiente |
| 30 | Plantilla de concreto | S5 | I5 | Pendiente |
| 35 | Acero 3/8 | E1/S4 | I2/S3 | Pendiente |
| 36 | Acero 1/2 | E1/I3/S1 | E1/I3/S1 | CIM-ACR-Z04 |
| 38 | Acero 3/4 | E1/S4 | I4/S1 | Pendiente |
| 39 | Acero 1 pulgada | E1/S4 | E1/I4 | 10401-176 |

E/I/S cuentan candidatos equivalentes, incompatibles e insuficientes, no conceptos resueltos ni precisión general. Los conteos incorporan las guardas del selector. En el antes se utiliza su salida original, previa a la auditoría manual de la selección incorrecta.

**Cambio principal:** la matriz 10401-558 pasó de seleccionada a incompatible porque describe construir un cimiento, no demolerlo. Esta vez la decisión fue de Nemotron con las nuevas instrucciones, sin la auditoría manual específica del ensayo anterior. Los campos de ConstruBase no se copiaron al concepto de demolición.

## Controles adicionales

| Control | Resultado esperado | Clasificación exacta | Segundos |
| --- | --- | --- | --- |
| piedra_vs_concreto | incompatible | Sí | 13.706 |
| plantilla_6_vs_3_4_5 | incompatible | No | 16.458 |
| demolicion_derribo | equivalente | Sí | 12.251 |
| accion_nominal_construccion | equivalente | Sí | 10.686 |
| cualquier_medio_admite_manual | equivalente | Sí | 9.766 |
| personal_calificado_cuadrilla | equivalente | Sí | 11.108 |

En los diez pares negativos no hubo selecciones automáticas; los cuatro positivos conservaron selección y comprobaciones válidas. La clasificación exacta pasó en cinco de los seis controles: el conjunto alternativo de plantillas quedó insuficiente en sus cinco candidatos aunque los motivos reconocen espesores distintos. Ese matiz sigue pendiente, no se oculta ni se transforma en aprobación. En los cinco candidatos de plantilla del caso focal sí se obtuvo incompatible. No se demuestra que la clasificación sea estable al cambiar el conjunto de candidatos.

Los dos controles negativos usaron cinco candidatos SQL reales cada uno: piedra frente a concreto armado y plantilla de 6 cm frente a 3/4/5 cm. Los cuatro positivos son controles sintéticos de redacción construidos a partir de descripciones SQL reales, cambiando solo la formulación: demolición/derribo, cimiento nominal/construcción explícita, procedimiento manual admitido por cualquier medio, y cuadrilla/personal técnico calificado. No son conceptos nuevos del cliente, no se exportan y no certifican equivalencia de trabajos con otras diferencias.

Los nueve conceptos focales tardaron **195.539 s**. Hubo 15 llamadas en el ensayo completo, controles incluidos. No se midieron otra extracción ni otra búsqueda, ni se repitió el presupuesto completo.

## Excel actualizado y comprobaciones

Se generó otro Excel de revisión con los veinte conceptos originales y cuatro agrupadores: **1 propuestas IA vigentes verificadas otra vez en SQL y 19 pendientes**. Los auxiliares, cantidades y jerarquía se cotejaron al reabrir el libro; las ocho columnas de Catálogo y seis de Copiar auxiliares siguen iguales. Los positivos sintéticos no aparecen en el Excel. No se respondieron preguntas por el usuario.

El borrador conserva los datos originales en auxiliares y deja vacíos los principales de los pendientes; el Excel final sigue bloqueado. El usuario debe revisar alcance e inclusiones de las propuestas y resolver las dudas antes del copiado completo a Neodata.

Nemotron propuso dos matrices. La auditoría del entregable retiró la de la fila 36: CIM-ACR-Z04 limita su aplicación a zapatas, contratrabes y dados, mientras que el cliente solo indica cimentación; no se debe asumir esa geometría ni todas sus inclusiones. La respuesta nativa se conserva intacta y el JSON de entrega identifica la intervención de Codex. La propuesta restante es la fila 39, con revisión humana de alcance todavía necesaria. Esta retirada no es una regla automática nueva.

Las filas 35 y 38 pasaron de propuestas a pendientes por inclusiones no acreditadas por el modelo. En el motivo de la fila 38 también aparece alambre recocido, aunque el cliente solo exige alambre: ese calificativo es un exceso de la explicación del modelo, no un requisito original ni una modificación del presupuesto. Sigue existiendo inconsistencia entre casos de acero; no se afirma que el ajuste haya resuelto su evaluación técnica general.

Pasaron 157 pruebas automatizadas, incluida una nueva que protege las opciones de estado de los siete aspectos, y la validación de la skill. Se añadieron dos escenarios a su archivo de evaluaciones para acción principal y sinónimos; son escenarios preparados, no sesiones ejecutadas en Cline. Los controles de la tabla sí se ejecutaron mediante los módulos reales y Ollama.

La primera pasada de instrucciones corrigió el caso de construcción/demolición, pero solo dos de cuatro positivos controlados llegaron a selección. En los otros dos el modelo reconoció la equivalencia y generó comprobaciones no_aplica para procedimiento/alcance, que las guardas rechazaron correctamente. También usó insuficiente para los diez negativos pese a describir diferencias reales. Se conservaron esos resultados; después se alineó el esquema y se aclaró el significado de las etiquetas antes de repetir los mismos casos.

Evidencia privada: `salidas/accion-principal-2026-11-07/` conserva la primera pasada; `pasada-02/` contiene la repetición con el contrato alineado y sus respuestas nativas. La entrega vigente, con auditoría de alcance, está en `pasada-02/entrega-revisada/`: evaluación consolidada, Excel y `reporte-prueba.md`. El primer borrador de la segunda pasada se conserva como antecedente, no como entrega vigente. La skill instalada se sincronizó con la versionada después de comprobar los controles.

## Límites

Es una corrección de instrucciones respaldada por estos controles, no una nueva guarda determinista ni una prueba de que el modelo nunca confundirá acciones. Se necesitan otros presupuestos y revisión de dominio. Los once pendientes conservados no se reevaluaron; no se mide precisión general ni rendimiento total del flujo. No se volvió a probar el pegado en Neodata y el PR #3 permanece sin fusionar.
