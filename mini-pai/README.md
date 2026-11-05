# Mini-PAI — Excel de presupuesto a Neodata

## Objetivo

Primera herramienta independiente dentro del repositorio PrecioAI. Convertir presupuestos de construcción recibidos en Excel, con estructuras variables o desordenadas, a un Excel que pueda copiarse/importarse en Neodata PU Win+. Resolver primero esta necesidad práctica y reutilizar después las herramientas en PrecioAI.

**Alcance de esta etapa:** transformar catálogos de conceptos y conservar partidas, subpartidas, códigos, descripciones, unidades y cantidades. No generar todavía matrices nuevas ni construir la plataforma web.

## Flujo deseado (aún no implementado de extremo a extremo)

1. El usuario proporciona un Excel de presupuesto. No asumir columnas, encabezados ni jerarquías fijas.
2. La IA identifica partidas, subpartidas y conceptos; extrae código, descripción, unidad y cantidad sin perder la relación con el archivo original. Las ambigüedades se reportan, no se inventan.
3. Para cada concepto, identifica palabras clave y atributos técnicos y consulta ConstruBase **en modo lectura**. Una coincidencia de palabras no demuestra equivalencia técnica; comparar también unidad, alcance y condiciones.
4. Si se encuentra una equivalencia técnicamente válida, utilizar el **Código** del concepto de ConstruBase y conservar en **Código auxiliar** la clave original del cliente. Mantener la descripción propia del concepto de ConstruBase y la descripción original en **Descripción auxiliar**.
5. Si no se encuentra equivalencia, conservar los datos originales en los campos principales y auxiliares, señalando el caso en el reporte. No inventar códigos, descripciones ni coincidencias. Resolver o marcar conflictos cuando un mismo código principal corresponda a descripciones diferentes.
6. Generar el Excel con la estructura de partidas/subpartidas y un reporte de conceptos encontrados, no encontrados y dudosos.
7. Validar el resultado copiándolo/importándolo realmente en Neodata PU Win+.

**Importante:** en Mini-PAI aún hay que decidir cómo confirmar coincidencias dudosas antes de reutilizar un concepto de ConstruBase. No asumir selección automática confiable.

## Formato de salida de referencia

El *Manual PUWIN+*, páginas 246 y 458, describe el uso de códigos auxiliares y el copiado desde Excel con las columnas **en este orden**:

```text
Partida | Código | Código auxiliar | Descripción auxiliar | Unidad | Cantidad
```

El Código auxiliar admite **hasta 20 caracteres** según el manual. El código principal identifica el concepto interno; el auxiliar permite conservar el código de la licitación o cliente sin duplicar conceptos prácticamente iguales. La descripción auxiliar conserva el texto del cliente.

**Pendiente de validar:** comportamiento exacto al pegar/importar conceptos no existentes en el catálogo, manejo de descripciones completas y conflictos de códigos, y correspondencia de la estructura de partidas y subpartidas. No afirmar compatibilidad definitiva hasta probarlo en Neodata.

## Etapas pequeñas

| Etapa | Tarea | Estado |
| --- | --- | --- |
| 0 | Conectar y consultar ConstruBase | **Parcialmente comprobado**: consultas SQL y recuperación de matrices; falta integrar IA y evaluar equivalencias |
| 1 | Interpretar un Excel desconocido y distinguir partidas, subpartidas y conceptos | **Pendiente**: existe un lector prototipo para un formato específico, no un lector flexible |
| 2 | Buscar y evaluar conceptos equivalentes en ConstruBase | **Pendiente de integración**: existen funciones de búsqueda iniciales |
| 3 | Generar Excel con códigos y descripciones auxiliares | **Pendiente** |
| 4 | Generar reporte y comprobar importación en Neodata | **Pendiente** |

**Próxima tarea: etapa 1.** Definir una representación intermedia revisable de partidas, subpartidas y conceptos y probar la interpretación de distintos archivos, sin programar reglas rígidas para un solo Excel.

## Arquitectura provisional

Se contempla una **skill** especializada (instrucciones para la IA) y herramientas concretas para inspeccionar Excel, consultar ConstruBase y generar el archivo de salida. La carpeta `references/` podría guardar reglas y documentación de Neodata; `scripts/` contendría funciones ejecutables. **Esta estructura aún es una propuesta, no está implementada.** Se busca mantener el sistema utilizable con distintos modelos de IA, sin depender de uno específico.

El código existente en la raíz de PrecioAI permanece donde está por ahora. No duplicarlo ni moverlo antes de determinar qué puede reutilizar Mini-PAI.

## Fuentes y ejemplos

- `Manual PUWIN+.pdf`, especialmente páginas 246 y 456–458 (archivo de referencia compartido en el proyecto, no necesariamente versionado en Git).
- `CATÁLOGO DE CONCEPTOS PARA ANALISIS DE MAESTRO.xls` (ejemplo del curso avanzado).
- `pepe-sucio.xlsx`, `pepe-limpio.xlsx` y `presupuesto_1.xlsx` (ejemplos de entrada/salida compartidos; no asumir que están en el repositorio).
- ConstruBase: catálogo y matrices de referencia, **sin modificar la base**.

## Reglas de trabajo

- Distinguir **comprobado**, **pendiente** e **hipótesis**.
- Preservar el archivo original y la trazabilidad de cada concepto.
- No crear códigos ni coincidencias ficticias.
- Implementar una etapa pequeña a la vez; reutilizar el código existente y evitar dependencias innecesarias.
- No subir presupuestos privados, bases de datos ni credenciales al repositorio.
- Antes de comercializar una solución que dependa de ConstruBase o Neodata, verificar los derechos y condiciones de uso correspondientes.
