# =============================================================================
# PANEL DE GRÁFICAS — 2D y(x)  /  3D z(x,y)
# =============================================================================

from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QGroupBox,
    QDoubleSpinBox, QSpinBox, QButtonGroup,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from calculadora.graficas import WidgetGrafica

MAX_FUNCIONES = 4


class PanelGraficas(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Panel izquierdo: controles ────────────────────────────────────────
        izq = QWidget()
        izq.setMaximumWidth(310)
        lay = QVBoxLayout(izq)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # ── Selector de modo ─────────────────────────────────────────────────
        grp_modo = QGroupBox("Modo de graficación")
        lay_modo = QHBoxLayout(grp_modo)
        lay_modo.setSpacing(4)
        self._btn_2d = QPushButton("📈  2D — y(x)")
        self._btn_2d.setCheckable(True)
        self._btn_2d.setChecked(True)
        self._btn_3d = QPushButton("🌐  3D — z(x,y)")
        self._btn_3d.setCheckable(True)
        self._btn_grp = QButtonGroup()
        self._btn_grp.setExclusive(True)
        self._btn_grp.addButton(self._btn_2d, 0)
        self._btn_grp.addButton(self._btn_3d, 1)
        lay_modo.addWidget(self._btn_2d)
        lay_modo.addWidget(self._btn_3d)
        self._btn_2d.toggled.connect(self._cambiar_modo)
        lay.addWidget(grp_modo)

        # Estilo de botón activo/inactivo para el modo
        self._estilo_btn_activo   = ("QPushButton { background-color:#1f6feb; "
                                     "color:white; border:none; }")
        self._estilo_btn_inactivo = ""
        self._btn_2d.setStyleSheet(self._estilo_btn_activo)
        self._btn_3d.setStyleSheet(self._estilo_btn_inactivo)

        # ── Entradas de funciones ─────────────────────────────────────────────
        self._grp_fn = QGroupBox("Funciones y(x)")
        grid_fn = QGridLayout(self._grp_fn)
        self._entradas: list[QLineEdit] = []
        self._lbl_fn:   list[QLabel]    = []
        colores = ["#0550ae", "#c0392b", "#1a6e2e", "#b8860b"]
        for i in range(MAX_FUNCIONES):
            lbl = QLabel(f"f{i+1}(x) =")
            lbl.setStyleSheet(f"color:{colores[i]}; font-weight:bold; font-size:12px;")
            inp = QLineEdit()
            inp.setFont(QFont("Consolas", 12))
            inp.setPlaceholderText("ej: sin(x)" if i == 0 else "")
            inp.returnPressed.connect(self._graficar)
            grid_fn.addWidget(lbl, i, 0)
            grid_fn.addWidget(inp, i, 1)
            self._entradas.append(inp)
            self._lbl_fn.append(lbl)
        lay.addWidget(self._grp_fn)

        # ── Rango X ──────────────────────────────────────────────────────────
        grp_x = QGroupBox("Rango X")
        lay_x = QHBoxLayout(grp_x)
        self._x_min = QDoubleSpinBox()
        self._x_min.setRange(-1e6, 1e6)
        self._x_min.setValue(-10)
        self._x_min.setDecimals(1)
        self._x_max = QDoubleSpinBox()
        self._x_max.setRange(-1e6, 1e6)
        self._x_max.setValue(10)
        self._x_max.setDecimals(1)
        lay_x.addWidget(QLabel("Min:"))
        lay_x.addWidget(self._x_min)
        lay_x.addWidget(QLabel("Max:"))
        lay_x.addWidget(self._x_max)
        lay.addWidget(grp_x)

        # ── Rango Y ──────────────────────────────────────────────────────────
        self._grp_y = QGroupBox("Rango Y (opcional)")
        lay_y = QHBoxLayout(self._grp_y)
        lay_y.setSpacing(4)
        self._y_auto = QPushButton("Auto")
        self._y_auto.setCheckable(True)
        self._y_auto.setChecked(True)
        self._y_auto.setFixedWidth(48)
        self._y_auto.clicked.connect(self._toggle_y_manual)
        self._y_min = QDoubleSpinBox()
        self._y_min.setRange(-1e6, 1e6)
        self._y_min.setValue(-10)
        self._y_min.setDecimals(1)
        self._y_min.setEnabled(False)
        self._y_max = QDoubleSpinBox()
        self._y_max.setRange(-1e6, 1e6)
        self._y_max.setValue(10)
        self._y_max.setDecimals(1)
        self._y_max.setEnabled(False)
        lay_y.addWidget(self._y_auto)
        lay_y.addWidget(QLabel("Min:"))
        lay_y.addWidget(self._y_min)
        lay_y.addWidget(QLabel("Max:"))
        lay_y.addWidget(self._y_max)
        lay.addWidget(self._grp_y)

        # ── Resolución (solo 3D) ──────────────────────────────────────────────
        self._grp_res = QGroupBox("Resolución de malla (3D)")
        lay_res = QHBoxLayout(self._grp_res)
        self._spin_res = QSpinBox()
        self._spin_res.setRange(10, 120)
        self._spin_res.setValue(45)
        self._spin_res.setSuffix(" puntos")
        lay_res.addWidget(QLabel("Puntos:"))
        lay_res.addWidget(self._spin_res)
        lay_res.addStretch()
        self._grp_res.setVisible(False)
        lay.addWidget(self._grp_res)

        # ── Botones de acción ─────────────────────────────────────────────────
        btn_graf = QPushButton("📈  Graficar")
        btn_graf.setObjectName("btn_primary")
        btn_graf.setFixedHeight(36)
        btn_graf.clicked.connect(self._graficar)
        lay.addWidget(btn_graf)

        btn_limpiar = QPushButton("🗑  Limpiar")
        btn_limpiar.clicked.connect(self._limpiar)
        lay.addWidget(btn_limpiar)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color:#f85149; font-size:11px;")
        self._lbl_error.setWordWrap(True)
        lay.addWidget(self._lbl_error)
        lay.addStretch()

        root.addWidget(izq)

        # ── Gráfica ───────────────────────────────────────────────────────────
        self._grafica = WidgetGrafica()
        root.addWidget(self._grafica, 1)

    # ── Cambio de modo ────────────────────────────────────────────────────────

    def _cambiar_modo(self, modo_2d: bool):
        if modo_2d:
            # 2D
            self._btn_2d.setStyleSheet(self._estilo_btn_activo)
            self._btn_3d.setStyleSheet(self._estilo_btn_inactivo)
            self._grp_fn.setTitle("Funciones y(x)")
            for i, lbl in enumerate(self._lbl_fn):
                lbl.setText(f"f{i+1}(x) =")
            self._entradas[0].setPlaceholderText("ej: sin(x)")
            self._grp_y.setTitle("Rango Y (opcional)")
            self._y_auto.setVisible(True)
            self._y_auto.setChecked(True)
            self._y_min.setEnabled(False)
            self._y_max.setEnabled(False)
            self._grp_res.setVisible(False)
        else:
            # 3D
            self._btn_2d.setStyleSheet(self._estilo_btn_inactivo)
            self._btn_3d.setStyleSheet(self._estilo_btn_activo)
            self._grp_fn.setTitle("Superficies z(x,y)")
            for i, lbl in enumerate(self._lbl_fn):
                lbl.setText(f"f{i+1}(x,y) =")
            self._entradas[0].setPlaceholderText("ej: x^2 + y^2")
            self._grp_y.setTitle("Rango Y (eje de profundidad)")
            self._y_auto.setVisible(False)
            self._y_min.setEnabled(True)
            self._y_max.setEnabled(True)
            self._grp_res.setVisible(True)
        self._lbl_error.setText("")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_y_manual(self, checked: bool):
        self._y_min.setEnabled(not checked)
        self._y_max.setEnabled(not checked)

    def _graficar(self):
        funciones = [e.text().strip() for e in self._entradas if e.text().strip()]
        if not funciones:
            self._lbl_error.setText("Ingresa al menos una función.")
            return

        if self._btn_3d.isChecked():
            error = self._grafica.graficar_3d(
                funciones,
                x_min=self._x_min.value(),
                x_max=self._x_max.value(),
                y_min=self._y_min.value(),
                y_max=self._y_max.value(),
                resolucion=self._spin_res.value(),
            )
        else:
            y_min = None if self._y_auto.isChecked() else self._y_min.value()
            y_max = None if self._y_auto.isChecked() else self._y_max.value()
            error = self._grafica.graficar_funciones(
                funciones,
                x_min=self._x_min.value(),
                x_max=self._x_max.value(),
                y_min=y_min,
                y_max=y_max,
            )
        self._lbl_error.setText(error)

    def _limpiar(self):
        for e in self._entradas:
            e.clear()
        self._grafica.limpiar()
        self._lbl_error.setText("")
