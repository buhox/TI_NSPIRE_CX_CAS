# =============================================================================
# CAMPOS ELÉCTRICOS Y MAGNÉTICOS — librería FX-880P, sección 5 (pág. 274)
# Las 17 fórmulas de esa sección, en forma estándar SI.
#
# El OCR del manual de 1990 llegó ilegible en varias de estas fórmulas, así que
# están escritas en su forma estándar de física, y las constantes se toman de
# `scipy.constants` (valores CODATA actuales) en vez de los redondeos del
# manual (k0 = 9×10⁹, etc.).
#
# Igual que en circuitos.py: se dan los valores conocidos y se deja en None la
# incógnita a despejar.
# =============================================================================

from __future__ import annotations
import logging
import math
from typing import Optional

from scipy import constants

from .formulas import REGISTRO, ResultadoFormula

logger = logging.getLogger("ti_nspire.campos")

# Constantes (CODATA, vía scipy.constants)
EPSILON_0 = constants.epsilon_0          # permitividad del vacío, F/m
MU_0      = constants.mu_0               # permeabilidad del vacío, H/m
K_E       = 1 / (4 * math.pi * EPSILON_0)   # constante de Coulomb eléctrica, N·m²/C²
K_M       = MU_0 / (4 * math.pi)            # constante de Coulomb magnética
CARGA_E   = constants.e                  # carga elemental, C
MASA_E    = constants.m_e                # masa del electrón, kg


def _falta_una(pares) -> list:
    """Nombres de los valores que vienen en None."""
    return [n for n, val in pares if val is None]


# ── 1. Ley de Coulomb (campo eléctrico) ──────────────────────────────────────

def ley_coulomb_electrica(f: Optional[float] = None, q1: Optional[float] = None,
                           q2: Optional[float] = None, r: Optional[float] = None
                           ) -> ResultadoFormula:
    """Ley de Coulomb: F = k₀·Q₁·Q₂/r². Da tres valores y deja el cuarto en None."""
    faltantes = _falta_una((("f", f), ("q1", q1), ("q2", q2), ("r", r)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (F, Q1, Q2, r) y deja el cuarto en None")
    try:
        if f is None:
            f = K_E * q1 * q2 / r ** 2
        elif q1 is None:
            q1 = f * r ** 2 / (K_E * q2)
        elif q2 is None:
            q2 = f * r ** 2 / (K_E * q1)
        else:
            r = math.sqrt(abs(K_E * q1 * q2 / f))
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa ceros y signos)")
    return ResultadoFormula({"f": f, "q1": q1, "q2": q2, "r": r},
                             texto=f"F = {f:.6g} N (Q1={q1:.6g} C, Q2={q2:.6g} C, r={r:.6g} m)")


# ── 2. Campo eléctrico ───────────────────────────────────────────────────────

def campo_electrico(e: Optional[float] = None, v: Optional[float] = None,
                     d: Optional[float] = None, q: Optional[float] = None
                     ) -> ResultadoFormula:
    """
    Campo eléctrico uniforme: E = V/d. Si además se da la carga Q, calcula la
    fuerza F = Q·E y el trabajo W = Q·V.
    """
    faltantes = _falta_una((("e", e), ("v", v), ("d", d)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (E, V, d) y deja el tercero en None")
    try:
        if e is None:
            e = v / d
        elif v is None:
            v = e * d
        else:
            d = v / e
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")

    valores = {"e": e, "v": v, "d": d}
    lineas = [f"E = V/d = {e:.6g} V/m (V={v:.6g} V, d={d:.6g} m)"]
    if q is not None:
        fuerza = q * e
        trabajo = q * v
        valores.update(q=q, f=fuerza, w=trabajo)
        lineas.append(f"F = Q·E = {fuerza:.6g} N,  W = Q·V = {trabajo:.6g} J")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 3. Capacidad eléctrica ───────────────────────────────────────────────────

def capacidad_electrica(c: Optional[float] = None, q: Optional[float] = None,
                         v: Optional[float] = None) -> ResultadoFormula:
    """Capacidad: Q = C·V. Da dos valores y deja el tercero en None."""
    faltantes = _falta_una((("c", c), ("q", q), ("v", v)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (C, Q, V) y deja el tercero en None")
    try:
        if q is None:
            q = c * v
        elif c is None:
            c = q / v
        else:
            v = q / c
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"c": c, "q": q, "v": v},
                             texto=f"C = {c:.6g} F, Q = {q:.6g} C, V = {v:.6g} V")


def capacidad_placas(area: float, d: float, epsilon_r: float = 1.0) -> ResultadoFormula:
    """Capacitor de placas paralelas: C = ε_r·ε₀·A/d."""
    if area <= 0 or d <= 0 or epsilon_r <= 0:
        return ResultadoFormula(error="Área, distancia y ε_r deben ser mayores que cero")
    c = epsilon_r * EPSILON_0 * area / d
    return ResultadoFormula({"c": c, "area": area, "d": d, "epsilon_r": epsilon_r},
                             texto=f"C = ε_r·ε₀·A/d = {c:.6g} F")


# ── 4. Capacidad en serie y paralelo ─────────────────────────────────────────

def capacidad_paralelo(*capacidades: float) -> ResultadoFormula:
    """Capacitores en paralelo: C = C1 + C2 + ..."""
    if len(capacidades) < 2:
        return ResultadoFormula(error="Da al menos dos capacidades")
    c = sum(capacidades)
    return ResultadoFormula({"c": c}, texto=f"C equivalente = {c:.6g} F")


def capacidad_serie(*capacidades: float) -> ResultadoFormula:
    """Capacitores en serie: 1/C = 1/C1 + 1/C2 + ..."""
    if len(capacidades) < 2:
        return ResultadoFormula(error="Da al menos dos capacidades")
    if any(x == 0 for x in capacidades):
        return ResultadoFormula(error="Ninguna capacidad puede ser 0")
    c = 1 / sum(1 / x for x in capacidades)
    return ResultadoFormula({"c": c}, texto=f"C equivalente = {c:.6g} F")


# ── 5. Constante dieléctrica ─────────────────────────────────────────────────

def constante_dielectrica(epsilon_r: float, e: Optional[float] = None,
                           c0: Optional[float] = None) -> ResultadoFormula:
    """
    Dieléctrico de permitividad relativa ε_r: el desplazamiento es D = ε_r·ε₀·E
    y la capacidad pasa de C₀ (en vacío) a C = ε_r·C₀.
    """
    if epsilon_r <= 0:
        return ResultadoFormula(error="ε_r debe ser mayor que cero")
    valores = {"epsilon_r": epsilon_r, "epsilon": epsilon_r * EPSILON_0}
    lineas = [f"ε = ε_r·ε₀ = {valores['epsilon']:.6g} F/m"]
    if e is not None:
        d_desp = epsilon_r * EPSILON_0 * e
        valores.update(e=e, d=d_desp)
        lineas.append(f"D = ε·E = {d_desp:.6g} C/m²")
    if c0 is not None:
        c = epsilon_r * c0
        valores.update(c0=c0, c=c)
        lineas.append(f"C = ε_r·C₀ = {c:.6g} F")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 6. Energía electrostática ────────────────────────────────────────────────

def energia_electrostatica(c: Optional[float] = None, v: Optional[float] = None,
                            q: Optional[float] = None) -> ResultadoFormula:
    """
    Energía almacenada en un capacitor: W = ½CV² = ½QV = Q²/(2C).
    Da dos cualesquiera de C, V, Q.
    """
    conocidos = sum(x is not None for x in (c, v, q))
    if conocidos < 2:
        return ResultadoFormula(error="Da al menos dos valores entre C, V, Q")
    try:
        if c is not None and v is not None:
            w = 0.5 * c * v ** 2
            if q is None:
                q = c * v
        elif q is not None and v is not None:
            w = 0.5 * q * v
            c = q / v
        else:
            w = q ** 2 / (2 * c)
            v = q / c
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"w": w, "c": c, "v": v, "q": q},
                             texto=f"W = {w:.6g} J (C={c:.6g} F, V={v:.6g} V, Q={q:.6g} C)")


# ── 7. Electrón en un campo eléctrico ────────────────────────────────────────

def electron_campo_electrico(v_aceleracion: float, carga: Optional[float] = None,
                              masa: Optional[float] = None) -> ResultadoFormula:
    """
    Partícula acelerada por una diferencia de potencial: ½·m·v² = q·V,
    de donde v = √(2qV/m). Por defecto usa la carga y la masa del electrón.
    """
    carga = CARGA_E if carga is None else carga
    masa = MASA_E if masa is None else masa
    if masa <= 0:
        return ResultadoFormula(error="La masa debe ser mayor que cero")
    energia = carga * v_aceleracion
    if energia < 0:
        return ResultadoFormula(error="q·V es negativo: la partícula no se acelera con ese signo")
    velocidad = math.sqrt(2 * energia / masa)
    return ResultadoFormula({"v_aceleracion": v_aceleracion, "carga": carga, "masa": masa,
                              "energia": energia, "velocidad": velocidad},
                             texto=f"Ec = q·V = {energia:.6g} J,  v = √(2qV/m) = {velocidad:.6g} m/s")


# ── 8. Ley de Coulomb (campo magnético) ──────────────────────────────────────

def ley_coulomb_magnetica(f: Optional[float] = None, m1: Optional[float] = None,
                           m2: Optional[float] = None, r: Optional[float] = None
                           ) -> ResultadoFormula:
    """Ley de Coulomb magnética entre polos: F = k_m·m₁·m₂/r², k_m = μ₀/4π."""
    faltantes = _falta_una((("f", f), ("m1", m1), ("m2", m2), ("r", r)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (F, m1, m2, r) y deja el cuarto en None")
    try:
        if f is None:
            f = K_M * m1 * m2 / r ** 2
        elif m1 is None:
            m1 = f * r ** 2 / (K_M * m2)
        elif m2 is None:
            m2 = f * r ** 2 / (K_M * m1)
        else:
            r = math.sqrt(abs(K_M * m1 * m2 / f))
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa ceros y signos)")
    return ResultadoFormula({"f": f, "m1": m1, "m2": m2, "r": r},
                             texto=f"F = {f:.6g} N (m1={m1:.6g}, m2={m2:.6g}, r={r:.6g} m)")


# ── 9. Campo magnético H de un hilo recto ────────────────────────────────────

def campo_magnetico_hilo(i: Optional[float] = None, r: Optional[float] = None,
                          h: Optional[float] = None) -> ResultadoFormula:
    """
    Campo magnético de un hilo recto infinito: H = I/(2πr), B = μ₀·H.
    Da dos valores y deja el tercero en None.
    """
    faltantes = _falta_una((("i", i), ("r", r), ("h", h)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (I, r, H) y deja el tercero en None")
    try:
        if h is None:
            h = i / (2 * math.pi * r)
        elif i is None:
            i = h * 2 * math.pi * r
        else:
            r = i / (2 * math.pi * h)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    b = MU_0 * h
    return ResultadoFormula({"i": i, "r": r, "h": h, "b": b},
                             texto=f"H = I/(2πr) = {h:.6g} A/m,  B = μ₀·H = {b:.6g} T")


# ── 10. Campo magnético de un solenoide ──────────────────────────────────────

def campo_magnetico_solenoide(i: float, vueltas: float, longitud: float,
                               mu_r: float = 1.0) -> ResultadoFormula:
    """Solenoide: H = N·I/L, B = μ_r·μ₀·H."""
    if longitud <= 0 or mu_r <= 0:
        return ResultadoFormula(error="La longitud y μ_r deben ser mayores que cero")
    h = vueltas * i / longitud
    b = mu_r * MU_0 * h
    return ResultadoFormula({"i": i, "vueltas": vueltas, "longitud": longitud,
                              "mu_r": mu_r, "h": h, "b": b},
                             texto=f"H = N·I/L = {h:.6g} A/m,  B = μ_r·μ₀·H = {b:.6g} T")


# ── 11. Densidad de flujo magnético ──────────────────────────────────────────

def flujo_magnetico(flujo: Optional[float] = None, b: Optional[float] = None,
                     area: Optional[float] = None, angulo: float = 0.0
                     ) -> ResultadoFormula:
    """
    Flujo magnético: Φ = B·A·cos(θ), con θ en grados entre B y la normal a la
    superficie. Da dos de (Φ, B, A) y deja el tercero en None.
    """
    faltantes = _falta_una((("flujo", flujo), ("b", b), ("area", area)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (Φ, B, A) y deja el tercero en None")
    cos_t = math.cos(math.radians(angulo))
    try:
        if flujo is None:
            flujo = b * area * cos_t
        elif b is None:
            b = flujo / (area * cos_t)
        else:
            area = flujo / (b * cos_t)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero (¿ángulo de 90°?)")
    return ResultadoFormula({"flujo": flujo, "b": b, "area": area, "angulo": angulo},
                             texto=f"Φ = B·A·cos(θ) = {flujo:.6g} Wb (B={b:.6g} T, A={area:.6g} m², θ={angulo:.6g}°)")


# ── 12. Fuerza de Lorentz ────────────────────────────────────────────────────

def fuerza_lorentz(q: float, v: float, b: float, angulo: float = 90.0,
                    masa: Optional[float] = None) -> ResultadoFormula:
    """
    Fuerza sobre una carga en movimiento: F = Q·v·B·sen(θ), θ en grados.
    Si se da la masa, calcula también el radio de la órbita r = m·v/(Q·B).
    """
    f = q * v * b * math.sin(math.radians(angulo))
    valores = {"q": q, "v": v, "b": b, "angulo": angulo, "f": f}
    lineas = [f"F = Q·v·B·sen(θ) = {f:.6g} N"]
    if masa is not None:
        try:
            r = masa * v / (q * b)
        except ZeroDivisionError:
            return ResultadoFormula(error="División por cero al calcular el radio")
        valores.update(masa=masa, r=r)
        lineas.append(f"r = m·v/(Q·B) = {r:.6g} m")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 13. Electrón en un campo magnético ───────────────────────────────────────

def electron_campo_magnetico(b: float, v: Optional[float] = None,
                              carga: Optional[float] = None,
                              masa: Optional[float] = None) -> ResultadoFormula:
    """
    Partícula cargada en un campo magnético uniforme: ω = Q·B/m (frecuencia de
    ciclotrón), f = ω/2π. Si se da la velocidad, también el radio r = m·v/(Q·B).
    Por defecto usa la carga y la masa del electrón.
    """
    carga = CARGA_E if carga is None else carga
    masa = MASA_E if masa is None else masa
    if masa <= 0:
        return ResultadoFormula(error="La masa debe ser mayor que cero")
    omega = carga * b / masa
    frecuencia = omega / (2 * math.pi)
    valores = {"b": b, "carga": carga, "masa": masa,
               "omega": omega, "frecuencia": frecuencia}
    lineas = [f"ω = Q·B/m = {omega:.6g} rad/s  (f = {frecuencia:.6g} Hz)"]
    if v is not None:
        try:
            r = masa * v / (carga * b)
        except ZeroDivisionError:
            return ResultadoFormula(error="División por cero al calcular el radio")
        valores.update(v=v, r=r)
        lineas.append(f"r = m·v/(Q·B) = {r:.6g} m")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 14. Ley de inducción de Faraday ──────────────────────────────────────────

def ley_faraday(delta_flujo: float, delta_t: float, vueltas: float = 1.0
                 ) -> ResultadoFormula:
    """Ley de Faraday: V = −N·ΔΦ/Δt (el signo es la ley de Lenz)."""
    if delta_t == 0:
        return ResultadoFormula(error="Δt no puede ser 0")
    v = -vueltas * delta_flujo / delta_t
    return ResultadoFormula({"v": v, "delta_flujo": delta_flujo,
                              "delta_t": delta_t, "vueltas": vueltas},
                             texto=f"V = −N·ΔΦ/Δt = {v:.6g} V")


# ── 15. Inducción electromagnética (conductor en movimiento) ─────────────────

def induccion_electromagnetica(b: Optional[float] = None, longitud: Optional[float] = None,
                                v: Optional[float] = None, fem: Optional[float] = None
                                ) -> ResultadoFormula:
    """Conductor moviéndose en un campo: V = B·L·v. Da tres valores."""
    faltantes = _falta_una((("b", b), ("longitud", longitud), ("v", v), ("fem", fem)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (B, L, v, fem) y deja el cuarto en None")
    try:
        if fem is None:
            fem = b * longitud * v
        elif b is None:
            b = fem / (longitud * v)
        elif longitud is None:
            longitud = fem / (b * v)
        else:
            v = fem / (b * longitud)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"b": b, "longitud": longitud, "v": v, "fem": fem},
                             texto=f"V = B·L·v = {fem:.6g} V (B={b:.6g} T, L={longitud:.6g} m, v={v:.6g} m/s)")


# ── 16. Inducción mutua ──────────────────────────────────────────────────────

def induccion_mutua(m: Optional[float] = None, delta_i: Optional[float] = None,
                     delta_t: Optional[float] = None, v: Optional[float] = None
                     ) -> ResultadoFormula:
    """Inducción mutua entre dos bobinas: V = −M·ΔI₁/Δt. Da tres valores."""
    faltantes = _falta_una((("m", m), ("delta_i", delta_i), ("delta_t", delta_t), ("v", v)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (M, ΔI, Δt, V) y deja el cuarto en None")
    try:
        if v is None:
            v = -m * delta_i / delta_t
        elif m is None:
            m = -v * delta_t / delta_i
        elif delta_i is None:
            delta_i = -v * delta_t / m
        else:
            delta_t = -m * delta_i / v
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"m": m, "delta_i": delta_i, "delta_t": delta_t, "v": v},
                             texto=f"V = −M·ΔI/Δt = {v:.6g} V (M={m:.6g} H)")


# ── 17. Autoinducción ────────────────────────────────────────────────────────

def autoinduccion(l: Optional[float] = None, delta_i: Optional[float] = None,
                   delta_t: Optional[float] = None, v: Optional[float] = None
                   ) -> ResultadoFormula:
    """Autoinducción de una bobina: V = −L·ΔI/Δt. Da tres valores."""
    faltantes = _falta_una((("l", l), ("delta_i", delta_i), ("delta_t", delta_t), ("v", v)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (L, ΔI, Δt, V) y deja el cuarto en None")
    try:
        if v is None:
            v = -l * delta_i / delta_t
        elif l is None:
            l = -v * delta_t / delta_i
        elif delta_i is None:
            delta_i = -v * delta_t / l
        else:
            delta_t = -l * delta_i / v
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"l": l, "delta_i": delta_i, "delta_t": delta_t, "v": v},
                             texto=f"V = −L·ΔI/Δt = {v:.6g} V (L={l:.6g} H)")


# ── Registro para invocar estas fórmulas desde la consola CAS ───────────────

REGISTRO.registrar(
    kwargs={
        "ley_coulomb_electrica": ley_coulomb_electrica,
        "campo_electrico": campo_electrico,
        "capacidad_electrica": capacidad_electrica,
        "capacidad_placas": capacidad_placas,
        "constante_dielectrica": constante_dielectrica,
        "energia_electrostatica": energia_electrostatica,
        "electron_campo_electrico": electron_campo_electrico,
        "ley_coulomb_magnetica": ley_coulomb_magnetica,
        "campo_magnetico_hilo": campo_magnetico_hilo,
        "campo_magnetico_solenoide": campo_magnetico_solenoide,
        "flujo_magnetico": flujo_magnetico,
        "fuerza_lorentz": fuerza_lorentz,
        "electron_campo_magnetico": electron_campo_magnetico,
        "ley_faraday": ley_faraday,
        "induccion_electromagnetica": induccion_electromagnetica,
        "induccion_mutua": induccion_mutua,
        "autoinduccion": autoinduccion,
    },
    posicionales={
        "capacidad_paralelo": capacidad_paralelo,
        "capacidad_serie": capacidad_serie,
    },
)
