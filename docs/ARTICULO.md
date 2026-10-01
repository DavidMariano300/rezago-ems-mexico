::: portada
titulo: Identificación de Municipios con Rezago en el Acceso a la Educación Media Superior: Un Modelo Replicable con Datos Abiertos para México
autor: Edgar David Mariano Ruiz
afiliacion: Facultad de Ingeniería, Universidad Autónoma de Guerrero
programa: Maestría en Ingeniería para la Innovación y el Desarrollo Tecnológico
fecha: 1 de octubre de 2026
nota: Edgar David Mariano Ruiz, Facultad de Ingeniería, Universidad Autónoma de Guerrero. La correspondencia relativa a este artículo debe dirigirse a Edgar David Mariano Ruiz, Facultad de Ingeniería, Universidad Autónoma de Guerrero, Chilpancingo de los Bravo, Guerrero, México. Correo electrónico: 25600451@uagro.mx. ORCID: [pendiente de registro]. Declaración de conflicto de intereses: el autor declara no tener conflictos de intereses. Los datos y el código que sustentan los resultados proceden en su totalidad de fuentes abiertas y se encuentran disponibles para su verificación.
:::

## Resumen

La reforma constitucional de 2012 estableció la obligatoriedad de la educación media superior en México, pero una década después el 27.20% de la población de 15 a 17 años no asistía a la escuela. El objetivo de este trabajo fue construir y validar un modelo capaz de identificar los municipios con mayor rezago en el acceso a ese nivel educativo, empleando exclusivamente datos abiertos. Se integraron el Censo de Población y Vivienda 2020, el Formato 911 de la Secretaría de Educación Pública y las bases municipales del Consejo Nacional de Evaluación de la Política de Desarrollo Social, para los 2,469 municipios y 189,432 localidades del país. La variable dependiente fue la tasa de inasistencia de 15 a 17 años medida por residencia, adoptada tras documentar que la tasa de deserción administrativa resulta inservible a escala municipal. La validación empleó bloqueo por entidad, de modo que cada municipio fue predicho por un modelo que no observó ninguno de su estado. El modelo basado únicamente en condiciones estructurales alcanzó un coeficiente de determinación de 0.627 fuera de muestra, frente a 0.112 de la mejor línea base disponible. Ordenar los municipios por tasa capturó el 9% de los adolescentes fuera de la escuela, por debajo del 10% que habría obtenido una selección aleatoria, mientras que ordenarlos por número absoluto capturó el 59%. Se concluye que el procedimiento es replicable en territorio no observado y que la elección del criterio de focalización constituye una decisión de política que debe explicitarse.

*Palabras clave:* inasistencia escolar, educación media superior, focalización territorial, datos abiertos, validación espacial

## Abstract

The 2012 constitutional reform made upper secondary education compulsory in Mexico, yet a decade later 27.20% of the population aged 15 to 17 was not attending school. This study aimed to build and validate a model capable of identifying the municipalities with the greatest deficit in access to this educational level, using exclusively open data. Three sources were integrated for all 2,469 municipalities and 189,432 localities in the country: the 2020 Population and Housing Census, the Ministry of Education's Formato 911 school census, and the municipal poverty and social lag databases of the National Council for the Evaluation of Social Development Policy. The dependent variable was the school non-attendance rate among those aged 15 to 17, measured by place of residence, which was adopted after documenting that the dropout rate derived from administrative school records is unusable at the municipal scale. Validation used blocking by federal entity, so that every municipality was predicted by a model that had observed no municipality from its own state. The model based solely on structural conditions reached a coefficient of determination of 0.627 out of sample, compared with 0.112 for the best available baseline. Ranking municipalities by rate captured 9% of out-of-school adolescents, below the 10% a random selection would have obtained, whereas ranking them by absolute number captured 59%. The procedure is replicable in unobserved territory, and the choice of targeting criterion constitutes a policy decision that must be made explicit.

*Keywords:* school non-attendance, upper secondary education, geographic targeting, open data, spatial validation

## Introducción

La reforma constitucional de febrero de 2012 incorporó la educación media superior al tramo obligatorio del sistema educativo mexicano y fijó el ciclo 2021-2022 como horizonte para alcanzar la cobertura universal. Transcurrido ese plazo, el Censo de Población y Vivienda 2020 registró que el 27.20% de la población de 15 a 17 años no asistía a la escuela, lo que equivale a casi tres de cada diez adolescentes en edad de cursar el bachillerato. Solís (2018) mostró que ese déficit se origina en dos momentos distintos y separables: la conclusión de la secundaria, que alcanzaba al 82.1% de los jóvenes de 16 y 17 años, y la absorción en el nivel siguiente, que llegaba al 80.7% de quienes concluían. El producto de ambas transiciones deja fuera a un tercio de cada generación. Miranda López (2018) documentó a su vez que las políticas dirigidas al problema concentran el 93.2% de su presupuesto en apoyos económicos, con escasa atención a los factores escolares e institucionales. La magnitud del rezago y la concentración de los instrumentos de política hacen de la focalización territorial una cuestión práctica de primer orden: saber dónde intervenir condiciona la eficacia de cualquier programa.

Esa pregunta, aparentemente simple, tropieza con un primer obstáculo de medición. Los indicadores municipales de deserción escolar se construyen en México a partir del Formato 911, un registro administrativo que censa planteles y no personas. La consecuencia es que todo estudiante se contabiliza en el municipio donde se ubica su escuela y no en aquel donde reside, de modo que los municipios que envían estudiantes hacia las cabeceras regionales aparecen con una deserción artificialmente elevada y los que los reciben con una artificialmente baja. Hashim et al. (2023) describieron este mismo problema de atribución territorial en el contexto estadounidense y propusieron imputar el área de influencia de cada escuela a partir de datos censales, lo que confirma que no se trata de una peculiaridad local sino de una limitación estructural de las fuentes administrativas. A ello se añade que, en municipios con matrícula reducida, la tasa anual fluctúa por razones puramente aritméticas: el cambio de condición de unos pocos estudiantes desplaza el indicador varios puntos porcentuales. La combinación de ambos problemas vuelve la tasa municipal de deserción del Formato 911 inadecuada para el análisis territorial, conclusión que este trabajo documenta empíricamente antes de proponer una alternativa.

El segundo obstáculo es de validación. Un modelo ajustado y evaluado sobre el mismo conjunto de municipios no demuestra capacidad alguna de generalización, porque los municipios vecinos comparten condiciones geográficas, económicas y culturales. Esa autocorrelación espacial permite que un modelo flexible memorice regiones enteras en lugar de aprender relaciones transferibles: al evaluarlo sobre municipios repartidos al azar, cada unidad de prueba tiene vecinos en el conjunto de entrenamiento y el desempeño aparente resulta inflado. Afirmar que un procedimiento es replicable en cualquier parte del país exige, por tanto, probarlo en territorio que no participó en su construcción. Esta exigencia, habitual en la literatura de aprendizaje estadístico aplicado a datos espaciales, rara vez se incorpora a los estudios educativos de corte territorial.

El tercer obstáculo concierne al criterio mismo de focalización. Ordenar los municipios por tasa de inasistencia y ordenarlos por número absoluto de adolescentes fuera de la escuela produce listas prácticamente disjuntas, porque las tasas más altas se registran en municipios rurales de población reducida mientras que los volúmenes mayores se concentran en las ciudades. La literatura sobre acceso geográfico a la educación ha documentado con detalle la relación entre distancia y matrícula —Filmer (2007) para 21 países de ingreso bajo, Rodriguez-Segura y Kim (2021) mediante el mapeo de desiertos educativos en Guatemala— pero suele dejar implícito cuál de las dos preguntas responde. Chávez Maciel y Murguía Ángeles (2010) señalaron en la misma línea que la oferta educativa mexicana ha atendido preferentemente a la población urbana, y que las modalidades a distancia surgieron como respuesta a poblaciones pequeñas y dispersas cuyas condiciones no justificaban servicios convencionales. La decisión entre equidad territorial y magnitud agregada es de política pública y no técnica, pero la evidencia debe presentarse de manera que la haga visible.

De la revisión de la literatura se desprende un vacío concreto. No se identificó para México un modelo municipal de inasistencia en educación media superior que reúna simultáneamente tres características: que emplee exclusivamente fuentes de acceso abierto, de modo que cualquier entidad pueda replicarlo sin infraestructura adicional; que valide su desempeño mediante bloqueo espacial, de modo que la afirmación de replicabilidad descanse en evidencia y no en supuesto; y que documente de manera explícita las limitaciones del Formato 911 como fuente de indicadores territoriales, en lugar de utilizarlo sin examinar sus propiedades. Los trabajos disponibles abordan el abandono escolar desde la encuesta a desertores, desde el análisis de políticas o desde el diagnóstico estadístico descriptivo, pero no desde la construcción y validación de un instrumento de focalización.

El presente trabajo se propone llenar ese vacío. La pregunta que lo orienta es la siguiente: ¿es posible construir, con datos abiertos, un modelo que identifique los municipios con mayor rezago en el acceso a la educación media superior y que conserve su capacidad predictiva en entidades federativas no observadas durante el entrenamiento? El objetivo consiste en construir dicho modelo para la totalidad de los municipios del país, evaluar su desempeño bajo bloqueo espacial por entidad, y derivar de él una clasificación de riesgo que distinga entre la restricción estructural que impone el territorio y el margen de acción que conserva la política pública.

## Materiales y Métodos

### Fuentes de Datos

Se emplearon tres conjuntos de datos abiertos de cobertura nacional:

1. *Censo de Población y Vivienda 2020. Principales resultados por localidad* (Instituto Nacional de Estadística y Geografía [INEGI], 2021), del que se obtuvieron coordenadas geográficas, población por grupo de edad, asistencia escolar y características socioeconómicas de 189,432 localidades.
2. *Registro de alumnado, personal docente y escuelas de educación básica y media superior* (Secretaría de Educación Pública [SEP], 2024b), conocido como Formato 911, para los ciclos 2019-2020 a 2024-2025, del que se obtuvieron la ubicación y la matrícula de cada plantel.
3. *Índice de Rezago Social 2020* (Consejo Nacional de Evaluación de la Política de Desarrollo Social [CONEVAL], 2021) y la medición de pobreza municipal del mismo organismo, incluida su desagregación por grupo de edad.

Cada archivo descargado quedó registrado con su función resumen SHA-256 y su fecha de obtención, dado que los portales de datos abiertos sustituyen archivos sin control de versiones y la reproducibilidad de los resultados depende de poder acreditar contra qué versión se obtuvieron.

### Variable Dependiente y Justificación de su Elección

El planteamiento inicial de esta investigación contemplaba predecir la tasa de deserción municipal construida con el Formato 911. Se intentó y no resultó viable, por dos razones que conviene documentar porque afectan a cualquier trabajo que utilice esa fuente a escala municipal.

La primera es de agregación. Los municipios con menos de 300 estudiantes presentaron una desviación estándar de 6.78 puntos porcentuales entre ciclos consecutivos, frente a 1.43 en los de más de 5,000 estudiantes. En una proporción considerable de municipios, la tasa anual es en lo esencial ruido estadístico.

La segunda es de atribución territorial. El cociente entre la cobertura medida por plantel y la asistencia medida por residencia reveló que, en el estado de Guerrero, 39 de 81 municipios son emisores netos de estudiantes. Su deserción medida aparece inflada por construcción, sin que ello refleje un abandono real.

En conjunto, la tasa de deserción municipal del Formato 911 arrojó un *R*² ajustado de 0.002 en corte transversal y de 0.017 dentro de municipios en un panel de cinco transiciones. No es que el fenómeno carezca de determinantes: es que esa medida no permite revelarlos.

Se adoptó en su lugar la tasa de inasistencia escolar de la población de 15 a 17 años del Censo 2020. Se mide por lugar de residencia, existe para la totalidad de los municipios, no depende de registros administrativos y capta el resultado acumulado de no inscribirse y de abandonar, que es precisamente lo que interesa focalizar.

### Construcción de la Variable de Distancia

Para cada localidad se calculó la distancia geodésica al plantel más cercano de primaria, secundaria y bachillerato, sin restricción municipal, dado que un estudiante cruza el límite administrativo cuando la escuela contigua le resulta más próxima. Con 189,432 localidades y 10,003 sedes de bachillerato, la evaluación exhaustiva implicaba cerca de 1,900 millones de pares de distancias.

Se empleó un árbol de bolas (*ball tree*) con métrica haversine, implementado en la clase `BallTree` de scikit-learn 1.9.1, que resuelve la consulta del vecino más próximo en tiempo logarítmico respecto del número de sedes. La elección de esta estructura y no de un árbol *k*-dimensional obedece a que este último opera sobre distancias euclidianas en coordenadas cartesianas y no admite la métrica haversine, que es la que mide correctamente la distancia sobre la superficie terrestre a partir de latitud y longitud. Los resultados se agregaron a municipio ponderando por la población de 15 a 17 años de cada localidad.

Todos los cálculos se realizaron en Python 3.12.3 con NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1 y statsmodels 0.15.0.

La distancia en línea recta subestima el traslado real en terreno montañoso y la ubicación de los planteles por centroide de localidad introduce error de medición. Ambas decisiones sesgan las estimaciones hacia cero, por lo que los coeficientes obtenidos deben leerse como cotas inferiores.

### Validación con Bloqueo Espacial

La validación cruzada aleatoria resulta engañosa con datos territoriales, porque los municipios vecinos comparten condiciones y repartirlos al azar permite que el modelo aprenda regiones en lugar de relaciones transferibles. Se empleó en su lugar bloqueo por entidad federativa en ocho pliegues, apartando estados completos en cada uno. El bloqueo por entidad garantiza que el modelo nunca haya visto un municipio del estado que está prediciendo, lo que simula la situación de un analista que aplica el procedimiento a una entidad sobre la cual no dispone de datos previos.

Se estimaron dos especificaciones. La estructural empleó únicamente condiciones del territorio —distancia a los planteles, pobreza, rezago social, dispersión del poblamiento, mercado laboral, características de la vivienda y composición de los hogares— sin incorporar ningún resultado educativo. La ampliada agregó la inasistencia escolar de la población de 12 a 14 años. Se excluyó el grado promedio de escolaridad por construirse sobre la población de 15 años y más, que incluye a la cohorte cuya inasistencia constituye la variable dependiente; su inclusión habría producido un ajuste elevado y vacío de contenido.

Como algoritmos se emplearon una regresión de cresta con penalización L2, cuyo parámetro de regularización se seleccionó por validación cruzada interna sobre una rejilla logarítmica de veinte valores entre 10⁻² y 10³, y una máquina de potenciación por gradiente basada en histogramas, configurada con 400 iteraciones, profundidad máxima de cinco niveles y tasa de aprendizaje de 0.05. Ambas se ajustaron sobre variables estandarizadas. Como referencias de comparación se calcularon dos líneas base: asignar a cada municipio la media nacional, y asignarle la media de su propia entidad calculada sin incluirlo.

### Identificación del Efecto Causal de la Distancia

El modelo predictivo no autoriza interpretaciones causales. Para estimar el efecto de la única variable claramente modificable mediante política pública se empleó, en el estado de Guerrero, un contraste entre cohortes de edad dentro de la misma localidad.

La intuición del diseño es la siguiente: dentro de una misma localidad, los adolescentes de 12 a 14 años suelen tener la secundaria cerca mientras que los de 15 a 17 deben trasladarse a un bachillerato más distante; la diferencia de asistencia entre ambas cohortes, puesta en relación con esa distancia diferencial, aísla el efecto del traslado. El procedimiento es viable porque Guerrero cuenta con 1,721 localidades con secundaria y solo 590 con bachillerato, de modo que una misma localidad puede tener próximo el nivel previo y lejano el siguiente. Al diferenciar entre cohortes se cancela todo factor que afecte por igual a ambas edades: pobreza del hogar, lengua materna, aislamiento en sí mismo y valoración comunitaria de la escuela.

Como prueba de falsación se incluyeron simultáneamente las dos distancias diferenciales —la que separa el bachillerato de la secundaria y la que separa la secundaria de la primaria— en cada una de las dos ecuaciones de brecha. Si el coeficiente capturara un rasgo general de las localidades aisladas y no el efecto de la distancia, ambas medidas deberían pesar de manera semejante en las dos ecuaciones.

## Resultados

### Panorama Nacional

La inasistencia escolar de la población de 15 a 17 años fue de 27.20% ponderada por población, y de 32.40% como promedio simple entre municipios. La mediana de la distancia de las localidades al bachillerato más cercano fue de 4.09 km, frente a 2.19 km para la secundaria y 1.26 km para la primaria.

### Desempeño Predictivo en Entidades No Observadas

::: tabla 1
titulo: Desempeño Predictivo del Modelo en Entidades Federativas No Observadas Durante el Entrenamiento
nota: *R*² = coeficiente de determinación. El error absoluto medio se expresa en puntos porcentuales. Cada municipio fue predicho por un modelo que no observó ningún municipio de su propia entidad durante el entrenamiento.
| Especificación | *R*² fuera de muestra | Error absoluto medio |
|---|---|---|
| Línea base: media nacional | 0.000 | 7.63 |
| Línea base: media de la propia entidad | 0.112 | 7.31 |
| Estructural, regresión de cresta | 0.526 | 5.27 |
| Estructural, potenciación por gradiente | 0.627 | 4.55 |
| Ampliada, con inasistencia de 12 a 14 años | 0.830 | 2.99 |
:::

El modelo estructural explicó el 62.7% de la variación empleando únicamente condiciones del territorio, sin ningún insumo educativo, en municipios cuya entidad no formó parte del conjunto de entrenamiento.

El coeficiente de determinación resultó negativo en 11 de las 32 entidades. El examen de ese resultado mostró que no obedece a una falla del modelo sino a la naturaleza de la métrica: el coeficiente compara el error contra la varianza interna de la entidad, y en estados homogéneos esa varianza es mínima. La correlación entre la dispersión interna y el coeficiente fue de .479, mientras que el error absoluto medio se mantuvo prácticamente constante, con 5.16 puntos porcentuales en las entidades de coeficiente negativo frente a 4.65 en el resto. Baja California Sur, con cinco municipios y una dispersión interna de 2.27 puntos, ilustra el caso. La implicación operativa es que el modelo discrimina adecuadamente a lo largo del rango nacional, pero no debe emplearse para ordenar municipios dentro de una entidad homogénea.

::: figura 1
archivo: fig5_validacion_estados.png
titulo: Desempeño Predictivo en Entidades No Observadas Durante el Entrenamiento
nota: Cada punto representa un municipio. La línea diagonal del panel izquierdo indica predicción perfecta y el área del punto corresponde a la población de 15 a 17 años. El panel derecho muestra que el coeficiente de determinación negativo en entidades homogéneas obedece a la baja varianza interna y no a una falla del modelo.
:::

### Focalización por Tasa y por Número Absoluto

::: tabla 2
titulo: Adolescentes Fuera de la Escuela Capturados Según el Criterio de Ordenamiento Municipal
nota: El decil superior por tasa reúne 247 municipios. La selección aleatoria captura el 10% por definición. El guión largo indica que la columna no aplica para ese criterio de ordenamiento.
ancho: 7.0cm
| Criterio de ordenamiento | Inasistencia media del decil superior (%) | Adolescentes fuera capturados (%) |
|---|---|---|
| Tasa predicha | 50.28 | 9 |
| Número absoluto de adolescentes fuera | — | 59 |
| Selección aleatoria | 27.20 | 10 |
:::

El resultado más contraintuitivo del trabajo es que la focalización por tasa captura menos adolescentes fuera de la escuela que una selección aleatoria. Los municipios de tasa más elevada son de población reducida: el decil superior por tasa reúne 247 municipios con 50.28% de inasistencia, pero concentra apenas el 9% del total nacional de adolescentes fuera de la escuela. El ordenamiento por número absoluto señala, en cambio, municipios urbanos —León con 33,474 adolescentes fuera de la escuela, Tijuana con 21,339 y Juárez con 21,146— y 246 municipios bastan para cubrir el 58.6% del total.

Ambos criterios son legítimos y responden a objetivos distintos: la equidad territorial frente a la magnitud agregada. Lo que no resulta admisible es dejar la elección implícita.

::: figura 2
archivo: fig6_focalizacion.png
titulo: Adolescentes Fuera de la Escuela Capturados Según el Criterio de Ordenamiento Municipal
nota: La diagonal corresponde a una selección aleatoria. La curva correspondiente a la tasa predicha queda por debajo de la diagonal, mientras que la del número absoluto queda muy por encima.
:::

### Condiciones Estructurales Asociadas a la Inasistencia

Los predictores de mayor peso fueron la pobreza extrema, el índice de rezago social, la proporción de población de 15 años y más sin escolaridad, la distancia al bachillerato y el número de personas por hogar. La proporción de población hablante de lengua indígena presentó asociación negativa una vez controladas las condiciones materiales, resultado coherente con el obtenido en el análisis por localidad para Guerrero, donde esa variable perdió toda significancia estadística.

Estos coeficientes describen asociaciones dentro de un modelo predictivo y no autorizan lectura causal. La asociación positiva entre disponibilidad de automóvil e inasistencia ilustra el punto: capta ruralidad y dispersión del poblamiento, no un efecto del vehículo sobre la escolarización.

::: figura 3
archivo: fig7_que_pesa.png
titulo: Asociación de Cada Condición Estructural con la Inasistencia Escolar
nota: Coeficientes expresados en puntos porcentuales por desviación estándar de la variable predictora. Los coeficientes describen asociaciones dentro de un modelo predictivo y no autorizan lectura causal.
:::

### Efecto Causal de la Distancia al Bachillerato

En el contraste entre cohortes para Guerrero, cada kilómetro adicional de distancia al bachillerato respecto de la secundaria se asoció con una reducción de 1.70 puntos porcentuales en la asistencia (*SE* = 0.14; IC 95% [−1.97, −1.42]; *n* = 4,519; *p* < .001). Una especificación independiente en niveles, con efectos fijos de municipio y catorce covariables, arrojó un coeficiente de −1.686, prácticamente idéntico pese a proceder de una estrategia de identificación distinta.

::: tabla 3
titulo: Prueba de Falsación Mediante Contraste Entre Cohortes de Edad Dentro de la Misma Localidad (Guerrero)
nota: Coeficientes expresados en puntos porcentuales por kilómetro de distancia diferencial. Cada ecuación incluye simultáneamente ambas distancias. La asimetría del patrón confirma que cada distancia afecta únicamente a la cohorte del nivel educativo correspondiente.
ancho: 6.6cm
| Variable dependiente | Distancia del nivel correspondiente | Distancia del otro nivel |
|---|---|---|
| Brecha 15-17 frente a 12-14 | −1.70 (*p* < .001) | −0.28 (*p* = .286) |
| Brecha 12-14 frente a 6-11 | −2.99 (*p* < .001) | −0.20 (*p* = .025) |
:::

Una explicación basada en el aislamiento general de las localidades remotas no genera ese patrón, puesto que cualquier medida de lejanía debería pesar de manera semejante en ambas ecuaciones.

El cierre de todos los diferenciales de distancia en Guerrero habría elevado la asistencia de 70.79% a 72.44%, esto es, 1.66 puntos porcentuales equivalentes a unos 3,347 adolescentes. El efecto por kilómetro es considerable, pero la exposición de la población a distancias elevadas es baja porque la política de expansión territorial ya cerró la mayor parte de esa brecha.

### Restricción Estructural Frente a Margen de Política

La diferencia entre la inasistencia observada y la predicha por las condiciones estructurales distingue dos situaciones cualitativamente distintas. Un municipio pobre y aislado que registra la inasistencia correspondiente a sus condiciones enfrenta una restricción material; uno que se desempeña muy por debajo de sus pares enfrenta algo adicional, sobre lo cual la política puede actuar sin esperar a transformar la geografía.

El análisis de esas diferencias se restringió a los 1,946 municipios con al menos 200 adolescentes de 15 a 17 años. Los 523 restantes, que concentran el 0.8% de la población de esa edad, presentan tasas en las que el cambio de condición de una sola persona desplaza el indicador varios puntos, de modo que su inclusión convertía el ordenamiento en una clasificación de varianza muestral.

Entre los municipios que se desempeñaron peor de lo predicho destacaron Chamula, con 80.2% observado frente a 57.4% predicho, y Zinacantán, con 84.2% frente a 62.5%, ambos en Chiapas, así como Riva Palacio en Chihuahua, con 80.1% frente a 46.4%.

En el extremo opuesto, los dos casos positivos más marcados del país se localizaron en la región de La Montaña de Guerrero: Malinaltepec, con 19.7% de inasistencia frente a 51.4% predicho, e Iliatenco, con 12.9% frente a 40.1%. Ambos municipios registran más del 83% de población hablante de lengua indígena y rezago social elevado, condiciones que anticipan el resultado contrario.

La disponibilidad de planteles no explica el desempeño de estos municipios. Malinaltepec cuenta con 5.26 planteles por cada mil adolescentes, pero Iliatenco solo con 2.99, mientras que Xalpatláhuac, con 6.74 planteles por cada mil adolescentes, registra 52% de inasistencia. El modelo identifica la anomalía; su explicación requiere trabajo de campo que estas fuentes no permiten.

::: figura 4
archivo: fig8_brecha.png
titulo: Inasistencia Observada Frente a la Predicha por las Condiciones Estructurales
nota: Municipios con 200 o más adolescentes de 15 a 17 años. Los puntos situados por debajo de la diagonal corresponden a municipios con menor inasistencia que la predicha por sus condiciones; los situados por encima, a municipios con mayor inasistencia que la predicha.
:::

## Discusión

### El Patrón en el Contexto de la Literatura Internacional

El hallazgo sobre la distancia —un coeficiente por kilómetro elevado junto con un efecto agregado modesto— coincide con lo que Filmer (2007) reportó para 21 países de ingreso bajo, donde la distancia y la matrícula se relacionan de manera estadísticamente significativa pero con magnitudes pequeñas, y con lo que Rodriguez-Segura y Kim (2021) encontraron en Guatemala, donde la mayoría de la población reside a menos de tres kilómetros de una primaria y la barrera persiste únicamente en bolsas concentradas. El resultado mexicano no constituye por tanto una anomalía local sino la confirmación de un patrón documentado, obtenida mediante una estrategia de identificación más exigente.

El contraste con Burde y Linden (2013), cuyo experimento aleatorizado en aldeas afganas sin oferta previa elevó la matrícula 35 puntos porcentuales entre los niños y 52 entre las niñas, delimita el alcance del hallazgo: donde la oferta educativa es prácticamente inexistente, el efecto de la proximidad es de otro orden de magnitud; donde ya es densa, como en la mayor parte del territorio mexicano, resulta marginal. La política de expansión territorial enfrenta rendimientos decrecientes y México se ubica en el tramo plano de esa curva.

Kondylis y Manacorda (2012) encontraron en Tanzania rural que la cercanía escolar eleva la asistencia sin reducir significativamente el trabajo infantil, lo que resulta pertinente dado que en el modelo nacional la participación económica local aparece asociada a la inasistencia.

### Implicaciones para la Focalización

El resultado de que ordenar por tasa capture menos adolescentes que una selección aleatoria no invalida ese criterio, pero obliga a explicitarlo. Un programa que busque reducir el número total de adolescentes fuera de la escuela debe dirigirse a las ciudades; uno que busque cerrar brechas territoriales debe dirigirse a los municipios rurales pequeños. Se trata de objetivos distintos y la evidencia no decide entre ellos: solamente hace visible la disyuntiva.

### La Desventaja Indígena y las Condiciones Materiales

La asociación negativa de la condición de hablante de lengua indígena al controlar por condiciones materiales, replicada en los dos niveles de análisis, sugiere focalizar por marginación y accesibilidad antes que por adscripción étnica. El resultado dialoga con el contexto nacional, en el que solo el 9.7% de la población indígena completó la educación media superior frente al 19.6% del total: la brecha existe, pero este análisis la atribuye a condiciones materiales y no a la pertenencia étnica en sí misma.

### Lo que el Modelo No Puede Hacer

Este trabajo produce analítica descriptiva, diagnóstica y predictiva; no produce analítica prescriptiva. Identificar dónde se concentra el rezago no equivale a saber qué intervención lo reduciría ni a qué costo. De las variables incorporadas al modelo, únicamente la distancia cuenta con estimación causal, y su margen agregado resultó reducido.

La unidad de análisis impone un segundo límite. El modelo opera sobre municipios, y un sistema de alerta temprana que active intervenciones individuales requiere datos de estudiantes y no agregados territoriales.

De Vries y Grijalva Martínez (2021) encontraron, mediante encuestas directas a desertores en Oaxaca, que la razón más mencionada para abandonar fue la vida social con amistades o pareja, por encima de las razones económicas. El presente trabajo identifica condiciones estructurales y no observa las motivaciones individuales de quienes tuvieron la escuela cerca y aun así no asistieron. Ambos niveles de explicación son complementarios y ninguno sustituye al otro.

### Limitaciones

1. El estudio se basa en un corte transversal único correspondiente al Censo 2020, por lo que el diseño no explota variación temporal.
2. La distancia se calculó en línea recta y los planteles se ubicaron en el centroide de su localidad; ambas decisiones sesgan las estimaciones hacia cero.
3. La asistencia de 15 a 17 años incluye a quienes permanecen en secundaria por rezago, sin que las fuentes censales permitan separarlos.
4. El coeficiente de determinación calculado dentro de entidades homogéneas no constituye una medida informativa, según se documentó en la sección de resultados.
5. La identificación causal del efecto de la distancia se realizó únicamente para el estado de Guerrero, por lo que su generalización al resto del país queda pendiente de verificación.

### Recomendaciones para la Política Pública

De los resultados se desprenden cuatro recomendaciones concretas. La primera consiste en revisar la regla de focalización de los programas federales y estatales dirigidos a la educación media superior: cuando el objetivo declarado sea reducir el número agregado de adolescentes fuera de la escuela, el ordenamiento de los municipios debe realizarse por número absoluto y no por tasa, dado que este último criterio captura menos población objetivo que una selección aleatoria.

La segunda recomendación consiste en sustituir el Formato 911 como fuente de los indicadores municipales de deserción escolar por la tasa de inasistencia censal medida por lugar de residencia. El registro administrativo conserva su valor para caracterizar la oferta educativa y la matrícula por plantel, pero no para comparar territorios, dado el sesgo de atribución documentado.

La tercera recomendación se refiere a las intervenciones de acceso geográfico. Dado el rendimiento decreciente que muestran los datos, la construcción de nuevos planteles debe concentrarse en las bolsas donde persiste una distancia residual elevada, identificables mediante el procedimiento descrito, y no distribuirse de manera uniforme sobre el territorio.

La cuarta recomendación es de investigación aplicada con fines de política: los casos de Malinaltepec e Iliatenco, que presentan una inasistencia más de veinticinco puntos porcentuales inferior a la que predicen sus condiciones materiales, merecen estudio cualitativo orientado a identificar mecanismos de retención escolar potencialmente replicables en otros contextos de alta marginación.

## Conclusiones

Se construyó un modelo de identificación de municipios con rezago en el acceso a la educación media superior que conserva su capacidad predictiva en entidades federativas no observadas durante el entrenamiento, con un *R*² de 0.627 frente a 0.112 de la mejor línea base disponible. El método emplea exclusivamente datos abiertos y resulta aplicable a cualquier entidad del país.

La elección del criterio de focalización modifica por completo la lista de municipios prioritarios: ordenar por tasa captura el 9% de los adolescentes fuera de la escuela, mientras que ordenar por número absoluto captura el 59%. Esa decisión es de política pública y no técnica, y debe explicitarse en el diseño de cualquier programa.

La distancia al plantel tiene un efecto causal identificado de 1.70 puntos porcentuales por kilómetro, replicado por dos estrategias independientes y sostenido ante una prueba de falsación simétrica, pero su margen agregado es reducido porque la política ya cerró la mayor parte de esa brecha.

El trabajo documenta además que la tasa de deserción municipal derivada del Formato 911 no resulta apta para el análisis territorial en contextos de alta movilidad estudiantil, y ofrece un procedimiento de diagnóstico basado en el contraste entre la cobertura medida por plantel y la asistencia medida por residencia.

El procedimiento descrito constituye una herramienta de diagnóstico territorial que cualquier entidad federativa puede replicar con datos abiertos, sin requerir infraestructura estadística adicional.

### Futuras Líneas de Investigación

1. Calibrar la distancia geodésica con el tiempo de traslado declarado en el Cuestionario Ampliado del Censo 2020, lo que permitiría cuantificar cuánto subestima la línea recta el traslado real en terreno montañoso. La restricción de esta vía es que el Cuestionario Ampliado constituye una muestra probabilística, representativa a escala municipal pero no de localidad.
2. Explicar mediante trabajo cualitativo los casos de Malinaltepec e Iliatenco, cuyo desempeño supera en más de veinticinco puntos porcentuales al que predicen sus condiciones estructurales.
3. Descender al nivel del estudiante con datos individuales de trayectoria escolar, lo que permitiría transformar la identificación territorial en sistemas de alerta temprana con intervenciones accionables.
4. Replicar el análisis con el Censo de Población y Vivienda 2030 para convertir el corte transversal en un panel y estimar el efecto de las políticas aplicadas en el periodo intercensal.

## Referencias

Arellano-Esparza, C. A., y Ortiz-Espinoza, Á. (2022). Educación media superior en México: Abandono escolar y políticas públicas durante la covid-19. *Íconos. Revista de Ciencias Sociales*, (74), 33-52. https://doi.org/10.17141/iconos.74.2022.5292

Burde, D., y Linden, L. L. (2013). Bringing education to Afghan girls: A randomized controlled trial of village-based schools. *American Economic Journal: Applied Economics*, *5*(3), 27-40. https://doi.org/10.1257/app.5.3.27

Chávez Maciel, F. J., y Murguía Ángeles, M. T. (2010). La educación media superior a distancia en México y sus efectos para la equidad educativa. *Apertura. Revista de Innovación Educativa*, (Extra 1), 18-31.

Consejo Nacional de Evaluación de la Política de Desarrollo Social. (2021). *Índice de Rezago Social 2020 a nivel nacional, estatal, municipal y por AGEB*. https://www.coneval.org.mx/Medicion/IRS/Paginas/Indice_Rezago_Social_2020.aspx

De la Cruz Orozco, I. (2016). Beneficios esperados de la educación media superior en comunidades rurales. *Sinéctica*, (46), 1-19.

De Vries, W., y Grijalva Martínez, O. (2021). ¿Dejar la escuela o la vida social? El abandono en la educación media superior en Oaxaca. *Revista de la Educación Superior*, *50*(197), 59-80. https://doi.org/10.36857/resu.2021.197.1579

Filmer, D. (2007). If you build it, will they come? School availability and school enrolment in 21 poor countries. *The Journal of Development Studies*, *43*(5), 901-928. https://doi.org/10.1080/00220380701384588

Hashim, S. A., Kelley-Kemple, T., y Laski, M. E. (2023). *An improved method for estimating school-level characteristics from census data* (EdWorkingPaper núm. 23-804). Annenberg Institute at Brown University. https://doi.org/10.26300/chqx-av23

Instituto Nacional de Estadística y Geografía. (2021). *Censo de Población y Vivienda 2020. Principales resultados por localidad* [Conjunto de datos]. https://www.inegi.org.mx/programas/ccpv/2020/

Kondylis, F., y Manacorda, M. (2012). School proximity and child labor: Evidence from rural Tanzania. *Journal of Human Resources*, *47*(1), 32-63. https://doi.org/10.3368/jhr.47.1.32

Miranda López, F. (2018). Abandono escolar en educación media superior: Conocimiento y aportaciones de política pública. *Sinéctica*, (51), 1-22. https://doi.org/10.31391/S2007-7033(2018)0051-010

Rodriguez-Segura, D., y Kim, B. H. (2021). The last mile in school access: Mapping education deserts in developing countries. *Development Engineering*, *6*, 100064. https://doi.org/10.1016/j.deveng.2021.100064

Secretaría de Educación Pública. (2024a). *Principales cifras del Sistema Educativo Nacional 2023-2024*. Dirección General de Planeación, Programación y Estadística Educativa. https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/principales_cifras/principales_cifras_2023_2024_bolsillo.pdf

Secretaría de Educación Pública. (2024b). *Registro de alumnado, personal docente y escuelas de educación básica y media superior (Formato 911)* [Conjunto de datos]. https://www.datos.gob.mx/dataset/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911

Solís, P. (2018). La transición de la secundaria a la educación media superior en México: El difícil camino a la cobertura universal. *Perfiles Educativos*, *40*(159), 66-84.

Subsecretaría de Educación Media Superior. (2024). *Documento base para el servicio educativo de Telebachillerato Comunitario*. Dirección General del Bachillerato. https://dgb.sep.gob.mx/storage/recursos/2024/01/OJmP75xHCN-Documento-Base-para-el-Servicio-Educativo-de-Telebachillerato-Comunitario-2024.pdf
