# Mapa del repositorio

Documentación vigente: [PrecioAI](../README.md) y [Mini-PAI](../mini-pai/README.md). El historial conserva resultados y decisiones anteriores, sin definir el comportamiento actual.

## Código ejecutable

| Grupo | Archivos | Responsabilidad |
| --- | --- | --- |
| Entrada flexible | `mini_pai_interpretar.py`, `mini_pai_tabla.py`, `mini_pai_completar.py` | Inspección, clasificación por bloques, evidencia y correcciones explícitas |
| Recuperación | `mini_pai_claves.py`, `mini_pai_buscar.py`, `buscar_conceptos.py`, `ranking_conceptos.py` | Consultas propuestas por IA, acceso SQL y orden de candidatos |
| Decisiones | `mini_pai_seleccionar.py`, `mini_pai_revision.py`, `mini_pai_confirmar.py` | Comparación técnica, revisión, decisiones y comprobación SQL |
| Entrega | `mini_pai_exportar.py` | Excel y Markdown con el formato existente |
| Compartidos | `proveedor_ia.py`, `numeros_tecnicos.py` | Configuración y llamadas IA; comprobaciones numéricas |
| Laboratorio | `laboratorio_coincidencias.py`, `comparar_evaluadores.py` | Experimentos separados; no sustituyen el modelo principal |
| Herramientas de análisis | `consultar_matriz.py`, `diagnosticar_matriz.py`, `calculo_importes.py` | Consultas y cálculos parciales; no constituyen un motor completo de precios unitarios |
| Prototipo anterior | `leer_presupuesto.py` | Lector de hoja y columnas fijas; no es la entrada flexible |

Los módulos siguen en la raíz porque se importan entre sí y buscan la skill y configuración desde ella. Un traslado futuro a un paquete debe actualizar imports, comandos y rutas; no se realiza solo para cambiar el aspecto de las carpetas.

## Documentación y pruebas

- `tests/`: 20 módulos de pruebas. Desde la raíz: `python -m unittest discover -v`. Algunos comparten ejemplos mediante imports del paquete `tests`.
- `mini-pai/`: especificación vigente, guía, búsqueda y reportes de experimentos.
- `docs/historial/` y `mini-pai/historial/`: copias completas de los README anteriores. Conservan los comandos y mediciones históricas.
- `skills/analizar-presupuesto/`: skill y escenarios de evaluación. Preparar escenarios no significa haberlos ejecutado satisfactoriamente en Cline.
- `.clinerules/`: reglas del asistente de desarrollo.
- `ejemplos/hola.py`: ejercicio inicial conservado fuera del flujo.

## Archivos locales

La configuración `.env`, bases, presupuestos y salidas no se publican. Los Excel existentes mantienen su ubicación en `mini-pai/` para conservar referencias. Para nuevos archivos se recomienda `datos_privados/entradas/` y `datos_privados/referencias/`. Crear una carpeta nueva por ejecución bajo `salidas/`.

Las evidencias históricas externas siguen donde indica [CONTINUIDAD.md](../mini-pai/CONTINUIDAD.md). No se copian datos privados al historial público.

## Reorganización

Se separaron pruebas, ejemplo inicial e historial; se actualizaron los imports entre pruebas. No se movieron los módulos del flujo ni se modificaron su lógica, la skill instalada, el formato Excel, el modelo, SQL o las credenciales.
