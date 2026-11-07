# Continuidad de Mini-PAI — 6 de noviembre de 2026

## Punto de partida

- Repositorio: Big-nenu/PrecioAI. [PR #3](https://github.com/Big-nenu/PrecioAI/pull/3), rama `mini-pai-busqueda-revisable`, abierto y sin fusionar.
- Último commit de código comprobado: `fe1096c2c4b2ffd237095333d3e13ca80c2d051d`. La documentación posterior puede añadir commits en la misma rama.
- Modelo principal: `nemotron-3.5-bolt:e4b`. La prueba final usó Ollama, razonamiento habilitado, contexto 12288 y máximo 6144 tokens.
- Hardware de la sesión: RTX 4060 de 8 GB. No se debe asumir que los modelos caben simultáneamente ni extrapolar velocidades de otra GPU.
- Modelos disponibles: `embeddinggemma-2:270m`, `qwen3-embedding:0.6b`, `d1:3b`, `d3:2b`. Los dos últimos candidatos nuevos descargados fueron Qwen3-Embedding y D3. Estar descargados no implica que estén integrados o evaluados en este flujo.

## Objetivo y reglas que deben mantenerse

Mini-PAI entrega Excel y Markdown para revisión y copiado manual a Neodata PU Win+. No controla Neodata ni importa automáticamente, y no desarrolla interfaz web.

La IA interpreta estructuras variables, conserva datos originales y jerarquía y busca matrices reales en ConstruBase solo por lectura. Código/Descripción completa/Unidad de una matriz elegida provienen de SQL; los auxiliares y cantidad son del cliente. En casos dudosos se muestran hasta tres opciones y la alternativa de conservar el original sin matriz. Se espera la respuesta real del usuario.

Sin matriz, se repiten código y descripción del cliente en principales y auxiliares. Si no tiene código, se solicita uno y se registra aparte, sin modificar el original. Una búsqueda vacía no prueba ausencia en todo ConstruBase. Un fallo nunca debe presentarse como búsqueda vacía. El formato de las hojas existentes está probado por el usuario; conservarlo.

## Qué quedó implementado y comprobado

- Interpretación por bloques y evidencia de celdas; búsqueda SQL parametrizada; comparación con referencias a fragmentos; confirmación y verificación SQL; exportador Excel + Markdown.
- Validación numérica compartida, fracciones completas y convención documentada de miles/decimales. No convierte unidades ni adivina todas las configuraciones regionales.
- Propuestas contradictorias o con pruebas inválidas quedan pendientes y auditadas. Las citas reales opcionales en no_aplica se verifican, sin ocultar requisitos explícitos o esenciales.
- Orden de revisión con puestos nominados y validación de IDs completos/únicos. Las tres matrices preferidas antes ocultas quedaron primeras en los casos focales.
- **127 pruebas automatizadas pasaron**. Controles piedra/concreto y plantilla de espesores distintos sin selección automática.
- Consolidado de 20: cuatro propuestas IA revalidadas por el código final y verificadas en SQL, trece pendientes y tres búsquedas vacías; cero errores operativos tras las repeticiones documentadas.
- Excel de prueba resuelto: cuatro selecciones IA, siete elecciones delegadas a Codex y nueve originales. No atribuir esas elecciones a una aprobación automática del modelo.

Las cuatro propuestas se revalidaron sobre respuestas guardadas, sin nueva inferencia. Los milisegundos de esa revalidación no son tiempos de generación. Los datos privados permanecen fuera de Git.

## Prioridad vigente tras la aclaración de producto

PrecioAI conserva el alcance futuro de plataforma web completa. Mini-PAI es el producto de menor alcance que debe funcionar primero localmente, después mediante interfaz familiar y finalmente como servicio por suscripción. Interfaz, autenticación y cobros no están implementados. Ver los README vigentes; los anteriores se conservan en las carpetas de historial.

1. Auditar el presupuesto actual de 78 conceptos: el resumen de Cline mezcló valores de dos filas. Cotejar archivos estructurados antes de atribuir el error al extractor o continuar a SQL. No resolverlo únicamente mediante nuevas instrucciones de chat.
2. Comprobar cobertura, jerarquía y correspondencia de campos; verificar conflictos de códigos entre matrices y conceptos originales conservados. La guarda actual del exportador cubre matrices seleccionadas, no demuestra la regla general.
3. Ejecutar y medir el flujo completo con decisiones humanas reales y Excel revisable. La suite no sustituye esta prueba.
4. Comparar EmbeddingGemma y Qwen3-Embedding en la misma muestra: recuperación, tiempo y memoria. Si se justifica un índice, mantenerlo separado de ConstruBase y medir construcción y consultas por separado.
5. Comparar D1/D3 sobre los mismos conceptos y candidatos; conservar los ensayos D1/TEV1 como antecedentes, no como autorización para cambiar Nemotron. Alta confianza no es aprobación.
6. Integrar solo mejoras demostradas reutilizando el laboratorio y proveedor actuales. Cuando el flujo sea confiable, preparar la interfaz familiar; después el servicio para otros usuarios.

Tras la reorganización documental y traslado de los 19 módulos a `tests/`, pasaron nuevamente las 127 pruebas automatizadas. No se repitieron inferencias ni pruebas reales de SQL y no se cambió la lógica del producto, el formato Excel o la skill instalada. Los originales y `.env` conservan sus rutas y contenido.

El orden no puede recuperar una matriz que quedó fuera de los cinco candidatos. Ocurrió con acero 5/16. M/ML y otras diferencias de unidad siguen bloqueando confirmaciones hasta resolverlas. La clasificación semántica aún necesita revisión: algunos incompatibles se etiquetan insuficientes, aunque no se aprueben.

## Evidencia local de la sesión

Los directorios siguientes están en la carpeta `outputs` de la sesión de Codex, fuera del repositorio. No subir presupuestos, credenciales, respuestas completas ni Excel privados al PR.

| Directorio | Evidencia |
| --- | --- |
| `prueba-nemotron-delegada-2026-11-06` | Tres conceptos, evaluación nativa, decisiones delegadas, Excel y reporte |
| `prueba-20-nemotron-2026-11-06` | Primera muestra de 20, `tiempos.json`, interpretaciones, candidatos, evaluación y entregables |
| `correcciones-20-nemotron-2026-11-06` | Pasadas de depuración, reintentos, `evaluacion-final.json`, focos con puestos nominados, `analisis-consolidado.json`, `resuelto.json`, Excel y `reporte-correcciones.md` |

No confundir esos archivos: `evaluacion-final.json` es una inferencia nativa con el contrato de desarrollo de esa pasada; `analisis-consolidado.json` incorpora focos y revalidación sin inferencia adicional. La procedencia y límites están en el reporte.

## Retomar sin perder trabajo

Leer primero este documento, [README.md](README.md), [BUSQUEDA.md](BUSQUEDA.md), [GUIA-CLINE.md](GUIA-CLINE.md) y la skill. Revisar `git status`, rama y estado del PR; no descartar cambios locales, no fusionar ni procesar el presupuesto completo por defecto. Usar rutas nuevas para resultados. No imprimir `.env` ni pedir credenciales en el chat.

Para repetir las comprobaciones de código, desde la raíz:

```powershell
python -m unittest discover -q
```

Si TEMP del entorno restringido impide las pruebas, dirigir TEMP/TMP a un directorio nuevo dentro del workspace; no alterar la lógica para sortear los tests. Los modelos y SQL no son necesarios para esta suite. Las pruebas nativas se ejecutan aparte y sus tiempos deben registrarse por fase.

## Auditoría del 7 de noviembre de 2026

Ver [AUDITORIA-EXTRACCION.md](AUDITORIA-EXTRACCION.md). La ejecución de referencia falló en filas 71–75 después de 285.779 s y veinte llamadas. En los 44 conceptos parciales hasta fila 70 hubo once campos omitidos y errores de jerarquía; no existe un JSON final válido. Los focos no resolvieron todos los controles y los cambios experimentales del intérprete se retiraron. Sigue pendiente corregir la extracción, antes de SQL y modelos adicionales.

La corrección definitiva de esta auditoría está en el exportador: impide códigos iguales con descripciones distintas también entre originales conservados y matrices seleccionadas. Pasaron 129 pruebas. Evidencia privada bajo salidas/auditoria-extraccion-2026-11-07/. No se modificó presupuesto, configuración, ConstruBase, formato Excel ni skill instalada; no se generó un Excel nuevo.

## Extracción tabular comprobada

La [nueva ruta --por-tabla](EXTRACCION-TABULAR.md) recuperó 78 conceptos, 15 agrupadores y 312 campos sin diferencias contra el Excel, en 39.467 s y tres llamadas incluido reintento. El presupuesto conserva SHA256. Pasaron 137 pruebas. La ruta antigua por bloques no se reemplazó; otros formatos requieren validación. Skill global y versionada sincronizadas; conversación Cline aún no probada.

Evidencia privada: salidas/estructura-tablas-2026-11-07/ejecucion-02/. Los ensayos del directorio padre y ejecución 01 incluyen fallos, no usarlos como resultado final. El siguiente paso del presupuesto actual es búsqueda y selección usando el JSON cotejado; no se ha generado su Excel final ni probado otros modelos.

## Prueba preparada para ejecutar por el usuario

`probar_modelos_mini_pai.py` compara secuencialmente Nemotron y Gemma con extracción de 78 conceptos y candidatos fijos de la muestra anterior de 20. Instrucciones en [PRUEBA-MODELOS.md](PRUEBA-MODELOS.md). El paquete privado preparado está en `datos_privados/prueba-modelos/`, excluido de Git; no contiene resultados nuevos de modelos. Se verificaron sus hashes y se prepararon dos controles negativos con candidatos reales incompatibles.

La herramienta genera un Markdown distinto por modelo, detalles JSON y reportes parciales tras errores o interrupción, sin SQL ni cambio de .env. Las ocho pruebas nuevas del script usan respuestas simuladas; la comparación real la ejecutará el usuario y compartirá los .md. No afirmar que ya se midió Gemma o que ganó un modelo antes de esos reportes.

## Pruebas reales completadas — 7 de noviembre de 2026

Esta sección actualiza las pendientes históricas anteriores. Se revisaron los reportes compartidos por el usuario: Nemotron completó la extracción de 78 conceptos y 15 agrupadores en 53.397 s; Gemma falló en el padre de un registro. La etapa técnica fija tardó 376.071 s con Nemotron y 810.076 s con Gemma. Se mantiene Nemotron; propuestas que pasan guardas no equivalen a decisiones semánticamente correctas. Ver [resultados y límites](PRUEBA-MODELOS.md).

Se ejecutaron las tres pruebas autorizadas: recuperación con EmbeddingGemma 270m y Qwen3-Embedding 0.6b contra 19,418 registros tipo 4, índices locales persistentes y comparación de D1/D3/Nemotron sobre los mismos 71 pares. [Reporte público completo](PRUEBA-RECUPERACION-DECISIONES.md).

- EmbeddingGemma recuperó referencias útiles entre tres candidatos en 10/12 consultas etiquetadas; Qwen 6/12, o 7/12 con centrado. Son referencias exploratorias, no equivalencias confirmadas ni precisión general.
- Índices en `datos_privados/indices/`, con construcción inicial de 309.70 y 233.44 s. Se reutilizaron 19,418 documentos por modelo sin embeddings nuevos del catálogo. Recuperación completa de 20 consultas con modelo cargado: 1.706 y 1.692 s, incluido ordenar los candidatos. No es tiempo de presupuesto completo.
- D1/D3/Nemotron: 12.44/10.83/529.23 s para los mismos 71 pares, cero errores de API. D1 clasificó cuatro controles incompatibles como equivalentes. D3 no etiquetó ninguno de los diez negativos como incompatible. Nemotron acertó nueve etiquetas, pero trató una diferencia de espesor como compatible y también hizo suposiciones en cimbra. Ninguna respuesta se aplicó al selector.
- Código mínimo: `indice_local.py`, prefijo oficial de Qwen y seis pruebas nuevas. Pasaron 151 pruebas automatizadas; se cotejó nuevamente el catálogo por SELECT y el SHA256 del Excel original.

Evidencia privada completa y reporte por concepto: `salidas/tres-pruebas-2026-11-07/`. No subir esos archivos ni los índices a GitHub. El siguiente incremento propuesto es conectar la recuperación con índice al buscador existente, conservando Nemotron, las guardas y la revalidación SQL. Falta medir ese flujo integrado, ampliar referencias expertas y revisar las decisiones dudosas; no se generó otro Excel, ni se implementó MCP, memoria de decisiones o interfaz. PR #3 sin fusionar.

## Índice conectado y Excel de revisión — 7 de noviembre de 2026

El incremento propuesto arriba ya se implementó: `mini_pai_buscar.py --indice archivo.sqlite` utiliza el catálogo SQL vigente, valida/reutiliza EmbeddingGemma 270m y devuelve el contrato existente de candidatos a `mini_pai_seleccionar.py`. No se cambió el selector ni el exportador; la búsqueda anterior sigue disponible. [Método, comandos y límites](INTEGRACION-INDICE.md).

Sobre los mismos 20 conceptos y cuatro agrupadores de la muestra anterior: 80 campos cotejados sin diferencias, 19,418 vectores reutilizados y cero nuevos. Recuperación completa 4.399 s, con carga y SQL; selección Nemotron 430.901 s en veinte llamadas, sin errores de API/contrato. No se midió otra extracción IA ni el presupuesto completo.

El modelo propuso cinco selecciones que pasaron guardas y SQL. La auditoría retiró una: construir un cimiento no equivale a demolerlo. El Excel revisado conserva cuatro propuestas de acero verificadas otra vez por SELECT y 16 pendientes, con opciones para el usuario. Se conservó sin alterar la ejecución original; el JSON revisado identifica la intervención de Codex. No se respondió por el usuario ni se generó un Excel final. La exportación final se comprobó bloqueada por las decisiones pendientes.

Evidencia y entregables privados en `salidas/integracion-indice-20-2026-11-07/`: `evaluacion-sin-auditar.json`, `evaluacion-revisada.json`, `mediciones.json`, `llamadas.json`, `presupuesto-revision.xlsx` y `reporte-prueba.md`. Se reabrió el libro y se cotejaron columnas, jerarquía, datos originales y datos SQL de las matrices vigentes; no se repitió el pegado en Neodata. Pasaron 156 pruebas automatizadas (cinco nuevas). Los hashes del original, muestra y `.env` permanecieron intactos.

**Siguiente prioridad:** corregir y comprobar la evaluación de la acción principal (construir/demoler) antes de confiar en la selección automática. La auditoría específica de este ensayo no es una guarda general del producto. Revisar con el usuario alcance/inclusiones de las propuestas, resolver las 16 dudas y generar el Excel final. La comparación sigue dominando el tiempo. La skill instalada no se modificó; la guía del repositorio explica la nueva ruta para cualquier agente con terminal. PR #3 sin fusionar.

## Acción principal corregida y controles — 7 de noviembre de 2026

Se ajustaron las instrucciones de la skill y del selector para comparar acción/objeto antes de material/unidad, admitir sinónimos y acciones nominales y separar contradicciones de omisiones. El esquema ya no permite no_aplica en procedimiento/alcance, coincidiendo con las guardas que ya lo prohibían. No se relajaron validadores, cambiaron campos, modelo, SQL ni Excel. [Reporte completo](ACCION-PRINCIPAL.md).

Se reevaluaron nueve conceptos con los mismos candidatos, incluidos todos los seleccionados anteriormente. Los once pendientes restantes se conservaron sin inferencia nueva. Nemotron pasó la construcción/demolición a incompatible sin auditoría manual específica. Cuatro positivos controlados conservaron selección y diez negativos no se seleccionaron. La clasificación exacta pasó en cinco de seis controles: el conjunto alternativo de plantillas sigue insuficiente pese al espesor diferente; el conjunto focal sí dio incompatible. No afirmar que todos los dictámenes son correctos o estables.

Primera pasada conservada: detectó respuestas no_aplica inválidas, antes de alinear el esquema. La segunda pasada tardó 195.539 s para nueve conceptos y usó quince llamadas incluidos los controles. Pasaron 157 pruebas automatizadas (una nueva del contrato de estados) y la validación de la skill. Se añadieron dos escenarios de skill; no son sesiones ejecutadas en Cline. La skill global instalada se sincronizó con la versionada y se cotejaron sus hashes.

La segunda pasada propuso dos matrices. La auditoría del entregable retiró CIM-ACR-Z04 por limitarse a zapatas/contratrabes/dados y no acreditar todas las inclusiones del cliente. La entrega revisada queda con una propuesta SQL vigente (fila 39) y 19 pendientes. Se documentan además excesos/inconsistencias en motivos sobre alambre; los originales no se alteraron. No atribuir la retirada de alcance a una decisión automática del modelo.

**Entrega vigente:** `salidas/accion-principal-2026-11-07/pasada-02/entrega-revisada/presupuesto-revision.xlsx` y `reporte-prueba.md`, con `evaluacion-actualizada.json`. Los directorios padre conservan respuestas nativas, controles y el primer borrador; no confundirlo con la entrega auditada. Se reabrió el libro y se cotejaron los veinte conceptos, cuatro agrupadores, columnas, jerarquía, auxiliares, cantidades y matriz SQL. Final bloqueado por pendientes. No se repitieron extracción, búsqueda ni pegado en Neodata. PR #3 sin fusionar; siguiente trabajo: resolver dudas y consistencia técnica antes de ampliar el presupuesto.

## Comando único reanudable — 7 de noviembre de 2026

`mini_pai.py` coordina los módulos existentes y guarda checkpoints por etapa completa. Inicia con Excel/índice/carpeta de sesión; se detiene con preguntas; admite JSON de decisiones parciales o la elección explícita de conservar todos los originales. No repite etapas terminadas; verifica entrada/código/artefactos y consulta de nuevo las matrices que se exportan. No agrega dependencias, interfaz, MCP ni modifica el formato Excel. La skill no cambió en este incremento; las guías enlazan el comando nuevo. Ver [FLUJO.md](FLUJO.md).

Validación: 165 pruebas automatizadas, ocho nuevas. Prueba positiva nativa sobre un fixture controlado del E2: cabecera, veinte conceptos y cuatro agrupadores con valores/coordenadas originales, sin portada/metadato global. Se cotejaron 80 campos y jerarquía antes de buscar. Interpretación 11.392 s, recuperación 6.054 s y evaluación 374.688 s. Quedaron veinte pendientes; conservar originales y exportar tardó 0.102 s dentro del proceso ya cargado. La reapertura CLI en otro proceso tardó 0.483 s. Se impidieron llamadas a interpretación, búsqueda, evaluación y conexión SQL durante la continuación; no se invocaron y los tres checkpoints no cambiaron. Se cotejó el Excel final: veinte originales, cuatro agrupadores y cero matrices.

**Prueba vigente del coordinador:** `salidas/prueba-flujo-controlado-20-2026-11-07/prueba-01/reporte-prueba.md` y `prueba-reanudacion.json`; entrega bajo `sesion/presupuesto.xlsx` y `sesion/presupuesto.md`. Se conserva aparte el final de la muestra anterior `salidas/conservar-originales-20-2026-11-07/`, donde el usuario eligió mantener los veinte conceptos de Propuesta sin matrices.

Los intentos con portada fallaron o dieron jerarquías incorrectas y no se presentan como exitosos: Propuesta por bloques falló en filas 33–37, la copia tabular produjo tipos/parentescos incorrectos y fragmentos de E2 no resolvieron el metadato global. Los diagnósticos están en las carpetas `flujo-unico-20-*`, `prueba-flujo-tabla-20-*` y `prueba-flujo-e2-20-*`. Se retiró el cambio experimental de instrucciones del intérprete; no se debilitaron sus guardas para pasar la prueba. Una primera copia con estilos quedó inválida y no se usó: la prueba final usa valores cotejados. Los originales permanecieron intactos.

**Siguiente prioridad concreta:** corregir y comprobar metadatos, partidas/subpartidas y conceptos contra los presupuestos originales sin preparar, antes de confiar en el flujo o desarrollar la interfaz familiar. Después, interfaz local mínima de subida, preguntas, conservar originales y descarga; finalmente acceso desde la laptop. La prueba controlada comprueba coordinación/reanudación, no interpretación general ni equivalencias técnicas. PR #3 sin fusionar.


## Estructura de originales y recorrido funcional — 7 de noviembre de 2026

Se continuó la prioridad de clasificación en el repositorio real de Projects. La IA clasifica por bloques de diez con estilos originales, grupos anteriores, trabajos vecinos y anticipación; Python recupera valores íntegros y asigna padres según los roles y la secuencia. El contrato interno solo pide tipo/motivo y distingue documento/resumen de grupos. Se mantienen los validadores; solo se permite un encabezado activo provisionalmente vacío entre bloques. No cambian SQL, modelo, Excel ni dependencias.

Resultado: E2 con 78 conceptos/15 agrupadores y 312 campos; Propuesta con 438/115 y 1,752 campos. Cotejos de valores y jerarquía sin diferencias en las pasadas aceptadas. El coordinador permite limitar etapas posteriores con --limite-conceptos, guardando íntegra la interpretación del original. Se probó búsqueda, evaluación, preguntas, conservar originales, Excel y Markdown con veinte conceptos por archivo. Entregas: salidas/flujo-originales-2026-11-07/01-sesion/ y 06-sesion/. Las resoluciones no repitieron etapas ni abrieron SQL; los checkpoints quedaron intactos. Pasaron 172 pruebas. Los fallos intermedios se conservan y no se cuentan como resultados válidos. Ver [ORIGINALES.md](ORIGINALES.md) para tiempos, procedencia y límites.

No se certifican las propuestas del selector. No se procesaron matrices de todos los conceptos, no se repitió el pegado ni se implementó interfaz. El MCP sigue pendiente y se plantea como capa mínima del coordinador existente, independiente de Cline. PR #3 para revisión, sin fusionar.


## Generalización de columnas y árbol — 7 de noviembre de 2026

Se eliminaron el límite interno de dos niveles y la exigencia de rótulos en una sola fila. El mismo árbol por padre se valida en materialización/búsqueda y se conserva al exportar, sin cambiar columnas. La clasificación tabular usa partida/subpartida/padre como la ruta por bloques; una duda estructural explícita detiene la etapa sin reintentos para forzar aprobación. La evidencia de columnas permite rótulos o filas medidas, con controles para no ocultar trabajos ni eliminar datos repetidos.

Pasaron 180 pruebas. Hay cotejos correctos de E2, Estándar, PRESUPUESTO DE OBRA y Propuesta; los dos últimos planes se revalidaron sin nueva inferencia después del ajuste de columnas. original siop sigue sin árbol correcto y Obra civil se detiene ante descripción compartida ambigua. No se certifican estos dos casos ni se afirma comprensión universal. No se ejecutaron SQL ni comparaciones técnicas nuevas. Ver [GENERALIZACION.md](GENERALIZACION.md) para evidencia, tiempos, contratos y límites.

Prioridad: revisión estructural y contexto de descripciones compartidas, después selección fiable de ruta y más formatos. MCP e interfaz siguen pendientes. La skill versionada se ajustó al contrato general; no hay reglas por archivo ni nuevas dependencias. PR #3 para revisión, sin fusionar.
