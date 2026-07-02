# TI-Nspire CX CAS — PC

Aplicación de escritorio en **PyQt5** para gestionar la calculadora **TI-Nspire CX CAS** desde el ordenador: cálculo simbólico (CAS), gráficas, matrices, intérprete TI-Basic y transferencia de archivos por USB.

> Desarrollada y probada en **Fedora Linux**.

## Características

- **CAS / Álgebra** (con SymPy): simplificar, expandir, factorizar, resolver ecuaciones, fracciones parciales, derivadas, integrales, límites y series de Taylor.
- **Matrices**: determinante, inversa y valores propios.
- **Teoría de números**: factores primos, test de primalidad y combinatoria.
- **Gráficas** (con Matplotlib): funciones 2D, superficies 3D y nubes de puntos.
- **TI-Basic**: intérprete para ejecutar programas TI-Basic con entrada/salida interactiva.
- **Transferencia de archivos por USB**: conectar, listar, enviar, recibir y eliminar archivos de la calculadora.
- **Detección USB sin libusb**: lee `/sys/bus/usb/devices` directamente para evitar conflictos con `ticables`.

## Requisitos

- Python 3.10 o superior
- Dependencias (ver `requirements.txt`):

```
PyQt5>=5.15
sympy>=1.12
numpy>=1.24
matplotlib>=3.7
pyusb>=1.2
scipy>=1.10
```

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/buhox/TI_NSPIRE_CX_CAS.git
cd TI_NSPIRE_CX_CAS

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Opción 1: directamente
python3 main.py

# Opción 2: con el lanzador
./lanzar.sh
```

En Fedora también puede instalarse un acceso directo en el menú de aplicaciones
(`~/.local/share/applications/ti-nspire-cx-cas.desktop`).

## Estructura del proyecto

```
TI_NSPIRE_CX_CAS/
├── main.py                      # Punto de entrada
├── lanzar.sh                    # Lanzador bash
├── requirements.txt
├── gui/                         # Interfaz gráfica (PyQt5)
│   ├── ventana_principal.py     # Ventana principal, pestañas y tema
│   ├── panel_cas.py             # Panel CAS / Álgebra
│   ├── panel_graficas.py        # Panel de gráficas
│   ├── panel_matriz.py          # Panel de matrices
│   ├── panel_tibasic.py         # Panel TI-Basic
│   ├── panel_archivos.py        # Panel de transferencia de archivos
│   └── barra_estado.py          # Barra de conexión USB
├── comunicacion/                # Comunicación con la calculadora
│   ├── detector.py              # Detección USB vía /sys/bus/usb/devices
│   └── transferencia.py         # Transferencia de archivos
└── calculadora/                 # Lógica de cálculo
    ├── cas.py                   # Cálculo simbólico con SymPy
    ├── graficas.py              # Gráficas con Matplotlib
    └── ti_basic.py              # Intérprete TI-Basic
```

## Notas técnicas

- **Vendor ID** Texas Instruments: `0x0451`
- **PIDs soportados**: `0xE022` (CX CAS), `0xE012` (CX), `0xE008` (Nspire), `0xE003` (CAS)
- El detector USB lee `/sys/bus/usb/devices` directamente, sin `libusb`/`pyusb`, para
  evitar conflictos con `ticables`.
