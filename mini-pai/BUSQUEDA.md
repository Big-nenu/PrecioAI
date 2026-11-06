# Del presupuesto interpretado a candidatos revisables

`mini_pai_buscar.py` lee el JSON de `mini_pai_interpretar.py`, consulta ConstruBase
en modo lectura y añade `busquedas_construbase`. Conserva los registros originales,
sus claves, descripciones, cantidades, jerarquía, evidencia, dudas, exclusiones y
alcance parcial. No selecciona matrices ni modifica el catálogo o el archivo de entrada.

## Preparación de consultas mediante IA (2026-11-06)

El punto de entrada recomendado es ahora `mini_pai_claves.py`. Antes de consultar
ConstruBase, Nemotron interpreta la actividad y atributos de la descripción y
unidad originales. Los nombres de atributos son abiertos: material, resistencia,
espesor o procedimiento son ejemplos, no columnas ni vocabulario obligatorio.
Python recupera las citas desde IDs de fragmentos originales y comprueba valores,
unidad y números; la cantidad del presupuesto no se envía como especificación.
Estas comprobaciones no sustituyen una evaluación semántica de los atributos.

```powershell
python mini_pai_claves.py salidas/interpretacion.json --env .env --salida salidas/candidatos-ia.json
```

Reutiliza el proveedor y la skill existentes (`PRECIOAI_AI_PROVIDER` y
`PRECIOAI_AI_MODEL`). No cambia el modelo configurado. Propone hasta tres consultas:
específicas primero y una final amplia de una o dos palabras. Se ejecutan todas
con el buscador SQL parametrizado existente, hasta 500 resultados por consulta,
y se unen por IdCodigo. Se prioriza unidad coincidente y después la consulta
más específica; el ranking léxico existente desempata. Se muestran cinco candidatos.
La unidad igual sirve para recuperar candidatos, nunca para aprobar equivalencia.

`interpretacion_tecnica_ia` conserva atributos, evidencia, dudas y consultas;
`intentos`, `recuperados_unicos` y `consulta_origen` permiten auditar la recuperación.
Un error de IA deja el concepto señalado y sin consultas: no vuelve silenciosamente
a las dos primeras palabras. La salida es nueva y los registros originales se
conservan íntegros. La selección técnica posterior sigue siendo un paso separado.

Cada consulta todavía usa coincidencia de términos con AND/LIKE; las variantes
son alternativas propuestas por IA. No es búsqueda semántica exhaustiva, ni una
consulta sin resultados demuestra que no exista matriz. Puede haber diferencias
de abreviaturas, términos o valores escritos de otra forma. No consulta composición
ni costos y no garantiza todas las inclusiones de una matriz.

## Buscador previo sin interpretación IA

```powershell
python mini_pai_buscar.py salidas/interpretacion.json --env .env --salida salidas/candidatos.json
```

Se reutilizan las variables `PRECIOAI_SQL_*` existentes. `--env` se resuelve
respecto a la carpeta del programa si es relativo; admite una ruta absoluta.
La conexión usa `readonly=True` y `ApplicationIntent=ReadOnly`. Solo ejecuta SELECT.
El flujo nuevo requiere contraseña configurada localmente y no la solicita en
el chat ni en una ejecución no interactiva. El buscador anterior conserva su
entrada interactiva cuando se ejecuta directamente.

## Qué hace esta primera conexión

1. Valida los registros y relaciones por hoja/fila antes de consultar SQL.
2. Propone hasta dos términos principales de la descripción anterior a «incluye»,
   retirando palabras genéricas. Es una regla sencilla, visible y revisable.
3. Busca conceptos de tipo 4 con el buscador existente, hasta 50 resultados SQL
   por intento. Si la propuesta de dos términos no devuelve nada, prueba solo
   el primero y registra la ampliación en `intentos`.
4. Prioriza la coincidencia del primer término principal y después reutiliza
   el ranking existente. Es una heurística; no demuestra igualdad de trabajo.
5. Muestra hasta cinco candidatos reales por concepto, identificados por
   `IdCodigo`, con descripción, código, unidad, razones y advertencias.

Para ajustar términos, usar `--terminos datos_privados/terminos.json`, con un
objeto que asocie `hoja:fila` a una cadena. Ejemplo: `{"Conceptos:25": "trazo nivelacion"}`.
Los términos indicados no se amplían automáticamente. Las claves deben referir
a conceptos existentes; no se agrupan conceptos por la clave del cliente.

## Cómo revisar la salida

- La búsqueda deja `seleccion` en `null`; todos los candidatos requieren revisión.
  La selección IA y la confirmación humana de excepciones se documentan en [README.md](README.md).
- `comparacion_unidad` indica `igual`, `diferente` o `sin_datos`. No convierte
  unidades ni establece equivalencia técnica. Leer también las advertencias.
- `observaciones_origen` señala campos vacíos del JSON interpretado. Verificar
  esos datos contra el Excel; el buscador no los reconstruye ni inventa.
- `limite_sql_alcanzado` advierte que se recuperaron 50 filas: puede haber más
  candidatos fuera del conjunto. El orden SQL previo es por código/IdCodigo.
- `sin_candidatos_en_busqueda` significa que estos términos no recuperaron
  candidatos; no prueba que el catálogo completo carezca de una equivalencia.
- `requiere_terminos` identifica conceptos sin descripción o términos utilizables.

Todavía no hay «buscar más», recuperación de matrices ni costos. Hay selección
IA, confirmación humana de excepciones y exportación con o sin selecciones verificadas, como está
documentada en [README.md](README.md#primer-excel-de-revisión-2026-11-06). No se aplican embeddings ni un modelo de decisiones en este
paso. El laboratorio sigue disponible como experimento independiente.

## Recuperación ampliada para comparación IA

`--ampliar` recorre páginas SQL de 50 hasta 500 coincidencias por intento, antes de
ordenar y mostrar cinco. Prioriza unidad coincidente, sin afirmar compatibilidad.
`limite_recuperacion` documenta el tope y `limite_sql_alcanzado` indica si se llegó.
Se mantienen términos e intentos visibles. En la muestra recuperó 149 demoliciones,
68 demoliciones con concreto y 62 resultados de trazo; no equivale a una búsqueda
semántica exhaustiva. La comparación posterior recibe descripciones completas.

## Comprobación parcial (2026-11-06)

Se consultaron los nueve conceptos de las filas 16–30 del presupuesto real ya
interpretado. Los datos y el Excel original permanecieron intactos. Se recuperó,
entre otros, el grupo de trazo `10301-002`/`10301-003`; se mantuvieron los IDs SQL
reales y las unidades del catálogo. Las unidades faltantes en cuatro
conceptos del JSON se señalaron para revisión, sin inferirlas. Varios intentos
alcanzaron el límite de 50: el resultado es una lista exploratoria acotada.

Pendiente: corregir o confirmar los campos incompletos de la interpretación,
revisar alcance, método, material, resistencia y dimensiones con una persona
conocedora del dominio, y confirmar una selección antes de reutilizar matrices.
Una unidad igual o un puntaje alto no bastan para aprobar un candidato.

## Completar campos omitidos con evidencia

Antes de buscar, `mini_pai_completar.py` permite completar campos nulos de conceptos
mediante referencias explícitas verificadas contra el Excel, sin reglas de columnas:

```powershell
python mini_pai_completar.py interpretacion.json original.xlsx cambios.json --salida interpretacion-completada.json
```

`cambios.json` contiene una lista, por ejemplo:
`[{"hoja":"Obra","fila":2,"campo":"unidad","celdas":["Z2"]}]`.
Solo admite clave, descripción, unidad o cantidad omitidas; rechaza sobrescrituras,
referencias vacías/inexistentes, duplicados y evidencia que comienza en otra fila.
Valida todos los datos contra el libro antes y después. Conserva evidencia y agrega
`completados` con valor anterior, valor exacto, referencias y SHA256 del Excel.
No reemplaza las entradas ni modifica el libro. Una salida que ya tenga búsquedas
se rechaza: completar primero y volver a buscar para evitar resultados obsoletos.
La comprobación de celdas acredita procedencia; revisar la interpretación semántica.

Comprobación local: se revisaron explícitamente las celdas D26, D27, D28 y D30 del
presupuesto de prueba. Sus unidades estaban presentes en el Excel y omitidas en
el JSON; se recuperaron exactamente, incluidos espacios, sin modificar cantidades.
Esto corrige esa muestra; no garantiza que la IA complete todos los campos futuros.
