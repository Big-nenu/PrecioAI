# PrecioAI

Plataforma en desarrollo para facilitar la elaboración de presupuestos de obra y análisis de precios unitarios, combinando búsqueda de matrices, datos estructurados e inteligencia artificial cuando aporte valor.

> **Estado:** definición funcional y exploración técnica. Las funciones descritas son objetivos del proyecto, no características ya implementadas.

## Visión

Reducir el trabajo repetitivo de localizar, comparar y adaptar análisis de precios unitarios. PrecioAI **no busca copiar Neodata ni trasladarlo a la nube**: busca ofrecer un flujo más sencillo para aprovechar matrices existentes y, progresivamente, ayudar a construir análisis nuevos.

La inteligencia artificial se utilizará principalmente para **interpretar conceptos de presupuestos importados** y reconocer sus características técnicas. La búsqueda, recuperación de datos y operaciones aritméticas deben ser verificables; no todo requiere IA.

## Flujo principal: importar un presupuesto (MVP)

1. El usuario carga un presupuesto en **Excel o PDF**.
2. El sistema extrae los **conceptos, descripciones, unidades y cantidades**, conservando la relación con el documento de origen.
3. Identifica características relevantes de cada descripción: por ejemplo, *manual*, *con equipo topográfico*, *hasta 1,000 m²*, *mayor a 1,000 m²*, *incluye elaboración de plano*, etc.
4. Busca en **ConstruBase** conceptos y matrices compatibles. No basta con encontrar las mismas palabras: deben considerarse el trabajo principal, las condiciones y la unidad.
5. Muestra **varias opciones** para que el usuario compare y elija. También debe existir una opción de **captura manual**.
6. Al elegir una matriz, recupera su análisis y los subanálisis necesarios para que el usuario pueda revisarlos y modificarlos.
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
