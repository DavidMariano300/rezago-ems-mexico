# Resultados

Documento de trabajo para la redacción del artículo. Cada cifra indica el script
que la produce, para que se pueda regenerar y verificar.

---

## 1. El giro del proyecto

El briefing planteaba explicar la **tasa de deserción municipal** calculada con
el Formato 911. Ese camino se agotó, con evidencia:

| Especificación | R² | Predictores significativos |
| --- | --- | --- |
| Corte municipal sobre abandono F911 (n=81, ponderado) | 0.089 (aj. **0.002**) | ninguno |
| Panel con efectos fijos de municipio y ciclo (n=405) | R² within **0.017** | tamaño de grupo (p=0.025) |

La variable dependiente está dominada por ruido de medición. Dos causas
identificadas y cuantificadas:

- **Ruido por tamaño.** Los municipios con menos de 300 alumnos tienen
  desviación estándar del abandono de 6.78 puntos entre ciclos, contra 1.43 en
  los de más de 5,000. Sin ponderar, `alumnos_por_docente` correlaciona +0.029
  con el abandono; ponderado por matrícula, +0.251.
- **Sesgo de movilidad intermunicipal.** El F911 registra planteles, no alumnos.
  Índice de importación = cobertura F911 / asistencia censal: **39 municipios
  emisores, 36 equilibrados, 6 importadores**. Los emisores registran 14.29% de
  abandono contra 11.78% de los equilibrados, sin que eso signifique más
  deserción real. Cochoapa el Grande tiene índice 0.40: seis de cada diez de sus
  adolescentes que estudian lo hacen fuera del municipio.

El resultado nulo se conserva como sección del artículo y como advertencia
metodológica, no se esconde.

---

### Validación contra la cifra oficial

Aunque el abandono del F911 no sirva como variable dependiente municipal, el
cálculo agregado sí es correcto, y eso se comprobó:

| | Abandono en media superior, Guerrero, ciclo 2022-2023 |
| --- | --- |
| SEP, *Principales cifras 2023-2024*, p. 34 | **10.80 %** |
| Cálculo propio desde el Formato 911 abierto | **10.79 %** |
| Diferencia | 0.01 puntos |

La coincidencia valida la cadena completa: la corrección del ciclo al que
pertenece `egresados`, el uso de `nvo_ing_01` como nuevo ingreso al nivel y el
filtro a modalidad escolarizada. **Sin la corrección de `egresados` el resultado
habría sido 11.05% (error de 0.25 puntos).**

El resultado nulo de la sección anterior es entonces un hallazgo sobre la
*variación municipal*, no un error de cálculo.

---

## 2. El diseño que sí funciona

**Unidad:** localidad (6,769 en Guerrero). **Fuente de la variable dependiente:**
Censo 2020 (asistencia por residencia). **Del Formato 911 solo se usan las
UBICACIONES de planteles**, que son dato administrativo confiable — el resultado
principal no depende de las tasas problemáticas del F911.

### Especificación

```
(asist_15a17 − asist_12a14)_loc = β·(dist_bach − dist_sec)_loc
                                  + EF_municipio + log(población) + controles + ε
```

Ponderado por población de las dos cohortes; errores agrupados por municipio.

La diferencia entre cohortes **dentro de la misma localidad** cancela todo lo que
afecta igual a las dos edades: pobreza del hogar, lengua materna, aislamiento per
se, valor que la comunidad da a la escuela, calidad del camino.

### La asimetría que lo hace posible (fig. 1)

| Nivel | Localidades con plantel | Distancia mediana |
| --- | --- | --- |
| Primaria | 3,239 | 0.52 km |
| Secundaria | 1,721 | 1.72 km |
| Bachillerato | **590** | **3.78 km** |

### Resultado principal (fig. 2)

**β = −1.70 puntos porcentuales de asistencia por kilómetro** (EE 0.14,
agrupado; IC 95% [−1.97, −1.42]; p < 0.0001; n = 4,519 localidades).

Robustez:
- Solo efectos fijos, sin controles: −2.21
- Restringido a localidades con secundaria a ≤ 2 km: −2.39
- Supresión por confidencialidad: las localidades usables cubren **99.3%** de la
  población de las cohortes.

### La identificación (fig. 3)

Las dos distancias diferenciales compiten en la misma ecuación:

| Variable dependiente | Distancia del nivel que toca | Distancia del otro nivel |
| --- | --- | --- |
| Brecha 15-17 vs 12-14 | **−1.70** (p<0.0001) | −0.28 (p=0.286) |
| Brecha 12-14 vs 6-11 | **−2.99** (p<0.0001) | −0.20 (p=0.025) |

El patrón es simétrico y es lo que la explicación rival no puede producir: si el
efecto fuera del aislamiento general deprimiendo la asistencia de los mayores,
las dos distancias cargarían parecido en las dos ecuaciones.

> Nota de honestidad: el primer intento de falsación (regresar la brecha 12-14 vs
> 6-11 sobre la distancia secundaria − primaria y esperar cero) **falló**, con
> coeficiente de −3.35. No era un placebo válido: sí hay variación real de
> distancia en ese margen. La carrera de caballos es la prueba que corresponde.

---

## 3. Magnitud: el efecto por km es grande, la exposición es baja

| | |
| --- | --- |
| Asistencia 15-17 observada (ponderada) | 70.79% |
| Contrafactual con `dist_bach = dist_sec` en toda localidad | 72.44% |
| **Ganancia** | **1.66 pp (~3,347 adolescentes)** |

La mediana ponderada del diferencial de distancia es **0.00 km**: el adolescente
mediano de Guerrero ya vive donde hay bachillerato. La distancia explica **1.7 de
los 29 puntos** que le faltan al estado. El resto es otra cosa, y no la hemos
identificado.

**Pero está concentrada.** Diez municipios acumulan 40% de la pérdida atribuible
a distancia: Coyuca de Catalán pierde 7.3 pp, La Unión 7.7 pp, Tlacoachistlahuaca
5.6 pp. La recomendación de política es focalizada, no estatal.

---

## 4. Evaluación de subsistemas (fig. 4)

Recomputando la distancia de cada localidad excluyendo un subsistema a la vez:

| Subsistema | Planteles | % matrícula | Aporte al acceso |
| --- | --- | --- | --- |
| **Telebachillerato Comunitario** | 315 (37%) | 9.4% | **1.18 km** |
| Colegio de Bachilleres | 85 | 16.2% | 0.46 km |
| Media Superior a Distancia (EMSAD) | 90 | 5.7% | 0.41 km |
| Preparatorias UAGro | 130 | 40.5% | 0.18 km |
| CBTIS | 23 | 12.6% | **0.00 km** |
| CONALEP | 16 | 5.1% | **0.00 km** |

El TBC sostiene ~2.00 puntos de asistencia (~4,054 adolescentes): **más que todo
el diferencial de distancia que queda abierto**. Medido por matrícula parece
marginal; medido por acceso es el subsistema decisivo del estado.

CBTIS y CONALEP aportan cero al acceso: están donde ya hay otras opciones. No es
una crítica a su calidad, es que su función no es la cobertura territorial.

---

## 4-bis. De qué está hecha la brecha restante

`src/09_brecha_restante.py`

### El embudo

| | |
| --- | --- |
| Asistencia 12-14 (edad de secundaria) | 89.17% |
| Asistencia 15-17 (edad de bachillerato) | 70.79% |
| **Brecha total** | **29.21 pp** |
| ├─ ya estaban fuera a los 12-14 | 10.83 pp (**37.1%**) |
| └─ salieron en la transición a bachillerato | 18.38 pp (**62.9%**) |

**Casi dos tercios de la brecha se generan en la transición a bachillerato**, no
aguas arriba. El foco del artículo en media superior está justificado por los
datos, no por conveniencia.

(Supuesto contable: la cohorte de 12-14 de hoy se parece a la que fue la de
15-17 hace tres años. No es causal.)

### Qué explica la variación entre localidades del mismo municipio

Bloques agregados en orden, con efectos fijos de municipio desde el inicio. La
distancia entra **al final** a propósito: así no se le regala la varianza que
comparte con el resto, y su aporte es un piso.

| Bloque | R² | ΔR² |
| --- | --- | --- |
| Solo efectos fijos de municipio | 0.369 | +0.369 |
| + embudo previo (asistencia 12-14) | 0.593 | **+0.224** |
| + tamaño y altitud de la localidad | 0.651 | +0.058 |
| + contexto socioeconómico | 0.686 | +0.035 |
| + composición étnica | 0.686 | +0.000 |
| + **distancia al bachillerato** | **0.712** | **+0.026** |

### Modelo completo (n=4,519, R²=0.712)

| Variable | β | t | p |
| --- | --- | --- | --- |
| asistencia 12-14 | +0.625 | +21.00 | <0.0001 |
| **distancia al bachillerato** | **−1.686** | **−9.59** | **<0.0001** |
| % 15+ sin escolaridad | −0.319 | −5.90 | <0.0001 |
| personas por hogar | −3.023 | −3.98 | 0.0001 |
| % población económicamente activa | −0.072 | −3.67 | 0.0002 |
| % viviendas con internet | +0.081 | +2.75 | 0.006 |
| % habla lengua indígena | −0.001 | −0.06 | 0.954 |

Tres cosas que salen de aquí:

1. **Convergencia del coeficiente de distancia.** Esta especificación
   (niveles, con efectos fijos y 14 covariables) da **−1.686**; el diseño de
   contraste entre cohortes daba **−1.696**. Dos estrategias de identificación
   distintas llegan al mismo número. Es la validación cruzada más fuerte del
   trabajo.
2. **La lengua indígena deja de importar al controlar.** β = −0.001, p = 0.954.
   La desventaja de las localidades hablantes de lengua indígena está
   íntegramente mediada por distancia, escolaridad adulta y composición del
   hogar; no hay efecto étnico directo. Es un resultado con implicación de
   política: focalizar por marginación y distancia, no por etnia.
3. **El costo de oportunidad aparece.** Mayor participación económica en la
   localidad se asocia a menor asistencia (β = −0.072, p = 0.0002).

### El mismo ejercicio sobre 12-14 (n=4,519, R²=0.441)

| Variable | β | t |
| --- | --- | --- |
| distancia a la secundaria | −3.153 | −9.58 |
| % 15+ sin escolaridad | −0.411 | −9.22 |
| personas por hogar | −3.151 | −4.48 |

El mecanismo de la distancia opera igual aguas arriba.

---

## 5. Posición en la literatura

Lo ya publicado, que el artículo debe citar y no puede reclamar como propio:

- La **SEP ya publica mapas coropléticos municipales de asistencia de 15 a 17
  años** con el Censo 2020 en su *Atlas de los servicios educativos*. La
  descripción municipal no es aporte.
- Para **CDMX** está documentado que 12% de quienes cursan básica se desplazan a
  otra demarcación, contra **43%** en media superior. Corrobora el sesgo de
  movilidad en otro contexto.
- El **EMSAD** opera con criterio de localidades de hasta 5,000 habitantes sin
  otra oferta en **30 km**; el **Telebachillerato Comunitario** (desde 2014) en
  localidades de menos de 2,500 habitantes sin bachillerato en **5 km**.
- Existe trabajo econométrico previo sobre deserción en municipios de Guerrero
  con regresión lineal, y estudios de caso en Iguala.
- Que la distancia a la escuela afecta la asistencia es un resultado establecido
  en economía del desarrollo. **El aporte aquí no es el signo, es el diseño de
  identificación y la cuantificación para Guerrero.**

### Tres corroboraciones independientes

Los resultados propios coinciden con cifras publicadas por vías que no comparten
método ni fuente, lo que es el mejor argumento de validez disponible:

| Resultado propio | Referencia externa | Coincidencia |
| --- | --- | --- |
| Abandono EMS Guerrero 2022-2023: **10.79%** | SEP, *Principales cifras*: **10.80%** | 0.01 pp |
| Abandono 1º → 2º: **21.6%** | Literatura nacional: *"uno de cada cuatro nuevos estudiantes no continúa"* (~25%) | mismo orden |
| Efecto por km grande, agregado pequeño (1.66 pp) | Estudio DHS de 21 países pobres: la distancia se asocia significativamente a la matrícula, pero *"simular grandes reducciones de distancia produce solo pequeños aumentos en la participación escolar"* | patrón idéntico |

La tercera es la más importante para encuadrar el artículo: **el patrón
"coeficiente fuerte, exposición baja" no es una anomalía de Guerrero, es el
hallazgo típico de esta literatura.** Permite escribir el resultado sin
disculparse por la magnitud y sin exagerarla.

### Referencias clave a incorporar

- *La transición de la secundaria a la educación media superior en México: el
  difícil camino a la cobertura universal* (Perfiles Educativos, 2018). Es la
  referencia obligada del tema, y reporta el **mismo problema de datos** que
  encontramos: la tasa de absorción oficial de 2014-2015 dio 100.7%, lo que es
  lógicamente imposible, porque el F911 no permite distinguir si quien ingresa a
  EMS viene de la generación que acaba de egresar de secundaria o de generaciones
  rezagadas.
- Burde y Linden, experimento de construcción de escuelas en Afganistán: la
  cercanía elevó la matrícula 47 pp y cerró casi por completo la brecha de
  género. Es la cota superior del efecto en contextos de oferta muy escasa.
- Literatura de *education deserts* para el encuadre territorial.
- Manacorda y coautores sobre distancia, asistencia y trabajo infantil: pertinente
  porque en nuestro modelo la participación económica local sale significativa
  (β = −0.072).

### Consecuencia para el argumento de endogeneidad

La objeción natural es que las escuelas se construyen donde hay demanda, de modo
que la cercanía estaría correlacionada con demanda latente y β inflado. Pero las
reglas de asignación del TBC y del EMSAD son **explícitamente la distancia**: la
política redujo la distancia justamente donde era grande. La variación que queda
es la que la política no alcanzó a cerrar, y el sesgo va hacia cero.

**β = −1.70 pp/km es un piso, no un techo.** La distancia geodésica en línea
recta refuerza esa lectura: en la Sierra subestima el traslado real.

---

## 6. Limitaciones que deben declararse

1. **Corte único.** Censo 2020. No hay panel de localidades; el diseño es
   transversal con contraste entre cohortes.
2. **Colocación endógena de escuelas.** Atenuada por el argumento de la sección
   anterior, no eliminada.
3. **Distancia en línea recta** y planteles ubicados en el centroide de su
   localidad. Sesga β hacia cero.
4. **La asistencia de 15-17 mezcla** bachillerato con quienes siguen en
   secundaria por rezago. No es separable con datos censales.
5. **Supresión por confidencialidad** en localidades muy pequeñas (0.7% de la
   población de las cohortes).
6. **El 27% restante** de la brecha de asistencia queda sin explicar.

---

## 7. Cómo reproducir

```bash
.venv/bin/python src/00_descargar.py            # 25 archivos, manifiesto con SHA256
.venv/bin/python src/01_puente_municipios.py    # tabla puente, valida los cruces
.venv/bin/python src/02_abandono.py             # panel F911 (resultado nulo)
.venv/bin/python src/03_cruce.py                # contexto CONEVAL + censo
.venv/bin/python src/04_distancia.py            # distancia municipal
.venv/bin/python src/05_asistencia_censal.py    # VD alterna e índice de importación
.venv/bin/python src/06_localidades.py          # DISEÑO PRINCIPAL
.venv/bin/python src/07_subsistemas.py          # evaluación de subsistemas
.venv/bin/python src/08_figuras.py              # figuras 1-4, PDF y PNG 300 dpi
.venv/bin/python src/09_brecha_restante.py      # embudo y descomposición de varianza
```

Verificaciones auditables:

```bash
.venv/bin/python src/00_descargar.py --verificar          # integridad por SHA256
.venv/bin/python src/01_puente_municipios.py --derivar-mapeo  # municipios escindidos
.venv/bin/python src/02_abandono.py --verificar-egresados     # a qué ciclo pertenece
```

---

## 8. Argumento del artículo, en una página

1. Guerrero tiene 70.8% de asistencia entre los 15 y 17 años. Faltan 29 puntos.
2. Casi dos tercios de ese hueco (18.4 pp) se abren **en la transición** de
   secundaria a bachillerato, no antes.
3. La deserción medida con el Formato 911 a nivel municipal **no explica nada**
   (R² ajustado 0.002), y se demuestra por qué: ruido en municipios pequeños y
   sesgo de movilidad intermunicipal, este último cuantificado con el índice de
   importación. El cálculo agregado sí es correcto (coincide con la SEP en 0.01
   puntos); lo que falla es su variación municipal.
4. Con asistencia censal a nivel localidad y un contraste entre cohortes de edad
   dentro de la misma localidad, la distancia al bachillerato tiene un efecto
   identificado de **−1.70 pp por km**, replicado en −1.686 por una
   especificación independiente, y con una prueba de falsación simétrica que
   descarta el aislamiento general como explicación.
5. La lengua indígena **deja de tener efecto** al controlar por distancia,
   escolaridad adulta y composición del hogar: la desventaja está mediada, no es
   étnica.
6. El efecto por kilómetro es grande pero la exposición es baja: cerrar todas las
   distancias recuperaría 1.66 pp. Es el patrón típico de esta literatura, no una
   anomalía. **La política ya cerró la mayor parte**: el Telebachillerato
   Comunitario sostiene por sí solo ~2.00 pp, más de lo que queda abierto.
7. Lo que queda es focalizado: diez municipios concentran 40% de la pérdida
   atribuible a distancia.

---

## 9. Pendientes

- **Revisión sistemática de literatura.** La sección 5 recoge las referencias
  centrales y tres corroboraciones, pero no es todavía una revisión sistemática
  con criterios de búsqueda documentados.
- **Violencia municipal** como covariable que varía en el tiempo. Su valor bajó:
  el diseño ya no descansa en el panel municipal.
- **Mecanismo del embudo previo.** La asistencia de 12-14 es el predictor más
  fuerte (β = +0.625) y solo sabemos que la distancia a la secundaria y la
  escolaridad adulta la explican en parte (R² 0.441). Ahí queda trabajo.
- **Distancia por camino en vez de línea recta.** Con datos de la red vial se
  podría medir tiempo de traslado; en la Sierra la diferencia es grande y todos
  los coeficientes actuales son cotas inferiores.
