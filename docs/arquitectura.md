# Arquitectura

Documento técnico para desarrolladores. Describe la organización interna del
proyecto y cómo se relacionan sus módulos.

## Visión general

La aplicación separa **interfaz** (`gui/`), **comunicación con la calculadora**
(`comunicacion/`) y **lógica de cálculo** (`calculadora/`). El punto de entrada
`main.py` arranca la aplicación PyQt5 y muestra la ventana principal.

```
main.py
  └── gui/ventana_principal.py         (ventana, pestañas, tema)
        ├── gui/panel_cas.py       ──▶ calculadora/cas.py
        ├── gui/panel_graficas.py  ──▶ calculadora/graficas.py
        ├── gui/panel_matriz.py    ──▶ calculadora/cas.py (matrices)
        ├── gui/panel_tibasic.py   ──▶ calculadora/ti_basic.py
        ├── gui/panel_archivos.py  ──▶ comunicacion/transferencia.py
        └── gui/barra_estado.py    ──▶ comunicacion/detector.py
```

## Capa de interfaz (`gui/`)

- `ventana_principal.py` — construye la ventana, las pestañas y el tema visual
  (estilo Fusion, fuente Segoe UI 11).
- Cada `panel_*.py` es un widget independiente para una función.
- `barra_estado.py` — muestra el estado de conexión USB en la parte inferior.

Los paneles **no acceden al hardware directamente**: delegan en la capa de
comunicación o en la de cálculo.

## Capa de comunicación (`comunicacion/`)

Ver [conexión USB](conexion_usb.md) para el detalle. En resumen:

- `detector.py` — detección por sysfs (sin libusb) + hilo `MonitorUSB`.
- `transferencia.py` — transferencia de archivos vía `ctypes` sobre
  `libticalcs2` / `libticables2` / `libtifiles2`.

La detección y la transferencia se coordinan mediante pausa/reanudación del
monitor para no competir por el dispositivo USB.

## Capa de cálculo (`calculadora/`)

Sin dependencias de PyQt5 — es lógica pura y testeable de forma aislada:

- `cas.py` — cálculo simbólico con SymPy. Las funciones devuelven un objeto
  `ResultadoCAS` (ver [referencia CAS](referencia_cas.md)).
- `graficas.py` — generación de figuras con Matplotlib.
- `ti_basic.py` — clase `TIBasicInterpreter` con la máquina de ejecución
  (ver [referencia TI-Basic](referencia_tibasic.md)).

## Principios de diseño

- **Separación de capas**: la GUI no habla con el hardware ni implementa
  matemáticas; solo orquesta.
- **Cálculo aislado**: `calculadora/` no importa PyQt5, por lo que puede
  probarse con scripts o tests sin levantar la interfaz.
- **Detección no intrusiva**: leer sysfs evita abrir el dispositivo y
  entrar en conflicto con las librerías de transferencia.

## Ejecutar sin interfaz (para pruebas)

Los módulos de cálculo pueden usarse directamente:

```python
from calculadora import cas

r = cas.derivar("x^3", "x")
print(r.texto)             # representación legible (pretty-print):  3⋅x²
print(r.expresion)         # objeto SymPy:                           3*x**2
print(r.latex_str)         # LaTeX:                                  3 x^{2}

from calculadora.ti_basic import TIBasicInterpreter
```
