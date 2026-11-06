# Mini-PAI — Excel de presupuesto a Neodata

## Objetivo

Primera herramienta independiente dentro del repositorio PrecioAI. Convertir presupuestos de construcción recibidos en Excel, con estructuras variables o desordenadas, a un archivo `.xlsx` revisable para copiar manualmente sus conceptos a Neodata PU Win+. El usuario realiza esa operación. Mini-PAI no controla Neodata, no se conecta a su interfaz ni automatiza la importación. Resolver primero esta necesidad práctica y reutilizar después las herramientas en PrecioAI.

**Alcance de esta etapa:** transformar catálogos de conceptos y conservar partidas, subpartidas, códigos, descripciones, unidades y cantidades. No generar todavía matrices nuevas ni construir la plataforma web.

## Flujo deseado (aún no implementado de extremo a extremo)

1. El usuario proporciona un Excel de presupuesto. No asumir columnas, encabezados ni jerarquías fijas.
2. La IA identifica partidas, subpartidas y conceptos; extrae código, descripción, unidad y cantidad sin perder la relación con el archivo original. Las ambigüedades se reportan, no se inventan.
3. Para cada concepto, identifica palabras clave y atributos técnicos y consulta ConstruBase **en modo lectura**. Una coincidencia de palabras no demuestra equivalencia técnica; comparar también unidad, alcance y condiciones.
4. Si se encuentra una equivalencia técnicamente válida, utilizar el **Código** del concepto de ConstruBase y conservar en **Código auxiliar** la clave original del cliente. Mantener la descripción propia del concepto de ConstruBase y la descripción original en **Descripción auxiliar**.
5. Si no se ha confirmado una equivalencia, conservar código y descripción completos del cliente en los auxiliares, así como unidad y cantidad originales. Dejar vacíos los campos de ConstruBase y señalar el caso en el reporte. No inventar códigos, descripciones ni coincidencias. Resolver o marcar conflictos cuando un mismo código principal corresponda a descripciones diferentes.
6. Generar el Excel con la estructura de partidas/subpartidas y un reporte de conceptos encontrados, no encontrados y dudosos.
7. El usuario revisa el archivo y realiza el copiado manual a Neodata PU Win+. La comprobación manual del resultado no requiere desarrollar automatización de Neodata.

**Importante:** la confirmación de equivalencias y su exportación están pendientes. El primer exportador solo genera conceptos sin selección confirmada; rechaza selecciones no nulas para no tratarlas como válidas ni descartarlas silenciosamente.

## Formato de salida de referencia

El *Manual PUWIN+*, páginas 246 y 458, describe el uso de códigos auxiliares y el copiado desde Excel con las columnas **en este orden**:

```text
Partida | Código | Código auxiliar | Descripción auxiliar | Unidad | Cantidad
```

El ejemplo privado `CATÁLOGO DE CONCEPTOS PARA ANALISIS DE MAESTRO.xls`, hojas PLANTILLA y EJEMPLO, usa **ocho columnas**: `Partida | Código | Código auxiliar | Descripción completa | Descripción auxiliar | Unidad | Cantidad | Tipo`. Es la referencia principal para la hoja Catálogo. Descripción completa corresponde al concepto de ConstruBase cuando exista una selección confirmada; nunca debe sustituirse por la descripción auxiliar del cliente. Los nombres de los encabezados de partida van en Descripción completa, como en el ejemplo.

El formato de seis columnas se conserva en la hoja Copiar auxiliares. No se debe copiar indistintamente la tabla de ocho columnas como si fuese la de seis. El manual (pp. 246–247 y 456–458) describe los campos completos, auxiliares y rutas de partidas separadas por punto; no demuestra por sí solo el comportamiento de pegado del ejemplo de ocho columnas.

El Código auxiliar admite **hasta 20 caracteres** según el manual. El código principal identifica el concepto interno; el auxiliar permite conservar el código de la licitación o cliente sin duplicar conceptos prácticamente iguales. La descripción auxiliar conserva el texto del cliente.

**Pendiente de validar:** comportamiento exacto al pegar/importar conceptos no existentes en el catálogo, manejo de descripciones completas y conflictos de códigos, y correspondencia de la estructura de partidas y subpartidas. No afirmar compatibilidad definitiva hasta probarlo en Neodata.

## Etapas pequeñas

| Etapa | Tarea | Estado |
| --- | --- | --- |
| 0 | Conectar y consultar ConstruBase | **Parcialmente comprobado**: consultas SQL y recuperación de matrices; falta integrar IA y evaluar equivalencias |
| 1 | Interpretar un Excel desconocido y distinguir partidas, subpartidas y conceptos | **En validación parcial**: inspección sin columnas fijas y clasificación IA con evidencia; tres bloques reales validados, libro completo pendiente |
| 2 | Buscar y evaluar conceptos equivalentes en ConstruBase | **Búsqueda inicial conectada** al JSON interpretado, con candidatos SQL revisables; equivalencias técnicas y selección pendientes |
| 3 | Generar Excel con códigos y descripciones auxiliares | **Primer Excel de revisión disponible**: ejemplo de ocho columnas, vista auxiliar de seis y reporte; selecciones confirmadas pendientes |
| 4 | Reporte y comprobación manual por el usuario en Neodata | **Reporte inicial disponible**; comprobación manual pendiente, sin automatizar Neodata |

**Avance actual:** representación intermedia y búsqueda SQL de candidatos comprobadas
con una parte de un presupuesto real. Revisar los campos incompletos y los candidatos
antes de confirmar equivalencias; siguen pendientes el libro completo y otros formatos.

## Primer Excel de revisión (2026-11-06)

Faltaba transformar el JSON ya interpretado y buscado en un libro, manteniendo
separados los campos de ConstruBase y del cliente. `mini_pai_exportar.py` reutiliza
la validación existente y `openpyxl`; no requiere SQL, IA ni dependencias nuevas.

```powershell
python mini_pai_exportar.py salidas/candidatos.json --salida salidas/revision.xlsx
```

La salida debe ser nueva: no sobrescribe archivos. También admite el JSON de
interpretación sin búsquedas, cuyos conceptos quedan Sin evaluar.

- **Catálogo:** las ocho columnas del ejemplo. Conserva las filas de partidas y
  subpartidas. Sin selección confirmada, Código y Descripción completa quedan
  vacíos en los conceptos; los auxiliares conservan los textos completos del
  cliente. Unidad y Cantidad son las originales, Tipo es 4 para los conceptos.
- **Copiar auxiliares:** las seis columnas del manual, en su orden. En encabezados,
  el nombre del grupo va en Descripción auxiliar. Sin filas vacías de separación.
- **Revisión:** alcance parcial, cero confirmadas, hoja/fila de origen, padre,
  claves de agrupación originales, cantidad original como texto, evidencia y
  observaciones. Distingue Dudosa (hay candidatos sin confirmar), No encontrada
  en esta búsqueda y Sin evaluar. No encontrada no prueba ausencia en el catálogo.

Las rutas respetan los padres por hoja/fila: si la subpartida ya contiene el prefijo
original, no lo duplica; si no, une los niveles por punto como en el manual. Sin
clave utiliza el nombre original. No agrega códigos ni agrupadores ficticios.
Rutas repetidas o sin partida se señalan para revisión, conservando todos los
registros. Los códigos permanecen como texto, incluidos ceros iniciales.
Las cantidades decimales inequívocas se guardan numéricamente; las ambiguas o de
precisión no representable se conservan como texto y se señalan. No hay conversiones
de unidades. Se advierten auxiliares mayores de 20 caracteres sin recortarlos y se
rechazan textos que excedan el límite de una celda, sin truncarlos.

**Comprobación:** primera salida real limitada a los nueve conceptos ya interpretados,
una partida y tres subpartidas, con las cuatro unidades completadas del PR #3.
Ninguna equivalencia fue confirmada. El libro original y ConstruBase permanecen
intactos; el exportador ni siquiera abre SQL ni el Excel original.

**Pendiente para la salida final:** revisar la estructura con el usuario, completar
la interpretación del libro, confirmar equivalencias técnicas y recuperar el código,
la descripción íntegra y la unidad validada de cada selección. Las diferencias de
unidad deberán señalarse sin convertir la cantidad original automáticamente.
Comprobar manualmente el copiado en Neodata y resolver conflictos de códigos.
Este archivo es una revisión parcial, no una declaración de compatibilidad de pegado.

## Arquitectura provisional

La conexión entre interpretación y búsqueda está en
[BUSQUEDA.md](BUSQUEDA.md): conserva el presupuesto original y añade hasta cinco
candidatos por concepto, pendientes de revisión humana.

La evaluación inicial de recuperación con embeddings y de pares con TEV1 está
documentada en [LABORATORIO.md](LABORATORIO.md). Reutiliza piezas de StoneWave
como búsqueda independiente, sin incorporar su memoria. Los resultados son
exploratorios: todavía no se confirman matrices automáticamente.

### Incremento de etapa 1 para revisión

`python mini_pai_interpretar.py entrada.xlsx --salida revision.json` reutiliza
`proveedor_ia.py` y `skills/analizar-presupuesto/SKILL.md`. Inspecciona las hojas
sin columnas fijas y solicita clasificación a la IA. Requiere configurar el
proveedor como indica el README principal; el contenido del Excel se envía a ese
proveedor. Usa únicamente archivos autorizados para ese destino.

La IA devuelve tipo, hoja, fila, **padre por fila**, evidencia por celda y motivo
de exclusión. Python recupera clave, descripción, unidad y cantidad directamente
del Excel, conservando espacios, saltos de línea y cantidades como texto. No se
pide al modelo transcribirlos ni normalizarlos. Las descripciones pueden abarcar
varias celdas. `partida` y `subpartida` conservan las claves de los padres cuando
existen; `padre` identifica el encabezado incluso sin clave o con claves repetidas.

Se solicita esquema JSON y temperatura cero mediante `response_format` (el
proveedor debe soportarlo). Se validan celdas, orden, padres anteriores de la
misma hoja y reinicio de subpartida al cambiar de partida. Las filas excluidas
se conservan en `excluidas` con motivo. Toda fila no vacía del alcance debe
quedar declarada o citada como continuación. Si falla la validación, se permite
un único intento de corrección con el error; una segunda respuesta inválida
se rechaza. Las respuestas truncadas y errores de conexión no se reintentan.

Para una prueba parcial reproducible, sin fijar columnas:

```powershell
$env:PRECIOAI_AI_PROVIDER = 'ollama'
$env:PRECIOAI_AI_MODEL = 'nemotron-3.5-bolt:e4b'
python mini_pai_interpretar.py entrada.xlsx --hoja Conceptos --fila-inicial 16 --fila-final 30 --tamano-bloque 5 --salida revision.json
```

`alcance.parcial` identifica estas pruebas. Un rango no trae contexto anterior a
su fila inicial: debe incluir los encabezados necesarios. Dentro del alcance,
se procesan bloques consecutivos de hasta 5 filas no vacías por defecto,
ajustables con `--tamano-bloque`. Cada bloque hereda únicamente la partida y
subpartida vigentes ya validadas de su hoja, sin volver a emitirlas. Al cambiar
de hoja se borra ese contexto.

Se anticipan dos filas no vacías para completar descripciones que crucen un
corte. Las filas usadas como continuación no se vuelven a procesar. El esquema
JSON limita filas emitibles, número de registros y coordenadas citables a la entrada del
bloque; la anticipación no puede aparecer como registro independiente en esa
petición. `bloques` registra filas objetivo y continuaciones para revisión.
Si un bloque falla tras su único reintento, se informa hoja/rango y se detiene
el proceso; no se presenta el resto como completado ni se genera el JSON final.
Todavía no hay guardado parcial ni reanudación. Continuaciones de más de dos
filas después del corte requieren evaluación; no asumir cobertura semántica
completa por el mero control de filas.

**Comprobado (2026-11-05):** con Nemotron local, las filas 16–25 de un presupuesto
real devolvieron una partida, dos subpartidas y cinco conceptos con padres y
evidencia correctos; dos filas de metadatos se excluyeron con motivo. Se verificó
contra las celdas originales. El bloque con portada completa no concluyó dentro
del límite de 120 segundos. El archivo y las respuestas privadas no se versionan.

**Prueba de continuidad (2026-11-05):** las filas 16–30 del mismo presupuesto,
en tres bloques de cinco filas con `nemotron-3.5-bolt:e4b`, produjeron una partida,
tres subpartidas, nueve conceptos y dos exclusiones. Las tres peticiones
concluyeron sin reintento de validación (aproximadamente 59, 65 y 60 segundos).
Se comprobaron los padres, ausencia de duplicados y todos los valores contra
las celdas originales; el SHA256 del archivo permaneció igual. La prueba con
bloques de diez filas agotó el límite; cinco es el valor inicial conservador,
no una garantía de tiempo de respuesta. La continuación multicelda en el corte
se verificó con datos sintéticos; estos conceptos reales ocupan una fila cada uno.

**Comprobado con pruebas sintéticas:** columnas variables, jerarquías, padres sin
clave, cantidades cero, descripciones multicelda, exclusiones, cobertura, rangos,
rechazo de referencias inventadas y un único reintento de validación. Las pruebas
de bloques cubren padres heredados sin clave, claves repetidas, cambio de partida,
aislamiento entre hojas, continuación en el corte, rechazo de contexto reemitido
y detención ante un bloque inválido.
**Pendiente:** distintos presupuestos, portada completa, fórmulas sin caché,
celdas combinadas y libros grandes. La cobertura solo comprueba que cada fila
fue declarada o citada: la IA aún puede omitir un concepto mediante una exclusión
incorrecta o seleccionar celdas/tipos equivocados. Revisar también `excluidas`.
El contrato actual admite dos niveles de agrupación; los niveles adicionales
deben reportarse como duda. Sigue pendiente validar el presupuesto completo y
diversos formatos con este procesamiento por bloques.
Todavía no hay agente con llamadas autónomas a herramientas. La exportación inicial de revisión está disponible; no confirma equivalencias.

Se contempla una **skill** especializada (instrucciones para la IA) y herramientas concretas para inspeccionar Excel, consultar ConstruBase y generar el archivo de salida. La carpeta `references/` podría guardar reglas y documentación de Neodata; `scripts/` contendría funciones ejecutables. **Esta estructura aún es una propuesta, no está implementada.** Se busca mantener el sistema utilizable con distintos modelos de IA, sin depender de uno específico.

El código existente en la raíz de PrecioAI permanece donde está por ahora. No duplicarlo ni moverlo antes de determinar qué puede reutilizar Mini-PAI.

## Fuentes y ejemplos

- `Manual PUWIN+.pdf`, especialmente páginas 246 y 456–458 (archivo de referencia compartido en el proyecto, no necesariamente versionado en Git).
- `CATÁLOGO DE CONCEPTOS PARA ANALISIS DE MAESTRO.xls` (ejemplo del curso avanzado).
- `pepe-sucio.xlsx`, `pepe-limpio.xlsx` y `presupuesto_1.xlsx` (ejemplos de entrada/salida compartidos; no asumir que están en el repositorio).
- ConstruBase: catálogo y matrices de referencia, **sin modificar la base**.

## Reglas de trabajo

- Distinguir **comprobado**, **pendiente** e **hipótesis**.
- Preservar el archivo original y la trazabilidad de cada concepto.
- No crear códigos ni coincidencias ficticias.
- Implementar una etapa pequeña a la vez; reutilizar el código existente y evitar dependencias innecesarias.
- No subir presupuestos privados, bases de datos ni credenciales al repositorio.
- Antes de comercializar una solución que dependa de ConstruBase o Neodata, verificar los derechos y condiciones de uso correspondientes.
