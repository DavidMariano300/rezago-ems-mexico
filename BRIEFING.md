# Alerta temprana de deserción escolar en Guerrero — briefing de inicio

> Este archivo es el punto de partida para el nuevo hilo de trabajo. Contiene todo el contexto necesario para retomar el proyecto sin tener que repetir la conversación previa.

## Quién y por qué

**Alumno:** Edgar David Mariano Ruiz
**Programa:** Maestría en Ingeniería para la Innovación y Desarrollo Tecnológico (MIIDT), área de Tecnologías de la Información y Comunicación — Facultad de Ingeniería, Universidad Autónoma de Guerrero
**Director de tesis:** Dr. Arnulfo Catalán Villegas
**Codirectora:** Dra. Mercedes Hernández de la Cruz

Este proyecto es independiente del tema de tesis (el asistente conversacional normativo de la UAGro), pero comparte dominio: ambos tocan datos institucionales de la universidad y del sistema educativo de Guerrero. Se eligió como propuesta 2 de un ranking de 8 ideas de proyecto de datos, ordenadas por potencial para una ponencia de posgrado en la UAGro y para publicar en una revista de acceso abierto sin costo.

## El problema

Guerrero registra una de las tasas de deserción escolar más altas del país. No existe un sistema de alerta temprana construido sobre datos abiertos que identifique, a nivel municipal, dónde es más probable que se concentre el abandono escolar.

## Pregunta de investigación

¿Qué variables de infraestructura escolar y contexto municipal predicen mejor la deserción escolar en Guerrero?

## Matriz de consistencia

| Elemento | Contenido |
| --- | --- |
| Objetivo general | Identificar los factores municipales que mejor predicen la tasa de deserción escolar en Guerrero |
| Hipótesis | Los municipios con mayor rezago en infraestructura escolar y mayor pobreza registran tasas de deserción significativamente más altas |
| Variable independiente | Infraestructura escolar (alumnos por docente, aulas disponibles) + pobreza municipal |
| Variable dependiente | Tasa de deserción escolar municipal |
| Indicadores | Alumnos por docente; % de pobreza municipal; tasa de abandono anual por municipio y nivel |
| Metodología | Regresión logística / modelo panel municipal |
| Nivel de análisis | Municipal, estado de Guerrero (comparable a nivel nacional) |

## Objetivo de entregables

- **Ponencia** en un foro de posgrado de la UAGro.
- **Artículo** dirigido a *RIDE — Revista Iberoamericana para la Investigación y el Desarrollo Educativo* (acceso abierto diamante, sin costo para autores, indexada en el Índice CONAHCYT y en SciELO).

## Fuentes de datos (links directos)

### 1. Variable dependiente — matrícula y deserción (SEP / Formato 911)

- Portal oficial: https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html
- Dataset completo (todas las descargas): https://www.datos.gob.mx/dataset/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911
- Descarga directa — educación básica, ciclo 2024-2025: https://www.datos.gob.mx/dataset/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/resource/da9459bd-c185-44e4-b054-6efc269ea609
- Descarga directa — educación media superior, ciclo 2023-2024: https://www.datos.gob.mx/dataset/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/resource/b3b82081-b4fe-4d3c-8c24-813c2c6f550f

**Nota importante:** el Formato 911 da matrícula, docentes y aulas por ciclo escolar — no da la tasa de deserción directamente. Hay que calcularla comparando la matrícula de un grado en el ciclo *N* contra la matrícula del grado siguiente en el ciclo *N+1*, por municipio.

### 2. Variables independientes — pobreza y rezago social (CONEVAL)

- Pobreza municipal 2010-2020, bases de datos y programas de cálculo: https://www.coneval.org.mx/Medicion/Paginas/Programas_BD_municipal_2010_2020.aspx
- Pobreza en Guerrero 2020 (específico del estado): https://www.coneval.org.mx/coordinacion/entidades/Guerrero/Paginas/Pobreza_2020.aspx
- Índice de Rezago Social 2020 (ya incluye indicadores educativos por municipio): https://www.coneval.org.mx/Medicion/IRS/Paginas/Indice_Rezago_Social_2020.aspx
- Rezago social, dataset abierto: https://www.datos.gob.mx/dataset/rezago_social

### 3. Marco demográfico (INEGI)

- Censo de Población y Vivienda 2020, resultados por municipio de Guerrero: https://www.inegi.org.mx/app/cpv/2020/resultadosrapidos/default.html?texto=Guerrero
- Portal de descarga de microdatos/bases: https://www.inegi.org.mx/app/descarga/

## El obstáculo técnico a resolver primero

Las tres fuentes usan su propia clave de municipio. Antes de cruzar nada, bajar el **catálogo de claves de entidades y municipios de INEGI** (disponible en el portal de descarga de INEGI) y usarlo como tabla puente. Nunca hacer el cruce por nombre de municipio — los acentos y mayúsculas entre fuentes son inconsistentes y rompen el join silenciosamente.

## Siguiente paso inmediato

1. Descargar los tres conjuntos de datos de los links de arriba a `datos/crudo/`.
2. Bajar el catálogo de claves municipales de INEGI y guardarlo como tabla puente.
3. Calcular la tasa de deserción municipal a partir de dos ciclos consecutivos del Formato 911.
4. Cruzar deserción + rezago social + pobreza municipal usando la clave INEGI.
5. Análisis exploratorio: distribución de deserción por municipio, correlación simple con rezago social.
6. Modelo: regresión logística como línea base, comparar contra un modelo de árboles con boosting si el desempeño lo justifica.
