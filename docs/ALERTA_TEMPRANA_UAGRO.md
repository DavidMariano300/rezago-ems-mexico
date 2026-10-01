# Sistema de alerta temprana de abandono escolar a nivel estudiante

**Diseño para la Universidad Autónoma de Guerrero**
Caso: 25,000 estudiantes, Control Escolar, Moodle (~2 millones de eventos
diarios), registros de asistencia y encuestas.

---

> **Por qué este documento existe.** El análisis municipal que precede a este
> diseño llegó a un resultado útil pero limitado: identifica *dónde* se concentra
> el rezago, no *a quién* intervenir. No se puede asignar un tutor a un
> municipio. Este documento aterriza el problema en la unidad donde la alerta sí
> es accionable, y aprovecha cuatro lecciones que costaron trabajo aprender.

## Las cuatro lecciones que traemos del análisis municipal

**1. Agregar destruye la señal.** La tasa de deserción municipal del Formato 911
tiene R² ajustado de 0.002: nada la explica. La misma información a nivel plantel
ya predice algo (R² 0.182 fuera de muestra), y a nivel estudiante debería
predecir bastante más. La regla general: **agregar promedia hacia la media y
borra justamente la variación que se quiere detectar.** Un sistema de alerta
trabaja sobre individuos o no trabaja.

**2. Sin línea base ingenua, cualquier métrica engaña.** A nivel plantel, el
modelo dio R² de 0.182, que suena pobre, hasta compararlo contra la línea base de
"usa el dato del ciclo pasado de ese mismo plantel", que da −0.295. La pregunta
correcta nunca es "¿qué tan bueno es el modelo?" sino **"¿qué tan bueno es
comparado con lo que ya sabríamos sin él?"**. En este sistema la línea base
obligatoria es: *reprobó materias el periodo anterior*. Si el modelo no le gana a
esa regla de una línea, no se despliega.

**3. Los números pequeños fabrican falsas alarmas.** En el modelo nacional, los
municipios con menos de 200 adolescentes copaban la lista de "peores" por pura
varianza muestral. El equivalente aquí: un estudiante con tres entregas, o un
programa educativo con once inscritos. **Toda tasa necesita un piso de
denominador**, y por debajo de él se reporta incertidumbre, no un número.

**4. El dato se atribuye a quien lo genera, no a quien le pertenece.** El
Formato 911 registra al alumno en el municipio de la *escuela*, no en el de su
*casa*, y eso inflaba la deserción de los municipios emisores. El equivalente
aquí: la actividad en Moodle se atribuye a la *cuenta*, no necesariamente a la
*persona* —cuentas compartidas, trabajo en equipo desde un dispositivo, un
estudiante que usa el equipo de un familiar—. Hay que documentarlo antes de
interpretar la inactividad como desinterés.

---

## 1. Tipos de datos involucrados

| Fuente | Naturaleza | Volumen | Latencia | Observaciones |
|---|---|---|---|---|
| Control Escolar | Estructurado, relacional | ~25,000 filas por periodo | Batch diario | Calificaciones, inscripción, plan de estudios, datos personales |
| Moodle — eventos | Semiestructurado (JSON), serie temporal | ~2 millones/día | Streaming o micro-batch | Clics, vistas, entregas, foros |
| Moodle — contenidos | No estructurado (texto) | Variable | Batch | Mensajes en foros, retroalimentación docente |
| Asistencia | Estructurado | ~500,000 registros/periodo | Batch diario | Puede provenir de lectores o captura manual |
| Encuestas | Estructurado + texto libre | Baja frecuencia | Batch | Socioeconómico, satisfacción |
| Contexto externo | Estructurado | Estático | Anual | Censo y CONEVAL por municipio de residencia |

La última fila es el puente con el trabajo municipal: la **inasistencia esperada
del municipio de residencia** entra como una variable más del modelo individual.

---

## 2. Variables predictoras propuestas

Ordenadas por lo que la literatura y nuestro propio análisis sugieren que pesa.
Se marca la latencia porque determina si la variable sirve para alertar temprano
o solo para explicar después.

### Trayectoria académica (la más predictiva, latencia media)

- Materias reprobadas en el periodo anterior y acumuladas
- Promedio y su **tendencia**, no solo su nivel
- Créditos aprobados contra créditos esperados por semestre
- Reinscripción tardía o fuera de plazo
- Cambios de programa educativo

### Compromiso en Moodle (la más temprana, latencia de horas)

- Días desde el último acceso
- Entregas a destiempo y entregas faltantes
- **Tendencia de la actividad semanal**, no el nivel absoluto: lo que anticipa el
  abandono es la caída, no la intensidad baja constante
- Dispersión del acceso: quien entra solo la noche anterior a la entrega
- Participación en foros

### Asistencia (latencia de días)

- Porcentaje de asistencia y su tendencia
- Rachas de inasistencia consecutiva

### Contexto (estático, pero útil para el arranque en frío)

- Municipio de residencia y su inasistencia esperada según el modelo municipal
- Distancia estimada al campus
- Trabajo remunerado declarado en encuesta
- Primera generación en educación superior

**Variable que NO debe entrar: el pago de inscripción.** Predice casi
perfectamente el abandono porque *es* el abandono registrado administrativamente.
Es fuga de información (*leakage*), no predicción.

---

## 3. Problemas de calidad esperables

Las dimensiones clásicas, con la forma concreta que toman aquí:

| Dimensión | Problema esperable en este sistema |
|---|---|
| **Exactitud** | Asistencia capturada a mano con errores; calificaciones corregidas después del cierre |
| **Completitud** | Encuestas con alta no respuesta, y **no aleatoria**: responden menos justo los de mayor riesgo |
| **Consistencia** | Misma persona con matrículas distintas entre Control Escolar y Moodle; nombres con acentos divergentes |
| **Oportunidad** | Calificaciones que llegan al final del periodo, cuando el abandono ya ocurrió |
| **Validez** | Fechas imposibles, calificaciones fuera de rango, centinelas tipo `-999` o `0` que significan "sin dato" |
| **Unicidad** | Duplicados por reinscripción o por cambio de programa |
| **Linaje** | Imposibilidad de saber con qué versión de los datos se emitió una alerta |

Dos problemas merecen atención especial porque no se resuelven con validaciones:

**Sesgo de supervivencia.** Si se entrena solo con quienes siguen inscritos, el
modelo aprende el perfil del que se queda, no del que se va. La población de
entrenamiento debe incluir a los que ya abandonaron.

**Desbalance de clases.** Si abandona entre 8 y 15 %, un modelo que prediga
"nadie abandona" acierta 85-92 % de las veces y es inútil. **La exactitud global
no es una métrica admisible aquí.**

---

## 4. Análisis descriptivos previos

Antes de modelar, y sin los cuales el modelo se construye a ciegas:

1. **Curva de supervivencia por cohorte y programa**: en qué semestre se va la
   gente. En nuestro análisis de media superior, el 21.6 % del abandono ocurría
   en el paso de primero a segundo; es de esperar un patrón análogo.
2. **Tasa de abandono por programa, turno y campus**, con intervalos de confianza
   y piso de denominador.
3. **Distribución de la actividad en Moodle** y su relación con la calificación.
4. **Mapa de calor de inactividad por semana** para ver si la caída es gradual o
   súbita; eso determina cuánta anticipación es posible.
5. **Calidad de los datos como entregable propio**: completitud por campo y por
   fuente, antes que cualquier modelo.

---

## 5. Enfoque predictivo

### Formulación

Clasificación binaria: probabilidad de que el estudiante **no se reinscriba en el
siguiente periodo**, estimada en varios cortes temporales (semana 4, 8 y 12).

El corte importa: una alerta en la semana 12 llega tarde para intervenir; una en
la semana 4 tiene menos información. Conviene reportar las tres y dejar que el
área de tutoría elija el punto de operación.

### Validación

**Temporal, nunca aleatoria.** Entrenar con cohortes de ciclos anteriores y
evaluar en el ciclo siguiente, que es la situación real de uso. Una validación
aleatoria mezclaría periodos y daría un desempeño inflado, por la misma razón que
el bloqueo espacial fue necesario en el análisis municipal.

Conviene además un bloqueo adicional **por programa educativo**, para saber si el
modelo sirve en carreras que no vio.

### Métricas

| Métrica | Para qué |
|---|---|
| **AUC-PR** | Métrica principal; apropiada con clases desbalanceadas, a diferencia de AUC-ROC |
| **Precisión en el top-k** | De los k estudiantes señalados, cuántos efectivamente abandonaron. Es lo que determina si tutoría pierde el tiempo |
| **Cobertura (recall) en el top-k** | Qué fracción de los que abandonan alcanza a señalar |
| **Lift sobre la línea base** | Única comparación que decide el despliegue |

**Línea base obligatoria:** señalar a quien reprobó una o más materias en el
periodo anterior. Es gratis y cualquier coordinador puede aplicarla. El modelo
solo se justifica si la supera de forma clara.

### Algoritmo

Regresión logística regularizada como punto de partida —interpretable, y el
tutor necesita saber *por qué* se señaló a alguien— y potenciación por gradiente
como contraste. La diferencia de desempeño entre ambas indica cuánta no
linealidad hay realmente; si es poca, conviene quedarse con la interpretable.

**Calibración obligatoria.** Una probabilidad de 0.7 debe significar que
aproximadamente 70 de cada 100 estudiantes así señalados abandonan. Sin
calibración no se puede fijar un umbral de intervención de forma defendible.

### Equidad

Evaluar el desempeño por sexo, programa, municipio de origen y condición de
hablante de lengua indígena. Un modelo con buen desempeño global puede fallar
sistemáticamente en un subgrupo. Nuestro propio análisis municipal mostró que la
condición indígena dejaba de predecir al controlar por condiciones materiales:
conviene verificar que el modelo individual no reintroduzca por la puerta
trasera una desventaja que es material y no étnica.

---

## 6. ¿Existe una necesidad real de Big Data?

**Para el modelo predictivo, no. Para la ingesta de eventos, sí.** Conviene
separar las dos cosas porque se responden distinto.

El conjunto de entrenamiento son ~25,000 estudiantes por unos cientos de
variables agregadas: decenas de megabytes. Eso cabe holgadamente en la memoria de
una laptop y se entrena en minutos con herramientas convencionales. **Montar
Spark para esto sería un error de diseño**, y es exactamente el error que este
proyecto cometería si no hubiera medido antes: el análisis municipal completo
—2,469 municipios, 189,432 localidades, seis ciclos del Formato 911— ocupa 770 MB
y corre en una máquina de escritorio. Incluso el cálculo de 1,900 millones de
pares de distancias se resolvió en segundos con una estructura de datos adecuada
(un árbol métrico) en lugar de escalar horizontalmente.

**La lección es que conviene optimizar antes de escalar.** Escalar
horizontalmente se justifica cuando el problema no cabe en una máquina, cuando la
carga es intrínsecamente paralela, o cuando se necesita tolerancia a fallos en
producción.

Los 2 millones de eventos diarios de Moodle sí califican: son ~730 millones de
registros al año, que crecen sin cota. Pero **lo que alimenta al modelo no son
los eventos crudos, sino rasgos agregados por estudiante y semana.** La
arquitectura debe reflejar esa asimetría: ingesta y almacenamiento a escala,
modelado en una escala mucho menor.

---

## 7. Arquitectura de datos

```
                    ┌──────────────────────────────────────────┐
  FUENTES           │  INGESTA                                 │
  ─────────         │  ────────                                │
  Control Escolar ──┼─► extracción incremental (CDC) ──┐       │
  Asistencia      ──┼─► batch nocturno ────────────────┤       │
  Encuestas       ──┼─► batch por evento ──────────────┤       │
                    │                                  ▼       │
  Moodle (logs)   ──┼─► bus de eventos ──► micro-batch ──┐     │
                    │   (Kafka)            (5-15 min)    │     │
                    └────────────────────────────────────┼─────┘
                                                         ▼
        ┌────────────────────────────────────────────────────────────┐
        │  ALMACENAMIENTO EN CAPAS (lakehouse con formato tabular     │
        │  transaccional: Delta Lake, Iceberg o Hudi)                 │
        │                                                             │
        │  BRONCE   datos crudos, inmutables, con marca de tiempo     │
        │           de ingesta. Nunca se corrigen; se reprocesan.     │
        │  PLATA    limpios, deduplicados, identidad resuelta,        │
        │           tipos validados, centinelas convertidos a nulo    │
        │  ORO      tablas de rasgos por estudiante y semana, listas  │
        │           para entrenar y para servir                       │
        └────────────────────────────────────────────────────────────┘
                              │                      │
                   ┌──────────┘                      └───────────┐
                   ▼                                             ▼
        ┌─────────────────────┐                      ┌──────────────────────┐
        │ ENTRENAMIENTO       │                      │ INFERENCIA           │
        │ semanal, por lotes  │─── modelo versionado ►│ semanal + bajo       │
        │ validación temporal │                      │ demanda              │
        └─────────────────────┘                      └──────────┬───────────┘
                                                                ▼
                                                     ┌──────────────────────┐
                                                     │ TABLERO DE TUTORÍA   │
                                                     │ lista priorizada +   │
                                                     │ razones + registro   │
                                                     │ de la intervención   │
                                                     └──────────────────────┘
```

### Por qué micro-batch y no streaming puro

El abandono escolar no es un fenómeno de milisegundos. Una alerta que llega 15
minutos después del evento vale exactamente lo mismo que una que llega al
instante, y cuesta mucho menos operar. **El streaming estricto se justifica
cuando la decisión debe tomarse antes de que termine el evento** —detección de
fraude en una transacción, por ejemplo—, que no es el caso.

Procesamiento en micro-lotes de 5 a 15 minutos para los eventos de Moodle, y
batch nocturno para Control Escolar y asistencia, que de todos modos se
actualizan una vez al día.

### Por qué un formato tabular transaccional

Las tres capas necesitan propiedades **ACID** —atomicidad, consistencia,
aislamiento y durabilidad— por una razón concreta: si la carga nocturna falla a
la mitad, no puede quedar un estado intermedio en el que unos estudiantes tengan
datos actualizados y otros no, porque el modelo correría sobre una base
inconsistente y nadie se enteraría. Delta Lake, Iceberg y Hudi aportan eso sobre
almacenamiento de objetos, además de **viaje en el tiempo**: poder reconstruir
exactamente los datos con los que se emitió una alerta hace tres meses.

Esa capacidad no es un lujo técnico. Si un estudiante o un tutor cuestiona una
alerta, hay que poder reproducirla.

### Gobierno, privacidad y seguridad

Este sistema maneja **datos personales de estudiantes identificables**, lo que
en México sitúa el proyecto bajo la normativa de protección de datos personales
en posesión de sujetos obligados. No es un detalle de implementación.

- **Minimización.** No recolectar lo que no se usa. Si el modelo no mejora con el
  dato socioeconómico, no se recolecta.
- **Separación de identidad.** Las tablas de modelado usan un identificador
  seudonimizado; la reidentificación vive en un servicio aparte con control de
  acceso propio y bitácora.
- **Acceso por rol.** Un tutor ve a sus tutorados, no al padrón completo.
- **Catálogo y linaje.** Cada rasgo documentado: de dónde sale, cómo se calcula,
  quién lo mantiene. Sin esto, en seis meses nadie sabe qué significa una columna.
- **Observabilidad.** Alertas automáticas sobre frescura, volumen inesperado,
  deriva en la distribución de los rasgos y caída de desempeño del modelo.
- **Retención.** Plazo definido para los eventos crudos; los agregados pueden
  conservarse más tiempo.
- **Aviso de privacidad y finalidad.** El estudiante debe saber que existe el
  sistema y para qué se usa. Un modelo de alerta usado para algo distinto de
  apoyar al estudiante —por ejemplo, para restringir su inscripción— es una
  desviación de finalidad.

### El riesgo que no es técnico

Una alerta puede convertirse en **profecía autocumplida**: si el tutor trata
distinto al estudiante señalado, el señalamiento influye en el resultado. Y un
modelo entrenado con datos históricos que reflejan desigualdades previas puede
reproducirlas. Por eso el sistema debe:

1. Presentarse como apoyo a la decisión, nunca como veredicto.
2. Registrar la intervención realizada, para poder evaluar si sirvió.
3. Someterse a auditoría de equidad por subgrupo de forma periódica.

---

## 8. IA generativa sin comprometer la confiabilidad

Tres usos con valor real, ordenados de menor a mayor riesgo:

**1. Redacción de resúmenes para el tutor.** A partir de cifras ya calculadas, un
modelo de lenguaje redacta en prosa el perfil del estudiante señalado. El dato lo
produce el sistema; el modelo solo lo verbaliza. **Riesgo bajo, porque no calcula
nada.**

**2. Clasificación de texto libre.** Las respuestas abiertas de encuestas y los
mensajes de foro pueden clasificarse por tema o por señal de riesgo. Requiere
validación contra un conjunto etiquetado a mano y medición de concordancia.

**3. Consulta en lenguaje natural sobre los datos (NL2SQL).** Es el uso más
atractivo y el más peligroso.

### Riesgos de NL2SQL y sus controles

| Riesgo | Control |
|---|---|
| Consulta sintácticamente válida pero semánticamente equivocada; devuelve un número creíble y falso | Mostrar siempre el SQL generado junto al resultado; nadie cita una cifra sin ver la consulta |
| Fuga de datos personales en respuestas agregadas | Ejecutar con un rol de solo lectura sobre vistas seudonimizadas; prohibir el acceso a la tabla de identidad |
| Inyección de instrucciones vía el texto de la pregunta | Lista blanca de tablas y operaciones; prohibir DDL y DML |
| Consultas que tumban el almacén | Límites de tiempo, de filas escaneadas y de concurrencia |
| Desagregación hasta identificar a una persona | Umbral mínimo de grupo: ninguna respuesta con menos de *n* individuos |
| El usuario no sabe distinguir una respuesta buena de una mala | Catálogo de consultas verificadas para las preguntas frecuentes; el lenguaje natural solo para exploración |

### Dónde NO usar generación de texto

**En la estimación del riesgo.** La probabilidad de abandono debe salir de un
modelo estadístico entrenado, validado y calibrado, con desempeño medido contra
una línea base. Un modelo de lenguaje no puede sustituirlo porque no está
calibrado, no es reproducible entre ejecuciones y no se puede auditar en el
sentido que exige una decisión que afecta a una persona.

### Humano en el ciclo

El sistema **prioriza**; el tutor **decide**. Concretamente:

- El tutor ve la lista con las razones del señalamiento, no solo un puntaje.
- Puede marcar falsos positivos, y esa marca retroalimenta el modelo.
- Ninguna consecuencia administrativa se deriva automáticamente de una alerta.
- Se registra qué intervención se hizo, lo que con el tiempo permite estimar
  **qué intervenciones funcionan**, que es la única vía para pasar de analítica
  predictiva a prescriptiva.

Ese último punto cierra el círculo con la limitación del análisis municipal:
sabemos identificar dónde y a quién, pero **no sabremos qué hacer hasta registrar
sistemáticamente qué se hizo y qué resultó.**

---

## 9. Resumen de las decisiones y su justificación

| Decisión | Razón |
|---|---|
| Unidad: estudiante, no programa ni campus | Agregar destruye la señal (R² 0.002 a nivel municipal) |
| Variable: no reinscripción al periodo siguiente | Observable, sin ambigüedad y con fecha cierta |
| Validación temporal y por programa | La aleatoria infla el desempeño con datos correlacionados |
| Métrica: AUC-PR y precisión en el top-k | Las clases están desbalanceadas; la exactitud global engaña |
| Línea base: reprobó el periodo anterior | Sin ella no se sabe si el modelo aporta algo |
| Micro-batch, no streaming puro | La decisión no es de milisegundos |
| Lakehouse con formato transaccional | Trazabilidad y reproducibilidad de cada alerta emitida |
| Modelo interpretable como punto de partida | El tutor necesita saber por qué, no solo cuánto |
| IA generativa para redactar, no para estimar | Un modelo de lenguaje no está calibrado ni es auditable |
