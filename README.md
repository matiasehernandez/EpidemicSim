# Modelo epidemiológico basado en agentes (SIRS)

Este proyecto implementa una simulación de la dinámica de una epidemia mediante un modelo basado en agentes desarrollado en Python con Pygame.

A diferencia de los modelos compartimentales clásicos (SIR o SIRS en formulación continua o discreta), este enfoque representa explícitamente a cada individuo, de modo que la dinámica global de la enfermedad emerge a partir de interacciones locales entre agentes.

![EpidemicSim.](images/sir_demo.gif)

## Autor
- Matías Ezequiel Hernández Rodríguez
- Email: matiasehernandez@gmail.com

## Descripción

El sistema simula dos poblaciones (ciudades) conectadas entre sí, en las cuales los individuos se desplazan de forma estocástica dentro de su entorno. Cada agente puede encontrarse en uno de los siguientes estados:

- Susceptible
- Infectado
- Recuperado

La transmisión de la enfermedad ocurre por contacto espacial entre individuos, mientras que la recuperación y posible reinfección permiten implementar una dinámica del tipo SIRS.

## Características principales

- Simulación de dos ciudades con movilidad interna y entre regiones.
- Modelo basado en agentes con dinámica individual.
- Contagio dependiente de la proximidad espacial.
- Evolución temporal de estados epidemiológicos.
- Parámetros configurables en tiempo real.
- Intervenciones mediante vacunación.
- Visualización simultánea de la simulación y de las curvas S, I y R.
- Exportación de resultados en formato de gráficos.

## Parámetros ajustables

El sistema permite modificar dinámicamente los siguientes parámetros:

- Nivel de distanciamiento entre individuos.
- Porcentaje de vacunación.
- Tamaño de la población.
- Velocidad de movimiento.
- Radio de contagio.
- Probabilidad de transmisión.
- Tiempo de recuperación.
- Tiempo de reinfección.
- Duración total de la simulación.

## Visualización

La aplicación incluye:

- Representación visual en tiempo real de la dinámica de la población.
- Gráficos de evolución temporal para cada ciudad.
- Comparación entre escenarios.
- Exportación de resultados en imágenes para análisis posterior.

## Objetivo

El objetivo del proyecto es estudiar cómo reglas locales simples pueden generar dinámicas complejas a nivel agregado, como la propagación de una enfermedad.

Este tipo de simulación resulta útil para:

* Introducción a modelos basados en agentes.
* Estudio cualitativo de dinámicas epidemiológicas.
* Enseñanza de modelos tipo SIR/SIRS.
* Exploración inicial de sistemas complejos en investigación.

## Tecnologías utilizadas

- Python
- Pygame
- NumPy
- Matplotlib

## Ejecución

```bash
python main.py
```

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.
