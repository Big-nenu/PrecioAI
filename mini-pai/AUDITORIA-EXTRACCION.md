# Auditoría de extracción — 7 de noviembre de 2026

> Actualización: la [ruta tabular](EXTRACCION-TABULAR.md) ya extrajo y cotejó los 78 conceptos. El diagnóstico siguiente corresponde al intento anterior por bloques, cuyos límites permanecen.

## Conclusión inicial

La lectura de celdas conserva los datos originales, pero **la interpretación IA por bloques todavía no es fiable para este presupuesto completo**. No basta corregir el resumen de Cline. Hay errores semánticos reales al clasificar agrupadores y omisiones de campos que las validaciones actuales permiten como valores ausentes.

No se recuperó un JSON de la prueba anterior de Cline en las salidas del repositorio. Por eso no se afirma que su mezcla de cantidades se originara en una función concreta. La reproducción nueva sí aporta evidencia independiente de fallos de extracción.

## Ejecución real de referencia

Se utilizó el presupuesto local de 78 conceptos, hoja CATALOGO, con Nemotron `nemotron-3.5-bolt:e4b`, la configuración existente y bloques de cinco filas no vacías. El código al iniciar la prueba correspondía al commit local `12035f9`; después se hicieron experimentos focales por separado.

- Inspección: una hoja, 121 filas no vacías. El conteo de 78 se cotejó para este archivo mediante sus claves originales; ese patrón no se incorporó al extractor.
- Tiempo: **285.779 s**, veinte llamadas, incluidos reintentos. Es una ejecución fallida de interpretación, no tiempo de generación de un presupuesto final ni del flujo completo.
- Se detuvo en el bloque de filas 71–75 después de dos respuestas inválidas: el modelo clasificó un concepto como partida y citó unidad/cantidad para ese encabezado.
- No se generó un JSON de interpretación completa ni se continuó a ConstruBase o al Excel final.
- Al reconstruir las respuestas aceptadas hasta la fila 70, se obtuvieron 44 conceptos. Sus códigos y descripciones coincidieron con la fuente; se detectaron **once campos omitidos** pese a estar presentes: seis unidades y cinco cantidades.
- No hubo sustitución de cantidades por las de otro renglón entre esos campos aceptados: las diferencias encontradas fueron valores ausentes.

## Fallos identificados

| Área | Evidencia | Alcance de la conclusión |
| --- | --- | --- |
| Cantidad de otra fila | Asignar la celda E107 al concepto de fila 19 fue rechazado por la validación existente | Esa mezcla concreta ya está protegida; no demuestra exactitud semántica completa |
| Agrupador omitido | El encabezado de fila 25 se omitió como supuesto resumen; agrupa los trabajos siguientes | La validación de cobertura acepta una exclusión con motivo, aunque el juicio semántico sea incorrecto |
| Nivel de agrupación incorrecto | Subpartidas de filas 26 y 56 se trataron como partidas nuevas | Las relaciones pueden ser coherentes con lo extraído y aun así no representar la estructura real |
| Campos presentes tratados como ausentes | Unidad de fila 46 y unidades/cantidades de filas 66–70 quedaron null | El contrato permite campos ausentes; comprobar que una cita existe no detecta una cita omitida |
| Concepto convertido en partida | Bloque 71–75 rechazado tras reintento | La validación evita continuar con ese resultado, pero no logra que el modelo lo corrija |

La etapa recibe solo filas objetivo, dos filas de anticipación y encabezados de agrupación vigentes; no conserva los títulos de columnas como contexto de tabla. Esta limitación es verificable en el código, pero **no se ha demostrado que explique por sí sola todos los errores**.

## Experimentos focales descartados

Se probaron los bloques con problemas de filas 25, 56 y 71, conservando modelo y fuentes: aclaraciones sobre encabezados e importes, uso exclusivo de la sección pertinente de la skill, y referencia a los últimos conceptos validados.

Ninguna variante resolvió todos los controles y conservó todos los campos. En particular, clasificar una fila como concepto no implica que se hayan conservado su unidad y cantidad. **Los cambios experimentales del intérprete se retiraron**. No se sustituyó el modelo, no se cambió la skill instalada ni se presenta un ajuste de instrucciones como solución comprobada.

No es una comparación de modelos ni un benchmark controlado de rendimiento; los reintentos y contratos probados se conservan separados.

## Corrección que sí queda integrada

`mini_pai_exportar.py` comprueba en entrega final que un código principal tenga una única descripción completa, incluyendo conceptos originales conservados y colisiones entre original y matriz seleccionada. Antes solo se controlaban conflictos entre matrices seleccionadas.

- Misma clave con descripción distinta: rechazar y pedir revisión, sin renombrar ni fusionar.
- Misma clave con descripción idéntica: permitir repetir el concepto.
- Si hay conflicto, el comando no crea ni el Excel ni su Markdown.
- No cambia columnas, formato, descripciones, cantidades ni datos de origen.

Una prueba reprodujo el fallo antes de corregirlo. Otra prueba conserva el control específico de cantidades de filas distintas. **129 pruebas automatizadas pasaron** tras los cambios finales, incluidos controles de las dos categorías de conflicto y de no creación de archivos.

## Siguiente incremento necesario

Corregir el contrato de extracción antes de continuar con búsquedas: identificar y conservar la estructura de tabla y agrupadores, y comprobar que los campos declarados ausentes realmente lo estén. Debe seguir siendo flexible por documento; no añadir columnas fijas ni reglas SIOP a producción.

La aceptación requiere recuperar los 78 conceptos con código, descripción, unidad, cantidad y jerarquía cotejados, incluidas unidades compuestas y cambios de bloque. No rellenar datos desde un resumen de conversación ni ocultar fallos como ausencia de matrices. Después corresponde medir el flujo completo y comparar los modelos pendientes con entradas fiables.

## Evidencia privada y límites

Las inspecciones, respuestas completas, errores, tiempos y cotejos están en `salidas/auditoria-extraccion-2026-11-07/`, excluida de Git. `auditoria-base.json` reconstruye respuestas aceptadas para diagnóstico; no sustituye una interpretación final. Los subdirectorios de focos contienen experimentos fallidos, no resultados consolidados.

Se verificó el SHA256 del presupuesto original antes y después. No se modificó ConstruBase ni se consultó SQL en vivo. No se generó un nuevo Excel de este presupuesto y no se probaron otros modelos. El problema de clasificación y omisiones sigue pendiente; el producto todavía requiere supervisión técnica.
