# Conexión USB

La aplicación se comunica con la TI-Nspire CX CAS por USB en **dos capas
separadas** que están diseñadas para no interferir entre sí:

1. **Detección** (`comunicacion/detector.py`) — lee `/sys/bus/usb/devices`
   directamente (sysfs), **sin abrir el dispositivo** ni usar libusb.
2. **Transferencia** (`comunicacion/transferencia.py`) — usa las librerías
   `libticalcs2` / `libticables2` / `libtifiles2` vía `ctypes` para leer y
   escribir archivos.

Esta separación evita que el monitor de detección y la transferencia peleen
por el mismo *handle* USB.

## Dispositivos compatibles

| Vendor ID | Product ID | Modelo |
|---|---|---|
| `0x0451` | `0xE022` | TI-Nspire CX CAS |
| `0x0451` | `0xE012` | TI-Nspire CX (sin CAS) |
| `0x0451` | `0xE008` | TI-Nspire (generación anterior) |
| `0x0451` | `0xE003` | TI-Nspire CAS |

## Cómo funciona la detección

- Un hilo `MonitorUSB` revisa la conexión **cada 1.5 segundos**.
- Cuando conectas o desconectas la calculadora, la barra de estado se actualiza
  automáticamente.
- Antes de una transferencia, el monitor se **pausa** para que las librerías
  `ticables` puedan abrir el dispositivo sin conflicto, y se **reanuda** al
  terminar.

## Requisitos del sistema (Linux)

La transferencia de archivos necesita las librerías de la suite **TiLP/libti**
instaladas en el sistema:

```
libticalcs2.so.13
libticables2.so.8
libtifiles2.so.11
```

En Fedora suelen venir con el paquete de TiLP (`tilp2`/`libticalcs`). Si no
están, la **detección seguirá funcionando** (usa sysfs), pero la
**transferencia de archivos no**.

## Permisos USB

Para acceder al dispositivo sin ser *root* puede ser necesaria una regla
**udev** que dé permiso al Vendor ID de Texas Instruments (`0451`). Si la
detección funciona pero la transferencia falla con errores de permiso, ese
suele ser el motivo.

## Solución de problemas

| Síntoma | Posible causa |
|---|---|
| No detecta la calculadora | Cable/puerto, calculadora apagada, o PID no soportado |
| Detecta pero no transfiere | Faltan las librerías `libticalcs2`/`libticables2`/`libtifiles2` |
| Error de permisos al transferir | Falta regla udev para el VID `0451` |
| Se desconecta durante la transferencia | Otro programa (TiLP, etc.) tomó el dispositivo |
