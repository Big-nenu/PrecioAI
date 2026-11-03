# PrecioAI

Plataforma web para analizar presupuestos de obra y apoyar la elaboración de precios unitarios mediante inteligencia artificial.

## Objetivo

Permitir que un usuario cargue un presupuesto de construcción (Excel o PDF), identifique sus conceptos y encuentre matrices de precios unitarios relacionadas para facilitar su análisis.

## Alcance inicial (MVP)

1. Cargar un presupuesto en Excel o PDF.
2. Extraer los conceptos, unidades y cantidades.
3. Buscar conceptos y matrices relacionadas en una base de datos de precios unitarios.
4. Presentar los resultados para revisión del usuario.

## Evolución prevista

- Consultar y estructurar los insumos de cada matriz: materiales, mano de obra y equipo.
- Incorporar precios de referencia por ubicación geográfica.
- Mostrar fuentes, fechas y ubicación de los precios consultados.

La recopilación automatizada de precios externos se abordará después de validar la búsqueda y recuperación de matrices.

## Principios del proyecto

- La IA ayuda a interpretar y relacionar conceptos; los cálculos deben ser deterministas y verificables.
- Los resultados deben ser trazables y permitir revisión humana.
- No asumir que una base de datos gratuita permite su reutilización comercial: revisar licencias y permisos antes de integrarla en un producto comercial.
- Mantener fuera del repositorio bases de datos, credenciales y archivos privados.

## Estado

En etapa inicial de definición y exploración técnica.

## Tecnologías

Por definir. La selección se hará conforme se valide el MVP y las necesidades reales del proyecto.