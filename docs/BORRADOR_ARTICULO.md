# Identificación de municipios con rezago en el acceso a la educación media superior: un modelo replicable con datos abiertos para México

*Borrador para RIDE — Revista Iberoamericana para la Investigación y el Desarrollo Educativo*

---

## Resumen

**Introducción.** La obligatoriedad de la educación media superior, decretada en
México en 2012, estableció una meta de cobertura universal que el sistema no ha
alcanzado. Focalizar la política requiere identificar en qué municipios se
concentra el rezago, pero los indicadores municipales de deserción derivados de
registros administrativos presentan limitaciones que rara vez se documentan.

**Objetivo.** Se construyó y validó un modelo para identificar los municipios del
país con mayor rezago en el acceso a la educación media superior, empleando
exclusivamente datos abiertos y una estrategia de validación que permitiera
estimar su desempeño en territorio no observado durante el entrenamiento.

**Método y material.** Se integraron el Censo de Población y Vivienda 2020, el
Formato 911 de la Secretaría de Educación Pública y las bases municipales del
CONEVAL, para los 2,469 municipios y 189,432 localidades del país. La variable
dependiente fue la tasa de inasistencia escolar de la población de 15 a 17 años,
medida por lugar de residencia. Se calculó la distancia de cada localidad al
plantel más cercano de primaria, secundaria y bachillerato mediante estructuras
de búsqueda espacial. La validación empleó bloqueo por entidad federativa: en
cada pliegue se apartaron estados completos, de modo que cada municipio fue
predicho por un modelo que no observó ninguno de su entidad. El efecto de la
distancia se estimó por separado mediante un contraste entre cohortes de edad
dentro de la misma localidad, con una prueba de falsación.

**Resultados.** La inasistencia nacional de 15 a 17 años fue de 27.20 %
ponderada por población. El modelo basado únicamente en condiciones
estructurales alcanzó un coeficiente de determinación de 0.627 fuera de muestra,
frente a 0.112 de una línea base que asignaba a cada municipio la media de su
propia entidad. El error absoluto medio se mantuvo entre 4.7 y 5.2 puntos
porcentuales con independencia de la entidad. La focalización por tasa
seleccionó municipios rurales de población reducida y capturó 9 % de los
adolescentes fuera de la escuela, por debajo del 10 % que habría obtenido una
selección aleatoria; la focalización por número absoluto capturó 59 %. La
proporción de población hablante de lengua indígena presentó asociación negativa
al controlar por condiciones materiales. En Guerrero, cada kilómetro adicional de
distancia al bachillerato se asoció con una reducción de 1.70 puntos
porcentuales en la asistencia.

**Conclusiones.** El método resultó replicable en entidades no observadas y
produjo una clasificación de riesgo para la totalidad de los municipios del país.
La elección entre focalizar por tasa o por número absoluto modifica por completo
la lista de municipios prioritarios, y constituye una decisión de política que
debe explicitarse. El modelo permite además distinguir restricción estructural de
margen de acción, al identificar municipios cuyo desempeño se aparta de lo que
predicen sus condiciones.

**Palabras clave:** inasistencia escolar, educación media superior, focalización
territorial, datos abiertos, validación espacial.

---

## Abstract

*[Pendiente de traducción una vez cerrada la versión en español. Debe conservar
la estructura de cinco apartados y el tiempo pasado.]*

**Keywords:** school non-attendance, upper secondary education, geographic
targeting, open data, spatial validation.

---

## Introducción

*[Sección por desarrollar con la literatura ya reunida en
`docs/REVISION_LITERATURA.md`. El esqueleto del argumento es el siguiente.]*

La reforma constitucional de 2012 estableció la obligatoriedad de la educación
media superior en México. Una década después, 27.20 % de la población de 15 a 17
años no asistía a la escuela. Focalizar la política pública sobre ese déficit
exige saber dónde se concentra, y esa pregunta aparentemente simple tropieza con
tres obstáculos que este trabajo aborda.

El primero es de medición. Los indicadores municipales de deserción se construyen
con el Formato 911, un registro administrativo de planteles. Quien estudia fuera
de su municipio se contabiliza en el municipio de la escuela, de modo que los
municipios que envían estudiantes aparecen con deserción inflada. A ello se suma
que en los municipios pequeños la tasa fluctúa por razones puramente aritméticas.

El segundo es de validación. Un modelo ajustado y evaluado sobre los mismos
municipios no demuestra que sirva en otro lugar, porque los municipios vecinos
comparten condiciones y el modelo puede memorizar regiones. Afirmar que un método
es replicable exige probarlo en territorio que no participó en su construcción.

El tercero es de criterio de focalización. Ordenar municipios por tasa de
inasistencia y ordenarlos por número de adolescentes fuera de la escuela produce
listas casi disjuntas, y la literatura rara vez explicita cuál de las dos
preguntas responde.

**Pregunta de investigación.** ¿Es posible construir, con datos abiertos, un
modelo que identifique los municipios con mayor rezago en el acceso a la
educación media superior y que conserve su capacidad predictiva en entidades
federativas no observadas durante el entrenamiento?

---

## Materiales y métodos

### Fuentes

Se emplearon tres conjuntos de datos abiertos de cobertura nacional:

1. **Censo de Población y Vivienda 2020** (INEGI), Principales Resultados por
   Localidad: coordenadas geográficas, población por grupo de edad, asistencia
   escolar y características socioeconómicas de 189,432 localidades.
2. **Formato 911** (SEP), ciclos 2019-2020 a 2024-2025: ubicación y matrícula de
   cada plantel de educación básica y media superior.
3. **Bases municipales del CONEVAL**: Índice de Rezago Social 2020 y medición de
   pobreza municipal, incluida la desagregación por grupo de edad.

Cada archivo quedó registrado con su función resumen SHA-256 y su fecha de
obtención, dado que los portales de datos abiertos sustituyen archivos sin
control de versiones.

### La variable dependiente, y por qué no es la tasa de deserción

El planteamiento inicial de esta investigación contemplaba predecir la tasa de
deserción municipal construida con el Formato 911. Se intentó y no resultó
viable, por dos razones que conviene documentar porque afectan a cualquier
trabajo que use esa fuente a nivel municipal.

La primera es de agregación. Los municipios con menos de 300 estudiantes
presentaron una desviación estándar de 6.78 puntos porcentuales entre ciclos
consecutivos, frente a 1.43 en los de más de 5,000. En una proporción
considerable de municipios la tasa anual es, en lo esencial, ruido.

La segunda es de atribución territorial. El cociente entre la cobertura medida
por plantel y la asistencia medida por residencia reveló que, en Guerrero, 39 de
81 municipios son emisores netos de estudiantes. Su deserción medida aparece
inflada por construcción.

En conjunto, la tasa de deserción municipal del Formato 911 arrojó un coeficiente
de determinación ajustado de 0.002 en corte transversal y de 0.017 dentro de
municipios en un panel de cinco transiciones. No es que el fenómeno carezca de
determinantes: es que esa medida no los puede revelar.

Se adoptó en su lugar la **tasa de inasistencia escolar de la población de 15 a
17 años** del Censo 2020. Se mide por lugar de residencia, existe para todos los
municipios, no depende de registros administrativos y capta el resultado
acumulado de no inscribirse y de abandonar, que es lo que interesa focalizar.

### Construcción de la distancia

Para cada localidad se calculó la distancia geodésica al plantel más cercano de
primaria, secundaria y bachillerato, sin restricción municipal. Con 189,432
localidades y 10,003 sedes de bachillerato, la evaluación exhaustiva implicaba
cerca de 1,900 millones de pares; se empleó una estructura de árbol métrico que
resuelve el mismo problema de forma exacta descartando regiones del espacio sin
medirlas. Los resultados se agregaron a municipio ponderando por la población de
15 a 17 años de cada localidad.

La distancia en línea recta subestima el traslado real en terreno montañoso y la
ubicación por centroide de localidad introduce error de medición. Ambas
decisiones sesgan las estimaciones hacia cero.

### Validación con bloqueo espacial

La validación cruzada aleatoria resulta engañosa con datos territoriales: los
municipios vecinos se parecen, de modo que repartirlos al azar deja al modelo
aprender regiones y el desempeño aparente se infla. Se empleó bloqueo por entidad
federativa en ocho pliegues, apartando estados completos. Cada municipio fue
predicho por un modelo que no observó ningún municipio de su entidad.

Se estimaron dos especificaciones. La **estructural** empleó únicamente
condiciones del territorio —distancia, pobreza, rezago social, dispersión del
poblamiento, mercado laboral, vivienda y composición de los hogares— sin incluir
ningún resultado educativo. La **ampliada** agregó la inasistencia de 12 a 14
años. Se excluyó el grado promedio de escolaridad por construirse sobre la
población de 15 años y más, que incluye a la cohorte cuya inasistencia constituye
la variable dependiente.

### Identificación del efecto de la distancia

El modelo predictivo no autoriza interpretaciones causales. Para estimar el
efecto de la única variable claramente modificable por política se empleó, en
Guerrero, un contraste entre cohortes de edad dentro de la misma localidad: dado
que el estado cuenta con 1,721 localidades con secundaria y solo 590 con
bachillerato, una misma localidad puede tener cerca el nivel previo y lejos el
siguiente. Al diferenciar entre cohortes se cancela todo factor que afecte por
igual a ambas edades. Como prueba de falsación se incluyeron simultáneamente las
dos distancias diferenciales en cada ecuación.

---

## Resultados

### Panorama nacional

La inasistencia escolar de 15 a 17 años fue de 27.20 % ponderada por población, y
de 32.40 % como promedio simple entre municipios. La mediana de distancia de las
localidades al bachillerato más cercano fue de 4.09 kilómetros, frente a 2.19
para secundaria y 1.26 para primaria.

### Desempeño predictivo en entidades no observadas

| Especificación | $R^2$ fuera de muestra | Error absoluto medio |
|---|---|---|
| Línea base: media nacional | 0.000 | 7.63 |
| Línea base: media de la propia entidad | 0.112 | 7.31 |
| Estructural, regresión penalizada | 0.526 | 5.27 |
| **Estructural, potenciación por gradiente** | **0.627** | **4.55** |
| Ampliada, con inasistencia de 12 a 14 años | 0.830 | 2.99 |

*(Figura 1)*

El modelo estructural explicó 62.7 % de la variación empleando solo condiciones
del territorio, sin ningún insumo educativo, en municipios cuyo estado no formó
parte del entrenamiento.

El coeficiente de determinación resultó negativo en 11 de las 32 entidades. El
examen de ese resultado mostró que no obedece a falla del modelo sino a la
naturaleza de la métrica: el coeficiente compara el error contra la varianza
interna de la entidad, y en estados homogéneos esa varianza es mínima. La
correlación entre la dispersión interna y el coeficiente fue de +0.479, mientras
que el error absoluto medio se mantuvo prácticamente constante —5.16 puntos
porcentuales en las entidades con coeficiente negativo contra 4.65 en el resto—.
Baja California Sur, con cinco municipios y una dispersión interna de 2.27
puntos, ilustra el caso. **La implicación operativa es que el modelo discrimina
bien a lo largo del rango nacional, pero no debe emplearse para ordenar
municipios dentro de una entidad homogénea.**

### Focalizar por tasa o por número produce listas distintas

*(Figura 2)*

| Criterio de ordenamiento | Inasistencia media del decil | Adolescentes fuera capturados |
|---|---|---|
| Tasa predicha | 50.28 % | 9 % |
| Número absoluto de adolescentes fuera | — | **59 %** |
| Selección aleatoria | 27.20 % | 10 % |

El resultado más contraintuitivo del trabajo es que **la focalización por tasa
captura menos adolescentes fuera de la escuela que una selección aleatoria**. Los
municipios de tasa más alta son de población reducida: el decil superior por tasa
reúne 247 municipios con 50.28 % de inasistencia, pero concentra apenas 9 % del
total nacional de adolescentes fuera de la escuela. El ordenamiento por número
absoluto señala, en cambio, municipios urbanos —León con 33,474 adolescentes
fuera de la escuela, Tijuana con 21,339, Juárez con 21,146— y 246 municipios
bastan para cubrir 58.6 % del total.

Ambos criterios son legítimos y responden a objetivos distintos: la equidad
territorial frente a la magnitud agregada. Lo que no es legítimo es dejar la
elección implícita.

### Qué condiciones pesan

*(Figura 3)*

Los predictores de mayor peso fueron la pobreza extrema, el índice de rezago
social, la proporción de población de 15 años y más sin escolaridad, la distancia
al bachillerato y el número de personas por hogar. La proporción de población
hablante de lengua indígena presentó asociación **negativa** una vez controladas
las condiciones materiales, resultado coherente con el obtenido en el análisis
por localidad para Guerrero, donde esa variable perdió toda significancia
estadística.

Estos coeficientes describen asociaciones dentro de un modelo predictivo y no
autorizan lectura causal. La asociación positiva entre disponibilidad de
automóvil e inasistencia ilustra el punto: capta ruralidad y dispersión, no un
efecto del vehículo.

### Efecto causal de la distancia

En el contraste entre cohortes para Guerrero, cada kilómetro adicional de
distancia al bachillerato respecto de la secundaria se asoció con una reducción
de 1.70 puntos porcentuales en la asistencia (EE = 0.14; IC 95 % [−1.97, −1.42];
n = 4,519). Una especificación independiente en niveles, con efectos fijos de
municipio y catorce covariables, arrojó −1.686.

La prueba de falsación resultó simétrica: en cada ecuación pesó únicamente la
distancia al nivel correspondiente a la edad.

| Variable dependiente | Distancia del nivel correspondiente | Distancia del otro nivel |
|---|---|---|
| Brecha 15-17 frente a 12-14 | **−1.70** (p < 0.001) | −0.28 (p = 0.286) |
| Brecha 12-14 frente a 6-11 | **−2.99** (p < 0.001) | −0.20 (p = 0.025) |

Una explicación basada en el aislamiento general no genera ese patrón.

El cierre de todos los diferenciales de distancia en Guerrero habría elevado la
asistencia de 70.79 % a 72.44 %: 1.66 puntos porcentuales, equivalentes a unos
3,347 adolescentes. El efecto por kilómetro es considerable, pero la exposición
es baja porque la política ya cerró la mayor parte de esa brecha.

### Restricción estructural frente a margen de política

*(Figura 4)*

La diferencia entre la inasistencia observada y la predicha por las condiciones
estructurales distingue dos situaciones. Un municipio pobre y aislado con la
inasistencia que le corresponde enfrenta una restricción material; uno que se
desempeña muy por debajo de sus pares enfrenta algo más.

El análisis de esas diferencias se restringió a los 1,946 municipios con al menos
200 adolescentes de 15 a 17 años. Los 523 restantes, que concentran 0.8 % de la
población de esa edad, presentan tasas en las que el cambio de condición de una
sola persona desplaza el indicador varios puntos, y su inclusión convertía el
ordenamiento en un ranking de varianza muestral.

Entre los municipios que se desempeñaron peor de lo predicho destacaron Chamula
(80.2 % observado contra 57.4 % predicho) y Zinacantán (84.2 contra 62.5) en
Chiapas, y Riva Palacio en Chihuahua (80.1 contra 46.4).

En el extremo opuesto, los dos casos positivos más marcados del país se
localizaron en la región de La Montaña de Guerrero: **Malinaltepec**, con 19.7 %
de inasistencia frente a 51.4 % predicho, e **Iliatenco**, con 12.9 % frente a
40.1 %. Ambos municipios registran más de 83 % de población hablante de lengua
indígena y rezago social alto, condiciones que anticipan lo contrario.

La disponibilidad de planteles no explica el resultado: Malinaltepec cuenta con
5.26 planteles por cada mil adolescentes, pero Iliatenco solo con 2.99, y
Xalpatláhuac, con 6.74, registra 52 % de inasistencia. **El modelo identifica la
anomalía; su explicación requiere trabajo de campo que estas fuentes no
permiten.**

---

## Discusión

### El patrón coincide con la literatura internacional

El hallazgo sobre la distancia —coeficiente por kilómetro elevado junto con un
efecto agregado modesto— coincide con lo que Filmer (2007) reportó para 21 países
de ingreso bajo y con lo que Rodriguez-Segura y Kim (2021) encontraron en
Guatemala, donde la mayoría de la población reside a menos de tres kilómetros de
una primaria y la barrera persiste solo en bolsas concentradas. El contraste con
Burde y Linden (2013), cuyo experimento en aldeas afganas sin oferta previa elevó
la matrícula 35 puntos entre niños y 52 entre niñas, delimita el alcance: la
política de expansión territorial enfrenta rendimientos decrecientes y México se
ubica en el tramo plano de esa curva.

### Sobre la focalización

El resultado de que ordenar por tasa capture menos que una selección aleatoria no
invalida ese criterio, pero obliga a explicitarlo. Un programa que busque reducir
el número total de adolescentes fuera de la escuela debe mirar a las ciudades; uno
que busque cerrar brechas territoriales debe mirar a los municipios rurales
pequeños. Son objetivos distintos y la evidencia no decide entre ellos.

### Sobre la desventaja indígena

La asociación negativa de la condición indígena al controlar por condiciones
materiales, replicada en los dos niveles de análisis, sugiere focalizar por
marginación y accesibilidad antes que por adscripción étnica. El resultado dialoga
con el contexto nacional, donde 9.7 % de la población indígena completó la
educación media superior frente a 19.6 % del total: la brecha existe, pero este
análisis la atribuye a condiciones materiales.

### Lo que el modelo no puede hacer

Este trabajo produce analítica descriptiva, diagnóstica y predictiva; no produce
analítica prescriptiva. Identificar dónde se concentra el rezago no equivale a
saber qué intervención lo reduciría ni a qué costo. De las variables del modelo,
solo la distancia cuenta con estimación causal, y su margen agregado resultó
reducido.

La unidad de análisis impone un segundo límite: es municipal. Un sistema de
alerta temprana que active intervenciones individuales requiere datos de
estudiantes, no agregados territoriales.

De Vries y Grijalva Martínez (2021) encontraron, con encuestas directas a
desertores en Oaxaca, que la razón más mencionada fue la vida social con
amistades o pareja, por encima de las económicas. El presente trabajo identifica
condiciones estructurales y no observa las motivaciones individuales de quienes
tuvieron la escuela cerca y aun así no asistieron.

### Limitaciones

1. Corte transversal único (Censo 2020); el diseño no explota variación temporal.
2. Distancia geodésica y planteles ubicados por centroide de localidad; ambas
   sesgan hacia cero.
3. La asistencia de 15 a 17 años incluye a quienes permanecen en secundaria por
   rezago, sin posibilidad de separarlos con datos censales.
4. El coeficiente de determinación dentro de entidades homogéneas no es una
   medida informativa, como se documentó.
5. La identificación causal de la distancia se realizó solo para Guerrero.

---

## Conclusiones

Se construyó un modelo de identificación de municipios con rezago en el acceso a
la educación media superior que conserva capacidad predictiva en entidades
federativas no observadas durante su entrenamiento, con un coeficiente de
determinación de 0.627 frente a 0.112 de la mejor línea base disponible. El
método emplea exclusivamente datos abiertos y es aplicable a cualquier entidad
del país.

La elección del criterio de focalización modifica por completo la lista de
municipios prioritarios: ordenar por tasa captura 9 % de los adolescentes fuera
de la escuela y ordenar por número absoluto captura 59 %. Esa decisión es de
política pública, no técnica, y debe explicitarse.

La distancia al plantel tiene un efecto causal identificado de 1.70 puntos
porcentuales por kilómetro, replicado por dos estrategias independientes y
sostenido ante una prueba de falsación simétrica, pero su margen agregado es
reducido porque la política ya cerró la mayor parte de esa brecha.

Finalmente, el trabajo documenta que la tasa de deserción municipal derivada del
Formato 911 no es apta para el análisis municipal en contextos de alta movilidad
estudiantil, y ofrece un procedimiento de diagnóstico basado en el contraste entre
la cobertura medida por plantel y la asistencia medida por residencia.

---

## Futuras líneas de investigación

1. **Calibrar la distancia con el tiempo de traslado declarado.** El Cuestionario
   Ampliado del Censo 2020 registra tiempo y medio de traslado al lugar de
   estudio. Contrastarlo contra la distancia geodésica permitiría cuantificar
   cuánto subestima la línea recta el traslado real. Su restricción es que se
   trata de una muestra probabilística, representativa a nivel municipal pero no
   de localidad.
2. **Explicar los casos positivos.** Malinaltepec e Iliatenco se desempeñan más
   de 27 puntos por encima de lo que predicen sus condiciones. Entender el
   mecanismo requiere trabajo cualitativo y constituye la continuación más
   prometedora de este trabajo.
3. **Descender al estudiante.** El paso de la identificación territorial a la
   alerta temprana accionable exige datos individuales de trayectoria escolar.
4. **Replicar con el Censo 2030** para convertir el corte transversal en panel.

---

## Referencias

> Las 16 referencias fueron verificadas en su fuente original. Los metadatos aún
> por confirmar y las fuentes identificadas pero no consultadas están en
> `docs/REVISION_LITERATURA.md`.

Arellano-Esparza, C. A., y Ortiz-Espinoza, Á. (2022). Educación media superior en
México: abandono escolar y políticas públicas durante la covid-19. *Íconos.
Revista de Ciencias Sociales*, (74), 33-52.
https://doi.org/10.17141/iconos.74.2022.5292

Burde, D., y Linden, L. L. (2013). Bringing education to Afghan girls: A
randomized controlled trial of village-based schools. *American Economic Journal:
Applied Economics*, *5*(3), 27-40. https://doi.org/10.1257/app.5.3.27

Chávez Maciel, F. J., y Murguía Ángeles, M. T. (2010). La educación media
superior a distancia en México y sus efectos para la equidad educativa.
*Apertura: Revista de Innovación Educativa*, (Extra 1), 18-31.

Consejo Nacional de Evaluación de la Política de Desarrollo Social. (2021).
*Índice de Rezago Social 2020 a nivel nacional, estatal, municipal y por AGEB*.
https://www.coneval.org.mx/Medicion/IRS/Paginas/Indice_Rezago_Social_2020.aspx

De la Cruz Orozco, I. (2016). Beneficios esperados de la educación media superior
en comunidades rurales. *Sinéctica*, (46), 1-19.

De Vries, W., y Grijalva Martínez, O. (2021). ¿Dejar la escuela o la vida social?
El abandono en la educación media superior en Oaxaca. *Revista de la Educación
Superior*, *50*(197), 59-80. https://doi.org/10.36857/resu.2021.197.1579

Filmer, D. (2007). If you build it, will they come? School availability and school
enrolment in 21 poor countries. *The Journal of Development Studies*, *43*(5),
901-928. https://doi.org/10.1080/00220380701384588

Hashim, S. A., Kelley-Kemple, T., y Laski, M. E. (2023). *An improved method
for estimating school-level characteristics from census data* (EdWorkingPaper
23-804). Annenberg Institute at Brown University.
https://doi.org/10.26300/chqx-av23

Instituto Nacional de Estadística y Geografía. (2021). *Censo de Población y
Vivienda 2020. Principales resultados por localidad (ITER)*.
https://www.inegi.org.mx/programas/ccpv/2020/

Kondylis, F., y Manacorda, M. (2012). School proximity and child labor: Evidence
from rural Tanzania. *Journal of Human Resources*, *47*(1), 32-63.
https://doi.org/10.3368/jhr.47.1.32

Miranda López, F. (2018). Abandono escolar en educación media superior:
conocimiento y aportaciones de política pública. *Sinéctica*, (51), 1-22.
https://doi.org/10.31391/S2007-7033(2018)0051-010

Rodriguez-Segura, D., y Kim, B. H. (2021). The last mile in school access: Mapping
education deserts in developing countries. *Development Engineering*, *6*, 100064.
https://doi.org/10.1016/j.deveng.2021.100064

Secretaría de Educación Pública. (2024a). *Principales cifras del Sistema
Educativo Nacional 2023-2024*. Dirección General de Planeación, Programación y
Estadística Educativa.
https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/principales_cifras/principales_cifras_2023_2024_bolsillo.pdf

Secretaría de Educación Pública. (2024b). *Registro de alumnado, personal docente
y escuelas de educación básica y media superior (Formato 911)* [Conjunto de
datos]. datos.gob.mx.
https://www.datos.gob.mx/dataset/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911

Solís, P. (2018). La transición de la secundaria a la educación media superior en
México: el difícil camino a la cobertura universal. *Perfiles Educativos*, *40*(159),
66-84.

Subsecretaría de Educación Media Superior. (2024). *Documento base para el
servicio educativo de Telebachillerato Comunitario*. Dirección General del
Bachillerato.
https://dgb.sep.gob.mx/storage/recursos/2024/01/OJmP75xHCN-Documento-Base-para-el-Servicio-Educativo-de-Telebachillerato-Comunitario-2024.pdf
