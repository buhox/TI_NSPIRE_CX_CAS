from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from comunicacion.detector import InfoCalculadora


class BarraEstado(QWidget):
    """Barra superior que indica el estado de conexión de la calculadora."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barra_estado")
        self.setFixedHeight(38)
        self.setStyleSheet("""
            #barra_estado {
                background-color: #161b22;
                border: 1px solid #21262d;
                border-radius: 6px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)

        self._lbl_icono  = QLabel("⚫")
        self._lbl_texto  = QLabel("Calculadora no conectada — todas las funciones disponibles en modo PC")
        self._lbl_modelo = QLabel("")

        self._lbl_texto.setStyleSheet("color:#8b949e; font-size:12px;")
        self._lbl_modelo.setStyleSheet("color:#58a6ff; font-size:12px; font-weight:bold;")

        layout.addWidget(self._lbl_icono)
        layout.addSpacing(6)
        layout.addWidget(self._lbl_texto, 1)
        layout.addWidget(self._lbl_modelo)

    def set_conectada(self, info: InfoCalculadora):
        self._lbl_icono.setText("🟢")
        self._lbl_texto.setText(f"Conectada:  {info.modelo}  |  Serial: {info.serial or 'N/A'}")
        self._lbl_texto.setStyleSheet("color:#7ee787; font-size:12px;")
        self._lbl_modelo.setText("USB activo")

    def set_info_dispositivo(self, info: dict):
        """Actualiza la barra con OS, batería y memoria libre."""
        partes = []

        os_ver = info.get("os_version", "")
        if os_ver and os_ver != "—":
            partes.append(f"OS {os_ver}")

        bat = info.get("battery")
        if bat is not None:
            icono_bat = "🔋" if not info.get("charging") else "⚡"
            partes.append(f"{icono_bat} {bat}%")

        ram = info.get("mem_free_ram")
        if ram is not None:
            partes.append(f"RAM libre: {self._fmt(ram)}")

        flash = info.get("mem_free_flash")
        if flash is not None:
            partes.append(f"Flash libre: {self._fmt(flash)}")

        if partes:
            self._lbl_modelo.setText("  ·  ".join(partes))

    @staticmethod
    def _fmt(n: int) -> str:
        if n >= 1_048_576:
            return f"{n/1_048_576:.1f} MB"
        if n >= 1024:
            return f"{n/1024:.0f} KB"
        return f"{n} B"

    def set_desconectada(self):
        self._lbl_icono.setText("⚫")
        self._lbl_texto.setText("Calculadora no conectada — modo PC activo")
        self._lbl_texto.setStyleSheet("color:#8b949e; font-size:12px;")
        self._lbl_modelo.setText("")
