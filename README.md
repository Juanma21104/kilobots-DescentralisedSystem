# Localización descentralizada en enjambres masivos: un análisis de simulación con Mesa

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Mesa](https://img.shields.io/badge/Mesa-Agent--Based-orange)](https://mesa.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📜 Descripción general

Este repositorio contiene una **implementación en Python/Mesa** de un
algoritmo descentralizado para la formación de sistemas de coordenadas
globales en enjambres de robots. El proyecto replica y valida la
metodología propuesta por **Pluhacek et al. (2025)**, permitiendo que un
enjambre de robots minimalistas (kilobots) se auto-localice sin
necesidad de GPS o brújulas, basándose únicamente en la comunicación
local y estimación de distancias (range-only).

El simulador permite evaluar la **escalabilidad**, **robustez** y
**tolerancia a fallos** del algoritmo en diferentes escenarios de
estrés.

## 📂 Estructura del proyecto

El repositorio está organizado en el código fuente principal (raíz) y
una carpeta de pruebas (`Tests`) que contiene los resultados de los
experimentos de validación:

``` text
.
├── agent.py           # Lógica del agente Kilobot (máquina de estados y manejo de mensajes)
├── constant.py        # Parámetros de simulación (ruido, tamaño grid, estados)
├── model.py           # Clase modelo de Mesa (scheduler, grid, DataCollection)
├── routines.py        # Subrutinas para asignación de IDs, descubrimiento y triangulación
├── run_batch.py       # Script para ejecutar experimentos masivos y generar gráficas
├── server.py          # Servidor de visualización (GUI en navegador)
│
└── Tests/             # Resultados de los experimentos de validación
    ├── Ideal_parameters_tests/  # Pruebas de escalabilidad en condiciones ideales
    │   ├── results.csv
    │   ├── scalability_chart_messages.png
    │   ├── scalability_chart_precision.png
    │   └── scalability_chart_time.png
    │
    ├── IR_error_tests/          # Robustez ante ruido sensorial (Error IR variable)
    │   ├── results.csv
    │   ├── scalability_chart_messages.png
    │   ├── scalability_chart_precision.png
    │   └── scalability_chart_time.png
    │
    ├── Lost_messages_tests/     # Robustez ante pérdida de paquetes (Comunicación inestable)
    │   ├── results.csv
    │   ├── scalability_chart_messages.png
    │   ├── scalability_chart_precision.png
    │   └── scalability_chart_time.png
    │
    └── Robot_fails_tests/       # Resiliencia ante la muerte de agentes (fallo de hardware)
        ├── results.csv
        ├── scalability_chart_messages.png
        ├── scalability_chart_precision.png
        └── scalability_chart_time.png
```

## 🚀 Características clave

-   **Lógica descentralizada**: Los agentes operan de forma asíncrona
    usando solo información local.
-   **Escalabilidad comprobada**: Validación con enjambres de hasta 900
    agentes con tiempo de convergencia constante.
-   **Simulación de entornos reales**:
    -   Ruido gaussiano: error en la medición de distancia (IR).
    -   Pérdida de paquetes: simulación de fallos en la red inalámbrica.
    -   Mortalidad: probabilidad de fallo permanente de los agentes.
-   **Visualización en tiempo real**: Interfaz web para observar la
    formación de gradientes y coordenadas.

## 🛠️ Instalación y uso

### Clonar el repositorio

``` bash
git clone https://github.com/Juanma21104/kilobots-DescentralisedSystem.git
cd mesa-swarm-coordinates
```

### Instalar dependencias

Se requiere Python 3.8+, Mesa v2.1.4 y las siguientes librerías:

``` bash
pip install mesa==2.1.4 pandas numpy seaborn matplotlib
```

### Modo visualización (GUI)

Para ver a los robots formando la cuadrícula en tiempo real:

``` bash
python server.py
```

Abre tu navegador en http://127.0.0.1:8521.

### Modo experimentos (batch)

Para ejecutar las simulaciones masivas y regenerar los archivos de la
carpeta `Tests`:

``` bash
python run_batch.py
```

## 📊 Resumen de resultados

Los datos almacenados en la carpeta `Tests` demuestran que:

-   **Escalabilidad**: El tiempo de convergencia se mantiene estable
    (\~700 pasos) independientemente del tamaño del enjambre.
-   **Robustez**: El sistema tolera hasta un 75% de pérdida de mensajes
    y un 3% de ruido en sensores manteniendo una precisión \>90%.
-   **Punto crítico**: Una tasa de fallo de agentes superior al 0.5%
    provoca la fragmentación de la red en enjambres grandes.

## 📚 Referencias

Esta implementación se basa en el trabajo teórico de:

Pluhacek, M., Garnier, S., Reina, A.: *Decentralised construction of a
global coordinate system in a large swarm of minimalistic robots*. Swarm
Intelligence (2025).
