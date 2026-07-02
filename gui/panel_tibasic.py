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
    # ── Estilo TI-Nspire CX CAS ──────────────────────────────────────────────
    "Hola mundo (Nspire)": """:ClrHome
:Disp "HOLA MUNDO"
:Disp "TI-NSPIRE CX CAS"
:Pause""",

    "Contador For (Nspire)": """:ClrHome
:Disp "CONTADOR:"
:For(I,1,10)
:Disp I
:End
:Disp "LISTO"
:Pause""",

    "Ecuación cuadrática (Nspire)": """:ClrHome
:Disp "AX²+BX+C=0"
:Input "A=",A
:Input "B=",B
:Input "C=",C
:B^2-4*A*C→D
:If D<0
:Then
:Disp "SIN SOLUCIÓN REAL"
:Else
:If D=0
:Then
:Disp "X="
:Disp -B/(2*A)
:Else
:Disp "X1="
:Disp (-B+√(D))/(2*A)
:Disp "X2="
:Disp (-B-√(D))/(2*A)
:End
:End
:Pause""",

    "Fibonacci (Nspire)": """:ClrHome
:Input "N términos:",N
:0→A
:1→B
:Disp "SERIE FIBONACCI:"
:For(I,1,N)
:Disp A
:A+B→C
:B→A
:C→B
:End
:Pause""",

    "Tabla de multiplicar (Nspire)": """:ClrHome
:Input "Tabla del:",N
:Disp "TABLA:"
:For(I,1,10)
:Disp N*I
:End
:Pause""",

    "Número primo": """:ClrHome
:Input "Número:",N
:1→P
:For(I,2,√(N))
:If frac(N/I)=0
:Then
:0→P
:End
:End
:If P=1 and N>1
:Then
:Disp "ES PRIMO"
:Else
:Disp "NO ES PRIMO"
:End
:Pause""",

    "While: suma de dígitos (Nspire)": """:ClrHome
:Input "Número:",N
:0→S
:While N>0
:N-int(N/10)*10→D
:S+D→S
:int(N/10)→N
:End
:Disp "SUMA DÍGITOS="
:Disp S
:Pause""",

    # ── Estilo TI-99/4A Extended Basic ───────────────────────────────────────
    "Hola mundo (TI-99/4A)": """100 REM HOLA MUNDO
110 CALL CLEAR
120 PRINT "HOLA MUNDO"
130 PRINT "TI-99/4A EXTENDED BASIC"
140 END""",

    "FOR/NEXT (TI-99/4A)": """100 REM SUMA DE 1 A N CON FOR/NEXT
110 INPUT "N=": N
120 S = 0
130 FOR I = 1 TO N
140   S = S + I
150 NEXT I
160 PRINT "SUMA 1 A ";N;" = ";S
170 END""",

    "GOSUB/RETURN (TI-99/4A)": """100 REM SUBRUTINAS CON GOSUB
110 INPUT "RADIO=": R
120 GOSUB 500
130 PRINT "AREA = ";A
140 PRINT "PERIMETRO = ";P
150 END
500 REM SUBRUTINA CIRCULO
510 A = PI * R * R
520 P = 2 * PI * R
530 RETURN""",

    "Cadenas: CHR$/ASC (TI-99/4A)": """100 REM FUNCIONES DE CADENA
110 CALL CLEAR
120 FOR I = 65 TO 90
130   PRINT CHR$(I);
140 NEXT I
150 PRINT
160 PRINT "LEN=";LEN("TEXAS")
170 PRINT "SEG=";SEG$("TEXAS",2,3)
180 PRINT "ASC(T)=";ASC("TEXAS")
190 PRINT "RPT=";RPT$("*",10)
200 END""",

    "DATA/READ (TI-99/4A)": """100 REM LECTURA DE DATOS
110 CALL CLEAR
120 DATA 10, 20, 30, 40, 50
130 S = 0
140 FOR I = 1 TO 5
150   READ X
160   S = S + X
170   PRINT "X=";X
180 NEXT I
190 PRINT "SUMA=";S
200 END""",

    "ON GOTO (TI-99/4A)": """100 REM MENU CON ON GOTO
110 CALL CLEAR
120 PRINT "1-CUADRADO  2-CUBO  3-RAIZ"
130 INPUT "OPCION (1-3)=": OP
140 ON OP GOTO 200, 300, 400
150 PRINT "OPCION INVALIDA"
160 GOTO 500
200 INPUT "N=": N
210 PRINT N;"^2 = ";N*N
220 GOTO 500
300 INPUT "N=": N
310 PRINT N;"^3 = ";N*N*N
320 GOTO 500
400 INPUT "N=": N
410 PRINT "SQR(";N;")=";SQR(N)
500 END""",

    "DEF función propia (TI-99/4A)": """100 REM FUNCIONES DEFINIDAS POR USUARIO
110 DEF CUADRADO(X) = X*X
120 DEF CUBO(X) = X*X*X
130 DEF HIPO(A,B) = SQR(A*A+B*B)
140 CALL CLEAR
150 FOR N = 1 TO 5
160   PRINT N;"  Q=";CUADRADO(N);"  C=";CUBO(N)
170 NEXT N
180 PRINT "HIPOTENUSA(3,4)=";HIPO(3,4)
190 END""",
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

        # Palabras clave de control (Nspire + TI-99/4A)
        rule(r'\b(If|Then|Else|End|For|While|Repeat|Goto|Lbl|Return|Stop|'
             r'Next|Gosub|To|Step|Sub|SubEnd|SubExit|On|Break|Continue|'
             r'Unbreak|Trace|UnTrace)\b',
             '#1f6feb', bold=True)
        # Comandos de I/O
        rule(r'\b(Disp|Print|Input|LinInput|Prompt|Output|Display|Accept|'
             r'ClrHome|Pause|Menu|Call)\b',
             '#3dc9b0', bold=True)
        # Definición / declaración
        rule(r'\b(Def|Dim|Data|Read|Restore|Let|Rem|Randomize|New|Bye|'
             r'Run|List|Size|Delete|Merge|Save|Load)\b',
             '#c678dd', bold=True)
        # Funciones matemáticas
        rule(r'\b(sin|cos|tan|asin|acos|atan|ATN|sqrt|SQR|abs|ABS|'
             r'log|LOG|ln|exp|EXP|int|INT|round|frac|iPart|'
             r'max|MAX|min|MIN|rand|RND|randInt|SGN|sgn|not|PI|pi)\s*\(',
             '#e5c07b')
        # Funciones de cadena
        rule(r'\b(LEN|ASC|CHR\$?|STR\$?|VAL|SEG\$?|RPT\$?|POS|TAB)\s*\(',
             '#56b6c2', bold=True)
        # Constantes
        rule(r'\b(pi|PI|e)\b', '#c678dd')
        # Variables de cadena Str1-Str9 y con $
        rule(r'\bStr[1-9]\b|\b\w+\$', '#e06c75')
        # Variables de lista L1-L6
        rule(r'\bL[1-6]\b', '#d19a66')
        # Cadenas entre comillas
        rule(r'"[^"]*"', '#98c379')
        # Números de línea al inicio
        rule(r'^\d+\b', '#888888')
        # Números
        rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', '#b5cea8')
        # Operador de asignación →
        rule(r'→', '#c678dd', bold=True)
        # Operadores de comparación
        rule(r'[≠≤≥]|!=|<=|>=', '#56b6c2')
        # Comentarios REM y //
        rule(r'(^\s*\d*\s*REM\b.*$|//.*$)', '#7f848e', italic=True)

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

        grp_ed = QGroupBox("Programa TI-Basic")
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
        _Highlighter(self._editor.document())
        lay_ed.addWidget(self._editor)

        # Fila de caracteres especiales
        lay_chars = QHBoxLayout()
        lay_chars.setSpacing(4)
        especiales = [
            ("→", "→"), ("≤", "≤"), ("≥", "≥"), ("≠", "≠"),
            ("√(", "√("), ("π", "π"), ("²", "²"), ("∞", "∞"),
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
        btn_guardar.setToolTip("Guardar programa como archivo .tib")
        btn_guardar.clicked.connect(self._guardar_programa)

        btn_abrir = QPushButton("📂  Abrir")
        btn_abrir.setFixedHeight(34)
        btn_abrir.setToolTip("Abrir un programa .tib guardado")
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

        grp_pan = QGroupBox("Pantalla")
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
            "Programas TI-Basic (*.tib);;Archivos de texto (*.txt);;Todos los archivos (*)"
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
            "Programas TI-Basic (*.tib);;Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            self._editor.setPlainText(contenido)
        except OSError as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
