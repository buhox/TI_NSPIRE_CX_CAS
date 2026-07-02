# =============================================================================
# PANEL DE MATRICES
# =============================================================================

from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QGroupBox,
    QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from calculadora import cas


class PanelMatriz(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Panel izquierdo: entrada de matriz ───────────────────────────────
        izq = QWidget()
        izq.setMaximumWidth(420)
        lay = QVBoxLayout(izq)
        lay.setContentsMargins(0, 0, 0, 0)

        # Tamaño de la matriz
        grp_tam = QGroupBox("Tamaño de la matriz")
        lay_tam = QHBoxLayout(grp_tam)
        self._spin_filas = QSpinBox()
        self._spin_filas.setRange(1, 6)
        self._spin_filas.setValue(3)
        self._spin_cols  = QSpinBox()
        self._spin_cols.setRange(1, 6)
        self._spin_cols.setValue(3)
        btn_crear = QPushButton("Crear")
        btn_crear.clicked.connect(self._crear_tabla)
        lay_tam.addWidget(QLabel("Filas:"))
        lay_tam.addWidget(self._spin_filas)
        lay_tam.addWidget(QLabel("Cols:"))
        lay_tam.addWidget(self._spin_cols)
        lay_tam.addWidget(btn_crear)
        lay.addWidget(grp_tam)

        # Tabla editable
        grp_mat = QGroupBox("Matriz A")
        lay_mat = QVBoxLayout(grp_mat)
        self._tabla = QTableWidget(3, 3)
        self._tabla.setFont(QFont("Consolas", 12))
        self._tabla.horizontalHeader().hide()
        self._tabla.verticalHeader().hide()
        self._tabla.setFixedHeight(160)
        self._tabla.setStyleSheet(
            "QTableWidget { background:#ffffff; color:#1a1a2e; "
            "gridline-color:#d0d7de; border:1px solid #d0d7de; }"
            "QTableWidget::item { padding:4px; }"
        )
        self._inicializar_tabla(3, 3)
        lay_mat.addWidget(self._tabla)
        lay.addWidget(grp_mat)

        # Operaciones
        grp_op = QGroupBox("Operaciones")
        grid_op = QGridLayout(grp_op)
        operaciones = [
            ("Determinante",    self._determinante),
            ("Inversa",         self._inversa),
            ("Transpuesta",     self._transpuesta),
            ("Valores propios", self._valores_propios),
            ("Rango",           self._rango),
            ("Escalonada",      self._escalonada),
        ]
        for i, (nombre, fn) in enumerate(operaciones):
            btn = QPushButton(nombre)
            btn.setFixedHeight(32)
            btn.clicked.connect(fn)
            grid_op.addWidget(btn, i // 2, i % 2)
        lay.addWidget(grp_op)
        lay.addStretch()
        root.addWidget(izq)

        # ── Panel derecho: resultado ──────────────────────────────────────────
        der = QWidget()
        lay_der = QVBoxLayout(der)
        lay_der.setContentsMargins(0, 0, 0, 0)

        grp_res = QGroupBox("Resultado")
        lay_res = QVBoxLayout(grp_res)
        self._resultado = QTextEdit()
        self._resultado.setReadOnly(True)
        self._resultado.setFont(QFont("Consolas", 13))
        self._resultado.setStyleSheet(
            "background:#ffffff; color:#1a6e2e; border:1px solid #d0d7de; "
            "border-radius:5px; padding:8px;")
        lay_res.addWidget(self._resultado)
        lay_der.addWidget(grp_res, 1)
        root.addWidget(der, 1)

    def _inicializar_tabla(self, filas: int, cols: int):
        self._tabla.setRowCount(filas)
        self._tabla.setColumnCount(cols)
        for r in range(filas):
            for c in range(cols):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignCenter)
                self._tabla.setItem(r, c, item)
        self._tabla.resizeColumnsToContents()

    def _crear_tabla(self):
        self._inicializar_tabla(self._spin_filas.value(),
                                self._spin_cols.value())

    def _leer_matriz(self) -> list[list] | None:
        filas = self._tabla.rowCount()
        cols  = self._tabla.columnCount()
        matriz = []
        for r in range(filas):
            fila = []
            for c in range(cols):
                item = self._tabla.item(r, c)
                texto = item.text().strip() if item else "0"
                try:
                    import sympy as sp
                    fila.append(sp.sympify(texto.replace("^", "**")))
                except Exception:
                    self._mostrar_error(f"Valor inválido en ({r+1},{c+1}): '{texto}'")
                    return None
            matriz.append(fila)
        return matriz

    def _mostrar(self, texto: str, error: bool = False):
        color = "#c0392b" if error else "#1a6e2e"
        self._resultado.setStyleSheet(
            f"background:#ffffff; color:{color}; border:1px solid #d0d7de; "
            f"border-radius:5px; padding:8px;")
        self._resultado.setPlainText(texto)

    def _mostrar_error(self, msg: str):
        self._mostrar(msg, error=True)

    def _determinante(self):
        m = self._leer_matriz()
        if m is None:
            return
        r = cas.determinante(m)
        self._mostrar(r.texto if r.ok else r.error, not r.ok)

    def _inversa(self):
        m = self._leer_matriz()
        if m is None:
            return
        r = cas.inversa(m)
        self._mostrar(r.texto if r.ok else r.error, not r.ok)

    def _transpuesta(self):
        m = self._leer_matriz()
        if m is None:
            return
        try:
            import sympy as sp
            mat = sp.Matrix(m)
            res = mat.T
            from sympy import pretty
            self._mostrar(pretty(res, use_unicode=True))
        except Exception as e:
            self._mostrar_error(str(e))

    def _valores_propios(self):
        m = self._leer_matriz()
        if m is None:
            return
        r = cas.valores_propios(m)
        self._mostrar(r.texto if r.ok else r.error, not r.ok)

    def _rango(self):
        m = self._leer_matriz()
        if m is None:
            return
        try:
            import sympy as sp
            mat = sp.Matrix(m)
            rango = mat.rank()
            self._mostrar(f"Rango = {rango}")
        except Exception as e:
            self._mostrar_error(str(e))

    def _escalonada(self):
        m = self._leer_matriz()
        if m is None:
            return
        try:
            import sympy as sp
            from sympy import pretty
            mat = sp.Matrix(m)
            res, _ = mat.rref()
            self._mostrar(pretty(res, use_unicode=True))
        except Exception as e:
            self._mostrar_error(str(e))
