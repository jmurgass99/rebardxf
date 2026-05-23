# DXFStructuralJm — Generación Automática de Planos Estructurales

[![CI](https://github.com/jmurgass99/dxfstructuraljm/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/dxfstructuraljm/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-84.23%25-brightgreen?style=flat)](https://github.com/jmurgass99/dxfstructuraljm)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

## Objetivo
Librería Python para la generación automática de planos estructurales en formato DXF (AutoCAD), conectada directamente con los resultados de diseño de **FastSAP**, **FoundationDesignJm** y **SteelConnectionJm**. Cierra el "último kilómetro" del flujo de trabajo: **del cálculo al plano sin intervención manual**.

---

## ¿Qué va a hacer?

### 1. Planta de Cimentación
- Dibujo de zapatas aisladas, combinadas y corridas con cotas
- Distribución de refuerzo inferior (malla + refuerzo adicional)
- Tabla de zapatas (dimensiones, profundidad, refuerzo, f'c)
- Ejes de columnas con nomenclatura (A-1, B-2, etc.)
- Input directo desde `FoundationDesignJm` (resultados de `drained_bearing_capacity()`)

### 2. Detalle de Sección de Columna
- Sección transversal con barras longitudinales posicionadas exactamente
- Estribos con radio de doblado
- Cotas de recubrimiento, separación entre barras
- Tabla de cuantía (As, ρ, número de barras, diámetro)
- Input directo desde `FastSAP/rc_section.py` (`RCColumnSection`)

### 3. Detalle de Sección de Viga
- Sección en corte con refuerzo superior e inferior
- Elevación lateral con zonas de confinamiento marcadas
- Estribos con separación variable (zona crítica vs zona central)
- Input directo desde `FastSAP/rc_section.py` (`RCBeamSection`)

### 4. Detalle de Muro Estructural
- Sección con elementos de borde (boundary elements) resaltados
- Refuerzo distribuido horizontal y vertical
- Cotas y cuantías mínimas según EC8/ACI

### 5. Cuadro de Despiece de Acero
- Tabla automática con: marca, diámetro, longitud, cantidad, peso total
- Agrupación por elemento (columna, viga, zapata)
- Longitudes de traslape, ganchos y dobleces según código

### 6. Cajetines y Formato
- Templates A1, A3 con marco, cajetín y logo
- Escala automática según dimensiones del dibujo
- Layers organizados por tipo (concreto, acero, cotas, texto)

---

## Estructura de Módulos Planificada

```
dxfstructuraljm/
├── __init__.py
├── core.py                 # Primitivas DXF: líneas, arcos, cotas, textos, hatching
├── layers.py               # Definición de layers (CONCRETO, ACERO, COTAS, ESTRIBO, etc.)
├── templates.py            # Cajetines A1, A3 con marco y leyenda
├── foundation_plan.py      # Planta de cimentación desde FoundationDesignJm
├── column_section.py       # Detalle de columna desde FastSAP RCColumnSection
├── beam_section.py         # Detalle de viga: sección + elevación con estribos
├── wall_detail.py          # Muro con boundary elements
├── rebar_schedule.py       # Cuadro de despiece automático
├── rebar_shapes.py         # Formas de doblado estándar (ganchos, U, L, S)
├── scales.py               # Escalado automático al formato de papel
├── export.py               # Guardar .dxf con ezdxf
└── tests/
    ├── test_column.py
    ├── test_beam.py
    ├── test_foundation.py
    └── test_schedule.py
```

---

## Fuentes de Información

### Librería Base
| Recurso | Contenido |
|---------|-----------|
| **ezdxf** (ya descargado en `Nuevos/ezdxf-master`) | Librería Python madura para leer/escribir DXF. Soporte para AutoCAD 2018+, layers, blocks, dimensions, hatching, MTEXT. **Esta es la dependencia principal.** |
| **OSAFE** (ya descargado en `Nuevos/OSAFE-master`) | Referencia de cómo vincular modelos ETABS/SAFE con representación gráfica en FreeCAD. Patrón de cómo extraer geometría de CSI y dibujarla. |

### Estándares de Dibujo
| Fuente | Contenido |
|--------|-----------|
| **ACI SP-66** | Manual de práctica de detallado de concreto reforzado |
| **ACI Detailing Manual** | Formas estándar de doblado de barras (#1 a #14) |
| **ISO 3766** | Representación simplificada de armaduras en planos |
| **PCI Design Handbook** | Convenciones de representación gráfica |

### Integración con el Ecosistema Existente

| Proyecto | Qué aporta | Cómo conecta |
|----------|------------|---------------|
| **FastSAP** | `rc_section.py` → `RCColumnSection`, `RCBeamSection` con posiciones exactas de barras | `column_section.py` lee el objeto y dibuja el detalle |
| **FastSAP** | `to_json()` → exportar sección a JSON | Entrada alternativa: cargar JSON → generar DXF |
| **FoundationDesignJm** | `drained_bearing_capacity()` → B, L, d, qult | `foundation_plan.py` dimensiona la zapata en planta |
| **FoundationDesignJm** | `punching_shear()` → perímetro crítico 2d | Dibuja el perímetro de punzonamiento como referencia |
| **SteelConnectionJm** | `end_plate()`, `base_plate()` → dimensiones y pernos | `dxf_detail.py` genera plano de la conexión |

---

## Criterio de Éxito
- [ ] Generar DXF de una sección de columna 500×500 con 8Ø25 que se abra correctamente en AutoCAD/LibreCAD
- [ ] Generar planta de cimentación con 4 zapatas acotadas y tabla de resumen
- [ ] Generar detalle de viga en sección + elevación con estribos variables
- [ ] Cuadro de despiece automático con longitudes y pesos
- [ ] Cajetín A3 con información del proyecto
- [ ] Suite de tests con ≥15 casos (verificación visual + coherencia de entidades DXF)

## Ecosystem

This project is part of the **jmurgass99 structural engineering ecosystem**:

- [fastsap](https://github.com/jmurgass99/fastsap) - orquestador SAP2000/ETABS
- [dynamicsjmpro](https://github.com/jmurgass99/dynamicsjmpro) - SaaS frontend + backend
- [dynamicsjm](https://github.com/jmurgass99/dynamicsjm) - motor dinamico
- [foundationdesignjm](https://github.com/jmurgass99/foundationdesignjm) - cimentaciones
- [windloadjm](https://github.com/jmurgass99/windloadjm) - cargas de viento
- [seismicrecordsjm](https://github.com/jmurgass99/seismicrecordsjm) - records sismicos
- [slopestabilityjm](https://github.com/jmurgass99/slopestabilityjm) - estabilidad de taludes
- [steelconnectionjm](https://github.com/jmurgass99/steelconnectionjm) - conexiones de acero
- [steeloptimizerjm](https://github.com/jmurgass99/steeloptimizerjm) - optimizacion GA
- [coldformedjm](https://github.com/jmurgass99/coldformedjm) - acero conformado en frio
- [fatiguejm](https://github.com/jmurgass99/fatiguejm) - analisis de fatiga
- [firesteeljm](https://github.com/jmurgass99/firesteeljm) - analisis termico al fuego
- [dxfstructuraljm](https://github.com/jmurgass99/dxfstructuraljm) - generacion DXF

## Plugins binarios (Grupo G — IDEAS_20)

### AutoCAD live (vía COM)

Dibuja directo en una sesión AutoCAD abierta usando `pyautocad`.

Instalación:
```
pip install dxfstructuraljm[autocad]
```
Requiere Windows + AutoCAD corriendo en la misma sesión.

Ejemplo: dibujar el cuadro de despiece de un puente:
```python
from dxfstructuraljm.integration.autocad_live import AutoCADClient

with AutoCADClient() as cad:
    cad.apply_layer_standard("US")     # AIA-NCS
    cad.set_layer("S-COLU-RBAR", color=1)
    cad.draw_polyline([(0, 0), (1000, 0), (1000, 500), (0, 500), (0, 0)])
    cad.draw_text((100, 600), "C-1 4#5", height=200)
```

### Revit Link CAD (DXF compatible)

Genera DXF con buenas prácticas para `Insert → Link CAD` en Revit
(solo 2D, unidades MM, layers AIA, SHX fonts).

```python
from dxfstructuraljm.integration import revit_dxf_link as rdl

ents = [
    rdl.polyline([(0, 0), (5000, 0), (5000, 5000), (0, 5000)],
                 layer="S-COLU-CONC", close=True),
    rdl.text((100, 100), "PLANTA", height=200),
]
rdl.make_revit_compatible_dxf(ents, "planta_revit.dxf")
```
