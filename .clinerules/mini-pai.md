# Ejecutar Mini-PAI con evidencia

Para presupuestos y ConstruBase, leer skills/analizar-presupuesto/SKILL.md y
mini-pai/GUIA-CLINE.md. Ejecutar los módulos mini_pai_* desde la raíz del proyecto.
No utilizar el prototipo leer_presupuesto.py para un libro de estructura variable.
Inspeccionar todas las hojas antes de afirmar un conteo; no heredar conteos previos.
Para una tabla estable con cabeceras reconocibles, usar la ruta --por-tabla del
intérprete según la skill. Cotejar su alcance; no tratar otras hojas como procesadas.
ConstruBase usa SQL Server local en lectura: no requiere autenticaciones de servicios
externos ni Composio. Un fallo debe corresponder a una herramienta realmente ejecutada.
No afirmar que se ejecutó lo que solo se planeó o se leyó. Guardar evidencia por etapa.
Si el usuario pide preguntas al final, acumularlas sin inventar sus respuestas.
Respetar la orden de no exportar. Nunca modificar el presupuesto ni ConstruBase.

Para probar solo el Excel con los conceptos originales, ejecutar desde la raíz:
`python mini_pai_exportar.py "RUTA_INTERPRETACION.json" --solo-originales --salida "RUTA_NUEVA.xlsx"`.
Usar el exportador oficial y verificar el archivo generado. En los encabezados, las claves de partida y subpartida van en Partida. En los conceptos conservados, Código y Código auxiliar llevan la clave original. Esta prueba no consulta ConstruBase ni solicita decisiones de matrices.

Para interpretar con `--por-tabla`, iniciar una sola sesión persistente y guardar su identificador. Mini-PAI imprime el PID y el avance por bloque en stderr. Consultar la salida de esa misma sesión hasta que termine, incluso si una lectura vence. Si se cancela, detener la sesión de ejecución y comprobar que el PID del intérprete ya salió. Si el intérprete informa que el archivo ya está en proceso, consultar la corrida activa.
