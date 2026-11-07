# Laboratorio de recuperación y decisiones

`laboratorio_coincidencias.py` compara el ranking existente de PrecioAI con
EmbeddingGemma, Qwen3-Embedding y Nomic y permite evaluar pares con TEV1. Es un experimento
independiente: no está conectado automáticamente al intérprete, no elige
matrices y no escribe en ConstruBase.

Se adapta el enfoque de `tests/embed_lab.py` y los prefijos de StoneWave;
no se importa su motor ni se accede a su memoria. La atribución MIT está en
`references/stonewave-license.txt`.

Pruebas separadas: [recuperación sobre catálogo completo, índice persistente y D1/D3 frente a Nemotron](PRUEBA-RECUPERACION-DECISIONES.md). `indice_local.py` reutiliza vectores de catálogo y reanuda lotes pendientes. La [integración posterior con mini_pai_buscar.py --indice](INTEGRACION-INDICE.md) ya genera candidatos para el selector existente y un Excel de revisión; no convierte rankings en equivalencias ni sustituye Nemotron.

## Ejecutar

```powershell
python -m pip install -r requirements-laboratorio.txt
python laboratorio_coincidencias.py datos_privados/muestra.json --salida salidas/laboratorio.json --tev1 tev1:0.8b
```

Ollama debe estar disponible localmente. Los modelos por defecto son
`embeddinggemma-2:270m` y `nomic-embed-text:latest`. `--modelos` permite escogerlos
y `--base-url` cambia el servidor. TEV1 es opcional y usa `/v1/systemone`.

La muestra JSON contiene:

- `candidatos`: objetos con `id` (IdCodigo convertido en texto), `codigo`,
  `descripcion` y `unidad`. No inventar referencias de ConstruBase.
- `consultas`: objetos con `id`, `descripcion`, `unidad` y `esperados`.
  `null` significa sin etiqueta; una lista no vacía identifica las referencias
  esperadas; `[]` significa caso sin respuesta conocida.
- `pares`, opcional: `consulta_id`, `candidato_id` y `esperado`, que puede ser
  `compatible`, `incompatible`, `dudoso` o `null` si no está etiquetado.
- `origen` y `notas`: documentan procedencia, selección y limitaciones.

El laboratorio no construye etiquetas a partir de la respuesta del modelo.
Las etiquetas técnicas deben revisarse por una persona conocedora del dominio.
Los presupuestos, muestras SQL y reportes con descripciones privadas deben
permanecer en `datos_privados/`, `salidas/` u otra carpeta local no versionada.

## Qué mide

- Prefijos de consulta/documento activados y desactivados. Para cada variante
  se calculan los embeddings en lotes y se comparan con y sin centrado usando
  exactamente los mismos vectores. La media procede solo de los candidatos.
- Coseno y ordenamiento en CPU con NumPy. Se rechazan truncamiento del texto,
  vectores nulos, no finitos y dimensiones inconsistentes. No se asume una
  dimensión por el nombre del modelo.
- Hit@1 y Hit@5 sobre consultas **positivas etiquetadas**: encontrar al menos una
  referencia esperada en el primer puesto o entre los cinco primeros.
- Las consultas sin etiqueta no cuentan como aciertos. Los casos `[]` se
  reportan, pero no se calcula rechazo sin un umbral calibrado.
- Comparación de unidad textual como `igual`, `diferente` o `sin_datos`. No es
  una conversión de unidades ni demuestra compatibilidad.
- Decisiones de TEV1 y discrepancias frente a etiquetas. Un fallo de API o
  contrato queda `no_evaluado`, nunca se convierte en `compatible`.

La puntuación coseno no es probabilidad de equivalencia. La confianza de TEV1
tampoco es su probabilidad de acertar. Toda decisión requiere confirmación.

Se guardan avances del reporte después de cada fase. `estado=en_curso` distingue
un experimento interrumpido de uno `completado`; comprobar también los errores
registrados. No hay reanudación automática ni índice vectorial persistente aún.

El tiempo de embeddings corresponde al lote completo de documentos y consultas,
no a una consulta individual. La primera variante incluye carga en frío; la
segunda aprovecha el modelo cargado. Los tiempos de ambas variantes no aíslan
el efecto de los prefijos. `size_vram` es memoria observada por Ollama después
de la petición, no el pico total de la GPU. El modelo de embeddings se descarga
al acabar sus variantes, antes de cargar el siguiente; TEV1 se descarga al final.
El reporte de CLI registra versiones y digests de los modelos instalados.

## Primera prueba local: 2026-11-05

Conexión SQL de solo lectura; 68 candidatos reales de tipo 4, seleccionados como
TOP 12 por palabras principales para nueve conceptos del bloque de presupuesto
ya validado. Es una **muestra cerrada**, no el catálogo completo de 19 418
conceptos/básicos. Algunos términos no recuperaron candidatos: esto no demuestra
que el catálogo carezca de una equivalencia.

Se conservaron nueve consultas originales **sin etiqueta de equivalencia** y se
añadieron nueve paráfrasis controladas de referencias del catálogo para evaluar
recuperación. Se evaluaron nueve pares con etiquetas provisionales del laboratorio,
pendientes de confirmación humana. No es un conjunto independiente de validación
ni una medición de precisión técnica sobre el presupuesto.

| Método | Primero | Entre los cinco primeros | VRAM observada |
| --- | --- | --- | --- |
| Ranking existente | 5/9 | 8/9 | Sin modelo |
| EmbeddingGemma 270m, prefijos, sin centrado | 7/9 | 9/9 | ≈363 MiB |
| EmbeddingGemma 270m, prefijos y centrado | 8/9 | 9/9 | ≈363 MiB |
| Nomic, sin prefijos ni centrado | 7/9 | 9/9 | ≈320 MiB |
| Nomic, prefijos, sin centrado | 6/9 | 9/9 | ≈320 MiB |
| Nomic, prefijos y centrado | 5/9 | 9/9 | ≈320 MiB |

Los embeddings reales tuvieron 768 dimensiones en ambos modelos. Las cifras de
memoria no incluyen otros programas ni garantizan el mismo uso con más carga.

TEV1 acertó **5/9 etiquetas provisionales**, sin errores de API. Aceptó como
compatibles diferencias claras entre trazo manual/topográfico y plantilla de
6 cm/5 cm. Observado: ≈1.22 GiB de VRAM; después de cargar, los pares tardaron
aproximadamente 0.03–0.06 s. La rapidez no permite aprobarlo como decisor técnico.

La opción a continuar evaluando es EmbeddingGemma 270m con prefijos, comparando
centrado y coseno normal sobre nuevos casos etiquetados. Los resultados actuales
no bastan para elegir umbrales ni confirmar equivalencias. TEV1 queda solo en el
laboratorio; hacen falta controles deterministas de atributos y pruebas separadas.

Durante la extracción se comprobó que `DescripcionLarga` tenía collation sensible
a acentos. `buscar_conceptos.py` ahora busca sin distinguir acentos/mayúsculas,
usa descripción corta si la larga está vacía y devuelve IdCodigo. Se verificó que
`trazo nivelacion` y `trazo nivelación` devuelven los mismos 12 IDs, incluido el
concepto de referencia conocido. El filtro opcional `tipo=4` está parametrizado.

## Referencias

- [Prefijos de EmbeddingGemma 2](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers)
- [API de embeddings de Ollama](https://docs.ollama.com/api/embed)
- [TEV1 y API System One](https://ollama.com/library/tev1)
