# PrecioAI (PAI)

PrecioAI es un proyecto para crear una plataforma web de presupuestos de obra y análisis de precios unitarios asistidos por IA. **Mini-PAI es el primer producto dentro de este mismo repositorio:** convierte presupuestos Excel de clientes en un Excel revisable para copiar y pegar manualmente en Neodata Precios Unitarios PU Win+.

La meta es que un ingeniero entregue su presupuesto, resuelva únicamente las dudas técnicas y reciba el archivo listo para copiar. No debería necesitar programar, acomodar columnas ni corregir al asistente con instrucciones sucesivas.

## Productos y alcance

| Producto | Objetivo | Estado |
| --- | --- | --- |
| **Mini-PAI** | Interpretar Excel, localizar matrices compatibles de ConstruBase y entregar Excel más reporte | Prototipo local en validación; prioridad actual |
| **PAI** | Elaborar y gestionar presupuestos y análisis de precios unitarios desde la web, con ayuda de IA | Visión futura; alcance detallado por definir |

Se prevén suscripciones con distinto alcance: Mini-PAI como opción de menor costo y PAI como producto más completo. No hay precios, periodos, cobros ni permisos por plan implementados. El repositorio conserva el nombre **PrecioAI**.

## Orden de desarrollo

1. **Validar Mini-PAI localmente:** extracción fiel, decisiones auditables, revisión de dudas y Excel correcto sobre presupuestos completos. Cline y la terminal son herramientas de desarrollo y prueba, no requisitos del producto final.
2. **Facilitar su uso familiar:** una interfaz sencilla accesible desde la laptop del ingeniero; el procesamiento se ejecutaría en la computadora local que aloja IA y acceso a ConstruBase. Todavía no existen esa interfaz ni el enlace de acceso.
3. **Ofrecer Mini-PAI a otros usuarios:** acceso web con usuario y contraseña, suscripciones y separación de los presupuestos. Diseño y despliegue pendientes.
4. **Desarrollar PAI:** ampliar hacia elaboración y gestión de presupuestos y análisis. No supone implementar esas funciones ahora.

## Estado actual

Existen módulos de inspección Excel, interpretación IA por bloques con evidencia de celdas, búsqueda SQL de candidatos, comparación técnica, confirmación, revisión y exportación Excel más Markdown. ConstruBase se consulta en modo lectura. El usuario comprobó el copiado del formato generado a Neodata; ese formato se conserva.

**Todavía no está validado el flujo completo para uso autónomo.** Después de la [auditoría inicial](mini-pai/AUDITORIA-EXTRACCION.md), la nueva [ruta tabular](mini-pai/EXTRACCION-TABULAR.md) recuperó 78 conceptos y 15 agrupadores: 312 campos cotejados sin diferencias. La extracción tardó 39.467 s con Nemotron; no incluye SQL, selección ni exportación. Es una ruta explícita para una tabla estable, no una garantía para todos los formatos.

El exportador final rechaza códigos con descripciones distintas entre originales conservados y matrices seleccionadas. Pasaron 145 pruebas; el formato Excel se conserva.

Nemotron sigue como modelo principal. Hay ensayos anteriores y herramientas de laboratorio, pero falta comparar la combinación propuesta de embeddings y evaluadores en el flujo actual, con los mismos datos y mediciones de calidad, tiempo y memoria. Tener modelos descargados no significa que estén integrados o evaluados.

Especificación, formato y pendientes: [Mini-PAI](mini-pai/README.md).

Comparación local preparada para Nemotron y Gemma: [ejecutar el test y obtener reportes Markdown](mini-pai/PRUEBA-MODELOS.md). No cambia el modelo configurado ni consulta SQL.

## Organización

| Ubicación | Contenido |
| --- | --- |
| `mini-pai/` | Documentación del producto, guía de pruebas y referencias |
| `docs/` | Mapa del código y documentación general |
| `docs/historial/` y `mini-pai/historial/` | README anteriores, decisiones y mediciones históricas |
| `tests/` | Pruebas automatizadas |
| `skills/analizar-presupuesto/` | Skill versionada |
| `.clinerules/` | Instrucciones para pruebas desde Cline |
| `ejemplos/` | Ejercicios iniciales ajenos al flujo |
| `datos_privados/` | Nuevas entradas y referencias locales; contenido excluido de Git |
| `salidas/` | Resultados por ejecución; excluidos de Git |
| `*.py` de la raíz | Módulos y comandos actuales; se mantienen sus rutas para conservar imports, comandos y acceso a la skill |

El [mapa del repositorio](docs/ESTRUCTURA.md) explica cada grupo de módulos. La estructura es pequeña y puede evolucionar con el producto. Los Excel privados existentes conservan su ubicación en `mini-pai/` para no romper referencias; están excluidos de Git. Los resultados históricos externos mantienen las rutas documentadas en [CONTINUIDAD.md](mini-pai/CONTINUIDAD.md).

## Preparación local y pruebas

Se utilizan Python, `openpyxl`, `pyodbc`, SQL Server con ODBC Driver 18 y Ollama para la configuración local. La instalación limpia en otro equipo sigue pendiente de comprobar. Desde la raíz:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-laboratorio.txt
python -m unittest discover -v
```

La segunda instalación añade las dependencias de las pruebas de laboratorio. No se necesitan IA ni SQL en vivo para la suite unitaria; sí para las pruebas reales de esas etapas.

Configurar el archivo local `.env` según [.env.example](.env.example), sin publicarlo. Para Ollama, definir `PRECIOAI_AI_PROVIDER=ollama` y `PRECIOAI_AI_MODEL` con un modelo instalado. SQL utiliza `PRECIOAI_SQL_*`.

Para probar las etapas, consultar [GUIA-CLINE.md](mini-pai/GUIA-CLINE.md). `leer_presupuesto.py` es un prototipo de columnas fijas, no la entrada apropiada para presupuestos variables. No hay todavía un comando único validado que orqueste todo el flujo autónomamente.

## Revisión e historial

El trabajo continúa en el [PR #3](https://github.com/Big-nenu/PrecioAI/pull/3), sin fusionar. Se conservan íntegros los [antecedentes de PAI](docs/historial/README-PAI-2026-11-06.md) y el [historial de Mini-PAI](mini-pai/historial/README-2026-11-06.md). Sus planes antiguos no sustituyen la especificación vigente.
