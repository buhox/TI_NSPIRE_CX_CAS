# TI-Nspire CX CAS — PC

Aplicación de escritorio PyQt5 para gestionar la calculadora TI-Nspire CX CAS.

## Rutas
- Proyecto: `/home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS/`
- Lanzador: `lanzar.sh`
- Acceso directo escritorio: `~/.local/share/applications/ti-nspire-cx-cas.desktop`

## Estructura del proyecto
- `main.py` — Punto de entrada
- `gui/ventana_principal.py` — Ventana principal, pestañas, tema visual
- `gui/panel_cas.py` — Panel CAS / Álgebra
- `gui/panel_graficas.py` — Panel de Gráficas
- `gui/panel_matriz.py` — Panel de Matrices
- `gui/panel_tibasic.py` — Panel TI-Basic
- `gui/panel_archivos.py` — Panel de transferencia de archivos
- `gui/barra_estado.py` — Barra de conexión USB
- `comunicacion/detector.py` — Detección USB via /sys/bus/usb/devices (sin libusb)
- `comunicacion/transferencia.py` — Transferencia de archivos
- `calculadora/cas.py` — Cálculos CAS con SymPy
- `calculadora/graficas.py` — Gráficas matemáticas con Matplotlib
- `calculadora/ti_basic.py` — Programas TI-Basic

## Dependencias
```
PyQt5>=5.15
sympy>=1.12
numpy>=1.24
matplotlib>=3.7
pyusb>=1.2
scipy>=1.10
```

## Lo que se hizo en la sesión
- Se creó `lanzar.sh` — script bash que lanza la app con `python3 main.py`
- Se creó `~/.local/share/applications/ti-nspire-cx-cas.desktop` — acceso directo en el menú de aplicaciones de Fedora
- La instalación en Fedora es Opción A (lanzador de escritorio, sin compilar)

## Comandos para activar la app en Fedora
```bash
# Instalar dependencias
pip install PyQt5 sympy numpy matplotlib pyusb scipy

# Dar permisos al lanzador
chmod +x /home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS/lanzar.sh

# Actualizar menú de aplicaciones
update-desktop-database ~/.local/share/applications/

# Ejecutar directamente
cd /home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS
python3 main.py
```

## Notas técnicas
- El detector USB lee `/sys/bus/usb/devices` directamente, sin libusb/pyusb, para evitar conflictos con ticables
- Vendor ID Texas Instruments: 0x0451
- PIDs soportados: 0xE022 (CX CAS), 0xE012 (CX), 0xE008 (Nspire), 0xE003 (CAS)
- No modificar código sin aprobación explícita del usuario
