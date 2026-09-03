# =============================================================================
# PANEL TI-BASIC — Editor e intérprete de programas
# =============================================================================
from __future__ import annotations

import re
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QTextEdit, QPlainTextEdit, QLabel,
    QGroupBox, QComboBox, QInputDialog, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QKeySequence,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from calculadora.ti_basic import TIBasicInterpreter


# ---------------------------------------------------------------------------
# Programas de ejemplo
# ---------------------------------------------------------------------------
EJEMPLOS: dict[str, str] = {

    "Hola mundo": """Define hola()=Prgm
  ClrIO
  Disp "HOLA MUNDO"
  Disp "TI-Nspire CX CAS"
EndPrgm""",

    "Contador con For": """Define contar(n)=Prgm
  Local i
  ClrIO
  For i,1,n
    Disp i
  EndFor
  Disp "listo"
EndPrgm

Define main()=Prgm
  contar(10)
EndPrgm""",

    "Ecuación cuadrática": """© Resuelve ax²+bx+c=0
Define cuadratica(a,b,c)=Func
  Local d
  b^2-4*a*c→d
  If d<0 Then
    Return "sin raíces reales"
  ElseIf d=0 Then
    Return {-b/(2*a)}
  Else
    Return {(-b+√(d))/(2*a),(-b-√(d))/(2*a)}
  EndIf
EndFunc

Define main()=Prgm
  Local a,b,c
  ClrIO
  Request "a=",a
  Request "b=",b
  Request "c=",c
  Disp "raíces:",cuadratica(a,b,c)
EndPrgm""",

    "Factorial (recursivo)": """Define fact(n)=Func
  If n≤1 Then
    Return 1
  EndIf
  Return n*fact(n-1)
EndFunc

Define main()=Prgm
  Local i
  ClrIO
  For i,1,10
    Disp i,"! =",fact(i)
  EndFor
EndPrgm""",

    "Listas y estadística": """Define main()=Prgm
  Local l,i,s
  ClrIO
  {4,8,15,16,23,42}→l
  Disp "lista:",l
  Disp "elementos:",dim(l)
  Disp "suma:",sum(l)
  Disp "media:",mean(l)
  Disp "máximo:",max(l)
  © las listas de la Nspire empiezan en 1
  Disp "primero:",l[1]
  Disp "último:",l[dim(l)]
  0→s
  For i,1,dim(l)
    s+l[i]^2→s
  EndFor
  Disp "suma de cuadrados:",s
EndPrgm""",

    "While y Exit": """Define colatz(n)=Prgm
  Local pasos
  0→pasos
  ClrIO
  Disp "Collatz de",n
  While n≠1
    If mod(n,2)=0 Then
      n/2→n
    Else
      3*n+1→n
    EndIf
    pasos+1→pasos
    Disp n
    If pasos>200
      Exit
  EndWhile
  Disp "pasos:",pasos
EndPrgm

Define main()=Prgm
  colatz(27)
EndPrgm""",

    "Try / manejo de errores": """Define seguro(a,b)=Func
  Try
    Return a/b
  Else
    Return "no se puede dividir entre cero"
  EndTry
EndFunc

Define main()=Prgm
  ClrIO
  Disp seguro(10,2)
  Disp seguro(10,0)
EndPrgm""",

    "Cadenas": """Define main()=Prgm
  Local s,i,r
  ClrIO
  "TI-Nspire"→s
  Disp "texto:",s
  Disp "longitud:",dim(s)
  Disp "primeras 2:",left(s,2)
  Disp "últimas 6:",right(s,6)
  Disp "del 4 al 6:",mid(s,4,3)
  ""→r
  For i,dim(s),1,-1
    r&s[i]→r
  EndFor
  Disp "al revés:",r
EndPrgm""",

    "Lbl y Goto": """Define main()=Prgm
  Local i
  ClrIO
  0→i
  Lbl otra
  i+1→i
  Disp "vuelta",i
  If i<5
    Goto otra
  Disp "fin"
EndPrgm""",

    "Matrices": """Define main()=Prgm
  Local m
  ClrIO
  [[1,2][3,4]]→m
  Disp "m[1,1]=",m[1,1]
  Disp "m[1,2]=",m[1,2]
  Disp "m[2,1]=",m[2,1]
  Disp "m[2,2]=",m[2,2]
  Disp "fila 1:",m[1]
EndPrgm""",
}


# ---------------------------------------------------------------------------
# Señales Qt para comunicación entre hilos
# ---------------------------------------------------------------------------
class _Signals(QObject):
    linea_salida = pyqtSignal(str)
    solicitar_input = pyqtSignal(str)
    limpiar_pantalla = pyqtSignal()
    programa_terminado = pyqtSignal()


# ---------------------------------------------------------------------------
# Resaltador de sintaxis TI-Basic
# ---------------------------------------------------------------------------
class _Highlighter(QSyntaxHighlighter):

    def __init__(self, doc):
        super().__init__(doc)
        self._rules: list[tuple] = []

        def rule(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(700)
            if italic:
                fmt.setFontItalic(True)
            self._rules.append((re.compile(pattern, re.IGNORECASE), fmt))

        # Estructuras de control
        rule(r'\b(If|Then|ElseIf|Else|EndIf|For|EndFor|While|EndWhile|'
             r'Loop|EndLoop|Exit|Cycle|Try|EndTry|ClrErr|PassErr|'
             r'Lbl|Goto|Return|Stop)\b',
             '#1f6feb', bold=True)
        # Definición de funciones y programas
        rule(r'\b(Define|Func|EndFunc|Prgm|EndPrgm|Local|DelVar|'
             r'LibPub|LibPriv)\b',
             '#c678dd', bold=True)
        # Entrada / salida
        rule(r'\b(Disp|DispAt|Text|Output|Request|RequestStr|Input|InputStr|'
             r'Pause|ClrIO|ClrHome)\b',
             '#3dc9b0', bold=True)
        # Funciones matemáticas
        rule(r'\b(abs|sqrt|root|ln|log|exp|int|iPart|fPart|round|floor|'
             r'ceiling|sign|mod|remain|gcd|lcm|nCr|nPr|factorial|'
             r'max|min|sum|product|mean|approx|'
             r'sin|cos|tan|arcsin|arccos|arctan|sinh|cosh|tanh|'
             r'rand|randInt|when)\s*\(',
             '#e5c07b')
        # Funciones de listas y cadenas
        rule(r'\b(dim|augment|left|right|mid|inString|sortA|sortD|'
             r'char|ord|string|expr)\s*\(',
             '#56b6c2', bold=True)
        # Constantes
        rule(r'\b(pi|true|false|undef|infinity)\b|π|∞', '#c678dd')
        # Operadores lógicos
        rule(r'\b(and|or|not|xor)\b', '#1f6feb')
        # Cadenas entre comillas
        rule(r'"[^"]*"', '#98c379')
        # Listas y matrices
        rule(r'[{}\[\]]', '#d19a66')
        # Números
        rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', '#b5cea8')
        # Operador de guardar y símbolos de la calculadora
        rule(r'→|:=', '#c678dd', bold=True)
        rule(r'[≠≤≥√²³⁻¹]|<=|>=|/=', '#56b6c2')
        # Comentarios: © de la calculadora (y // por comodidad)
        rule(r'(©.*$|//.*$)', '#7f848e', italic=True)

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ---------------------------------------------------------------------------
# Editor con soporte de -> → y tabulación inteligente
# ---------------------------------------------------------------------------
class _Editor(QPlainTextEdit):

    def keyPressEvent(self, event):
        # Convertir -> en →
        if (event.key() == Qt.Key_Greater and
                self.toPlainText().endswith('-')):
            cur = self.textCursor()
            cur.deletePreviousChar()
            cur.insertText('→')
            return
        # Tab inserta 2 espacios
        if event.key() == Qt.Key_Tab:
            self.textCursor().insertText('  ')
            return
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------
class PanelTIBasic(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interprete = TIBasicInterpreter()
        self._signals = _Signals()
        self._hilo: threading.Thread | None = None
        self._input_result: list[str] = []
        self._input_event = threading.Event()
        self._construir_ui()
        self._conectar_signals()
        self._interprete.set_callbacks(
            output_cb=self._signals.linea_salida.emit,
            input_cb=self._pedir_input_desde_hilo,
            clrhome_cb=self._signals.limpiar_pantalla.emit,
        )

    # ── UI ────────────────────────────────────────────────────────────────────

    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        splitter = QSplitter(Qt.Horizontal)

        # ── Editor (izquierda) ────────────────────────────────────────────────
        izq = QWidget()
        lay_izq = QVBoxLayout(izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.setSpacing(5)

        grp_ed = QGroupBox("Programa TI-Basic (TI-Nspire)")
        lay_ed = QVBoxLayout(grp_ed)

        self._editor = _Editor()
        self._editor.setFont(QFont("Consolas", 12))
        self._editor.setStyleSheet(
            "QPlainTextEdit { background:#1e1e2e; color:#cdd6f4; "
            "border:1px solid #313244; border-radius:5px; "
            "padding:6px; selection-background-color:#45475a; }"
        )
        self._editor.setPlaceholderText(
            ":ClrHome\n:Disp \"Hola mundo\"\n:Pause"
        )
        # hay que guardar la referencia: si Python recolecta el
        # resaltador, el coloreado desaparece sin dar ningún error
        self._resaltador = _Highlighter(self._editor.document())
        lay_ed.addWidget(self._editor)

        # Fila de caracteres especiales
        lay_chars = QHBoxLayout()
        lay_chars.setSpacing(4)
        especiales = [
            ("→", "→"), ("≠", "≠"), ("≤", "≤"), ("≥", "≥"),
            ("√(", "√("), ("π", "π"), ("²", "²"), ("©", "© "),
        ]
        for label, char in especiales:
            btn = QPushButton(label)
            btn.setFixedWidth(38)
            btn.setFixedHeight(28)
            btn.setFont(QFont("Consolas", 11))
            btn.setToolTip(f"Insertar {char}")
            btn.clicked.connect(lambda _, c=char: self._insertar(c))
            lay_chars.addWidget(btn)
        lay_chars.addStretch()
        lay_ed.addLayout(lay_chars)
        lay_izq.addWidget(grp_ed, 1)

        # Barra de botones
        lay_btn = QHBoxLayout()
        self._btn_run = QPushButton("▶  Ejecutar")
        self._btn_run.setObjectName("btn_primary")
        self._btn_run.setFixedHeight(34)
        self._btn_run.clicked.connect(self._ejecutar)

        self._btn_stop = QPushButton("■  Detener")
        self._btn_stop.setObjectName("btn_danger")
        self._btn_stop.setFixedHeight(34)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._detener)

        btn_clear = QPushButton("🗑  Limpiar editor")
        btn_clear.setFixedHeight(34)
        btn_clear.clicked.connect(self._editor.clear)

        btn_guardar = QPushButton("💾  Guardar")
        btn_guardar.setFixedHeight(34)
        btn_guardar.setToolTip("Guardar el programa como archivo de texto")
        btn_guardar.clicked.connect(self._guardar_programa)

        btn_abrir = QPushButton("📂  Abrir")
        btn_abrir.setFixedHeight(34)
        btn_abrir.setToolTip("Abrir un programa guardado")
        btn_abrir.clicked.connect(self._abrir_programa)

        lay_btn.addWidget(self._btn_run)
        lay_btn.addWidget(self._btn_stop)
        lay_btn.addWidget(btn_clear)
        lay_btn.addWidget(btn_guardar)
        lay_btn.addWidget(btn_abrir)
        lay_izq.addLayout(lay_btn)

        # Selector de ejemplos
        grp_ej = QGroupBox("Ejemplos")
        lay_ej = QHBoxLayout(grp_ej)
        self._combo_ej = QComboBox()
        self._combo_ej.addItem("— Seleccionar ejemplo —")
        self._combo_ej.addItems(list(EJEMPLOS.keys()))
        btn_cargar = QPushButton("Cargar")
        btn_cargar.clicked.connect(self._cargar_ejemplo)
        lay_ej.addWidget(self._combo_ej, 1)
        lay_ej.addWidget(btn_cargar)
        lay_izq.addWidget(grp_ej)

        splitter.addWidget(izq)

        # ── Pantalla de salida (derecha) ──────────────────────────────────────
        der = QWidget()
        lay_der = QVBoxLayout(der)
        lay_der.setContentsMargins(0, 0, 0, 0)

        grp_pan = QGroupBox("Pantalla — se ejecuta en el PC, no en la calculadora")
        lay_pan = QVBoxLayout(grp_pan)

        lbl_modelo = QLabel("TI-Nspire CX CAS")
        lbl_modelo.setAlignment(Qt.AlignCenter)
        lbl_modelo.setStyleSheet(
            "color:#888; font-size:10px; font-style:italic; margin-bottom:2px;")
        lay_pan.addWidget(lbl_modelo)

        self._pantalla = QTextEdit()
        self._pantalla.setReadOnly(True)
        self._pantalla.setFont(QFont("Consolas", 13))
        self._pantalla.setStyleSheet(
            "QTextEdit { background:#0a0f1e; color:#00e676; "
            "border:3px solid #1a237e; border-radius:6px; "
            "padding:10px; selection-background-color:#1a237e; }"
        )
        lay_pan.addWidget(self._pantalla, 1)

        btn_clear_pan = QPushButton("🗑  Limpiar pantalla")
        btn_clear_pan.clicked.connect(self._pantalla.clear)
        lay_pan.addWidget(btn_clear_pan)

        lay_der.addWidget(grp_pan, 1)
        splitter.addWidget(der)
        splitter.setSizes([500, 400])
        root.addWidget(splitter, 1)

    # ── Señales ───────────────────────────────────────────────────────────────

    def _conectar_signals(self):
        self._signals.linea_salida.connect(self._mostrar_linea)
        self._signals.limpiar_pantalla.connect(self._pantalla.clear)
        self._signals.programa_terminado.connect(self._al_terminar)
        self._signals.solicitar_input.connect(self._mostrar_dialogo_input)

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def _ejecutar(self):
        codigo = self._editor.toPlainText().strip()
        if not codigo:
            return
        self._pantalla.clear()
        self._btn_run.setEnabled(False)
        self._btn_stop.setEnabled(True)

        def _run():
            self._interprete.ejecutar(codigo)
            self._signals.programa_terminado.emit()

        self._hilo = threading.Thread(target=_run, daemon=True)
        self._hilo.start()

    def _detener(self):
        self._interprete.detener()
        self._input_event.set()  # desbloquear si está esperando input

    def _al_terminar(self):
        self._btn_run.setEnabled(True)
        self._btn_stop.setEnabled(False)

    # ── I/O pantalla ──────────────────────────────────────────────────────────

    def _mostrar_linea(self, texto: str):
        self._pantalla.append(texto)
        self._pantalla.verticalScrollBar().setValue(
            self._pantalla.verticalScrollBar().maximum())

    def _pedir_input_desde_hilo(self, prompt: str) -> str:
        """Llamado desde el hilo del intérprete. Bloquea hasta recibir respuesta."""
        self._input_result.clear()
        self._input_event.clear()
        self._signals.solicitar_input.emit(prompt)
        self._input_event.wait(timeout=120)
        return self._input_result[0] if self._input_result else "0"

    def _mostrar_dialogo_input(self, prompt: str):
        """Ejecutado en hilo principal. Muestra QInputDialog."""
        self._pantalla.append(f"? {prompt}")
        text, ok = QInputDialog.getText(self, "Input", prompt)
        val = text if ok else "0"
        self._pantalla.append(f"  {val}")
        self._input_result.append(val)
        self._input_event.set()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _insertar(self, char: str):
        cursor = self._editor.textCursor()
        cursor.insertText(char)
        self._editor.setFocus()

    def _cargar_ejemplo(self):
        nombre = self._combo_ej.currentText()
        if nombre in EJEMPLOS:
            self._editor.setPlainText(EJEMPLOS[nombre])

    def _guardar_programa(self):
        codigo = self._editor.toPlainText().strip()
        if not codigo:
            QMessageBox.warning(self, "Editor vacío", "No hay nada que guardar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar programa TI-Basic", "",
            "Programa TI-Basic (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(codigo)
        except OSError as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    def _abrir_programa(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir programa TI-Basic", "",
            "Programa TI-Basic (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            self._editor.setPlainText(contenido)
        except OSError as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
