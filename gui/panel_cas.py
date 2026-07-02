# =============================================================================
# PANEL CAS — Álgebra, Cálculo, Números
# =============================================================================

from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QLabel, QTextEdit,
    QGroupBox, QComboBox, QSplitter,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextBlockFormat, QTextCursor

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from calculadora import cas


BOTONES_SIMBOLOS = [
    ("x",   "x"),   ("y",   "y"),   ("π",   "pi"),   ("e",   "e"),
    ("x²",  "**2"), ("√",   "sqrt("),("^",   "**"),   ("|x|", "Abs("),
    ("sin", "sin("),("cos", "cos("), ("tan", "tan("),  ("ln",  "log("),
    ("(",   "("),   (")",   ")"),    (",",   ","),      ("∞",   "oo"),
]


# =============================================================================
# CONSOLA INTERACTIVA CAS
# =============================================================================
class _ConsolaCAS(QTextEdit):
    """
    QTextEdit que funciona como consola interactiva:
    - Muestra un prompt  >>  donde el usuario escribe la expresión
    - Al presionar Enter evalúa y muestra el resultado en el mismo widget
    - Todo el contenido anterior queda protegido (no editable)
    - ↑ / ↓ navegan el historial de expresiones anteriores
    """

    def __init__(self, evaluar_cb, parent=None):
        super().__init__(parent)
        self._evaluar_cb  = evaluar_cb   # fn(expr) -> (texto_resultado, ok: bool)
        self._entradas:   list[str] = []
        self._hist_idx:   int       = -1
        self._borrador:   str       = ""
        self._prompt_pos: int       = 0  # posición donde empieza la entrada del usuario

        self.setFont(QFont("Consolas", 13))
        self.setStyleSheet(
            "QTextEdit {"
            "  background: #ffffff;"
            "  color: #1a1a2e;"
            "  border: 2px solid #b0b8c1;"
            "  border-radius: 6px;"
            "  padding: 8px;"
            "}"
        )
        self._nuevo_prompt()

    # ── Prompt ────────────────────────────────────────────────────────────────

    def _nuevo_prompt(self):
        """Inserta un nuevo prompt >> al final y fija la posición de entrada."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Estilo del prompt (gris oscuro, como la TI-Nspire)
        fmt_prompt = QTextCharFormat()
        fmt_prompt.setForeground(QColor("#555555"))
        fmt_prompt.setFontWeight(400)
        cursor.insertText(">> ", fmt_prompt)

        # Formato para lo que escribe el usuario (negro, normal)
        fmt_input = QTextCharFormat()
        fmt_input.setForeground(QColor("#1a1a2e"))
        fmt_input.setFontWeight(400)
        cursor.setCharFormat(fmt_input)

        self._prompt_pos = cursor.position()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    # ── Acceso a la entrada actual ─────────────────────────────────────────────

    def _entrada_actual(self) -> str:
        """Devuelve el texto que el usuario escribió en la línea del prompt."""
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        return cursor.selectedText().strip()

    def _set_entrada(self, texto: str):
        """Reemplaza el texto de entrada sin tocar el prompt ni el historial."""
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#1a1a2e"))
        fmt.setFontWeight(400)
        cursor.setCharFormat(fmt)
        cursor.insertText(texto)
        self.setTextCursor(cursor)

    # ── Insertar símbolo (desde los botones del panel izquierdo) ──────────────

    def insertar_simbolo(self, texto: str):
        cursor = self.textCursor()
        if cursor.position() < self._prompt_pos:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        cursor.insertText(texto)
        self.setFocus()

    # ── Limpiar consola ───────────────────────────────────────────────────────

    def limpiar(self):
        self.clear()
        self._entradas.clear()
        self._hist_idx = -1
        self._nuevo_prompt()

    # ── Teclado ───────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        # Si el cursor está antes del prompt, llevarlo al final
        if cursor.position() < self._prompt_pos:
            if event.key() not in (Qt.Key_Up, Qt.Key_Down,
                                   Qt.Key_PageUp, Qt.Key_PageDown):
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)

        # Backspace: no borrar más allá del inicio de la entrada
        if event.key() == Qt.Key_Backspace:
            if self.textCursor().position() <= self._prompt_pos:
                return

        # Delete: no borrar si el cursor está dentro del prompt
        if event.key() == Qt.Key_Delete:
            if self.textCursor().position() < self._prompt_pos:
                return

        # Enter: ejecutar expresión
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._ejecutar()
            return

        # Flecha arriba: expresión anterior del historial
        if event.key() == Qt.Key_Up:
            if not self._entradas:
                return
            if self._hist_idx == -1:
                self._borrador = self._entrada_actual()
            if self._hist_idx < len(self._entradas) - 1:
                self._hist_idx += 1
                self._set_entrada(self._entradas[self._hist_idx])
            return

        # Flecha abajo: expresión siguiente del historial
        if event.key() == Qt.Key_Down:
            if self._hist_idx == -1:
                return
            if self._hist_idx > 0:
                self._hist_idx -= 1
                self._set_entrada(self._entradas[self._hist_idx])
            else:
                self._hist_idx = -1
                self._set_entrada(self._borrador)
            return

        super().keyPressEvent(event)

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def _ejecutar(self):
        expr = self._entrada_actual()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

        if not expr:
            cursor.insertText("\n")
            self._nuevo_prompt()
            return

        if not self._entradas or self._entradas[0] != expr:
            self._entradas.insert(0, expr)
        self._hist_idx = -1

        resultado_txt, ok = self._evaluar_cb(expr)

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt_der = QTextBlockFormat()
        fmt_der.setAlignment(Qt.AlignRight)
        fmt_izq = QTextBlockFormat()
        fmt_izq.setAlignment(Qt.AlignLeft)

        if ok:
            fmt_res = QTextCharFormat()
            fmt_res.setForeground(QColor("#1a1a2e"))
            fmt_res.setFontWeight(700)
            for linea in resultado_txt.strip().split("\n"):
                cursor.insertText("\n")
                cursor.setBlockFormat(fmt_der)
                cursor.insertText(linea, fmt_res)
        else:
            fmt_err = QTextCharFormat()
            fmt_err.setForeground(QColor("#c0392b"))
            fmt_err.setFontWeight(400)
            for linea in resultado_txt.strip().split("\n"):
                cursor.insertText("\n")
                cursor.setBlockFormat(fmt_izq)
                cursor.insertText(f"  {linea}", fmt_err)

        fmt_sep = QTextCharFormat()
        fmt_sep.setForeground(QColor("#cccccc"))
        cursor.insertText("\n")
        cursor.setBlockFormat(fmt_izq)
        cursor.insertText("─" * 60, fmt_sep)
        cursor.insertText("\n")
        cursor.setBlockFormat(fmt_izq)
        self.setTextCursor(cursor)
        self._nuevo_prompt()


# =============================================================================
# PANEL PRINCIPAL CAS
# =============================================================================
class PanelCAS(QWidget):
    """Panel principal de CAS: consola interactiva + teclado de símbolos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        splitter = QSplitter(Qt.Horizontal)

        # ── Panel izquierdo: operación + parámetros + símbolos ────────────────
        izq = QWidget()
        izq.setMaximumWidth(360)
        lay_izq = QVBoxLayout(izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.setSpacing(6)

        # Selector de operación
        grp_op = QGroupBox("Operación")
        lay_op = QVBoxLayout(grp_op)
        self._combo_op = QComboBox()
        self._combo_op.addItems([
            "Evaluar / Simplificar",
            "Expandir",
            "Factorizar",
            "Resolver (variable x)",
            "Derivar (respecto a x)",
            "Integrar (indefinida)",
            "Integrar (definida)",
            "Límite",
            "Serie de Taylor",
            "Fracciones parciales",
            "Factores primos",
            "Es primo",
        ])
        self._combo_op.currentIndexChanged.connect(self._al_cambiar_op)
        lay_op.addWidget(self._combo_op)
        lay_izq.addWidget(grp_op)

        # Parámetros extra
        self._grp_params = QGroupBox("Parámetros")
        lay_par = QGridLayout(self._grp_params)
        self._lbl_p1 = QLabel("Variable:")
        self._inp_p1 = QLineEdit("x"); self._inp_p1.setMaximumWidth(60)
        self._lbl_p2 = QLabel("Desde:")
        self._inp_p2 = QLineEdit("0"); self._inp_p2.setMaximumWidth(60)
        self._lbl_p3 = QLabel("Hasta:")
        self._inp_p3 = QLineEdit("1"); self._inp_p3.setMaximumWidth(60)
        self._lbl_p4 = QLabel("Orden:")
        self._inp_p4 = QLineEdit("6"); self._inp_p4.setMaximumWidth(60)
        lay_par.addWidget(self._lbl_p1, 0, 0); lay_par.addWidget(self._inp_p1, 0, 1)
        lay_par.addWidget(self._lbl_p2, 0, 2); lay_par.addWidget(self._inp_p2, 0, 3)
        lay_par.addWidget(self._lbl_p3, 1, 0); lay_par.addWidget(self._inp_p3, 1, 1)
        lay_par.addWidget(self._lbl_p4, 1, 2); lay_par.addWidget(self._inp_p4, 1, 3)
        self._grp_params.setVisible(False)
        lay_izq.addWidget(self._grp_params)

        # Teclado de símbolos
        grp_tec = QGroupBox("Símbolos")
        grid = QGridLayout(grp_tec)
        grid.setSpacing(3)
        for i, (etiq, val) in enumerate(BOTONES_SIMBOLOS):
            btn = QPushButton(etiq)
            btn.setFixedHeight(30)
            btn.setFixedWidth(60)
            btn.setFont(QFont("Consolas", 11))
            btn.clicked.connect(lambda _, v=val: self._insertar(v))
            grid.addWidget(btn, i // 4, i % 4)
        lay_izq.addWidget(grp_tec)

        # Botón limpiar
        btn_limpiar = QPushButton("🗑  Limpiar consola")
        btn_limpiar.setObjectName("btn_danger")
        btn_limpiar.clicked.connect(self._limpiar)
        lay_izq.addWidget(btn_limpiar)
        lay_izq.addStretch()

        splitter.addWidget(izq)

        # ── Panel derecho: consola interactiva ────────────────────────────────
        der = QWidget()
        lay_der = QVBoxLayout(der)
        lay_der.setContentsMargins(0, 0, 0, 0)

        grp_cons = QGroupBox("Consola CAS  —  escribe la expresión y pulsa Enter  (↑↓ historial)")
        lay_cons = QVBoxLayout(grp_cons)

        self._consola = _ConsolaCAS(evaluar_cb=self._evaluar_expr)
        lay_cons.addWidget(self._consola)

        lay_der.addWidget(grp_cons, 1)
        splitter.addWidget(der)
        splitter.setSizes([340, 620])
        root.addWidget(splitter, 1)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _al_cambiar_op(self, idx: int):
        ops_con_params = {6, 7, 8}
        self._grp_params.setVisible(idx in ops_con_params)
        etiquetas = {
            6: ("Variable", "Desde",  "Hasta", "—"),
            7: ("Variable", "Punto",  "Dir +-", "—"),
            8: ("Variable", "Punto",  "—",      "Orden"),
        }
        if idx in etiquetas:
            p1, p2, p3, p4 = etiquetas[idx]
            self._lbl_p1.setText(p1 + ":")
            self._lbl_p2.setText(p2 + ":")
            self._lbl_p3.setText(p3 + ":")
            self._lbl_p4.setText(p4 + ":")

    def _insertar(self, texto: str):
        self._consola.insertar_simbolo(texto)

    def _limpiar(self):
        self._consola.limpiar()

    def _evaluar_expr(self, expr: str) -> tuple[str, bool]:
        """Evalúa expr según la operación seleccionada. Retorna (texto, ok)."""
        op  = self._combo_op.currentIndex()
        var = self._inp_p1.text().strip() or "x"

        ops = {
            0:  lambda: cas.evaluar(expr),
            1:  lambda: cas.expandir(expr),
            2:  lambda: cas.factorizar(expr),
            3:  lambda: cas.resolver(expr, var),
            4:  lambda: cas.derivar(expr, var),
            5:  lambda: cas.integrar(expr, var),
            6:  lambda: cas.integrar(expr, var,
                                     self._inp_p2.text(),
                                     self._inp_p3.text()),
            7:  lambda: cas.limite(expr, var,
                                   self._inp_p2.text(),
                                   self._inp_p3.text() or "+-"),
            8:  lambda: cas.serie_taylor(expr, var,
                                         int(self._inp_p2.text() or 0),
                                         int(self._inp_p4.text() or 6)),
            9:  lambda: cas.fracciones_parciales(expr, var),
            10: lambda: cas.factores_primos(expr),
            11: lambda: cas.es_primo(expr),
        }

        resultado = ops.get(op, lambda: cas.evaluar(expr))()

        if resultado.ok:
            return resultado.texto, True
        return resultado.error, False
