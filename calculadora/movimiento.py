# =============================================================================
# MOVIMIENTO Y ENERGÍA — librería FX-880P, sección 1 de física (pág. 270)
# Las 20 fórmulas de esa sección, en forma estándar SI.
#
# Igual que en campos.py: el OCR del manual de 1990 llegó ilegible en la
# columna de fórmulas, así que están escritas en su forma estándar de física y
# las constantes (g, G) se toman de `scipy.constants` en vez de los redondeos
# del manual (G = 6.7×10⁻¹¹).
#
# Se dan los valores conocidos y se deja en None la incógnita a despejar.
# =============================================================================

from __future__ import annotations
import logging
import math
from typing import Optional

from scipy import constants

from .formulas import REGISTRO, ResultadoFormula

logger = logging.getLogger("ti_nspire.movimiento")

G_GRAV = constants.G          # constante de gravitación universal, N·m²/kg²
G_ACEL = constants.g          # aceleración de la gravedad en la Tierra, m/s²


def _falta_una(pares) -> list:
    return [n for n, val in pares if val is None]


# ── 1. Movimiento uniformemente acelerado ────────────────────────────────────

def movimiento_acelerado(v0: Optional[float] = None, a: Optional[float] = None,
                          t: Optional[float] = None, v: Optional[float] = None,
                          s: Optional[float] = None) -> ResultadoFormula:
    """
    MRUA, deduciendo con las cuatro ecuaciones: v = v₀+a·t, s = v₀·t+½a·t²,
    v² = v₀²+2a·s y s = (v₀+v)/2·t. Da los valores que conozcas (bastan tres)
    y deduce el resto.
    """
    x = {"v0": v0, "a": a, "t": t, "v": v, "s": s}
    for _ in range(4):          # varias pasadas: cada deducción habilita otras
        if x["v"] is None and None not in (x["v0"], x["a"], x["t"]):
            x["v"] = x["v0"] + x["a"] * x["t"]
        if x["a"] is None and None not in (x["v"], x["v0"], x["t"]) and x["t"]:
            x["a"] = (x["v"] - x["v0"]) / x["t"]
        if x["t"] is None and None not in (x["v"], x["v0"], x["a"]) and x["a"]:
            x["t"] = (x["v"] - x["v0"]) / x["a"]
        if x["v0"] is None and None not in (x["v"], x["a"], x["t"]):
            x["v0"] = x["v"] - x["a"] * x["t"]
        if x["s"] is None and None not in (x["v0"], x["a"], x["t"]):
            x["s"] = x["v0"] * x["t"] + 0.5 * x["a"] * x["t"] ** 2
        if x["s"] is None and None not in (x["v0"], x["v"], x["t"]):
            x["s"] = (x["v0"] + x["v"]) / 2 * x["t"]
        if x["v"] is None and None not in (x["v0"], x["a"], x["s"]):
            disc = x["v0"] ** 2 + 2 * x["a"] * x["s"]
            if disc >= 0:
                x["v"] = math.sqrt(disc)
        if x["a"] is None and None not in (x["v"], x["v0"], x["s"]) and x["s"]:
            x["a"] = (x["v"] ** 2 - x["v0"] ** 2) / (2 * x["s"])
        if x["s"] is None and None not in (x["v"], x["v0"], x["a"]) and x["a"]:
            x["s"] = (x["v"] ** 2 - x["v0"] ** 2) / (2 * x["a"])

    faltan = [k for k, val in x.items() if val is None]
    if faltan:
        return ResultadoFormula(
            error=f"Faltan datos para deducir {', '.join(faltan)} — da al menos tres valores")
    return ResultadoFormula(x, texto=(f"v₀ = {x['v0']:.6g} m/s, a = {x['a']:.6g} m/s², "
                                       f"t = {x['t']:.6g} s, v = {x['v']:.6g} m/s, "
                                       f"s = {x['s']:.6g} m"))


# ── 2. Segunda ley de Newton ─────────────────────────────────────────────────

def segunda_ley_newton(f: Optional[float] = None, m: Optional[float] = None,
                        a: Optional[float] = None) -> ResultadoFormula:
    """Segunda ley de Newton: F = m·a. Da dos valores y deja el tercero en None."""
    faltantes = _falta_una((("f", f), ("m", m), ("a", a)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (F, m, a) y deja el tercero en None")
    try:
        if f is None:
            f = m * a
        elif m is None:
            m = f / a
        else:
            a = f / m
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"f": f, "m": m, "a": a},
                             texto=f"F = m·a = {f:.6g} N (m={m:.6g} kg, a={a:.6g} m/s²)")


# ── 3-4. Movimiento circular ─────────────────────────────────────────────────

def movimiento_circular(r: float, v: Optional[float] = None,
                         omega: Optional[float] = None,
                         m: Optional[float] = None) -> ResultadoFormula:
    """
    Movimiento circular uniforme: v = ω·r, a_c = v²/r = ω²·r, T = 2π/ω, f = 1/T.
    Con la masa calcula también la fuerza centrípeta F = m·v²/r.
    Da el radio y una de las dos velocidades (lineal v o angular ω).
    """
    if r <= 0:
        return ResultadoFormula(error="El radio debe ser mayor que cero")
    if (v is None) == (omega is None):
        return ResultadoFormula(error="Da exactamente una de las dos: v (lineal) u omega (angular)")
    if v is None:
        v = omega * r
    else:
        omega = v / r

    a_c = v ** 2 / r
    periodo = 2 * math.pi / omega if omega else float("inf")
    frecuencia = 1 / periodo if periodo not in (0, float("inf")) else 0.0
    valores = {"r": r, "v": v, "omega": omega, "a_c": a_c,
               "periodo": periodo, "frecuencia": frecuencia}
    lineas = [f"v = ω·r = {v:.6g} m/s,  ω = {omega:.6g} rad/s",
              f"a_c = v²/r = {a_c:.6g} m/s²",
              f"T = 2π/ω = {periodo:.6g} s,  f = {frecuencia:.6g} Hz"]
    if m is not None:
        fuerza = m * a_c
        valores.update(m=m, f=fuerza)
        lineas.append(f"F_c = m·v²/r = {fuerza:.6g} N")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 5. Oscilación armónica simple ────────────────────────────────────────────

def oscilacion_armonica(amplitud: float, omega: float, t: float,
                         fase: float = 0.0) -> ResultadoFormula:
    """
    Movimiento armónico simple: x = A·sen(ωt+φ), v = A·ω·cos(ωt+φ), a = −ω²·x.
    El ángulo `fase` va en radianes.
    """
    ang = omega * t + fase
    x = amplitud * math.sin(ang)
    v = amplitud * omega * math.cos(ang)
    a = -(omega ** 2) * x
    periodo = 2 * math.pi / omega if omega else float("inf")
    return ResultadoFormula({"x": x, "v": v, "a": a, "amplitud": amplitud,
                              "omega": omega, "t": t, "fase": fase, "periodo": periodo},
                             texto=(f"x = {x:.6g} m,  v = {v:.6g} m/s,  a = {a:.6g} m/s²  "
                                    f"(T = {periodo:.6g} s)"))


# ── 6. Ley de Hooke ──────────────────────────────────────────────────────────

def ley_hooke(f: Optional[float] = None, k: Optional[float] = None,
               x: Optional[float] = None) -> ResultadoFormula:
    """Ley de Hooke: F = k·x (magnitud; la fuerza del resorte se opone a x)."""
    faltantes = _falta_una((("f", f), ("k", k), ("x", x)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (F, k, x) y deja el tercero en None")
    try:
        if f is None:
            f = k * x
        elif k is None:
            k = f / x
        else:
            x = f / k
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"f": f, "k": k, "x": x},
                             texto=f"F = k·x = {f:.6g} N (k={k:.6g} N/m, x={x:.6g} m)")


# ── 7. Oscilación de un resorte ──────────────────────────────────────────────

def oscilacion_resorte(m: Optional[float] = None, k: Optional[float] = None,
                        periodo: Optional[float] = None) -> ResultadoFormula:
    """Masa-resorte: T = 2π·√(m/k). Da dos valores y deja el tercero en None."""
    faltantes = _falta_una((("m", m), ("k", k), ("periodo", periodo)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (m, k, periodo) y deja el tercero en None")
    try:
        if periodo is None:
            periodo = 2 * math.pi * math.sqrt(m / k)
        elif m is None:
            m = k * (periodo / (2 * math.pi)) ** 2
        else:
            k = m / (periodo / (2 * math.pi)) ** 2
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (m y k deben ser positivos)")
    frecuencia = 1 / periodo if periodo else float("inf")
    return ResultadoFormula({"m": m, "k": k, "periodo": periodo, "frecuencia": frecuencia},
                             texto=f"T = 2π√(m/k) = {periodo:.6g} s  (f = {frecuencia:.6g} Hz)")


# ── 8. Péndulo simple ────────────────────────────────────────────────────────

def pendulo_simple(longitud: Optional[float] = None, periodo: Optional[float] = None,
                    g: Optional[float] = None) -> ResultadoFormula:
    """Péndulo simple (oscilaciones pequeñas): T = 2π·√(L/g). g por defecto: 9.80665 m/s²."""
    g = G_ACEL if g is None else g
    if (longitud is None) == (periodo is None):
        return ResultadoFormula(error="Da exactamente uno: la longitud o el periodo")
    try:
        if periodo is None:
            periodo = 2 * math.pi * math.sqrt(longitud / g)
        else:
            longitud = g * (periodo / (2 * math.pi)) ** 2
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (longitud y g deben ser positivos)")
    frecuencia = 1 / periodo if periodo else float("inf")
    return ResultadoFormula({"longitud": longitud, "periodo": periodo,
                              "g": g, "frecuencia": frecuencia},
                             texto=(f"T = 2π√(L/g) = {periodo:.6g} s  "
                                    f"(L = {longitud:.6g} m, g = {g:.6g} m/s², f = {frecuencia:.6g} Hz)"))


# ── 9. Energía potencial gravitatoria (cerca de la superficie) ──────────────

def energia_potencial(m: Optional[float] = None, h: Optional[float] = None,
                       energia: Optional[float] = None,
                       g: Optional[float] = None) -> ResultadoFormula:
    """Energía potencial: Ep = m·g·h. Da dos de (m, h, energia)."""
    g = G_ACEL if g is None else g
    faltantes = _falta_una((("m", m), ("h", h), ("energia", energia)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (m, h, energia) y deja el tercero en None")
    try:
        if energia is None:
            energia = m * g * h
        elif m is None:
            m = energia / (g * h)
        else:
            h = energia / (m * g)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"m": m, "h": h, "energia": energia, "g": g},
                             texto=f"Ep = m·g·h = {energia:.6g} J (m={m:.6g} kg, h={h:.6g} m)")


# ── 10. Energía elástica (resorte) ───────────────────────────────────────────

def energia_elastica(k: Optional[float] = None, x: Optional[float] = None,
                      energia: Optional[float] = None) -> ResultadoFormula:
    """Energía elástica de un resorte: Ep = ½·k·x². Da dos de los tres."""
    faltantes = _falta_una((("k", k), ("x", x), ("energia", energia)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (k, x, energia) y deja el tercero en None")
    try:
        if energia is None:
            energia = 0.5 * k * x ** 2
        elif k is None:
            k = 2 * energia / x ** 2
        else:
            x = math.sqrt(2 * energia / k)
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa ceros y signos)")
    return ResultadoFormula({"k": k, "x": x, "energia": energia},
                             texto=f"Ep = ½k·x² = {energia:.6g} J (k={k:.6g} N/m, x={x:.6g} m)")


# ── 11. Energía cinética ─────────────────────────────────────────────────────

def energia_cinetica(m: Optional[float] = None, v: Optional[float] = None,
                      energia: Optional[float] = None) -> ResultadoFormula:
    """Energía cinética: Ek = ½·m·v². Da dos de los tres."""
    faltantes = _falta_una((("m", m), ("v", v), ("energia", energia)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (m, v, energia) y deja el tercero en None")
    try:
        if energia is None:
            energia = 0.5 * m * v ** 2
        elif m is None:
            m = 2 * energia / v ** 2
        else:
            v = math.sqrt(2 * energia / m)
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa ceros y signos)")
    return ResultadoFormula({"m": m, "v": v, "energia": energia},
                             texto=f"Ek = ½m·v² = {energia:.6g} J (m={m:.6g} kg, v={v:.6g} m/s)")


# ── 12. Coeficiente de fricción ──────────────────────────────────────────────

def coeficiente_friccion(f: Optional[float] = None, mu: Optional[float] = None,
                          n: Optional[float] = None) -> ResultadoFormula:
    """Fuerza de fricción: F = μ·N. Da dos valores y deja el tercero en None."""
    faltantes = _falta_una((("f", f), ("mu", mu), ("n", n)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (F, μ, N) y deja el tercero en None")
    try:
        if f is None:
            f = mu * n
        elif mu is None:
            mu = f / n
        else:
            n = f / mu
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"f": f, "mu": mu, "n": n},
                             texto=f"F = μ·N = {f:.6g} N (μ={mu:.6g}, N={n:.6g} N)")


# ── 13. Trabajo ──────────────────────────────────────────────────────────────

def trabajo(f: Optional[float] = None, s: Optional[float] = None,
             w: Optional[float] = None, angulo: float = 0.0) -> ResultadoFormula:
    """Trabajo: W = F·s·cos(θ), con θ en grados (0 por defecto). Da dos de (F, s, W)."""
    faltantes = _falta_una((("f", f), ("s", s), ("w", w)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (F, s, W) y deja el tercero en None")
    cos_t = math.cos(math.radians(angulo))
    try:
        if w is None:
            w = f * s * cos_t
        elif f is None:
            f = w / (s * cos_t)
        else:
            s = w / (f * cos_t)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero (¿ángulo de 90°?)")
    return ResultadoFormula({"f": f, "s": s, "w": w, "angulo": angulo},
                             texto=f"W = F·s·cos(θ) = {w:.6g} J (F={f:.6g} N, s={s:.6g} m, θ={angulo:.6g}°)")


# ── 14. Tercera ley de Kepler ────────────────────────────────────────────────

def ley_kepler(t1: Optional[float] = None, r1: Optional[float] = None,
                t2: Optional[float] = None, r2: Optional[float] = None
                ) -> ResultadoFormula:
    """Tercera ley de Kepler: T²/r³ = constante, es decir T₁²/r₁³ = T₂²/r₂³.
    Da tres valores y deja el cuarto en None."""
    faltantes = _falta_una((("t1", t1), ("r1", r1), ("t2", t2), ("r2", r2)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (T1, r1, T2, r2) y deja el cuarto en None")
    try:
        if t2 is None:
            t2 = math.sqrt(t1 ** 2 * r2 ** 3 / r1 ** 3)
        elif t1 is None:
            t1 = math.sqrt(t2 ** 2 * r1 ** 3 / r2 ** 3)
        elif r2 is None:
            r2 = (t2 ** 2 * r1 ** 3 / t1 ** 2) ** (1 / 3)
        else:
            r1 = (t1 ** 2 * r2 ** 3 / t2 ** 2) ** (1 / 3)
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (deben ser positivos)")
    constante = t1 ** 2 / r1 ** 3
    return ResultadoFormula({"t1": t1, "r1": r1, "t2": t2, "r2": r2, "constante": constante},
                             texto=(f"T1={t1:.6g}, r1={r1:.6g}, T2={t2:.6g}, r2={r2:.6g}  "
                                    f"(T²/r³ = {constante:.6g})"))


# ── 15. Gravitación universal ────────────────────────────────────────────────

def gravitacion_universal(f: Optional[float] = None, m1: Optional[float] = None,
                           m2: Optional[float] = None, r: Optional[float] = None
                           ) -> ResultadoFormula:
    """Gravitación universal: F = G·m₁·m₂/r². Da tres valores y deja el cuarto en None."""
    faltantes = _falta_una((("f", f), ("m1", m1), ("m2", m2), ("r", r)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (F, m1, m2, r) y deja el cuarto en None")
    try:
        if f is None:
            f = G_GRAV * m1 * m2 / r ** 2
        elif m1 is None:
            m1 = f * r ** 2 / (G_GRAV * m2)
        elif m2 is None:
            m2 = f * r ** 2 / (G_GRAV * m1)
        else:
            r = math.sqrt(G_GRAV * m1 * m2 / f)
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa ceros y signos)")
    return ResultadoFormula({"f": f, "m1": m1, "m2": m2, "r": r},
                             texto=f"F = G·m₁m₂/r² = {f:.6g} N (m1={m1:.6g} kg, m2={m2:.6g} kg, r={r:.6g} m)")


# ── 16. Energía potencial interplanetaria ────────────────────────────────────

def energia_potencial_gravitatoria(m1: float, m2: float, r: float) -> ResultadoFormula:
    """Energía potencial gravitatoria entre dos masas: Ep = −G·m₁·m₂/r."""
    if r <= 0:
        return ResultadoFormula(error="La distancia debe ser mayor que cero")
    energia = -G_GRAV * m1 * m2 / r
    return ResultadoFormula({"m1": m1, "m2": m2, "r": r, "energia": energia},
                             texto=f"Ep = −G·m₁m₂/r = {energia:.6g} J")


# ── 17. Energía cinética / velocidad orbital ─────────────────────────────────

def velocidad_orbital(m_central: float, r: float,
                      m_satelite: Optional[float] = None) -> ResultadoFormula:
    """
    Órbita circular: v = √(G·M/r), T = 2π·r/v. Con la masa del satélite calcula
    también su energía cinética y su energía total (Ek + Ep).
    """
    if r <= 0 or m_central <= 0:
        return ResultadoFormula(error="La masa central y el radio deben ser mayores que cero")
    v = math.sqrt(G_GRAV * m_central / r)
    periodo = 2 * math.pi * r / v
    valores = {"m_central": m_central, "r": r, "v": v, "periodo": periodo}
    lineas = [f"v = √(G·M/r) = {v:.6g} m/s",
              f"T = 2πr/v = {periodo:.6g} s ({periodo / 3600:.6g} h)"]
    if m_satelite is not None:
        ek = 0.5 * m_satelite * v ** 2
        ep = -G_GRAV * m_central * m_satelite / r
        valores.update(m_satelite=m_satelite, ek=ek, ep=ep, e_total=ek + ep)
        lineas.append(f"Ek = {ek:.6g} J,  Ep = {ep:.6g} J,  E total = {ek + ep:.6g} J")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 18. Momento de inercia ───────────────────────────────────────────────────

_FORMAS_INERCIA = {
    "puntual":        (1.0,       "masa puntual: I = m·r²"),
    "aro":            (1.0,       "aro / cilindro hueco de pared fina: I = m·r²"),
    "disco":          (0.5,       "disco / cilindro macizo: I = ½·m·r²"),
    "cilindro":       (0.5,       "cilindro macizo: I = ½·m·r²"),
    "esfera":         (0.4,       "esfera maciza: I = ⅖·m·r²"),
    "esfera_hueca":   (2 / 3,     "esfera hueca: I = ⅔·m·r²"),
    "varilla_centro": (1 / 12,    "varilla por su centro: I = (1/12)·m·L²"),
    "varilla_extremo": (1 / 3,    "varilla por un extremo: I = ⅓·m·L²"),
}


def momento_inercia(m: float, r: float, forma: str = "puntual") -> ResultadoFormula:
    """
    Momento de inercia I = c·m·r², con `forma` eligiendo el cuerpo:
    puntual, aro, disco, cilindro, esfera, esfera_hueca, varilla_centro,
    varilla_extremo (en las varillas, r es la longitud L).
    """
    forma = (forma or "puntual").strip().lower()
    if forma not in _FORMAS_INERCIA:
        return ResultadoFormula(
            error=f"forma debe ser una de: {', '.join(_FORMAS_INERCIA)}")
    coef, descripcion = _FORMAS_INERCIA[forma]
    i = coef * m * r ** 2
    return ResultadoFormula({"i": i, "m": m, "r": r, "forma": forma, "coeficiente": coef},
                             texto=f"I = {i:.6g} kg·m²  ({descripcion})")


# ── 19. Momento angular ──────────────────────────────────────────────────────

def momento_angular(i: Optional[float] = None, omega: Optional[float] = None,
                     m: Optional[float] = None, v: Optional[float] = None,
                     r: Optional[float] = None, l: Optional[float] = None
                     ) -> ResultadoFormula:
    """
    Momento angular: L = I·ω (sólido rígido) o L = m·v·r (partícula).
    Da I y ω, o m, v y r; o da L con uno de los factores para despejar el otro.
    """
    if m is not None and v is not None and r is not None:
        l = m * v * r
        return ResultadoFormula({"l": l, "m": m, "v": v, "r": r},
                                 texto=f"L = m·v·r = {l:.6g} kg·m²/s")
    faltantes = _falta_una((("i", i), ("omega", omega), ("l", l)))
    if len(faltantes) != 1:
        return ResultadoFormula(
            error="Da dos valores (I, ω, L) y deja el tercero en None, o bien m, v y r")
    try:
        if l is None:
            l = i * omega
        elif i is None:
            i = l / omega
        else:
            omega = l / i
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"l": l, "i": i, "omega": omega},
                             texto=f"L = I·ω = {l:.6g} kg·m²/s (I={i:.6g} kg·m², ω={omega:.6g} rad/s)")


# ── 20. Conservación de la cantidad de movimiento ────────────────────────────

def conservacion_momento(m1: float, m2: float, v1i: Optional[float] = None,
                          v2i: Optional[float] = None, v1f: Optional[float] = None,
                          v2f: Optional[float] = None) -> ResultadoFormula:
    """
    Conservación del momento en un choque: m₁·v₁ᵢ + m₂·v₂ᵢ = m₁·v₁f + m₂·v₂f.
    Da las dos masas y tres de las cuatro velocidades; despeja la que falte.
    """
    faltantes = _falta_una((("v1i", v1i), ("v2i", v2i), ("v1f", v1f), ("v2f", v2f)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres velocidades (v1i, v2i, v1f, v2f) y deja la cuarta en None")
    try:
        if v2f is None:
            v2f = (m1 * v1i + m2 * v2i - m1 * v1f) / m2
        elif v1f is None:
            v1f = (m1 * v1i + m2 * v2i - m2 * v2f) / m1
        elif v2i is None:
            v2i = (m1 * v1f + m2 * v2f - m1 * v1i) / m2
        else:
            v1i = (m1 * v1f + m2 * v2f - m2 * v2i) / m1
    except ZeroDivisionError:
        return ResultadoFormula(error="Las masas no pueden ser 0")

    p_inicial = m1 * v1i + m2 * v2i
    ek_inicial = 0.5 * m1 * v1i ** 2 + 0.5 * m2 * v2i ** 2
    ek_final = 0.5 * m1 * v1f ** 2 + 0.5 * m2 * v2f ** 2
    elastico = abs(ek_final - ek_inicial) < 1e-9 * max(1.0, abs(ek_inicial))
    return ResultadoFormula(
        {"m1": m1, "m2": m2, "v1i": v1i, "v2i": v2i, "v1f": v1f, "v2f": v2f,
         "p": p_inicial, "ek_inicial": ek_inicial, "ek_final": ek_final,
         "elastico": elastico},
        texto=(f"v1i={v1i:.6g}, v2i={v2i:.6g} → v1f={v1f:.6g}, v2f={v2f:.6g} m/s\n"
               f"p = {p_inicial:.6g} kg·m/s (se conserva)\n"
               f"Ek: {ek_inicial:.6g} J → {ek_final:.6g} J "
               f"({'choque elástico' if elastico else 'choque inelástico, se pierde energía'})"))


# ── Registro para invocar estas fórmulas desde la consola CAS ───────────────

REGISTRO.registrar(
    kwargs={
        "movimiento_acelerado": movimiento_acelerado,
        "segunda_ley_newton": segunda_ley_newton,
        "movimiento_circular": movimiento_circular,
        "oscilacion_armonica": oscilacion_armonica,
        "ley_hooke": ley_hooke,
        "oscilacion_resorte": oscilacion_resorte,
        "pendulo_simple": pendulo_simple,
        "energia_potencial": energia_potencial,
        "energia_elastica": energia_elastica,
        "energia_cinetica": energia_cinetica,
        "coeficiente_friccion": coeficiente_friccion,
        "trabajo": trabajo,
        "ley_kepler": ley_kepler,
        "gravitacion_universal": gravitacion_universal,
        "energia_potencial_gravitatoria": energia_potencial_gravitatoria,
        "velocidad_orbital": velocidad_orbital,
        "momento_inercia": momento_inercia,
        "momento_angular": momento_angular,
        "conservacion_momento": conservacion_momento,
    },
)
