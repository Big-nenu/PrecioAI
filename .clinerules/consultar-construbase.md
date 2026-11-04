# Consultas a ConstruBase

Cuando el usuario pida buscar conceptos en ConstruBase, NO busques archivos de base de datos dentro del repositorio. ConstruBase es una base SQL Server instalada en el equipo local.

Utiliza el script existente `buscar_conceptos.py` desde la terminal del proyecto:

```powershell
python buscar_conceptos.py "trazo nivelación"
```

El script devuelve JSON con `Codigo`, `Descripcion`, `DescripcionLarga`, `IdUnidad` e `IdTipo`. Compara las descripciones completas y explica qué coincidencias parecen pertinentes; no afirmes haber recuperado matrices o costos, porque este script solo consulta conceptos.

Para búsquedas complejas, comienza con las palabras principales (por ejemplo `trazo nivelación`) y analiza los resultados, en lugar de pasar toda la frase literal: el script actual requiere que aparezcan todas las palabras buscadas.

Si el script solicita una contraseña, NO la pidas en el chat ni intentes almacenarla en archivos del proyecto. Pide al usuario que ejecute el comando localmente si no es posible completar la entrada segura desde la terminal. No muestres credenciales en comandos, registros o respuestas.

Solo se permiten consultas de lectura. No alteres datos ni esquema de ConstruBase.
