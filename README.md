# Rezago en el acceso a la educación media superior en México

Modelo replicable para identificar los municipios con mayor rezago en el acceso
a la educación media superior, construido exclusivamente con datos abiertos y
validado en entidades federativas que no participaron en su entrenamiento.

Cubre los **2,469 municipios** y **189,432 localidades** del país.

---

## Resultado principal

Un modelo que emplea únicamente condiciones estructurales del territorio
—distancia a los planteles, pobreza, rezago social, dispersión del poblamiento,
mercado laboral y vivienda— alcanza un **R² de 0.627 fuera de muestra**
prediciendo municipios de estados que nunca observó durante el entrenamiento.

| Especificación | R² fuera de muestra | Error absoluto medio |
|---|---|---|
| Línea base: media nacional | 0.000 | 7.63 |
| Línea base: media de la propia entidad | 0.112 | 7.31 |
| Estructural, regresión de cresta | 0.526 | 5.27 |
| **Estructural, potenciación por gradiente** | **0.627** | **4.55** |
| Ampliada, con inasistencia de 12 a 14 años | 0.830 | 2.99 |

La validación aparta **estados completos** en cada pliegue. Una validación
cruzada aleatoria habría inflado el resultado, porque los municipios vecinos
comparten condiciones y el modelo puede memorizar regiones.

## Tres hallazgos que conviene destacar

**Focalizar por tasa captura menos que elegir al azar.** Ordenar los municipios
por tasa de inasistencia y seleccionar el decil superior alcanza al 9% de los
adolescentes fuera de la escuela, por debajo del 10% que daría una selección
aleatoria, porque los municipios de tasa más alta son de población reducida.
Ordenar por número absoluto captura el 59%. Son dos políticas distintas.

**La tasa de deserción municipal del Formato 911 no sirve para análisis
territorial.** Arroja R² ajustado de 0.002 en corte transversal y 0.017 en panel.
Dos causas documentadas: los municipios con menos de 300 estudiantes tienen una
desviación estándar de 6.78 puntos entre ciclos, y el registro atribuye cada
alumno al municipio de su escuela y no al de su residencia.

**La distancia al plantel tiene efecto causal pero margen agregado reducido.**
Cada kilómetro adicional reduce la asistencia en 1.70 puntos porcentuales, con
una prueba de falsación simétrica que descarta explicaciones alternativas. Pero
cerrar todas las distancias en Guerrero recuperaría solo 1.66 puntos, porque la
política ya cerró la mayor parte de esa brecha.

---

## Reproducir los resultados

```bash
uv venv && uv pip install -r requirements.txt
```

Los datos crudos (785 MB) no están versionados. Se descargan con:

```bash
.venv/bin/python src/00_descargar.py
```

El script verifica cada archivo contra el SHA-256 registrado en
`datos/crudo/MANIFIESTO.csv`, de modo que se obtiene exactamente el mismo
conjunto con el que se produjeron estos resultados. Los portales de datos
abiertos sustituyen archivos sin control de versiones, y por eso el manifiesto
es parte del repositorio.

Después, en orden:

```bash
for s in 01_puente_municipios 02_abandono 03_cruce 04_distancia \
         05_asistencia_censal 06_localidades 07_subsistemas 08_figuras \
         09_brecha_restante 11_alerta_temprana 12_nacional 13_modelo_riesgo \
         14_figuras_nacional 10_pdf; do
  .venv/bin/python "src/$s.py"
done
```

## Estructura

```
src/      pipeline numerado; cada script documenta en su encabezado qué
          decide, qué supone y qué limitación conserva
docs/     manuscrito en APA 7, revisión de literatura, resultados y el diseño
          del sistema de alerta temprana a nivel estudiante
datos/    limpio/ contiene las salidas analíticas; crudo/ solo el manifiesto
salidas/  PDF del manuscrito y figuras en PNG a 300 dpi
```

Archivos de interés inmediato:

- `datos/limpio/riesgo_municipal.csv` — los 2,469 municipios clasificados, con
  inasistencia observada, predicha, y la brecha entre ambas.
- `salidas/Articulo_APA7.pdf` — el manuscrito completo.
- `docs/ALERTA_TEMPRANA_UAGRO.md` — diseño de un sistema de alerta temprana a
  nivel estudiante, que es la unidad donde una alerta sí resulta accionable.

## Fuentes

Las tres son de acceso abierto y se citan en el manuscrito:

- **INEGI**, Censo de Población y Vivienda 2020, Principales Resultados por
  Localidad (ITER).
- **SEP**, Formato 911, ciclos 2019-2020 a 2024-2025.
- **CONEVAL**, Índice de Rezago Social 2020 y medición de pobreza municipal.

## Entorno

Python 3.12.3, NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1,
statsmodels 0.15.0. El PDF se compila con pdfLaTeX.

## Licencia

El código se publica bajo licencia MIT (ver `LICENSE`). Los datos pertenecen a
las instituciones que los publican y se rigen por sus propios términos; los
conjuntos de datos.gob.mx empleados aquí están bajo CC BY 4.0.

## Cita

Mariano Ruiz, E. D. (2026). *Identificación de municipios con rezago en el
acceso a la educación media superior: un modelo replicable con datos abiertos
para México* [Manuscrito no publicado]. Facultad de Ingeniería, Universidad
Autónoma de Guerrero.
