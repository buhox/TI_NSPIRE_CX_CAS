# =============================================================================
# VENTANA PRINCIPAL — TI-Nspire CX CAS para PC
# =============================================================================

from __future__ import annotations
import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QStatusBar,
    QApplication,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from .panel_cas import PanelCAS
from .panel_graficas import PanelGraficas
from .panel_matriz import PanelMatriz
from .panel_tibasic import PanelTIBasic
from .panel_archivos import PanelArchivos
from .panel_manual import PanelManual
from .barra_estado import BarraEstado
from comunicacion.detector import MonitorUSB, InfoCalculadora

logger = logging.getLogger("ti_nspire.gui")


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación TI-Nspire CX CAS para PC."""

    def __init__(self):
        super().__init__()
        self._info_calc: InfoCalculadora | None = None
        self._construir_ui()
        self._iniciar_monitor_usb()

    # ── Construcción de la interfaz ───────────────────────────────────────────

    def _construir_ui(self):
        self.setWindowTitle("TI-Nspire CX CAS — PC")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # Centrar en pantalla
        pantalla = QApplication.primaryScreen().availableGeometry()
        self.move(
            (pantalla.width()  - self.width())  // 2,
            (pantalla.height() - self.height()) // 2,
        )

        self._aplicar_tema()

        # ── Layout central ────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(4)

        # ── Barra de conexión ─────────────────────────────────────────────────
        self._barra_conexion = BarraEstado()
        layout.addWidget(self._barra_conexion)

        # ── Pestañas principales ──────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)

        self._panel_cas      = PanelCAS()
        self._panel_graficas = PanelGraficas()
        self._panel_matriz   = PanelMatriz()
        self._panel_tibasic  = PanelTIBasic()
        self._panel_archivos = PanelArchivos()
        self._panel_manual   = PanelManual()

        self._tabs.addTab(self._panel_cas,      "🧮  CAS / Álgebra")
        self._tabs.addTab(self._panel_graficas, "📈  Gráficas")
        self._tabs.addTab(self._panel_matriz,   "⬛  Matrices")
        self._tabs.addTab(self._panel_tibasic,  "💾  TI-Basic")
        self._tabs.addTab(self._panel_archivos, "📁  Archivos")
        self._tabs.addTab(self._panel_manual,   "📖  Manual")

        layout.addWidget(self._tabs, 1)

        # ── Barra de estado inferior ──────────────────────────────────────────
        sb = QStatusBar()
        sb.setStyleSheet("QStatusBar { background:#0d1117; color:#6e7681; "
                         "border-top:1px solid #21262d; font-size:11px; }")
        self._lbl_status = QLabel("Calculadora no conectada")
        sb.addWidget(self._lbl_status)
        self.setStatusBar(sb)

    # ── Monitor USB ───────────────────────────────────────────────────────────

    def _iniciar_monitor_usb(self):
        self._monitor = MonitorUSB(
            on_conectada=self._al_conectar,
            on_desconectada=self._al_desconectar,
        )
        self._monitor.iniciar()

    def _al_conectar(self, info: InfoCalculadora):
        self._info_calc = info
        QTimer.singleShot(0, lambda: self._actualizar_estado_conexion(True, info))
        QTimer.singleShot(0, lambda: self._panel_archivos.notificar_usb_detectada(info))

    def _al_desconectar(self):
        self._info_calc = None
        QTimer.singleShot(0, lambda: self._actualizar_estado_conexion(False, None))
        QTimer.singleShot(0, lambda: self._panel_archivos.notificar_usb_perdida())

    def _actualizar_estado_conexion(self, conectada: bool,
                                    info: InfoCalculadora | None):
        if conectada and info:
            self._barra_conexion.set_conectada(info)
            self._lbl_status.setText(f"✅ {info}")
        else:
            self._barra_conexion.set_desconectada()
            self._lbl_status.setText("⚫ Calculadora no conectada — modo PC activo")

    # ── Cierre ────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._monitor.detener()
        # Cerrar la sesión USB explícitamente: no confiar en el GC del gestor
        try:
            self._panel_archivos._gestor.cerrar()
        except Exception:
            pass
        event.accept()

    # ── Tema visual ───────────────────────────────────────────────────────────

    def _aplicar_tema(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #21262d;
                background: #161b22;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #161b22;
                color: #8b949e;
                padding: 8px 20px;
                border: 1px solid #21262d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #21262d;
                color: #58a6ff;
                border-bottom: 2px solid #58a6ff;
            }
            QTabBar::tab:hover { background: #1c2333; color: #c9d1d9; }

            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover   { background-color: #30363d; color: #58a6ff; }
            QPushButton:pressed { background-color: #388bfd22; }

            QPushButton#btn_primary {
                background-color: #1f6feb;
                color: white;
                border: none;
            }
            QPushButton#btn_primary:hover { background-color: #388bfd; }

            QPushButton#btn_danger {
                background-color: #da3633;
                color: white;
                border: none;
            }

            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 5px;
                padding: 5px 8px;
                font-size: 13px;
                selection-background-color: #1f6feb;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #58a6ff;
            }

            QGroupBox {
                border: 1px solid #21262d;
                border-radius: 6px;
                margin-top: 8px;
                padding: 8px 6px 6px 6px;
                font-weight: bold;
                color: #58a6ff;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }

            QLabel#lbl_resultado {
                background-color: #161b22;
                border: 1px solid #21262d;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                color: #7ee787;
                font-family: 'Consolas', 'Courier New', monospace;
            }

            QScrollBar:vertical {
                background: #0d1117; width: 7px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #30363d; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QTableWidget {
                background: #161b22;
                gridline-color: #21262d;
                border: 1px solid #21262d;
                border-radius: 4px;
            }
            QHeaderView::section {
                background: #21262d;
                color: #58a6ff;
                padding: 4px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected { background: #1f6feb44; }
        """)
