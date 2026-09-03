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
    ("campos",    "🧲  Campos eléc./magn."),
    ("movimiento", "🚀  Movimiento y energía"),
    ("ondas",     "🌊  Ondas"),
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
<p>En la consola va <b>solo la expresión</b>, sin el nombre de la operación: la
operación se elige en el menú y los datos extra (variable, límites, punto, orden)
van en los campos de <b>Parámetros</b>, debajo del menú.</p>
<table>
<tr><th>Operación del menú</th><th>Qué escribes en la consola</th><th>Campos de Parámetros que usa</th><th>Resultado</th></tr>
<tr><td>Evaluar / Simplificar</td><td><code>2+3</code><br><code>sin(pi/2)</code><br><code>sqrt(18)</code></td><td>ninguno</td><td>5 · 1 · 3√2</td></tr>
<tr><td>Expandir</td><td><code>(x+1)^2</code></td><td>ninguno</td><td>x² + 2x + 1</td></tr>
<tr><td>Factorizar</td><td><code>x^2-4</code></td><td>ninguno</td><td>(x−2)(x+2)</td></tr>
<tr><td>Resolver</td><td><code>x^2-4</code><br><code>x^2-4=0</code><br><code>x+y=5, x-y=1</code> (sistema)</td><td><b>Variable</b> = <code>x</code><br>o <code>x,y</code> para un sistema</td><td>[−2, 2]<br>{x: 3, y: 2}</td></tr>
<tr><td>Derivar</td><td><code>x^3</code><br><code>sin(x)*x^2</code></td><td><b>Variable</b> = <code>x</code></td><td>3x²</td></tr>
<tr><td>Integrar (indefinida)</td><td><code>x^2</code></td><td><b>Variable</b> = <code>x</code></td><td>x³/3</td></tr>
<tr><td>Integrar (definida)</td><td><code>x^2</code></td><td><b>Variable</b>=<code>x</code>, <b>Desde</b>=<code>0</code>, <b>Hasta</b>=<code>1</code></td><td>1/3</td></tr>
<tr><td>Límite</td><td><code>sin(x)/x</code></td><td><b>Variable</b>=<code>x</code>, <b>Punto</b>=<code>0</code>, <b>Dir +-</b>=<code>+-</code></td><td>1</td></tr>
<tr><td>Serie de Taylor</td><td><code>exp(x)</code></td><td><b>Variable</b>=<code>x</code>, <b>Punto</b>=<code>0</code>, <b>Orden</b>=<code>6</code></td><td>1+x+x²/2+…</td></tr>
<tr><td>Fracciones parciales</td><td><code>1/(x^2-1)</code></td><td><b>Variable</b> = <code>x</code></td><td>−1/(2(x+1)) + 1/(2(x−1))</td></tr>
<tr><td>Factores primos</td><td><code>360</code> (solo un entero)</td><td>ninguno</td><td>2³ × 3² × 5</td></tr>
<tr><td>Es primo</td><td><code>17</code> (solo un entero)</td><td>ninguno</td><td>17 es primo</td></tr>
</table>
<p><b>Detalles de los campos de Parámetros:</b></p>
<table>
<tr><th>Campo</th><th>Qué acepta</th></tr>
<tr><td><b>Variable</b></td><td>El nombre de la variable respecto a la que se opera: <code>x</code>, <code>y</code>, <code>t</code>… (por defecto <code>x</code>)</td></tr>
<tr><td><b>Desde</b> / <b>Hasta</b></td><td>Límites de la integral definida. Admiten expresiones: <code>0</code>, <code>pi</code>, <code>2*pi</code>, <code>oo</code> (infinito)</td></tr>
<tr><td><b>Punto</b></td><td>Dónde se evalúa el límite o dónde se centra la serie: <code>0</code>, <code>1</code>, <code>pi/2</code>, <code>oo</code></td></tr>
<tr><td><b>Dir +-</b></td><td>Dirección del límite: <code>+</code> (por la derecha), <code>-</code> (por la izquierda) o <code>+-</code> (bilateral, por defecto)</td></tr>
<tr><td><b>Orden</b></td><td>Grado de la serie de Taylor (por defecto <code>6</code>)</td></tr>
</table>
<p><b>Símbolos TI que se traducen automáticamente:</b>
<code>^</code>→potencia, <code>√</code>→raíz, <code>π</code>→pi, <code>∞</code>→infinito,
<code>×</code>→<code>*</code>, <code>÷</code>→<code>/</code>. La multiplicación implícita
funciona: <code>2x</code> = <code>2*x</code>. Variables por defecto:
<code>x y z t n k a b c</code>.</p>
<p><b>Escribir sin nombre de operación no siempre alcanza:</b> además de esas 12
operaciones del menú, la consola reconoce por nombre las <b>77 fórmulas de física</b>
de las secciones de Circuitos, Campos, Movimiento y Ondas — esas sí se escriben como
llamada de función, ej. <code>ley_ohm(v=12, i=2)</code>, y no dependen del menú
(basta con tener seleccionado "Evaluar / Simplificar").</p>
<p class="nota">En un sistema de ecuaciones, si el campo Variable nombra menos
incógnitas que ecuaciones, se resuelve para todas las que aparezcan.</p>

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

<h3>RC de primer orden (elige el orden de los elementos)</h3>
<p><code>circuito_rc_primer_orden</code> — no es de la librería FX-880P, es el
análisis completo de un RC serie. El parámetro <code>orden</code> decide qué
elemento va primero desde la fuente, es decir dónde se toma la salida:</p>
<table>
<tr><th>orden</th><th>Circuito</th><th>Salida en</th><th>Comportamiento</th></tr>
<tr><td><code>RC</code></td><td>fuente → R → C</td><td>el capacitor</td><td>pasa-bajos / integrador</td></tr>
<tr><td><code>CR</code></td><td>fuente → C → R</td><td>la resistencia</td><td>pasa-altos / diferenciador</td></tr>
</table>
<p>Parámetros: <code>r, c, v_fuente, orden</code> (por defecto <code>RC</code>) +
opcionalmente <code>t, v0</code> para la respuesta al escalón v(t), y/o
<code>f</code> para la respuesta en frecuencia (ganancia, dB y fase) en ese
punto. Siempre calcula τ = R·C y la frecuencia de corte fc = 1/(2πτ).</p>
<pre>circuito_rc_primer_orden(r=1000, c=1e-6, v_fuente=5, orden=RC, t=0.001)
  → τ = 0.001 s, fc = 159.155 Hz, v(t=0.001 s) = 3.1606 V

circuito_rc_primer_orden(r=1000, c=1e-6, v_fuente=5, orden=CR, f=159.155)
  → |H| = 0.707107 (-3.01 dB), fase = 45°</pre>

<h3>RLC de segundo orden (elige el elemento de salida)</h3>
<p><code>circuito_rlc_segundo_orden</code> — circuito serie fuente–R–L–C ante un
escalón Vs. El parámetro <code>salida</code> elige qué elemento se observa:</p>
<table>
<tr><th>salida</th><th>Voltaje observado</th><th>Comportamiento</th></tr>
<tr><td><code>C</code></td><td>en el capacitor</td><td>pasa-bajos</td></tr>
<tr><td><code>R</code></td><td>en la resistencia (∝ la corriente)</td><td>pasa-banda</td></tr>
<tr><td><code>L</code></td><td>en el inductor</td><td>pasa-altos</td></tr>
</table>
<p>Parámetros: <code>r, l, c, v_fuente, salida</code> (por defecto <code>C</code>) +
opcionalmente <code>t, v0, i0</code> para la respuesta al escalón v(t), y/o
<code>f</code> para la respuesta en frecuencia. Siempre calcula ω0=1/√(LC), α=R/(2L),
ζ=α/ω0, Q=1/(2ζ) y el régimen: <b>subamortiguado</b> (ζ&lt;1, oscila),
<b>críticamente amortiguado</b> (ζ=1) o <b>sobreamortiguado</b> (ζ&gt;1, no oscila).</p>
<pre>circuito_rlc_segundo_orden(r=20, l=0.1, c=100e-6, v_fuente=10, salida=C, t=0.006)
  → ζ=0.316 (subamortiguado), v_out=9.47 V [vC=9.47 V, vR=3.56 V, vL=-3.03 V, i=0.178 A]

circuito_rlc_segundo_orden(r=20, l=0.1, c=100e-6, v_fuente=10, salida=R, f=50.33)
  → en f0 la salida en R tiene ganancia 1 (pasa todo); en C o en L, ganancia = Q</pre>
<p class="nota">Verificado integrando numéricamente la ecuación diferencial del
circuito (SciPy) en los tres regímenes de amortiguamiento — coincide hasta 10⁻¹⁰.</p>

<h2 id="campos">🧲 Campos eléctricos y magnéticos</h2>
<p>Las 17 fórmulas de la sección 5 de la librería FX-880P (pág. 274). Se invocan
igual, desde la consola CAS. Las constantes (ε₀, μ₀, k₀, carga y masa del
electrón) salen de <code>scipy.constants</code>, con los valores CODATA
actuales en vez de los redondeos del manual de 1990.</p>
<pre>ley_coulomb_electrica(q1=1e-6, q2=2e-6, r=0.05)   → F = 7.19 N
electron_campo_electrico(v_aceleracion=1)          → v = 593097 m/s
capacidad_serie(10e-6, 20e-6)                      → C = 6.67 µF
autoinduccion(l=0.1, delta_i=2, delta_t=0.01)      → V = -20 V</pre>
<table>
<tr><th>Función</th><th>Fórmula</th><th>Parámetros (deja en blanco la incógnita)</th></tr>
<tr><td><code>ley_coulomb_electrica</code></td><td>F = k₀·Q₁Q₂/r²</td><td><code>f, q1, q2, r</code></td></tr>
<tr><td><code>campo_electrico</code></td><td>E = V/d; F = QE; W = QV</td><td><code>e, v, d</code> + opcional <code>q</code></td></tr>
<tr><td><code>capacidad_electrica</code></td><td>Q = C·V</td><td><code>c, q, v</code></td></tr>
<tr><td><code>capacidad_placas</code></td><td>C = ε_r·ε₀·A/d</td><td><code>area, d, epsilon_r</code></td></tr>
<tr><td><code>capacidad_paralelo</code></td><td>C = C1+C2+…</td><td>valores por posición</td></tr>
<tr><td><code>capacidad_serie</code></td><td>1/C = 1/C1+1/C2+…</td><td>valores por posición</td></tr>
<tr><td><code>constante_dielectrica</code></td><td>D = ε·E; C = ε_r·C₀</td><td><code>epsilon_r</code> + opcional <code>e, c0</code></td></tr>
<tr><td><code>energia_electrostatica</code></td><td>W = ½CV² = ½QV = Q²/2C</td><td><code>c, v, q</code> (dos cualesquiera)</td></tr>
<tr><td><code>electron_campo_electrico</code></td><td>½mv² = qV</td><td><code>v_aceleracion</code> + opcional <code>carga, masa</code></td></tr>
<tr><td><code>ley_coulomb_magnetica</code></td><td>F = k_m·m₁m₂/r²</td><td><code>f, m1, m2, r</code></td></tr>
<tr><td><code>campo_magnetico_hilo</code></td><td>H = I/(2πr); B = μ₀H</td><td><code>i, r, h</code></td></tr>
<tr><td><code>campo_magnetico_solenoide</code></td><td>H = N·I/L; B = μ_r·μ₀·H</td><td><code>i, vueltas, longitud, mu_r</code></td></tr>
<tr><td><code>flujo_magnetico</code></td><td>Φ = B·A·cos(θ)</td><td><code>flujo, b, area, angulo</code></td></tr>
<tr><td><code>fuerza_lorentz</code></td><td>F = QvB·sen(θ); r = mv/QB</td><td><code>q, v, b, angulo</code> + opcional <code>masa</code></td></tr>
<tr><td><code>electron_campo_magnetico</code></td><td>ω = QB/m; r = mv/QB</td><td><code>b</code> + opcional <code>v, carga, masa</code></td></tr>
<tr><td><code>ley_faraday</code></td><td>V = −N·ΔΦ/Δt</td><td><code>delta_flujo, delta_t, vueltas</code></td></tr>
<tr><td><code>induccion_electromagnetica</code></td><td>V = B·L·v</td><td><code>b, longitud, v, fem</code></td></tr>
<tr><td><code>induccion_mutua</code></td><td>V = −M·ΔI/Δt</td><td><code>m, delta_i, delta_t, v</code></td></tr>
<tr><td><code>autoinduccion</code></td><td>V = −L·ΔI/Δt</td><td><code>l, delta_i, delta_t, v</code></td></tr>
</table>
<p class="nota">El OCR del manual llegó ilegible en varias de estas fórmulas, así
que están escritas en su forma estándar SI y verificadas contra valores de
referencia conocidos (k₀, ε₀, el electrón a 1 V = 5.93×10⁵ m/s, el ciclotrón
del electrón en 1 T = 27.99 GHz).</p>

<h2 id="movimiento">🚀 Movimiento y energía</h2>
<p>Las 20 fórmulas de la sección 1 de física de la librería FX-880P (pág. 270).
Constantes g y G desde <code>scipy.constants</code>.</p>
<pre>movimiento_acelerado(v0=0, a=9.81, t=3)      → v = 29.4 m/s, s = 44.1 m
pendulo_simple(longitud=1)                    → T = 2.006 s
ley_kepler(t1=1, r1=1, r2=1.524)              → T2 = 1.881 años (Marte)
velocidad_orbital(m_central=5.972e24, r=6.771e6) → v = 7672 m/s, T = 92 min
conservacion_momento(m1=2, m2=1, v1i=3, v2i=0, v1f=2)  → v2f = 2 m/s</pre>
<table>
<tr><th>Función</th><th>Fórmula</th><th>Parámetros (deja en blanco la incógnita)</th></tr>
<tr><td><code>movimiento_acelerado</code></td><td>v=v₀+at; s=v₀t+½at²; v²=v₀²+2as</td><td><code>v0, a, t, v, s</code> — da tres, deduce el resto</td></tr>
<tr><td><code>segunda_ley_newton</code></td><td>F = m·a</td><td><code>f, m, a</code></td></tr>
<tr><td><code>movimiento_circular</code></td><td>v=ωr; a_c=v²/r; T=2π/ω</td><td><code>r</code> + <code>v</code> u <code>omega</code>, opcional <code>m</code></td></tr>
<tr><td><code>oscilacion_armonica</code></td><td>x=A·sen(ωt+φ)</td><td><code>amplitud, omega, t, fase</code></td></tr>
<tr><td><code>ley_hooke</code></td><td>F = k·x</td><td><code>f, k, x</code></td></tr>
<tr><td><code>oscilacion_resorte</code></td><td>T = 2π√(m/k)</td><td><code>m, k, periodo</code></td></tr>
<tr><td><code>pendulo_simple</code></td><td>T = 2π√(L/g)</td><td><code>longitud, periodo, g</code></td></tr>
<tr><td><code>energia_potencial</code></td><td>Ep = m·g·h</td><td><code>m, h, energia, g</code></td></tr>
<tr><td><code>energia_elastica</code></td><td>Ep = ½k·x²</td><td><code>k, x, energia</code></td></tr>
<tr><td><code>energia_cinetica</code></td><td>Ek = ½m·v²</td><td><code>m, v, energia</code></td></tr>
<tr><td><code>coeficiente_friccion</code></td><td>F = μ·N</td><td><code>f, mu, n</code></td></tr>
<tr><td><code>trabajo</code></td><td>W = F·s·cos(θ)</td><td><code>f, s, w, angulo</code></td></tr>
<tr><td><code>ley_kepler</code></td><td>T²/r³ = constante</td><td><code>t1, r1, t2, r2</code></td></tr>
<tr><td><code>gravitacion_universal</code></td><td>F = G·m₁m₂/r²</td><td><code>f, m1, m2, r</code></td></tr>
<tr><td><code>energia_potencial_gravitatoria</code></td><td>Ep = −G·m₁m₂/r</td><td><code>m1, m2, r</code></td></tr>
<tr><td><code>velocidad_orbital</code></td><td>v = √(GM/r); T = 2πr/v</td><td><code>m_central, r</code> + opcional <code>m_satelite</code></td></tr>
<tr><td><code>momento_inercia</code></td><td>I = c·m·r²</td><td><code>m, r, forma</code></td></tr>
<tr><td><code>momento_angular</code></td><td>L = I·ω  o  L = m·v·r</td><td><code>i, omega, l</code>  o  <code>m, v, r</code></td></tr>
<tr><td><code>conservacion_momento</code></td><td>m₁v₁ᵢ+m₂v₂ᵢ = m₁v₁f+m₂v₂f</td><td><code>m1, m2, v1i, v2i, v1f, v2f</code></td></tr>
</table>
<p><b>Formas de <code>momento_inercia</code></b>: <code>puntual</code>, <code>aro</code>,
<code>disco</code>, <code>cilindro</code>, <code>esfera</code>, <code>esfera_hueca</code>,
<code>varilla_centro</code>, <code>varilla_extremo</code> (en las varillas, r es la longitud).</p>
<p class="nota"><code>conservacion_momento</code> además compara la energía cinética
antes y después, y dice si el choque fue elástico o inelástico. Verificado contra
valores de libro: péndulo de 1 m = 2.006 s, Kepler da Marte = 1.881 años, órbita
de 400 km = 7.67 km/s y 92 min de periodo.</p>

<h2 id="ondas">🌊 Ondas</h2>
<p>Las 16 fórmulas de la sección 2 de física de la librería FX-880P (pág. 272),
desde ondas mecánicas hasta física cuántica. Constantes h, c y masa del electrón
desde <code>scipy.constants</code>.</p>
<pre>velocidad_sonido(temperatura=25)                      → 346.8 m/s
efecto_doppler(f_fuente=1000, v_fuente=30)            → 1095 Hz (se acerca)
angulo_critico(n1=1.33)                               → θc = 48.75° (agua-aire)
efecto_fotoelectrico(trabajo_ev=2.28, longitud_onda=400e-9) → Ek = 0.82 eV
onda_luminosa(longitud_onda=500e-9)                   → 2.48 eV</pre>
<table>
<tr><th>Función</th><th>Fórmula</th><th>Parámetros (deja en blanco la incógnita)</th></tr>
<tr><td><code>onda</code></td><td>v = λ·f</td><td><code>v, longitud_onda, frecuencia</code></td></tr>
<tr><td><code>onda_viajera</code></td><td>y = A·sen[2π(t/T − x/λ)]</td><td><code>amplitud, longitud_onda, periodo, x, t</code></td></tr>
<tr><td><code>velocidad_cuerda</code></td><td>v = √(F/μ)</td><td><code>tension, densidad_lineal, v</code></td></tr>
<tr><td><code>interferencia</code></td><td>Δl = nλ (constr.) · (n+½)λ (destr.)</td><td><code>diferencia_camino, longitud_onda, n, tipo</code></td></tr>
<tr><td><code>onda_estacionaria</code></td><td>L = nλ/2  ·  L = (2n−1)λ/4</td><td><code>longitud, longitud_onda, n, extremos, v</code></td></tr>
<tr><td><code>refraccion</code></td><td>n₁·sen(θ₁) = n₂·sen(θ₂)</td><td><code>theta1, theta2, n1, n2, v1</code></td></tr>
<tr><td><code>frecuencia_natural_cuerda</code></td><td>f = (n/2L)·√(F/μ)</td><td><code>longitud, tension, densidad_lineal, n</code></td></tr>
<tr><td><code>velocidad_sonido</code></td><td>v = 331.5 + 0.61·T</td><td><code>temperatura</code> (°C)</td></tr>
<tr><td><code>efecto_doppler</code></td><td>f' = f·(v+v_obs)/(v−v_fuente)</td><td><code>f_fuente, v_observador, v_fuente, v_sonido, temperatura</code></td></tr>
<tr><td><code>batido</code></td><td>f = |f₁ − f₂|</td><td><code>f1, f2</code></td></tr>
<tr><td><code>reflectividad</code></td><td>R = ((n₁−n₂)/(n₁+n₂))²</td><td><code>n1, n2</code></td></tr>
<tr><td><code>angulo_critico</code></td><td>sen(θc) = n₂/n₁</td><td><code>n1, n2</code></td></tr>
<tr><td><code>onda_de_broglie</code></td><td>λ = h/(m·v)</td><td><code>masa, velocidad, longitud_onda</code></td></tr>
<tr><td><code>condicion_cuantica</code></td><td>2πr = nλ; m·v·r = n·ħ</td><td><code>n, masa, velocidad, r</code></td></tr>
<tr><td><code>efecto_fotoelectrico</code></td><td>h·ν = W + Ek_máx</td><td><code>trabajo_ev</code> + <code>longitud_onda</code> o <code>frecuencia</code></td></tr>
<tr><td><code>condicion_frecuencia</code></td><td>h·ν = Em − En</td><td><code>em_ev, en_ev, frecuencia, longitud_onda</code></td></tr>
<tr><td><code>onda_luminosa</code></td><td>λ = c/ν;  E = h·ν</td><td>uno de <code>longitud_onda, frecuencia, energia_ev</code></td></tr>
</table>
<p class="nota"><code>interferencia</code> deduce sola si el patrón es constructivo,
destructivo o parcial cuando le das Δl y λ. <code>onda_estacionaria</code> distingue
extremos <code>fijos</code> (L=nλ/2) de un extremo <code>libre</code> (L=(2n−1)λ/4).
Verificado contra valores de libro: Snell 30°→22.08° al agua, ángulo crítico
agua-aire 48.75°, radio de Bohr 0.529 Å, Balmer α 656 nm, fotón de 500 nm = 2.48 eV.</p>

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
