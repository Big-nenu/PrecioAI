# PrecioAI

Plataforma en desarrollo para facilitar la elaboración de presupuestos de obra y análisis de precios unitarios, combinando búsqueda de matrices, datos estructurados e inteligencia artificial cuando aporte valor.

> **Estado (2026-11-04):** búsqueda y recuperación de matrices/subanálisis probadas contra ConstruBase. El flujo completo Excel/PDF → coincidencias → selección → Excel sigue pendiente. Distinguir funcionalidades probadas de propuestas.

## Visión

Reducir el trabajo repetitivo de localizar, comparar y adaptar análisis de precios unitarios. PrecioAI **no busca copiar Neodata ni trasladarlo a la nube**: busca ofrecer un flujo más sencillo para aprovechar matrices existentes y, progresivamente, ayudar a construir análisis nuevos.

La inteligencia artificial se utilizará principalmente para **interpretar conceptos de presupuestos importados** y reconocer sus características técnicas. La búsqueda, recuperación de datos y operaciones aritméticas deben ser verificables; no todo requiere IA.

## Flujo principal: importar un presupuesto (MVP)

1. El usuario carga un presupuesto en **Excel o PDF**.
2. El sistema extrae los **conceptos, descripciones, unidades y cantidades**, conservando la relación con el documento de origen.
3. Identifica características relevantes de cada descripción: por ejemplo, *manual*, *con equipo topográfico*, *hasta 1,000 m²*, *mayor a 1,000 m²*, *incluye elaboración de plano*, etc.
4. Busca en **ConstruBase** conceptos y matrices compatibles. No basta con encontrar las mismas palabras: deben considerarse el trabajo principal, las condiciones y la unidad.
5. Muestra **hasta cinco coincidencias compatibles** por concepto, ordenadas por relevancia. «Buscar más» trae hasta cinco nuevas, sin repetir; si solo hay dos válidas, muestra dos. Si no hay ninguna, informa «Sin coincidencias» y conserva el concepto original. No inventar opciones.
6. El usuario selecciona una matriz y decide **conservar su descripción original** o **usar la descripción de ConstruBase**. Recupera su análisis y los subanálisis necesarios para revisión.
7. Las modificaciones se guardan **dentro del presupuesto del usuario**, sin alterar ConstruBase.

**Ejemplo:** al importar «Trazo y nivelación con equipo topográfico, hasta 1,000 m²», una búsqueda de texto puede devolver trazo manual, trazo topográfico general, trazo con plano, trabajos para tuberías e incluso otros conceptos que solo mencionan «trazo y nivelación». PrecioAI debe distinguir estos casos y presentar primero las coincidencias técnicamente más pertinentes.

La IA puede sugerir coincidencias, pero **la elección de la matriz corresponde al usuario**. Si no existe una opción adecuada, no debe inventarse una coincidencia como si fuera válida.

## Matrices y análisis

ConstruBase es la **base de referencia** de conceptos, insumos y matrices. En la primera etapa se utilizará para recuperar análisis existentes, no para sobrescribir sus datos.

El sistema deberá contemplar la estructura real de los análisis de precios unitarios, incluidos:

- **Materiales (tipo 1).**
- **Mano de obra (tipo 2)**, incluidas cuadrillas con análisis propio.
- **Equipo y herramienta (tipo 3)**, con sus distintas formas de obtener el costo: costo horario, porcentaje, matriz/equipo en renta o costo capturado directamente, según corresponda.
- **Conceptos y básicos (tipo 4)**, que pueden contener otros análisis.
- **Subcontratos (tipo 5).**

Las matrices pueden tener **análisis anidados**. Recuperar un concepto no significa únicamente traer su descripción y precio: también interesa conservar sus insumos, cantidades, operadores, costos, importes y relaciones con subanálisis.

Algunos costos provienen de otros análisis y no son valores independientes. Por ejemplo, en un insumo de equipo configurado como **porcentaje**, el costo base puede provenir de la suma de los **importes** del tipo de insumo seleccionado; después se aplica la cantidad o factor correspondiente para obtener el importe del renglón.

Los cálculos deben hacerse con lógica **determinista, reproducible y comprobable**, respetando las reglas aplicables al análisis. La IA no debe inventar rendimientos, cantidades ni precios sin sustento.

El campo interno **nivel de análisis (N)** puede ser útil para interpretar los datos, pero **no es necesario mostrarlo al usuario** en la interfaz de PrecioAI.

## Edición y conservación de datos

- **ConstruBase permanece intacta** como fuente de referencia.
- La matriz seleccionada se incorpora al presupuesto como una **copia editable**.
- Los cambios realizados en esa copia pertenecen al presupuesto del usuario.
- Debe conservarse la **procedencia** de la matriz y distinguirse el dato original del modificado.
- Queda por diseñar cómo se almacenarán las copias, sus dependencias y los cambios de cada presupuesto.

## Evolución prevista (fuera del primer MVP)

### Crear presupuestos desde cero

Permitir que el usuario escriba un concepto y reciba coincidencias mientras captura. Se busca una búsqueda **flexible por palabras y características**, sin exigir que escriba el código o la descripción exacta de ConstruBase.

Esta función puede comenzar con un **filtro o buscador convencional**; no necesita IA por obligación. Podrá reutilizar el mismo mecanismo de búsqueda desarrollado para presupuestos importados.

### Construir o adaptar análisis nuevos

Cuando no exista una matriz adecuada, explorar la posibilidad de que PrecioAI ayude a **proponer o construir un análisis** a partir de insumos, cuadrillas, equipos y básicos existentes. Las propuestas deberán justificarse y quedar sujetas a revisión humana. **No forma parte de la primera prueba.**

### Precios de referencia

Evaluar posteriormente la consulta de precios por ubicación geográfica, mostrando **fuente, fecha y ubicación**. La recopilación automatizada de precios externos se abordará después de validar la búsqueda y recuperación de matrices.

## Decisiones funcionales y prioridades (2026-11-04)

**Objetivo principal:** importar el presupuesto de un ingeniero (Excel o PDF), interpretar sus partidas y conceptos, buscar análisis similares en ConstruBase, permitir seleccionar coincidencias y generar un **Excel de presupuesto con análisis**. La interfaz gráfica queda para después; el Excel puede servir como primera salida revisable. No crear una hoja por concepto: organizar presupuesto, alternativas y análisis en hojas consolidadas (diseño sujeto a prueba con archivos reales). Conservar partidas, unidades, cantidades y descripciones originales salvo elección explícita del usuario.

**Reglas de coincidencia:** identificar palabras clave y atributos técnicos (unidad, resistencia, dimensiones, método, condiciones). Ranking con puntuación y penalizaciones, sin confundir similitud textual con equivalencia técnica. Hasta 5 resultados por lote, «Buscar más» sin repetidos, sin completar artificialmente el cupo. El usuario siempre confirma la opción. Un concepto sin coincidencia se señala y permanece en el presupuesto, sin inventar análisis.

**Ideas futuras, NO parte del MVP:**
- **Embeddings/RAG local:** indexar descripciones del catálogo una vez y recuperar candidatos sin enviar todo ConstruBase al modelo de lenguaje. Comparar primero contra el ranking existente; no implica integrar StoneWave completo.
- **StoneWave-mini:** memoria/caché de selecciones confirmadas y conceptos usados con frecuencia, para proponerlos primero en futuras búsquedas. Guardar procedencia (IdCodigo, IdExpIns, IdPresupuesto, versión de base) y revalidar costos/datos actuales antes de usarlos; no sustituye la fuente de verdad SQL.
- **Rapidpre:** posible fuente adicional para especialidades no cubiertas por ConstruBase (p. ej., albercas). Investigar antes exportación/acceso permitido por licencia; no asumir autorización para scraping ni depender de macros en el MVP.

## Avance técnico comprobado

- `buscar_conceptos.py`: búsqueda SQL de conceptos por descripción; `ranking_conceptos.py`: ordenamiento inicial de candidatos. **No** están todavía conectados al flujo de importación Excel/PDF ni implementan paginación de 5.
- Relación **verificada**: `PuCatalogo.IdCodigo → PuExpIns.IdCodigo`; `PuExpIns.IdExpIns → PuMatrices.IdCodigoMatriz` (matriz) y `PuMatrices.IdCodigoInsumo → PuExpIns.IdExpIns` (insumo). Cada concepto puede existir en varios presupuestos.
- `diagnosticar_matriz.py`: localiza instancias por presupuesto. Para `10301-003` se hallaron cuatro instancias (presupuestos 48–51), cada una con nueve renglones.
- `consultar_matriz.py`: recupera renglones reales, `Dividir`, `Volumen` y subanálisis con profundidad limitada y protección de ciclos. **Probado**: matriz `860468` (trazo/nivelación, presupuesto 48) → básico `860902` (concreto `10401-291`), con ocho renglones.
- **Costos:** Cline reportó que `PuExpInsCostos` contiene costos relacionados por `IdExpIns`; falta verificar cardinalidad y elegir registro correcto. Existe `--diagnosticar-costos`, pendiente de ejecutar y revisar.
- `calculo_importes.py` y sus pruebas: operación decimal multiplicar/dividir con redondeo normal o hacia arriba. **No está validada** todavía la política real de Neodata ni el cálculo completo de porcentajes, costos horarios y subanálisis. No reconstruir rendimientos a partir de importes redondeados.

**Próximo objetivo del MVP:** leer un Excel real sin modificar el original, distinguir partidas de conceptos y producir una lista revisable de coincidencias de ConstruBase. Después integrar selección humana y exportación. Los costos y redondeos no deben bloquear esta primera prueba.

## Primera validación técnica

Antes de construir una interfaz completa o una arquitectura compleja:

1. Comprobar que podemos consultar correctamente los conceptos, matrices y relaciones de ConstruBase.
2. Probar la búsqueda con ejemplos reales, empezando por las variantes de **«trazo y nivelación»**.
3. Evaluar si una búsqueda por términos y reglas distingue correctamente las variantes; introducir IA donde las búsquedas convencionales resulten insuficientes.
4. Recuperar **una matriz completa con sus análisis anidados** y comprobar que los datos y cálculos son coherentes.

El objetivo de esta prueba es demostrar que podemos **encontrar y recuperar el análisis adecuado**, antes de abordar la edición completa o la generación autónoma de matrices.

## Principios del proyecto

- **Priorizar el MVP:** resolver primero un flujo completo y verificable.
- **IA donde aporte valor:** especialmente en la interpretación de conceptos importados y ambigüedades.
- **Control humano:** presentar alternativas y permitir seleccionar, capturar y modificar.
- **Cálculos verificables:** separar interpretación inteligente de operaciones matemáticas.
- **Trazabilidad:** conservar origen de datos, matrices seleccionadas y cambios del usuario.
- **Datos de referencia protegidos:** no modificar ConstruBase durante la edición de presupuestos.
- **Uso responsable de datos:** verificar licencias y permisos antes de utilizar bases de terceros comercialmente; no subir bases de datos, credenciales ni archivos privados al repositorio.
- **Simplicidad:** evitar agentes, dependencias e infraestructura innecesaria antes de validar el flujo principal.

## Tecnologías

**Por definir.** Se elegirán después de validar las necesidades reales del MVP.

## Primer lector de presupuesto Excel

Se agregó `leer_presupuesto.py` como prototipo de lectura **sin modificar el archivo original**. La primera prueba se hizo con `Propuesta pepe - original.xlsx` (hojas `Conceptos` y `Resumen`), cuyo formato tiene encabezados antes de la tabla, partidas y conceptos. El lector debe preservar clave, descripción, unidad, cantidad, fila de origen y partida. `test_leer_presupuesto.py` cubre casos básicos; faltan pruebas con formatos distintos y conectar la extracción a la búsqueda en ConstruBase. No subir presupuestos privados al repositorio.

**Prioridad siguiente:** validar el lector con el Excel original y revisar los conceptos extraídos antes de agregar embeddings, caché o interfaz.
