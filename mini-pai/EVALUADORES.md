# Evaluación adicional de D1 y TEV1 — PR #3

**Conclusión:** no hay evidencia para sustituir Nemotron ni sumar aprobaciones por voto o confianza. Hay rechazos justificados, otros excesivamente literales y documentación insuficiente. D1 aporta alguna discriminación, pero acepta pares con contradicciones; TEV1 no discrimina de forma útil en esta prueba.

**E** equivalente técnicamente; **D** compatible con diferencias (requiere revisión/adaptación); **I** incompatible; **S** información insuficiente. Los números cuentan los **cinco candidatos de cada concepto**, no aprobaciones ni conceptos resueltos.

| Fila / concepto | Nemotron anterior | Nemotron, 4 categorías | D1:3B | TEV1:0.8B | Evidencia y diagnóstico |
| --- | --- | --- | --- | --- | --- |
| 20 — Cimiento de piedra | I5 | I5 | E4/D1 | E5 | Piedra braza con mortero frente a firme/losa de concreto armado: incompatibilidad real. D1/TEV dan falsos equivalentes. |
| 21 — Concreto armado | S5 | D5 | E5 | E5 | Cliente abarca varios elementos y retiro a tiradero; candidatos parciales sin retiro acreditado. No sustitución directa; revisar alcance. |
| 22 — Demolición integral | S5 | I5 | D5 | E5 | Edificio completo e instalaciones, medidos por proyección de cubierta, frente a muros de 7–14 cm. Rechazo justificado. |
| 23 — Demolición integral | I5 | I5 | D5 | E5 | Demolición integral, cubierta, madera e instalaciones frente a muros aislados. Rechazo justificado. |
| 25 — Trazo y nivelación | I1/S4 | D4/I1 | E5 | E5 | Tránsito/nivel y ejes/bancos coinciden semánticamente. «Cuadrilla» vs «personal calificado» parece rigor excesivo; estacas/mojoneras y límites de área aún requieren verificar alcance. |
| 26 — Excavación en cepas | I3/S2 | D3/I2 | E3/I2 | E5 | Tipo B, 0–2 m y seco coinciden en 14301-004/14401-013. Falta acreditar afine/traspaleos/acarreos. «Cualquier medio» admite maquinaria: no es una incompatibilidad. |
| 27 — Excavación a cielo abierto | I1/S4 | D1/I4 | E4/D1 | E5 | B vs I-B/II-B no demuestra contradicción sin leyenda técnica. Manual no contradice «cualquier medio». Otros candidatos sí cambian profundidad/material. Rechazo general excesivo; falta información. |
| 28 — Carga y acarreo | E1/I3/S1 | D5 | E3/D2 | E5 | 10401-104 coincide en excavación, camión, fuera de obra, tiro autorizado y medición en banco. El control Nemotron lo baja a D por inclusiones no enumeradas; muestra sensibilidad a instrucciones/contexto. |
| 30 — Plantilla de concreto | I5 | I5 | I5 | E5 | Cliente pide 6 cm y TMA 3/4; candidatos de 3, 4 o 5 cm. Mismo f’c=100 y M2 no compensan el espesor. Rechazo justificado. |

**Lectura de la tabla:** E4/D1 significa cuatro candidatos etiquetados equivalentes y uno compatible con diferencias. S se ofreció a los tres evaluadores, pero ninguno la eligió en esta ejecución; eso no elimina las lagunas documentales observadas.

## Qué explica el 1/9 anterior

- **Las validaciones no retiraron ocho aprobaciones:** los ocho `seleccion_id` ya eran null, sin errores, y sus comprobaciones estaban vacías. Solo la selección de acarreo pasó a verificación SQL. Cambiar las guardas no recuperaría esas ocho decisiones actuales.
- **Criterio/instrucciones:** la rúbrica automática solo permite E/I/S y exige acreditar cada inclusión. Mezcla omisiones de detalle con diferencias reales. La comparación de conjuntos numéricos de fragmentos completos y ciertas guardas de no_aplica podrían ser demasiado amplias en otros casos; no causaron estos ocho pendientes porque no se ejecutaron para selecciones null.
- **Exceso probable:** trazo (sinónimos y personal especializado), tipo B frente a I-B/II-B sin correspondencia acreditada y considerar manual/maquinaria incompatible con «cualquier medio». No está probado que todo el alcance sea equivalente: faltan inclusiones o una leyenda técnica.
- **Diferencias reales:** piedra/concreto, edificio completo/muro aislado y espesores de 6 frente a 3/4/5 cm. Aquí bajar el rigor produciría errores.
- **Información insuficiente:** inclusiones de afine, traspaleos, acarreos internos, estacas/mojoneras o clasificación de terreno no demostradas en las descripciones. Una omisión no acredita ni descarta automáticamente su costo/alcance.

## ¿Mejoran los otros modelos?

- **D1:** E24/D14/I7 en 45 pares. Detectó los cinco espesores incorrectos y los dos casos explícitos B/C, pero dio E a cuatro de los cinco pares piedra/concreto. También aprobó variantes de trazo con restricciones o alcance adicional. Puede servir como contraste, no como autorización.
- **TEV1:0.8B:** E45/45, incluidos piedra/concreto, B/C y todos los espesores incorrectos. Por ejemplo, el candidato de plantilla de 5 cm recibió una probabilidad E de 0.877 y confianza reportada de 0.835, pese a pedir 6 cm. Esas puntuaciones no son probabilidades verificadas de acierto.
- **Nemotron con la rúbrica nueva:** I27/D18; sin E ni S. Reconoce diferencias/compatibilidad parcial, pero sigue confundiendo algunas omisiones con diferencias comprobadas y conserva descartes literales. El mismo 10401-104, antes E, pasó a D: no se puede atribuir un cambio solo al modelo, pues también cambian rúbrica y contexto pareado.
- **Controles claros, no precisión general:** en diez pares con contradicción explícita (piedra/concreto y 6 cm frente a 3/4/5), Nemotron dio I10; D1 I5/E4/D1; TEV E10. Nueve conceptos, cinco opciones y un solo positivo operativo previo no bastan para medir precisión, sensibilidad o calibración generales.
- **Orden de opciones:** se invirtieron las cuatro categorías en cuatro pares por cada modelo de decisión (8 llamadas adicionales). TEV siguió dando E; el falso equivalente de piedra/concreto de D1 tampoco cambió. D1 sí cambió un caso B/C de I a S. No es únicamente que el programa lea siempre la primera etiqueta.

## Protocolo, límites y reproducción

La selección automática, el proveedor principal y el formato Excel no cambiaron.
Se utilizaron 45 pares (nueve conceptos, cinco candidatos), idénticos en los tres
modelos, con huellas por par. La instantánea coincide exactamente con los conceptos
y candidatos del resultado Nemotron anterior. No se recuperaron nuevas opciones
ni se abrió SQL; no hay aprobaciones, escrituras a ConstruBase ni generación de Excel.

La columna Nemotron anterior es la ejecución operativa de tres categorías y cinco
candidatos juntos. El control nuevo cambia conjuntamente la rúbrica a cuatro
categorías y el contexto a un par independiente: no aísla el efecto de cada cambio.
Los tres controles nuevos reciben el mismo par, instrucciones y categorías; la
interfaz de Nemotron además pide un motivo breve. D1/TEV devuelven puntuaciones,
no explicaciones: la evidencia de la tabla es un cotejo técnico de los textos,
no una justificación inventada atribuida a esos modelos.

Disponibles: `nemotron-3.5-bolt:e4b`, `d1:3b`, `tev1:0.8b`; Ollama 0.40.15.
Nemotron: contexto 8192, generación máxima 2048, razonamiento activado.
No hubo errores en los 135 pares principales. Los ocho controles de orden son
adicionales; no se mezclaron con los recuentos de la tabla. Ningún modelo eligió S
en el control nuevo, aunque hubo información faltante: eso también es una limitación.
No existe un conjunto de referencia completo etiquetado por especialista; estos
resultados no son una medición de precisión general. No está demostrado que corregir
solo instrucciones baste para aumentar las selecciones correctas.

El experimento usa `comparar_evaluadores.py`, separado del flujo operativo, y las
funciones HTTP del laboratorio y del proveedor existentes. No se instalaron modelos
ni dependencias. Se puede repetir sobre los JSON privados ya guardados:

```powershell
python comparar_evaluadores.py salidas/candidatos-ampliados.json --baseline salidas/decisiones-ia-razonamiento.json --salida salidas/comparacion-evaluadores.json
```

La salida debe ser nueva; se guardan respuestas, puntuaciones, motivos de Nemotron,
huellas y modelos disponibles. Las confidencias nunca se convierten en aprobaciones.
Los controles de orden usan `evaluar_decision(..., orden=list(reversed(CRITERIOS)))`
sobre los mismos cuatro pares; no cambian los textos ni las definiciones.
Las respuestas y presupuestos privados permanecen fuera de Git.

Interfaces oficiales: [D1](https://ollama.com/library/d1:3b) y
[TEV1](https://ollama.com/library/tev1:0.8b). Pasaron 96 pruebas: incluidas identidad
de pares, detección de cambios en candidatos, cuatro etiquetas, probabilidades
inválidas, control de orden y ausencia de aprobación por confianza alta.
