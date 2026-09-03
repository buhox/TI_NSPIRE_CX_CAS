# =============================================================================
# PANEL DE MANUAL — referencia de todos los comandos de la app
# =============================================================================

from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QGroupBox, QTextBrowser,
)
from PyQt5.QtGui import QTextCursor

_SECCIONES = [
    ("cas",       "🧮  CAS / Álgebra"),
    ("matrices",  "⬛  Matrices"),
    ("circuitos", "⚡  Circuitos AC/DC"),
    ("graficas",  "📈  Gráficas"),
    ("tibasic",   "💾  TI-Basic"),
    ("archivos",  "📁  Archivos"),
]

_HTML_MANUAL = """
<style>
  body { color:#c9d1d9; font-family:'Segoe UI','Ubuntu',sans-serif; font-size:13px; }
  h1 { color:#58a6ff; font-size:19px; }
  h2 { color:#58a6ff; font-size:16px; border-bottom:1px solid #21262d; padding-bottom:4px;
       margin-top:26px; }
  h3 { color:#7ee787; font-size:13px; margin-top:16px; }
  code { background:#161b22; color:#7ee787; padding:1px 5px; border-radius:3px;
         font-family:'Consolas','Courier New',monospace; }
  pre  { background:#161b22; color:#c9d1d9; padding:8px; border-radius:5px;
         border:1px solid #21262d; font-family:'Consolas','Courier New',monospace; }
  table { border-collapse:collapse; margin:8px 0 16px 0; }
  th, td { border:1px solid #21262d; padding:5px 10px; text-align:left; }
  th { background:#161b22; color:#58a6ff; }
  a { color:#58a6ff; }
  .nota { color:#8b949e; font-size:12px; }
</style>

<h1>Manual de comandos — TI-Nspire CX CAS (PC)</h1>
<p class="nota">Referencia de todo lo que se puede escribir o pulsar en la app.
Usa la lista de la izquierda para saltar de sección, o el buscador de arriba.</p>

<h2 id="cas">🧮 CAS / Álgebra</h2>
<p>Pestaña <b>CAS / Álgebra</b>: escribe la expresión en la consola (prompt <code>&gt;&gt;</code>)
y presiona Enter. El menú <b>Operación</b> decide cómo se interpreta lo que escribas.</p>
<table>
<tr><th>Operación del menú</th><th>Función</th><th>Ejemplo de entrada</th></tr>
<tr><td>Evaluar / Simplificar</td><td><code>evaluar</code></td><td><code>2+3</code> · <code>sin(pi/2)</code></td></tr>
<tr><td>Expandir</td><td><code>expandir</code></td><td><code>(x+1)^2</code></td></tr>
<tr><td>Factorizar</td><td><code>factorizar</code></td><td><code>x^2-4</code></td></tr>
<tr><td>Resolver (variable x)</td><td><code>resolver</code></td><td><code>x^2-4=0</code></td></tr>
<tr><td>Derivar (respecto a x)</td><td><code>derivar</code></td><td><code>x^3</code></td></tr>
<tr><td>Integrar (indefinida)</td><td><code>integrar</code></td><td><code>x^2</code></td></tr>
<tr><td>Integrar (definida)</td><td><code>integrar</code></td><td>usa los campos Punto/Orden como límites</td></tr>
<tr><td>Límite</td><td><code>limite</code></td><td>campo Punto = valor, campo Orden = dirección (+, -, +-)</td></tr>
<tr><td>Serie de Taylor</td><td><code>serie_taylor</code></td><td>campo Punto = centro, campo Orden = grado</td></tr>
<tr><td>Fracciones parciales</td><td><code>fracciones_parciales</code></td><td><code>1/(x^2-1)</code></td></tr>
<tr><td>Factores primos</td><td><code>factores_primos</code></td><td><code>360</code> → 2³×3²×5</td></tr>
<tr><td>Es primo</td><td><code>es_primo</code></td><td><code>17</code></td></tr>
</table>
<p><b>Símbolos TI que se traducen automáticamente:</b>
<code>^</code>→potencia, <code>√</code>→raíz, <code>π</code>→pi, <code>∞</code>→infinito,
<code>×</code>→<code>*</code>, <code>÷</code>→<code>/</code>. La multiplicación implícita
funciona: <code>2x</code> = <code>2*x</code>. Variables por defecto:
<code>x y z t n k a b c</code>.</p>
<p class="nota">Además de esas 12 operaciones, la consola reconoce por nombre las 20
fórmulas de Circuitos AC/DC — ver la sección de más abajo.</p>

<h2 id="matrices">⬛ Matrices</h2>
<p>Pestaña <b>Matrices</b>: define el tamaño, llena la tabla y pulsa el botón de
la operación que quieras.</p>
<table>
<tr><th>Botón</th><th>Qué hace</th></tr>
<tr><td>Determinante</td><td>Determinante de la matriz</td></tr>
<tr><td>Inversa</td><td>Matriz inversa (si existe)</td></tr>
<tr><td>Transpuesta</td><td>Transpuesta</td></tr>
<tr><td>Valores propios</td><td>Eigenvalues, con multiplicidad</td></tr>
<tr><td>Rango</td><td>Rango de la matriz</td></tr>
<tr><td>Escalonada</td><td>Forma escalonada reducida (RREF)</td></tr>
</table>

<h2 id="circuitos">⚡ Circuitos AC/DC</h2>
<p>No tienen pestaña propia: se invocan <b>desde la consola CAS</b> (pestaña
CAS/Álgebra, con <b>Evaluar / Simplificar</b> seleccionado), escribiendo la
fórmula como si fuera una llamada de función. Deja en blanco (o pon
<code>?</code>) el valor que quieres despejar.</p>
<pre>ley_ohm(v=12, i=2)              → R = 6 Ω
resistencia_paralelo(10,10)     → R equivalente = 5 Ω
impedancia(r=3, xl=4)           → Z = 5 Ω, ángulo = 53.1°
kirchhoff_corrientes(2,-1,?)    → I[2] = -1 A</pre>
<table>
<tr><th>Función</th><th>Fórmula</th><th>Sintaxis (clave=valor, deja una en blanco)</th></tr>
<tr><td><code>ley_ohm</code></td><td>V = I·R</td><td><code>v, i, r</code></td></tr>
<tr><td><code>resistencia_serie</code></td><td>R = R1+R2+…</td><td>valores por posición: <code>10,20,30</code></td></tr>
<tr><td><code>resistencia_paralelo</code></td><td>1/R = 1/R1+1/R2+…</td><td>valores por posición: <code>10,20</code></td></tr>
<tr><td><code>circuito_dc</code></td><td>V = E − I·R</td><td><code>e, i, r, v</code></td></tr>
<tr><td><code>potencia_dc</code></td><td>P = IV = I²R = V²/R</td><td><code>i, v, r</code> (dos cualesquiera)</td></tr>
<tr><td><code>calor_joule</code></td><td>W = P·t</td><td><code>t</code> + (<code>potencia</code> o <code>i,v,r</code>)</td></tr>
<tr><td><code>conductancia</code></td><td>G = 1/R</td><td><code>r, g</code></td></tr>
<tr><td><code>kirchhoff_corrientes</code></td><td>ΣI = 0</td><td>lista por posición, <code>?</code> en la incógnita</td></tr>
<tr><td><code>kirchhoff_voltajes</code></td><td>ΣV = 0</td><td>lista por posición, <code>?</code> en la incógnita</td></tr>
<tr><td><code>puente_wheatstone</code></td><td>R1·R4 = R2·R3</td><td><code>r1, r2, r3, r4</code></td></tr>
<tr><td><code>valor_instantaneo</code></td><td>x(t) = X0·sin(ωt+φ)</td><td><code>amplitud, t, frecuencia</code> u <code>omega</code>, <code>fase</code></td></tr>
<tr><td><code>valor_efectivo</code></td><td>Xrms = X0/√2</td><td><code>pico</code> o <code>rms</code></td></tr>
<tr><td><code>potencia_ac</code></td><td>P = Vrms·Irms·cosφ</td><td><code>v0/vrms, i0/irms, cos_phi</code></td></tr>
<tr><td><code>factor_potencia</code></td><td>cosφ = P/(Vrms·Irms)</td><td><code>p, vrms, irms, cos_phi</code></td></tr>
<tr><td><code>transformador</code></td><td>N1V2 = N2V1</td><td><code>n1, n2</code> + (<code>v1/v2</code> y/o <code>i1/i2</code>)</td></tr>
<tr><td><code>reactancia_inductiva</code></td><td>X_L = ωL = 2πfL</td><td><code>l, f/omega, x</code></td></tr>
<tr><td><code>reactancia_capacitiva</code></td><td>X_C = 1/(ωC)</td><td><code>c, f/omega, x</code></td></tr>
<tr><td><code>impedancia</code></td><td>Z = √(R²+(X_L−X_C)²)</td><td><code>r, xl, xc</code></td></tr>
<tr><td><code>frecuencia_natural</code></td><td>f0 = 1/(2π√(LC))</td><td><code>l, c, f0</code></td></tr>
<tr><td><code>oscilacion_electrica</code></td><td>½LI² + Q²/2C = cte</td><td><code>l, i, q, c, energia_total</code></td></tr>
</table>
<p class="nota">Portadas de la sección "AC & DC Circuits" (pág. 273) de la librería
científica de la Casio FX-880P. Documentado también en
<code>calculadora/circuitos.py</code>.</p>

<h2 id="graficas">📈 Gráficas</h2>
<p>Pestaña <b>Gráficas</b>: elige el modo con los botones superiores.</p>
<table>
<tr><th>Modo</th><th>Qué grafica</th></tr>
<tr><td>📈 2D — y(x)</td><td>Una o varias funciones y(x), con rango X/Y (o Auto) y resolución en puntos</td></tr>
<tr><td>🌐 3D — z(x,y)</td><td>Superficie z(x,y)</td></tr>
</table>
<p>Botones: <b>Graficar</b>, <b>Limpiar</b>, <b>Guardar PNG…</b> (exporta la gráfica actual).</p>

<h2 id="tibasic">💾 TI-Basic</h2>
<p>Pestaña <b>TI-Basic</b>: intérprete del TI-Basic de la TI-Nspire. Los programas
corren en el PC (Python), no se pueden subir a la calculadora — sirven para
escribir y depurar antes de teclearlos allí.</p>
<h3>Definir</h3>
<pre>Define f(x)=Func
  Return x^2+1
EndFunc

Define saluda()=Prgm
  Disp "hola"
EndPrgm</pre>
<h3>Variables</h3>
<table>
<tr><th>Qué</th><th>Sintaxis</th></tr>
<tr><td>Guardar</td><td><code>expr→var</code> · <code>var:=expr</code></td></tr>
<tr><td>Guardar en lista</td><td><code>valor→l[3]</code></td></tr>
<tr><td>Declarar local</td><td><code>Local a,b,c</code></td></tr>
<tr><td>Borrar</td><td><code>DelVar a,b</code></td></tr>
</table>
<h3>Control de flujo</h3>
<p><code>If/Then/ElseIf/Else/EndIf</code> · <code>For i,1,10,2/EndFor</code> ·
<code>While/EndWhile</code> · <code>Loop/EndLoop</code> · <code>Try/Else/EndTry</code> ·
<code>Exit</code> (sale del bucle) · <code>Cycle</code> (siguiente vuelta) ·
<code>Lbl</code>/<code>Goto</code> · <code>Return</code> · <code>Stop</code> ·
<code>ClrErr</code> · <code>PassErr</code></p>
<h3>Entrada y salida</h3>
<table>
<tr><th>Comando</th><th>Qué hace</th></tr>
<tr><td><code>Disp expr[,expr…]</code></td><td>Muestra los valores</td></tr>
<tr><td><code>Text expr</code></td><td>Igual que Disp en este panel</td></tr>
<tr><td><code>Request "texto",var</code></td><td>Pide un valor, lo evalúa como expresión</td></tr>
<tr><td><code>RequestStr "texto",var</code></td><td>Pide un valor, lo guarda como cadena</td></tr>
<tr><td><code>Input [prompt,]var</code></td><td>Como Request</td></tr>
<tr><td><code>Pause [expr]</code></td><td>Muestra y espera</td></tr>
<tr><td><code>ClrIO</code> / <code>ClrHome</code></td><td>Limpia la pantalla</td></tr>
</table>
<h3>Operadores</h3>
<p>Aritméticos <code>+ - * / ^</code>, <code>√(x)</code>, <code>x²</code> ·
Comparación <code>= ≠ &lt; &gt; ≤ ≥</code> (<code>=</code> compara, <code>→</code> guarda) ·
Lógicos <code>and or not xor</code> · Cadenas <code>&amp;</code> concatena</p>
<h3>Listas, cadenas y matrices (se indexan desde 1)</h3>
<pre>{4,8,15}→l        "Nspire"→s          [[1,2][3,4]]→m
Disp l[1]  © 4     Disp s[1]  © N      Disp m[2,1]  © 3
Disp dim(l)  © 3   Disp mid(s,2,3)  © spi</pre>
<h3>Funciones disponibles</h3>
<table>
<tr><th>Categoría</th><th>Funciones</th></tr>
<tr><td>Números</td><td><code>abs root ln log exp int iPart fPart round floor ceiling sign mod remain gcd lcm nCr nPr factorial approx</code></td></tr>
<tr><td>Trigonometría (radianes)</td><td><code>sin cos tan arcsin arccos arctan sinh cosh tanh</code> (también <code>sin⁻¹ cos⁻¹ tan⁻¹</code>)</td></tr>
<tr><td>Listas</td><td><code>dim sum product mean max min augment sortA sortD left right</code></td></tr>
<tr><td>Cadenas</td><td><code>dim left right mid inString char ord</code></td></tr>
<tr><td>Otras</td><td><code>when(cond,a,b)</code> · <code>rand([n])</code> · <code>randInt(a,b[,n])</code></td></tr>
<tr><td>Constantes</td><td><code>pi</code> (o <code>π</code>), <code>e</code>, <code>true</code>, <code>false</code>, <code>undef</code>, <code>infinity</code> (<code>∞</code>)</td></tr>
</table>
<p class="nota"><code>©</code> o <code>//</code> comienzan un comentario. <code>:</code>
separa varias sentencias en una línea. No hay CAS simbólico ni gráficos dentro de
TI-Basic — para eso están las pestañas CAS y Gráficas.</p>

<h2 id="archivos">📁 Archivos</h2>
<p>Pestaña <b>Archivos</b>: gestión de la calculadora conectada por USB.</p>
<table>
<tr><th>Botón</th><th>Qué hace</th></tr>
<tr><td>🔌 Conectar / ⛔ Desconectar</td><td>Abre o cierra la sesión con la calculadora</td></tr>
<tr><td>🔄 Actualizar</td><td>Refresca el listado de archivos</td></tr>
<tr><td>→ / ←</td><td>Enviar / recibir el archivo seleccionado</td></tr>
<tr><td>📁+ Carpeta</td><td>Crea una carpeta en la calculadora</td></tr>
<tr><td>✏️ Renombrar</td><td>Renombra el archivo seleccionado</td></tr>
<tr><td>🗑 Eliminar</td><td>Borra el archivo seleccionado de la calculadora</td></tr>
<tr><td>📷 Captura</td><td>Captura la pantalla de la calculadora (RGB888, 320×240) y permite guardarla como PNG</td></tr>
<tr><td>⚙ Actualizar OS…</td><td>Reinstala el sistema operativo — <b>operación de riesgo</b>,
    valida el archivo y la batería antes de empezar. Ver nota abajo.</td></tr>
</table>
<p class="nota">El flasheo de OS está implementado pero nunca se ha ejecutado contra
hardware real: falta una imagen <code>.tcc</code> oficial. Ver <code>CLAUDE.md</code>.</p>
"""


class PanelManual(QWidget):
    """Manual de referencia: todos los comandos disponibles en la app."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        barra = QHBoxLayout()
        self._buscador = QLineEdit()
        self._buscador.setPlaceholderText("Buscar un comando…")
        self._buscador.returnPressed.connect(self._buscar_siguiente)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self._buscar_siguiente)
        barra.addWidget(self._buscador, 1)
        barra.addWidget(btn_buscar)
        root.addLayout(barra)

        cuerpo = QHBoxLayout()

        grp_indice = QGroupBox("Secciones")
        grp_indice.setMaximumWidth(210)
        lay_indice = QVBoxLayout(grp_indice)
        self._indice = QListWidget()
        self._indice.addItems([nombre for _, nombre in _SECCIONES])
        self._indice.currentRowChanged.connect(self._ir_a_seccion)
        lay_indice.addWidget(self._indice)
        cuerpo.addWidget(grp_indice)

        self._texto = QTextBrowser()
        self._texto.setOpenExternalLinks(False)
        self._texto.setHtml(_HTML_MANUAL)
        cuerpo.addWidget(self._texto, 1)

        root.addLayout(cuerpo, 1)

    def _ir_a_seccion(self, indice: int):
        if indice < 0:
            return
        ancla, _ = _SECCIONES[indice]
        self._texto.scrollToAnchor(ancla)

    def _buscar_siguiente(self):
        texto = self._buscador.text().strip()
        if not texto:
            return
        if not self._texto.find(texto):
            # No se encontró desde el cursor actual: reinicia desde el principio
            cursor = self._texto.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self._texto.setTextCursor(cursor)
            self._texto.find(texto)
