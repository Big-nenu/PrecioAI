# Un comando para iniciar y continuar Mini-PAI

`mini_pai.py` coordina los módulos existentes: interpretación, recuperación con índice, comparación Nemotron, preguntas, decisiones, revalidación SQL y Excel más Markdown. No depende de Cline, no instala un MCP y no cambia el formato de salida. Sigue siendo una herramienta local por terminal, previa a la interfaz familiar.

## Iniciar

Desde la raíz del repositorio, con Ollama, el índice local y la configuración existente:

El índice usa NumPy de `requirements-laboratorio.txt`, que ya incluye las dependencias principales. No se añadió una dependencia nueva; en una instalación nueva, instalar ese archivo antes de usar la ruta con índice.

```powershell
python mini_pai.py "ruta/presupuesto.xlsx" --sesion salidas/ejecucion-001 --indice datos_privados/indices/catalogo-embeddinggemma.sqlite --por-tabla
```

Usar la ruta real del índice ya construido para reutilizarlo. Una ruta nueva crea otro índice; una identidad incompatible exige otra ruta. La conexión SQL permanece en lectura. La interpretación y evaluación usan el proveedor configurado; este comando no cambia modelos ni `.env`.

`--por-tabla` corresponde a la [ruta tabular](EXTRACCION-TABULAR.md) para una tabla estable. Sin ese indicador se utiliza el intérprete por bloques existente. Este admite `--hoja`, `--fila-inicial` y `--fila-final` para pruebas parciales; no combinarlos con `--por-tabla`. Si el intérprete informa un error o solicita revisión estructural, el flujo se detiene. El registro de decisiones de matrices no cambia el árbol. Para aplicar una revisión estructural explícita al iniciar, usar `--por-tabla --revision-estructura revision.json`, con el [contrato de revisión](REVISION-ESTRUCTURAL.md). Su hash se protege al reanudar; no se corrigen estructuras silenciosamente. El coordinador no añade una validación semántica de la estructura: una clasificación errónea que pase las guardas existentes todavía requiere revisión. No se supone que todos los formatos estén resueltos.

Para pruebas acotadas se puede añadir `--limite-conceptos 20`. Se interpreta el Excel original completo y se guarda ese checkpoint; solo la búsqueda, evaluación y entrega se limitan a los primeros veinte conceptos y sus agrupadores. El alcance se marca parcial y registra cuántos conceptos se interpretaron y procesaron. No recorta ni prepara el archivo original. Sin esa opción se procesan todos.

La carpeta debe ser nueva o vacía. El programa conserva el hash del Excel, los parámetros, la versión del código y los hashes de los archivos generados. Nunca coloca resultados sobre el presupuesto original.

## Preguntas y decisiones

Si faltan decisiones, termina con estado `esperando_decisiones` e indica la ruta de `preguntas-000.md`. Incluye hasta tres alternativas admisibles por concepto y conservar el original. Los incompatibles se excluyen; puede haber menos opciones. Las propuestas automáticas y sus limitaciones quedan registradas en `evaluacion.json`.

Para ver otra vez el estado, sin repetir interpretación, SQL de recuperación ni evaluación:

```powershell
python mini_pai.py --sesion salidas/ejecucion-001
```

Un agente o el usuario prepara un JSON con elecciones reales, usando el contrato existente:

```json
[
  {"hoja":"Conceptos","fila":20,"IdCodigo":null,"revisor":"Luis","motivo":"Conservar el original"}
]
```

`IdCodigo` es el ID SQL real de una opción o `null` para conservar el original. Para un código original ausente se puede incluir `codigo`, proporcionado realmente por el usuario. Los ejemplos de hoja/fila no son un límite ni una plantilla del presupuesto.

```powershell
python mini_pai.py --sesion salidas/ejecucion-001 --decisiones decisiones.json
```

Se admiten decisiones parciales: conserva cada resolución y genera otra lista de preguntas con los pendientes. La misma lista ya aplicada no se aplica dos veces. Las matrices elegidas se verifican por SELECT. No se reemplaza silenciosamente una decisión existente; se mantienen las restricciones del confirmador.

Para la elección global explícita usada en las pruebas, sin necesitar decisiones de ingeniería:

```powershell
python mini_pai.py --sesion salidas/ejecucion-001 --conservar-originales --revisor Luis
```

Esta opción conserva **todos** los conceptos originales, incluso si había propuestas IA o decisiones anteriores. Es una elección expresa de salida, no una afirmación de que no existen matrices equivalentes. Las evaluaciones y resoluciones anteriores se conservan. Si falta un código original, se detiene para pedirlo: no lo inventa. La resolución global no consulta SQL ni vuelve a llamar a IA; no evita las etapas iniciales al comenzar una sesión nueva.

Cuando no quedan pendientes, entrega `presupuesto.xlsx` y `presupuesto.md`. Antes de exportar, las matrices conservadas se consultan nuevamente en SQL. Conservar originales no necesita esa consulta. Volver a ejecutar una sesión terminada devuelve la misma entrega sin regenerarla.

## Qué conserva y qué no repite

- `sesion.json`: estado, parámetros, hashes y tiempos de cada etapa terminada.
- `interpretacion.json`, `candidatos.json`, `evaluacion.json`: resultados de los módulos existentes.
- `decisiones-NNN.json`, `resolucion-NNN.json`: elecciones y resultados sucesivos, sin sobrescribir los anteriores.
- `preguntas-NNN.md`: preguntas correspondientes a cada resolución.
- `presupuesto.xlsx` y `presupuesto.md`: entrega final, con las validaciones existentes.

Los archivos permanecen en `salidas/`, excluidos de Git. No editar los checkpoints: si cambia el original, el código del flujo o un archivo registrado, la reanudación se bloquea. Usar la misma versión o una sesión nueva. El estado no sustituye las comprobaciones del selector, confirmador o exportador.

Los checkpoints son por etapa completa, no por bloque ni llamada IA. Si una etapa falla, se conservan las etapas anteriores; al continuar se repite solo la etapa no terminada. No se promete recuperar una petición en curso. Un archivo escrito justo antes de una interrupción, sin registro en el estado, se conserva y provoca un error explícito; no se adopta ni sobrescribe automáticamente.

`sesion.lock` evita dos procesos sobre la misma sesión. Si una terminación forzada deja el bloqueo, comprobar que el proceso ya terminó antes de retirarlo manualmente. No se elimina el bloqueo de otra ejecución automáticamente.

## Qué sigue

La clasificación de metadatos, partidas y subpartidas se corrigió y se cotejó sobre dos archivos originales. La [prueba actual](ORIGINALES.md) separa extracción completa del catálogo y recorrido funcional de veinte conceptos por archivo, conservando originales. La prueba controlada histórica de abajo se mantiene como antecedente; los nuevos resultados no convierten cualquier formato en compatible.

La prioridad sigue siendo facilitar las preguntas y confirmaciones de estructura, y comprobar más archivos, según [GENERALIZACION.md](GENERALIZACION.md). Una vez fiable la extracción, se plantea un MCP mínimo que exponga este mismo flujo a distintos agentes, sin duplicar etapas ni depender de Cline. Después, una interfaz local mínima sobre el flujo: subir Excel, consultar estado/preguntas, registrar elecciones o conservar originales y descargar Excel/reporte. Después se comprueba el acceso desde la laptop del papá del usuario. No están implementadas esas pantallas, autenticación, suscripciones ni despliegue web.

Las inconsistencias técnicas conocidas de Nemotron siguen requiriendo revisión; un coordinador no convierte una propuesta incorrecta en equivalente. Ver [controles de acción principal](ACCION-PRINCIPAL.md).

## Comprobación real del coordinador — 7 de noviembre de 2026

La prueba positiva usó un fixture controlado de los primeros veinte conceptos del E2 y sus cuatro agrupadores, copiados con celdas y valores originales, sin portada/metadato global. Antes de buscar, se cotejaron los 80 campos originales y la jerarquía contra la referencia. Hubo inferencia nueva y SQL reales; no se reutilizó una interpretación anterior para esta prueba.

| Etapa | Segundos |
| --- | --- |
| Interpretación nueva | 11.392 |
| Recuperación con índice | 6.054 |
| Evaluación Nemotron | 374.688 |
| Conservar originales y exportar, proceso ya cargado | 0.102 |
| Reabrir sesión terminada por CLI en proceso nuevo | 0.483 |

El flujo llegó a veinte pendientes. Se continuó con la elección global de conservar originales, sin llamar a interpretación, búsqueda, evaluación ni conexión SQL. Esas funciones se sustituyeron por errores durante la comprobación: ninguna se invocó. Los tres checkpoints conservaron sus hashes. La entrega final tiene veinte conceptos originales, cuatro agrupadores y cero matrices; se reabrió y se cotejaron códigos/descripciones principales y auxiliares, unidades, cantidades, jerarquía y columnas. Reabrir la sesión no regeneró el Excel.

Pasaron **165 pruebas automatizadas**, ocho nuevas de pausa/reanudación, decisiones parciales, idempotencia, modificación de entrada/checkpoints/código, bloqueo, protección de carpeta, revalidación SQL y ayuda redirigida en Windows.

Los intentos con portada no se cuentan como éxito: la ruta por bloques de Propuesta falló en filas 33–37 y una copia tabular clasificó encabezados como conceptos; los fragmentos de E2 con metadato global tampoco completaron una estructura válida. Se detuvieron esos ensayos sin entrega final. Se retiró un ajuste experimental del intérprete que no corrigió los controles. El fixture positivo controlado no demuestra que un presupuesto arbitrario sin preparar sea interpretado bien.

Evidencia y entrega vigentes: `salidas/prueba-flujo-controlado-20-2026-11-07/prueba-01/`, con `prueba-reanudacion.json`, cotejo, llamadas reales y `reporte-prueba.md`; Excel y Markdown finales bajo `sesion/`. Las carpetas de los intentos anteriores conservan sus diagnósticos/estados, no son entregas finales. No se modificaron los presupuestos originales ni se repitió el pegado en Neodata. No se implementó interfaz, MCP ni cambio de modelos.
