# Probar Nemotron y Gemma y compartir los reportes

El script `probar_modelos_mini_pai.py` ejecuta ambos modelos **secuencialmente**, con las mismas entradas y configuración. Usa Ollama local y las funciones actuales de Mini-PAI. No necesita Cline. No cambia `.env`, no sustituye el modelo de producción, no consulta SQL ni genera un Excel final.

## Ejecutar en esta computadora

Dejar Ollama abierto y cerrar otras aplicaciones que estén usando los modelos. No cambiar código, muestras ni modelos mientras corre la prueba. Desde PowerShell:

```powershell
cd "C:\Users\Luis_Hdez\Projects\PrecioAI"
python .\probar_modelos_mini_pai.py
```

El script muestra la carpeta de salida y el progreso por concepto. Puede tardar varios minutos. Libera de memoria el modelo probado antes y después, para incluir una carga inicial en ambos casos. No descarga modelos ni borra sus archivos. Si no está disponible alguno, lo indica sin inventar resultados.

Para ejecutar uno por separado:

```powershell
python .\probar_modelos_mini_pai.py --modelos gemma4:e4b-it-qat
python .\probar_modelos_mini_pai.py --modelos nemotron-3.5-bolt:e4b
```

Cada ejecución crea una carpeta nueva `salidas/prueba-modelos-FECHA-HORA/`. Dentro hay una subcarpeta por modelo con:

- `reporte-nemotron-3.5-bolt_e4b.md` o `reporte-gemma4_e4b-it-qat.md`: **los archivos para compartir**.
- `resultados.json`: respuestas completas, tiempos y datos para depuración local.
- `interpretacion.json`: extracción obtenida, si esa etapa terminó sin error.

No sobrescribe ejecuciones anteriores. Con Ctrl+C conserva lo completado en un reporte parcial. Una extracción fallida no impide probar la comparación técnica con la muestra fija independiente. Terminar el script no significa que el modelo haya pasado las pruebas: revisar sus errores y controles.

## Qué compara

| Parte | Entrada común | Comprobación |
| --- | --- | --- |
| Extracción | Presupuesto E2 de 78 conceptos y referencia cotejada | Conceptos, campos originales, evidencia de celdas, jerarquía, exclusiones y alcance |
| Comparación técnica | Muestra anterior de 20 conceptos, con candidatos reales ya guardados; 18 casos tienen candidatos | Mismas descripciones completas, orden inicial, instrucciones, validaciones y reintentos |
| Controles negativos | Piedra frente a concreto armado; plantilla de 6 cm frente a 3/4/5 cm | Detectar propuestas de equivalencia indebida, incluso si las guardas las bloquean |

**Las dos partes usan presupuestos distintos.** La muestra técnica anterior permite comparar candidatos idénticos sin esperar otra búsqueda SQL; no significa que se hayan buscado matrices del nuevo presupuesto E2. Los cinco candidatos de concreto del control de piedra se incluyeron expresamente para comprobar el rechazo. Los dos casos sin candidatos no se cuentan como fallos ni aciertos del modelo.

Las evaluaciones técnicas son **propuestas sin verificación SQL actual**, no selecciones confirmadas. Pasar las validaciones de formato y evidencia no demuestra exactitud semántica general. No hay etiquetas positivas completas para calcular una precisión total; los dos controles negativos tampoco bastan para declarar ganador. El reporte conserva el orden técnico, motivos, citas y propuestas degradadas para revisión.

La configuración es la misma para ambos: contexto 12288, máximo de salida 6144, razonamiento activado y temperatura 0. Los tiempos incluyen carga inicial y reintentos; se registran aparte tiempos de extracción, casos técnicos, tokens y carga. Una sola ejecución es una medición exploratoria. La memoria observada vía `/api/ps` es residencia entre llamadas, no el pico de uso. Otros programas pueden alterar las medidas; el reporte señala otros modelos observados en GPU.

Esta prueba evalúa las tareas internas de Mini-PAI, **no el uso autónomo de herramientas por un agente**, MCP, rendimiento de búsqueda SQL ni embeddings.

Está preparada para los dos modelos de chat indicados. D1/D3 requieren sus ensayos de decisiones por separado; no se cambia automáticamente de API al escribir otro nombre de modelo.

## Muestra privada preparada

En esta computadora está en `datos_privados/prueba-modelos/`: copia del Excel, referencia cotejada, candidatos fijos y `muestra.json` con hashes y controles. Está excluida de Git. No incluye credenciales ni decisiones humanas previas como etiquetas de exactitud.

El script comprueba los hashes antes de comenzar y después de cada modelo. Si cambian, marca la prueba como inválida. Registra versión de Ollama, digest de modelo y hashes del código para cotejar los reportes.

En otra computadora o después de clonar solo GitHub, la muestra privada no estará presente: hace falta transferirla de forma privada o preparar otra referencia cotejada. `--muestra ruta/muestra.json` permite seleccionar ese paquete; `--salida carpeta_nueva` permite elegir un destino nuevo. Los reportes contienen descripciones privadas del presupuesto y catálogo: no publicarlos en GitHub.

## Verificación del script

Se probaron cotejo, controles negativos, aislamiento de configuración, ausencia de SQL, reportes de fallos/modelos no disponibles, interrupción con guardado parcial, protección de entradas, rechazo de muestra alterada e instrumentación. Los ensayos unitarios utilizan respuestas simuladas y no constituyen resultados de Nemotron ni Gemma. La comparación real la ejecuta el usuario con los comandos anteriores.

Al preparar esta herramienta pasaron las 145 pruebas de la suite, incluidas ocho nuevas del script. En esa preparación no se ejecutaron inferencias reales.

## Resultados compartidos por el usuario — 7 de noviembre de 2026

Se revisaron los JSON y Markdown de `salidas/prueba-modelos-20261107-085548-696404/`, con las mismas entradas y configuración por modelo. Nemotron recuperó 78 conceptos y 15 agrupadores sin diferencias con la referencia, en 53.397 s. Gemma falló en la extracción por una referencia de padre inválida, tras 107.846 s; no produjo una interpretación final válida.

En la muestra técnica fija, ambos completaron 18 casos y hubo dos sin candidatos. Nemotron tardó 376.071 s y Gemma 810.076 s; no hubo errores de API. Los tiempos totales fueron 429.662 s y 918.778 s, respectivamente. Son tiempos de esas tareas y ejecuciones, no del flujo completo con SQL y revisión humana.

Nemotron produjo cuatro propuestas que pasaron las guardas locales y Gemma tres; **no son conteos de equivalencias correctas**. La propuesta Nemotron de cimbra reconoce inclusiones no acreditadas y requiere revisión. También se observaron criterios inconsistentes entre diámetros de acero. Ninguno seleccionó automáticamente los controles de piedra/concreto o plantilla de espesor distinto, aunque clasificarlos como insuficientes tampoco acredita una clasificación técnica correcta.

Se mantiene Nemotron. La comparación posterior de recuperación, caché y evaluadores está en [PRUEBA-RECUPERACION-DECISIONES.md](PRUEBA-RECUPERACION-DECISIONES.md). Esta prueba no midió agentes ni herramientas autónomas; no demuestra cuál modelo es mejor en general.
