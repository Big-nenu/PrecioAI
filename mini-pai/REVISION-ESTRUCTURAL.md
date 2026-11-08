# Revisión estructural y descripciones comunes

Este incremento permite resolver una estructura ambigua con decisiones revisadas como datos, sin añadir reglas al código para cada presupuesto. El clasificador automático y el perfil de columnas anteriores se conservan. No se afirma que Nemotron haya aprendido a resolver automáticamente los dos casos pendientes.

## Qué se confirmó

Las decisiones siguientes las hizo **Codex como revisión estructural asistida**, cotejando las celdas originales. No se registran como aprobación del usuario ni como inferencias nuevas de Nemotron.

| Archivo | Conceptos | Grupos | Campos originales cotejados | Resolución |
| --- | ---: | ---: | ---: | --- |
| Obra civil | 11 | 14 | 44 | Nueve textos comunes se conservan en sus grupos y se relacionan con sus variantes medidas |
| original siop | 392 | 51 | 1,568 | Se conservaron los tres niveles, incluso los dos encabezados sin clave; no se inventaron sus códigos |

En original siop se contrastaron las relaciones de las claves existentes con las familias visuales de los encabezados. Las filas sin clave se mantuvieron sin clave. En Obra civil se cotejaron los once conceptos, sus padres, las descripciones propias y sus textos comunes. Ambos archivos pasaron materialización, validación, entrada por CLI y generación de un borrador estructural con las mismas columnas.

Los originales conservaron sus hashes. La evidencia privada está en `salidas/revision-estructural-20261107-213942/`: archivos de revisión, interpretaciones, borradores, resultados, cotejos y regresión. La materialización reutiliza una revisión ya hecha y no llama al modelo; sus tiempos no incluyen el trabajo de revisión ni son una medición de velocidad de Nemotron.

## Contrato de revisión

Un JSON de revisión contiene exactamente:

- `version`: entero 1.
- `archivo_sha256`: hash del Excel original completo. Cambiar de archivo o modificarlo invalida la revisión.
- `estructura`: hoja, final de cabecera y coordenadas originales que identifican las columnas, con el contrato tabular existente.
- `plan`: `filas`, `dudas`, `resumen_desde` y, opcionalmente, `contextos`.
- `revisor` y `motivo`: autor y fundamento reales. Un agente debe identificarse como agente.

`plan.filas` clasifica todas las filas no medidas anteriores al resumen mediante tipo, padre y motivo; no contiene textos ni cantidades para sustituir al original. Python recupera los valores desde las celdas. Se mantienen las validaciones de cobertura, padres, grupos vacíos, resumen y evidencia.

Ejemplo sintético del campo opcional para un texto común en la fila 3, acreditado por su variante medida de la fila 4:

```json
"contextos": {
  "3": {"hijo": 4, "motivo": "Esta fila aporta la actividad común y la variante sus dimensiones"}
}
```

El hijo debe existir y pertenecer directamente al grupo. La aplicación se limita a variantes directas del grupo marcado, no se heredan automáticamente los textos de todas las partidas. Las relaciones de descripción más complejas necesitan revisión.

## Uso

Desde la raíz, con archivos de salida nuevos:

```powershell
python mini_pai_interpretar.py "presupuesto.xlsx" --por-tabla --revision-estructura "revision.json" --salida "salidas/interpretacion-revisada.json"
```

El coordinador admite el mismo archivo al iniciar:

```powershell
python mini_pai.py "presupuesto.xlsx" --por-tabla --revision-estructura "revision.json" --indice "ruta/indice.sqlite" --sesion "salidas/sesion-nueva"
```

Para continuar se conserva la misma carpeta de sesión, sin repetir parámetros. El estado protege también el hash de la revisión; cambiarla exige otra sesión. La opción no se ignora en la ruta por bloques: exige `--por-tabla`. La salida del intérprete debe ser distinta del Excel y del JSON de revisión.

## Texto del cliente y contexto técnico

La descripción propia del cliente no se reescribe ni se concatena en los auxiliares. Los registros mantienen:

- El grupo original y su evidencia de celda.
- Una marca `descripcion_compartida` con hijo acreditado y motivo.
- En sus variantes, `contexto_descripcion` con hoja, fila, texto y evidencia originales del grupo común.

La entrada a búsqueda comprueba que ese contexto coincida con el grupo real; rechaza contexto alterado u omitido. Las búsquedas por términos y embeddings usan actividad común más descripción propia. La comparación técnica recibe ambas fuentes y puede citar fragmentos `CC...`; las citas deben pertenecer a una fuente original. Las guardas de unidad, valores técnicos e información insuficiente se conservan, también para especificaciones presentes en el texto común.

Sin contexto, se mantienen los fragmentos y el contenido de las solicitudes anteriores. El formato Excel no añade columnas ni intercambia campos: los textos propios siguen en los auxiliares; el grupo conserva el texto común. Markdown y Revisión indican la procedencia del contexto.

## Comprobaciones y límites

Pasaron **193 pruebas automatizadas**, incluidas revisión ligada al hash, rechazo de otro origen/cobertura inválida, protección al reanudar, contexto sin fuga a otra rama, citas verificables, valores técnicos distintos y uso de contexto por términos/embeddings. El validador de skill y los enlaces también se comprueban.

Se revalidaron los planes nativos guardados de los cuatro presupuestos anteriores con el código actual, sin diferencias de campos o jerarquía. Esto no es una nueva inferencia. Se comprobó por AST que `preparar_tabla` y `clasificar_tabla` no cambiaron; se retiraron los experimentos de nuevas instrucciones que producían regresiones.

Se ejecutó una búsqueda real en SQL Server, solo lectura, de tres conceptos de Obra civil con contexto: cinco candidatos por concepto, cero selecciones. Reutilizó 19,418 vectores sin recalcularlos y tardó 6.073 s. Recuperar candidatos no demuestra equivalencia técnica. No se compararon nuevos modelos ni se procesaron matrices para los presupuestos completos.

Los borradores son para revisar estructura y todavía no son Excel finales con matrices resueltas. No se repitió el pegado en Neodata. Otros archivos pueden requerir aclaraciones; esta capacidad de revisión no garantiza interpretar cualquier presupuesto de forma autónoma. El autor de la revisión es parte de la procedencia, no una firma criptográfica ni un sistema de autenticación.

Falta presentar las dudas estructurales como preguntas en una interfaz o herramienta para el agente. Ya existe el contrato para registrar la respuesta y continuar; MCP e interfaz siguen pendientes. El PR #3 continúa para revisión, sin fusión automática.
