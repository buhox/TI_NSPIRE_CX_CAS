# =============================================================================
# TI-Nspire CX CAS — PC
# Punto de entrada principal
# =============================================================================

from __future__ import annotations
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 11))
    app.setApplicationName("TI-Nspire CX CAS — PC")

    from gui.ventana_principal import VentanaPrincipal
    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
