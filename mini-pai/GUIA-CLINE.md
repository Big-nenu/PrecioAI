# Probar Mini-PAI con Cline

Mini-PAI es una skill del repositorio más scripts Python. No requiere instalar un servidor MCP. Cline necesita poder leer los archivos y usar la terminal del proyecto.

## Preparación

1. Abrir en VS Code un checkout que contenga el código del [PR #3](https://github.com/Big-nenu/PrecioAI/pull/3), rama `mini-pai-busqueda-revisable`. Main puede no incluirlo. Revisar `git status` antes de cambiar de rama y conservar modificaciones locales.
2. Usar el Python del proyecto con sus dependencias existentes y Ollama local. Mantener `nemotron-3.5-bolt:e4b`; descargar otros modelos no cambia el flujo automáticamente.
3. Tener la configuración SQL local existente. No copiar secretos al prompt ni a Git. El puerto TCP dinámico puede cambiar: comprobar la conexión antes de medir y no reconfigurar SQL Server para hacer la prueba.
4. Elegir un directorio de salida nuevo y conservar intacto el Excel de entrada. No reutilizar resultados obsoletos para medir una ejecución limpia.

## Prompt para pegar en Cline

Sustituir las dos rutas entre corchetes. El rango corresponde exclusivamente al presupuesto de referencia probado; en otro Excel se debe inspeccionar la estructura antes de escoger hoja y filas.

```text
Quiero probar Mini-PAI con los cambios actuales del PR #3 de Big-nenu/PrecioAI.

Revisa git status, la rama y los archivos antes de ejecutar. No descartes cambios
locales ni fusiones el PR. No modifiques código ni cambies de modelo para esta prueba.

Lee primero mini-pai/CONTINUIDAD.md, mini-pai/README.md,
mini-pai/BUSQUEDA.md y skills/analizar-presupuesto/SKILL.md.

Presupuesto: [RUTA_ABSOLUTA_DEL_EXCEL]
Configuración SQL local: [RUTA_ABSOLUTA_DEL_ENV]
No muestres credenciales. ConstruBase y el presupuesto son de solo lectura.

Usa nemotron-3.5-bolt:e4b en Ollama, con razonamiento habilitado,
contexto 12288 y máximo 6144 tokens, igual que la referencia documentada.

Trabaja únicamente los primeros 20 conceptos del presupuesto de referencia:
hoja Conceptos, filas 18 a 41, incluyendo partidas y subpartidas.
Comprueba que resulten exactamente 20 conceptos y que los valores tengan evidencia.
No avances al presupuesto completo.

Crea una carpeta nueva para los resultados. Para medir una ejecución limpia,
no reutilices interpretaciones ni respuestas de IA anteriores. Registra tiempos
separados de interpretación, preparación/búsqueda, comparación y exportación.
Si hay errores o reintentos, consérvalos y cuenta su tiempo; no los ocultes.

Ejecuta los módulos existentes de interpretación, búsqueda, comparación y revisión.
Ante un caso dudoso, muéstrame hasta tres candidatos admisibles con código,
descripción completa, unidad, diferencias y motivo. Ofrece también:
4. Conservar concepto original — sin matriz de ConstruBase.

Espera mi elección real; no respondas por mí ni inventes confirmaciones.
Si no hay candidatos en una búsqueda válida, conserva el original. Un error
no equivale a ausencia de candidatos. Si falta el código necesario, pregúntamelo.
No conviertas unidades ni cantidades para forzar una matriz.

Registra las decisiones con auditoría y verifica de nuevo en SQL las matrices
elegidas. Cuando esté todo resuelto, genera Excel con --final y su Markdown.
Mantén las columnas actuales. Abre de nuevo el Excel y verifica los 20 conceptos,
jerarquía, códigos, descripciones íntegras, unidades y cantidades.

Entrega los archivos, resumen de resultados, errores y tiempos. Separa el tiempo
automático del tiempo en que esperaste mis respuestas. No controles Neodata;
yo copiaré manualmente. No integres embeddings, D1 o D3 en esta prueba.
```

## Secuencia de herramientas de referencia

Desde la raíz del repositorio, con las rutas reales y una carpeta nueva ya creada:

```powershell
$env:PRECIOAI_AI_PROVIDER = 'ollama'
$env:PRECIOAI_AI_MODEL = 'nemotron-3.5-bolt:e4b'
$env:PRECIOAI_OLLAMA_NUM_CTX = '12288'
$env:PRECIOAI_OLLAMA_NUM_PREDICT = '6144'
$env:PRECIOAI_OLLAMA_THINK = 'true'

python mini_pai_interpretar.py "RUTA_EXCEL" --hoja Conceptos --fila-inicial 18 --fila-final 41 --tamano-bloque 5 --salida "CARPETA_NUEVA/interpretacion.json"
python mini_pai_claves.py "CARPETA_NUEVA/interpretacion.json" --env "RUTA_ENV" --salida "CARPETA_NUEVA/candidatos.json"
python mini_pai_seleccionar.py "CARPETA_NUEVA/candidatos.json" --env "RUTA_ENV" --salida "CARPETA_NUEVA/evaluacion.json"
python mini_pai_revision.py "CARPETA_NUEVA/evaluacion.json" --salida "CARPETA_NUEVA/opciones.md"
```

Si falla una etapa, revisar y registrar el fallo antes de continuar; no etiquetar un archivo incompleto como final. La IA puede dejar aspectos para revisión sin que eso sea un error operativo.

Después de preguntar al usuario, Cline guarda sus respuestas en un JSON. Ejemplo ilustrativo, no decisión real:

```json
[
  {"hoja": "Conceptos", "fila": 25, "IdCodigo": null,
   "revisor": "Usuario", "motivo": "Prefiero conservar mi concepto original"}
]
```

Para matriz se usa el IdCodigo SQL mostrado, no el número de opción. Si el código original falta y se conserva el concepto, añadir `codigo` con el valor que dio el usuario. No cambiar una clave existente.

```powershell
python mini_pai_confirmar.py "CARPETA_NUEVA/evaluacion.json" "CARPETA_NUEVA/respuestas.json" --env "RUTA_ENV" --salida "CARPETA_NUEVA/resuelto.json"
python mini_pai_exportar.py "CARPETA_NUEVA/resuelto.json" --final --salida "CARPETA_NUEVA/presupuesto.xlsx"
```

Se pueden registrar respuestas por grupos, usando el último JSON resuelto como entrada. No reemplazar decisiones anteriores. Si no hay preguntas pendientes, exportar directamente la evaluación con --final. Cada Excel lleva un Markdown con el mismo nombre base.

## Qué comprobar al recibirlo

- 20 conceptos y sus encabezados, con la jerarquía original.
- Con matriz: Código, Descripción completa y Unidad de ConstruBase; auxiliares y cantidad del cliente.
- Sin matriz: código y descripción del cliente repetidos en principales y auxiliares.
- Reporte con sin candidatos, conservación manual, matrices elegidas y origen IA/usuario.
- Cantidades con comas que permanecen como texto identificadas para probar su pegado.
- Al copiar a Neodata, revisar también los conceptos sin matriz. La prueba nueva en Neodata la hace el usuario.
