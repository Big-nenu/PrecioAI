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

## Pendientes, en orden

1. Medir una ejecución limpia con el código actual, sin mezclar intentos de desarrollo ni revalidación de respuestas guardadas con inferencia nueva.
2. Comparar EmbeddingGemma 2:270m y Qwen3-Embedding:0.6b en la misma muestra: tiempo, memoria y presencia de matrices útiles entre los primeros candidatos. No declarar ganador por tamaño o benchmarks generales.
3. Preparar un índice local separado de ConstruBase si el experimento lo justifica. Medir por separado construcción inicial, actualización y consultas habituales. SQL permanece en lectura.
4. Comparar D1 y D3 con exactamente los mismos conceptos y candidatos. Medir latencia y decisiones, incluidas diferencias reales, omisiones e información insuficiente. Confianza alta no es aprobación ni probabilidad calibrada de acierto.
5. Integrar únicamente la combinación que demuestre mejora; reutilizar `laboratorio_coincidencias.py`, `comparar_evaluadores.py`, proveedor, skill y módulos actuales antes de crear infraestructura.
6. Probar conversación completa en Cline y copiar el nuevo Excel a Neodata, incluyendo conceptos sin matriz y cantidades con comas conservadas como texto.

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
