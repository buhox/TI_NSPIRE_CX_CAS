# =============================================================================
# DETECCIÓN Y CONEXIÓN USB — TI-Nspire CX CAS
# =============================================================================
# Detecta la calculadora TI-Nspire CX CAS leyendo /sys/bus/usb/devices
# directamente, SIN usar libusb/pyusb. Esto evita que el contexto libusb
# del monitor entre en conflicto con el contexto que abre ticables al conectar.
#
# Vendor ID : 0x0451  (Texas Instruments)
# Product IDs compatibles:
#   0xE022 → TI-Nspire CX CAS
#   0xE012 → TI-Nspire CX (sin CAS)
#   0xE008 → TI-Nspire (generación anterior)
#   0xE003 → TI-Nspire CAS
# =============================================================================

from __future__ import annotations
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("ti_nspire.detector")

TI_VID = 0x0451
TI_PIDS = {
    0xE022: "TI-Nspire CX CAS",
    0xE012: "TI-Nspire CX",
    0xE008: "TI-Nspire",
    0xE003: "TI-Nspire CAS",
}

_SYSFS_USB = Path("/sys/bus/usb/devices")


class InfoCalculadora:
    """Información del dispositivo USB detectado."""

    def __init__(self, pid: int, fabricante: str, producto: str, serial: str):
        self.pid = pid
        self.modelo = TI_PIDS.get(pid, "TI-Nspire (desconocido)")
        self.fabricante = fabricante
        self.producto = producto
        self.serial = serial

    def __str__(self) -> str:
        return f"{self.modelo} | Serial: {self.serial or 'N/A'}"


def buscar_calculadora() -> Optional[InfoCalculadora]:
    """
    Busca una calculadora TI-Nspire leyendo /sys/bus/usb/devices.
    No usa libusb ni pyusb — evita conflictos de handle con ticables.
    """
    try:
        for entry in _SYSFS_USB.iterdir():
            vid_file = entry / "idVendor"
            pid_file = entry / "idProduct"
            if not vid_file.exists() or not pid_file.exists():
                continue
            try:
                vid = int(vid_file.read_text().strip(), 16)
                if vid != TI_VID:
                    continue
                pid = int(pid_file.read_text().strip(), 16)
                if pid not in TI_PIDS:
                    continue
                # Leer serial si está disponible (no abre el dispositivo USB)
                serial_file = entry / "serial"
                serial = serial_file.read_text().strip() if serial_file.exists() else ""
                modelo = TI_PIDS[pid]
                logger.info("Calculadora detectada: %s (PID=0x%04X)", modelo, pid)
                return InfoCalculadora(pid, "Texas Instruments", modelo, serial)
            except (ValueError, OSError):
                continue
    except OSError as e:
        logger.debug("buscar_calculadora (sysfs): %s", e)
    return None


class MonitorUSB:
    """
    Hilo que vigila la conexión/desconexión de la calculadora cada 1.5 s
    usando /sys/bus/usb/devices (sin libusb).
    """

    def __init__(
        self,
        on_conectada:    Callable[[InfoCalculadora], None],
        on_desconectada: Callable[[], None],
        intervalo_seg:   float = 1.5,
    ):
        self._on_conectada    = on_conectada
        self._on_desconectada = on_desconectada
        self._intervalo       = intervalo_seg
        self._activo          = False
        self._pausado         = False
        self._hilo:   Optional[threading.Thread] = None
        self._estado_anterior: Optional[InfoCalculadora] = None

    def iniciar(self) -> None:
        if self._activo:
            return
        self._activo  = True
        self._pausado = False
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()
        logger.info("Monitor USB iniciado (intervalo %.1f s)", self._intervalo)

    def detener(self) -> None:
        self._activo = False
        if self._hilo:
            self._hilo.join(timeout=3)
        logger.info("Monitor USB detenido.")

    def pausar(self) -> None:
        """Pausa el polling para que ticables pueda abrir el dispositivo."""
        self._pausado = True
        # Esperar a que el ciclo actual (sysfs, sin libusb) termine
        time.sleep(self._intervalo + 0.1)
        logger.info("Monitor USB pausado")

    def reanudar(self) -> None:
        self._pausado = False
        logger.info("Monitor USB reanudado")

    def _bucle(self) -> None:
        while self._activo:
            if self._pausado:
                time.sleep(0.2)
                continue

            info = buscar_calculadora()

            if info and self._estado_anterior is None:
                self._estado_anterior = info
                try:
                    self._on_conectada(info)
                except Exception as e:
                    logger.error("Error en callback on_conectada: %s", e)

            elif not info and self._estado_anterior is not None:
                self._estado_anterior = None
                try:
                    self._on_desconectada()
                except Exception as e:
                    logger.error("Error en callback on_desconectada: %s", e)

            time.sleep(self._intervalo)
