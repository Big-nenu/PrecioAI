# Del presupuesto interpretado a candidatos revisables

`mini_pai_buscar.py` lee el JSON de `mini_pai_interpretar.py`, consulta ConstruBase
en modo lectura y añade `busquedas_construbase`. Conserva los registros originales,
sus claves, descripciones, cantidades, jerarquía, evidencia, dudas, exclusiones y
alcance parcial. No selecciona matrices ni modifica el catálogo o el archivo de entrada.

## Ejecutar

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

- `seleccion` permanece en `null`; todos los candidatos requieren revisión.
- `comparacion_unidad` indica `igual`, `diferente` o `sin_datos`. No convierte
  unidades ni establece equivalencia técnica. Leer también las advertencias.
- `observaciones_origen` señala campos vacíos del JSON interpretado. Verificar
  esos datos contra el Excel; el buscador no los reconstruye ni inventa.
- `limite_sql_alcanzado` advierte que se recuperaron 50 filas: puede haber más
  candidatos fuera del conjunto. El orden SQL previo es por código/IdCodigo.
- `sin_candidatos_en_busqueda` significa que estos términos no recuperaron
  candidatos; no prueba que el catálogo completo carezca de una equivalencia.
- `requiere_terminos` identifica conceptos sin descripción o términos utilizables.

Todavía no hay «buscar más», confirmación persistente, recuperación de matrices,
costos o exportación. No se aplican embeddings ni un modelo de decisiones en este
paso. El laboratorio sigue disponible como experimento independiente.

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
