# Generalizar la interpretación de presupuestos

La entrada no debe ajustarse a una plantilla del cliente. La plantilla fija corresponde al Excel de salida para Neodata. Este incremento elimina la limitación de dos niveles del modelo interno y permite identificar columnas con rótulos en varias filas o sin todos sus nombres.

## Contrato común

Los registros mantienen los mismos campos. `padre` identifica el grupo inmediato por hoja y fila original, nunca por código. Una partida es raíz; una subpartida puede pertenecer a una partida o a otra subpartida. Un concepto pertenece al grupo vigente. Las ramas hermanas cierran la rama anterior; no se permiten ciclos, padres futuros, grupos cerrados ni conceptos usados como padre.

`partida` y `subpartida` se conservan por compatibilidad: raíz y agrupador inmediato cuando corresponde. No representan por sí solos todo el árbol. Para recorrer o exportar la jerarquía se debe usar `padre`. Las entradas antiguas sin ese campo conservan el comportamiento anterior de dos niveles; no se inventan niveles adicionales.

La ruta tabular y la ruta por bloques utilizan los mismos tipos y la misma identidad de padres. En tabular, la IA clasifica encabezados y propone padres de los grupos; Python recupera las celdas y coloca los conceptos medidos en el grupo vigente. La rama activa completa pasa al siguiente bloque. No hay códigos, nombres de presupuestos ni vocabularios de clientes usados como reglas del producto.

El materializador, el validador compartido con búsqueda y el exportador conservan los niveles. El Excel mantiene exactamente sus columnas existentes. Las rutas de Partida se construyen recorriendo padres y no duplican un prefijo relativo que ya incluya el código del padre.

## Evidencia de columnas

`estructura_tabla_ia.columnas` conserva coordenadas originales: pueden ser rótulos de distintas filas o ejemplos de datos de la columna, dentro de las primeras veinte filas no vacías. Se prefieren rótulos; si faltan, el ejemplo debe pertenecer a una fila con descripción, unidad y cantidad numérica. Las columnas deben ser distintas. Una referencia de rótulo posterior al límite declarado no se acepta como dato.

La cabecera no puede ocultar un posible trabajo medido. Los ejemplos de datos no se usan como patrones para eliminar filas repetidas. Las cantidades numéricas se reconocen para automatizar la lectura, sin normalizar ni cambiar su valor original; las filas con cantidades de texto pasan a clasificación IA. Se valida el perfil antes de clasificar y se permite un reintento con el error concreto.

## Ambigüedad y revisión

La ruta tabular ya no convierte automáticamente en concepto una fila sin unidad ni cantidad. Si la IA considera que puede ser un trabajo autónomo, puede declarar `revision`. Eso detiene la etapa con fila y motivo, sin buscar matrices. Esa declaración no se reintenta para presionar al modelo a aceptarla. El materializador general conserva la capacidad de representar campos ausentes cuando hay una interpretación explícita.

Esto no demuestra que la IA detecte todas las ambigüedades: un árbol formalmente válido todavía puede ser semánticamente incorrecto. Los cotejos independientes siguen siendo necesarios. No se sustituye una revisión estructural por confianza del modelo.

## Pruebas de código

Las pruebas sintéticas usan claves sin prefijos comunes y cuatro niveles, verifican ramas hermanas, padres inválidos/cerrados, campos originales, exportación final con las mismas columnas, prefijos relativos y detención ante revisión explícita. No son pruebas hechas con códigos de un cliente. Se conserva la suite anterior. Pasaron **180 pruebas automatizadas** con `python -m unittest discover -q`, incluidas pruebas de cabeceras distribuidas, anclas reales, protección de primeros trabajos y conceptos repetidos.

## Resultados y procedencia

| Archivo | Comprobación |
| --- | --- |
| Estándar | 22 conceptos y 3 agrupadores; corregido el encabezado que antes era contado como concepto. |
| PRESUPUESTO DE OBRA | 35 conceptos y 6 agrupadores cotejados. |
| E2 | 78 conceptos y 15 agrupadores, 312 campos sin diferencias contra su referencia completa. |
| Propuesta pepe | 438 conceptos y 115 agrupadores; campos y padres cotejados. Su hoja Resumen sigue declarada no procesada. |
| original siop | Sigue rechazado por agrupación inconsistente. La nueva representación admite sus niveles, pero la IA todavía no produjo un árbol correcto; no se da por resuelto. |
| Obra civil | El lector ya identifica las columnas con rótulos partidos, pero se detiene por una descripción sin medición que puede ser compartida. No se fuerza una elección. La ruta por bloques también falló y no se presenta como alternativa validada. |

La pasada nativa conjunta está en `salidas/jerarquia-general-20261107-155156/pasada-03/`. El código definitivo repitió inferencia y cotejos del E2 (42.428 s, tres llamadas) y Estándar (17.229 s, dos llamadas) bajo `pasada-final/`. Los planes nativos ya cotejados de PRESUPUESTO DE OBRA y Propuesta se revalidaron con el materializador definitivo, sin nuevas inferencias: `pasada-final/revalidacion.json`. No se suman esos controles como ejecuciones nativas nuevas. Obra civil con el código definitivo se detuvo en revisión estructural, fila 19, tras 49.472 s y tres llamadas; evidencia en `pasada-final/obra-civil-tabla/`.

Los borradores son solo para inspección de estructura, con matrices sin resolver: no son Excel finales para copiar a Neodata. No se ejecutaron búsqueda ni evaluación SQL, no se repitió el pegado, y todos los originales conservaron sus hashes. No se volvieron a ejecutar comparaciones de modelos. La profundidad arbitraria se verifica con ejemplos sintéticos de cuatro niveles; no se afirma que la IA haya resuelto el árbol profundo de original siop.

Los intentos anteriores y cambios experimentales descartados quedan privados en las carpetas de pasadas; no se cuentan como resultados válidos ni se publican presupuestos. Los resultados positivos no garantizan otros archivos ni equivalencia técnica. La revisión estructural actualmente detiene la etapa: falta una experiencia para confirmar/corregir esas dudas y continuar sin instrucciones improvisadas al agente.

## Alcance pendiente

Este es el primer incremento de generalización, no una promesa de comprender cualquier Excel. La ruta tabular todavía requiere columnas estables y un comienzo de tabla identificable en la muestra inicial. La ruta por bloques sigue disponible para otras estructuras; su validación debe indicarse por separado.

Siguen pendientes la selección automática y comprobada de la ruta de lectura, archivos sin comienzo identificable o con varias tablas/cambios de columnas, el contexto técnico de descripciones compartidas y resolución de dudas estructurales dentro de una experiencia sencilla. No se debe concatenar ni reescribir la descripción auxiliar del cliente para resolver una descripción compartida: hay que conservar el texto y su procedencia.

La prioridad sigue siendo el lector y sus cotejos con archivos nuevos. MCP e interfaz vienen después. No se cambiaron el modelo, las consultas SQL, los códigos/descripciones originales ni las columnas del Excel. No hay dependencias ni frameworks nuevos.
