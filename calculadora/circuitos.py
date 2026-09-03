# =============================================================================
# CIRCUITOS AC Y DC — Librería científica de la FX-880P, sección 4 (pág. 273)
# 16 fórmulas de circuitos eléctricos portadas a Python.
# Cada función recibe los valores conocidos y deja en None la incógnita a
# despejar; si sobran o faltan datos, devuelve un ResultadoFormula con error.
# =============================================================================

from __future__ import annotations
import logging
import math
from typing import Optional, Sequence

from .formulas import ResultadoFormula

logger = logging.getLogger("ti_nspire.circuitos")


# ── 1. Ley de Ohm ──────────────────────────────────────────────────────────

def ley_ohm(v: Optional[float] = None, i: Optional[float] = None,
            r: Optional[float] = None) -> ResultadoFormula:
    """Ley de Ohm: V = I·R. Da dos valores y deja el tercero en None."""
    faltantes = [n for n, val in (("v", v), ("i", i), ("r", r)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da exactamente dos valores (V, I, R) y deja el tercero en None")
    try:
        if v is None:
            v = i * r
        elif i is None:
            i = v / r
        else:
            r = v / i
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"v": v, "i": i, "r": r},
                             texto=f"V = {v:.6g} V, I = {i:.6g} A, R = {r:.6g} Ω")


# ── 2. Resistencia equivalente (serie / paralelo) ──────────────────────────

def resistencia_serie(*resistencias: float) -> ResultadoFormula:
    """Resistencia equivalente en serie: R = R1 + R2 + ..."""
    if len(resistencias) < 2:
        return ResultadoFormula(error="Da al menos dos resistencias")
    r = sum(resistencias)
    return ResultadoFormula({"r": r}, texto=f"R equivalente = {r:.6g} Ω")


def resistencia_paralelo(*resistencias: float) -> ResultadoFormula:
    """Resistencia equivalente en paralelo: 1/R = 1/R1 + 1/R2 + ..."""
    if len(resistencias) < 2:
        return ResultadoFormula(error="Da al menos dos resistencias")
    if any(r == 0 for r in resistencias):
        return ResultadoFormula(error="Ninguna resistencia puede ser 0")
    r = 1 / sum(1 / r for r in resistencias)
    return ResultadoFormula({"r": r}, texto=f"R equivalente = {r:.6g} Ω")


# ── 3. Circuito DC (con resistencia interna) ───────────────────────────────

def circuito_dc(e: Optional[float] = None, i: Optional[float] = None,
                 r: Optional[float] = None, v: Optional[float] = None) -> ResultadoFormula:
    """Circuito DC con resistencia interna: V = E − I·R. Da tres valores."""
    faltantes = [n for n, val in (("e", e), ("i", i), ("r", r), ("v", v)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (E, I, R, V) y deja el cuarto en None")
    try:
        if v is None:
            v = e - i * r
        elif e is None:
            e = v + i * r
        elif i is None:
            i = (e - v) / r
        else:
            r = (e - v) / i
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"e": e, "i": i, "r": r, "v": v},
                             texto=f"E = {e:.6g} V, I = {i:.6g} A, R = {r:.6g} Ω, V = {v:.6g} V")


# ── 4. Potencia DC y calor de Joule ─────────────────────────────────────────

def potencia_dc(i: Optional[float] = None, v: Optional[float] = None,
                 r: Optional[float] = None) -> ResultadoFormula:
    """Potencia DC: P = I·V = I²·R = V²/R. Da al menos dos de (I, V, R)."""
    conocidos = sum(x is not None for x in (i, v, r))
    if conocidos < 2:
        return ResultadoFormula(error="Da al menos dos valores entre I, V, R")
    try:
        if i is not None and v is not None:
            p = i * v
            if r is None:
                r = v / i
        elif i is not None and r is not None:
            p = i ** 2 * r
            v = i * r
        else:
            p = v ** 2 / r
            i = v / r
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"p": p, "i": i, "v": v, "r": r},
                             texto=f"P = {p:.6g} W (I={i:.6g} A, V={v:.6g} V, R={r:.6g} Ω)")


def calor_joule(t: float, potencia: Optional[float] = None, i: Optional[float] = None,
                 v: Optional[float] = None, r: Optional[float] = None) -> ResultadoFormula:
    """Calor de Joule: W = P·t. La potencia se puede dar directa o vía I/V/R."""
    if potencia is None:
        res_p = potencia_dc(i=i, v=v, r=r)
        if not res_p.ok:
            return res_p
        potencia = res_p.valores["p"]
    w = potencia * t
    return ResultadoFormula({"w": w, "p": potencia, "t": t},
                             texto=f"W = {w:.6g} J (P={potencia:.6g} W, t={t:.6g} s)")


# ── 5. Conductancia ─────────────────────────────────────────────────────────

def conductancia(r: Optional[float] = None, g: Optional[float] = None) -> ResultadoFormula:
    """Conductancia: G = 1/R. Da exactamente uno de los dos."""
    if (r is None) == (g is None):
        return ResultadoFormula(error="Da exactamente uno de R o G")
    try:
        if g is None:
            g = 1 / r
        else:
            r = 1 / g
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"r": r, "g": g}, texto=f"G = {g:.6g} S, R = {r:.6g} Ω")


# ── 6. Leyes de Kirchhoff ────────────────────────────────────────────────────

def kirchhoff_corrientes(corrientes: Sequence[Optional[float]]) -> ResultadoFormula:
    """
    Primera ley de Kirchhoff (nodos): ΣI = 0. Entra/sale se distingue por el
    signo. Deja una corriente en None para despejarla, o pásalas todas para
    validar que la suma dé cero.
    """
    faltantes = [idx for idx, val in enumerate(corrientes) if val is None]
    if len(faltantes) > 1:
        return ResultadoFormula(error="Deja como máximo una corriente en None")
    suma = sum(c for c in corrientes if c is not None)
    if faltantes:
        idx = faltantes[0]
        valor = -suma
        completas = list(corrientes)
        completas[idx] = valor
        return ResultadoFormula({"corrientes": completas},
                                 texto=f"I[{idx}] = {valor:.6g} A (ΣI = 0)")
    if abs(suma) > 1e-9:
        return ResultadoFormula(error=f"No se cumple ΣI=0 (suma = {suma:.6g} A)")
    return ResultadoFormula({"corrientes": list(corrientes)}, texto="Se cumple ΣI = 0")


def kirchhoff_voltajes(voltajes: Sequence[Optional[float]]) -> ResultadoFormula:
    """Segunda ley de Kirchhoff (mallas): ΣV = 0 en un lazo cerrado."""
    faltantes = [idx for idx, val in enumerate(voltajes) if val is None]
    if len(faltantes) > 1:
        return ResultadoFormula(error="Deja como máximo un voltaje en None")
    suma = sum(v for v in voltajes if v is not None)
    if faltantes:
        idx = faltantes[0]
        valor = -suma
        completos = list(voltajes)
        completos[idx] = valor
        return ResultadoFormula({"voltajes": completos},
                                 texto=f"V[{idx}] = {valor:.6g} V (ΣV = 0)")
    if abs(suma) > 1e-9:
        return ResultadoFormula(error=f"No se cumple ΣV=0 (suma = {suma:.6g} V)")
    return ResultadoFormula({"voltajes": list(voltajes)}, texto="Se cumple ΣV = 0")


# ── 7. Puente de Wheatstone ──────────────────────────────────────────────────

def puente_wheatstone(r1: Optional[float] = None, r2: Optional[float] = None,
                       r3: Optional[float] = None, r4: Optional[float] = None) -> ResultadoFormula:
    """
    Puente de Wheatstone en equilibrio: R1·R4 = R2·R3.
    Da tres resistencias y deja la desconocida (típicamente R4/Rx) en None.
    """
    faltantes = [n for n, val in (("r1", r1), ("r2", r2), ("r3", r3), ("r4", r4)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres resistencias y deja la cuarta en None")
    try:
        if r1 is None:
            r1 = r2 * r3 / r4
        elif r2 is None:
            r2 = r1 * r4 / r3
        elif r3 is None:
            r3 = r1 * r4 / r2
        else:
            r4 = r2 * r3 / r1
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"r1": r1, "r2": r2, "r3": r3, "r4": r4},
                             texto=f"R1={r1:.6g} Ω, R2={r2:.6g} Ω, R3={r3:.6g} Ω, R4={r4:.6g} Ω")


# ── 8. Valor instantáneo (AC) ────────────────────────────────────────────────

def valor_instantaneo(amplitud: float, t: float, frecuencia: Optional[float] = None,
                       omega: Optional[float] = None, fase: float = 0.0) -> ResultadoFormula:
    """Valor instantáneo AC: x(t) = X0·sin(ωt + φ), con ω = 2πf si no se da directo."""
    if omega is None:
        if frecuencia is None:
            return ResultadoFormula(error="Da la frecuencia f o la velocidad angular ω")
        omega = 2 * math.pi * frecuencia
    valor = amplitud * math.sin(omega * t + fase)
    return ResultadoFormula({"valor": valor, "omega": omega},
                             texto=f"x(t) = {valor:.6g} (ω={omega:.6g} rad/s)")


# ── 9. Valor efectivo (RMS) ──────────────────────────────────────────────────

def valor_efectivo(pico: Optional[float] = None, rms: Optional[float] = None) -> ResultadoFormula:
    """Valor eficaz de una señal senoidal: X_rms = X0 / √2. Da exactamente uno."""
    if (pico is None) == (rms is None):
        return ResultadoFormula(error="Da exactamente uno: el valor pico o el RMS")
    if rms is None:
        rms = pico / math.sqrt(2)
    else:
        pico = rms * math.sqrt(2)
    return ResultadoFormula({"pico": pico, "rms": rms}, texto=f"Pico = {pico:.6g}, RMS = {rms:.6g}")


# ── 10. Potencia AC ──────────────────────────────────────────────────────────

def potencia_ac(v0: Optional[float] = None, i0: Optional[float] = None,
                 vrms: Optional[float] = None, irms: Optional[float] = None,
                 cos_phi: float = 1.0) -> ResultadoFormula:
    """Potencia activa AC: P = Vrms·Irms·cos(φ). Acepta valores pico o RMS."""
    if vrms is None:
        if v0 is None:
            return ResultadoFormula(error="Da V0 o Vrms")
        vrms = v0 / math.sqrt(2)
    if irms is None:
        if i0 is None:
            return ResultadoFormula(error="Da I0 o Irms")
        irms = i0 / math.sqrt(2)
    p = vrms * irms * cos_phi
    return ResultadoFormula({"p": p, "vrms": vrms, "irms": irms},
                             texto=f"P = {p:.6g} W (Vrms={vrms:.6g} V, Irms={irms:.6g} A, cosφ={cos_phi:.3g})")


# ── 11. Factor de potencia ───────────────────────────────────────────────────

def factor_potencia(p: Optional[float] = None, vrms: Optional[float] = None,
                     irms: Optional[float] = None, cos_phi: Optional[float] = None) -> ResultadoFormula:
    """Factor de potencia: cos(φ) = P / (Vrms·Irms). Da tres valores."""
    faltantes = [n for n, val in (("p", p), ("vrms", vrms), ("irms", irms), ("cos_phi", cos_phi))
                 if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres valores (P, Vrms, Irms, cosφ) y deja el cuarto en None")
    try:
        if cos_phi is None:
            cos_phi = p / (vrms * irms)
        elif p is None:
            p = vrms * irms * cos_phi
        elif vrms is None:
            vrms = p / (irms * cos_phi)
        else:
            irms = p / (vrms * cos_phi)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"p": p, "vrms": vrms, "irms": irms, "cos_phi": cos_phi},
                             texto=f"cosφ = {cos_phi:.6g}")


# ── 12. Transformador ideal ──────────────────────────────────────────────────

def transformador(n1: float, n2: float, v1: Optional[float] = None, v2: Optional[float] = None,
                   i1: Optional[float] = None, i2: Optional[float] = None) -> ResultadoFormula:
    """
    Transformador ideal: N1·V2 = N2·V1 y N1·I1 = N2·I2.
    Da N1, N2 y una magnitud de un lado para obtener la del otro.
    """
    razon = n2 / n1
    resultado = {"n1": n1, "n2": n2}
    if v1 is not None or v2 is not None:
        if v2 is None:
            v2 = v1 * razon
        elif v1 is None:
            v1 = v2 / razon
        resultado.update(v1=v1, v2=v2)
    if i1 is not None or i2 is not None:
        if i2 is None:
            i2 = i1 / razon
        elif i1 is None:
            i1 = i2 * razon
        resultado.update(i1=i1, i2=i2)
    return ResultadoFormula(resultado, texto=f"Relación de vueltas N2/N1 = {razon:.6g}")


# ── 13. Reactancia (inductiva / capacitiva) ──────────────────────────────────

def reactancia_inductiva(l: Optional[float] = None, f: Optional[float] = None,
                          omega: Optional[float] = None, x: Optional[float] = None) -> ResultadoFormula:
    """Reactancia inductiva: X_L = ωL = 2πfL."""
    if omega is None and f is not None:
        omega = 2 * math.pi * f
    faltantes = [n for n, val in (("l", l), ("omega", omega), ("x", x)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da L y (f u ω), o X y uno de los dos, dejando el resto en None")
    try:
        if x is None:
            x = omega * l
        elif l is None:
            l = x / omega
        else:
            omega = x / l
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"l": l, "omega": omega, "x": x}, texto=f"X_L = {x:.6g} Ω")


def reactancia_capacitiva(c: Optional[float] = None, f: Optional[float] = None,
                           omega: Optional[float] = None, x: Optional[float] = None) -> ResultadoFormula:
    """Reactancia capacitiva: X_C = 1/(ωC) = 1/(2πfC)."""
    if omega is None and f is not None:
        omega = 2 * math.pi * f
    faltantes = [n for n, val in (("c", c), ("omega", omega), ("x", x)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da C y (f u ω), o X y uno de los dos, dejando el resto en None")
    try:
        if x is None:
            x = 1 / (omega * c)
        elif c is None:
            c = 1 / (omega * x)
        else:
            omega = 1 / (c * x)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"c": c, "omega": omega, "x": x}, texto=f"X_C = {x:.6g} Ω")


# ── 14. Impedancia ────────────────────────────────────────────────────────────

def impedancia(r: float, xl: float = 0.0, xc: float = 0.0) -> ResultadoFormula:
    """Impedancia de un circuito RLC serie: Z = √(R² + (X_L − X_C)²)."""
    z = math.hypot(r, xl - xc)
    angulo = math.degrees(math.atan2(xl - xc, r))
    return ResultadoFormula({"z": z, "angulo_grados": angulo},
                             texto=f"Z = {z:.6g} Ω, ángulo = {angulo:.3g}°")


# ── 15. Frecuencia natural (resonancia LC) ────────────────────────────────────

def frecuencia_natural(l: Optional[float] = None, c: Optional[float] = None,
                        f0: Optional[float] = None) -> ResultadoFormula:
    """Frecuencia natural de resonancia LC: f0 = 1 / (2π√(LC))."""
    faltantes = [n for n, val in (("l", l), ("c", c), ("f0", f0)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos de L, C, f0 y deja el tercero en None")
    try:
        if f0 is None:
            f0 = 1 / (2 * math.pi * math.sqrt(l * c))
        elif l is None:
            l = 1 / (c * (2 * math.pi * f0) ** 2)
        else:
            c = 1 / (l * (2 * math.pi * f0) ** 2)
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (revisa signos y ceros)")
    return ResultadoFormula({"l": l, "c": c, "f0": f0}, texto=f"f0 = {f0:.6g} Hz")


# ── 16. Oscilación eléctrica (conservación de energía en LC) ─────────────────

def oscilacion_electrica(l: Optional[float] = None, i: Optional[float] = None,
                          q: Optional[float] = None, c: Optional[float] = None,
                          energia_total: Optional[float] = None) -> ResultadoFormula:
    """
    Oscilación eléctrica en un circuito LC ideal (conservación de energía):
    ½·L·I² + Q²/(2·C) = constante.
    Da L, I, Q, C completos para obtener la energía total, o da la energía
    total y tres de (L, I, Q, C) para despejar el cuarto.
    """
    if energia_total is None:
        if None in (l, i, q, c):
            return ResultadoFormula(error="Da L, I, Q y C para calcular la energía total")
        energia = 0.5 * l * i ** 2 + q ** 2 / (2 * c)
        return ResultadoFormula({"energia_total": energia}, texto=f"Energía total = {energia:.6g} J")

    faltantes = [n for n, val in (("l", l), ("i", i), ("q", q), ("c", c)) if val is None]
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da tres de L, I, Q, C y deja la cuarta en None")
    try:
        if i is None:
            i = math.sqrt(2 * (energia_total - q ** 2 / (2 * c)) / l)
        elif l is None:
            l = 2 * (energia_total - q ** 2 / (2 * c)) / i ** 2
        elif q is None:
            q = math.sqrt(2 * c * (energia_total - 0.5 * l * i ** 2))
        else:
            c = q ** 2 / (2 * (energia_total - 0.5 * l * i ** 2))
    except (ValueError, ZeroDivisionError):
        return ResultadoFormula(error="Valores inconsistentes (energía negativa o división por cero)")
    return ResultadoFormula({"l": l, "i": i, "q": q, "c": c, "energia_total": energia_total},
                             texto=f"L={l:.6g} H, I={i:.6g} A, Q={q:.6g} C, C={c:.6g} F")


# ── Invocación por nombre desde la consola CAS ───────────────────────────────
# Permite escribir, por ejemplo, "ley_ohm(v=12, i=2)" directamente en la
# consola de la pestaña CAS (con "Evaluar / Simplificar" seleccionado).

_FUNCIONES_KWARGS = {
    "ley_ohm": ley_ohm,
    "circuito_dc": circuito_dc,
    "potencia_dc": potencia_dc,
    "calor_joule": calor_joule,
    "conductancia": conductancia,
    "puente_wheatstone": puente_wheatstone,
    "valor_instantaneo": valor_instantaneo,
    "valor_efectivo": valor_efectivo,
    "potencia_ac": potencia_ac,
    "factor_potencia": factor_potencia,
    "transformador": transformador,
    "reactancia_inductiva": reactancia_inductiva,
    "reactancia_capacitiva": reactancia_capacitiva,
    "impedancia": impedancia,
    "frecuencia_natural": frecuencia_natural,
    "oscilacion_electrica": oscilacion_electrica,
}
_FUNCIONES_POSICIONALES = {
    "resistencia_serie": resistencia_serie,
    "resistencia_paralelo": resistencia_paralelo,
}
_FUNCIONES_LISTA = {
    "kirchhoff_corrientes": kirchhoff_corrientes,
    "kirchhoff_voltajes": kirchhoff_voltajes,
}

NOMBRES_DISPONIBLES = sorted(
    set(_FUNCIONES_KWARGS) | set(_FUNCIONES_POSICIONALES) | set(_FUNCIONES_LISTA))


def _parsear_valor(token: str) -> Optional[float]:
    token = token.strip()
    if token in ("", "?", "none", "None"):
        return None
    return float(token)


def _parsear_argumentos(texto: str) -> tuple[list, dict]:
    texto = texto.strip()
    if not texto:
        return [], {}
    posicionales, nombrados = [], {}
    for parte in texto.split(","):
        if "=" in parte:
            clave, _, val = parte.partition("=")
            nombrados[clave.strip()] = _parsear_valor(val)
        else:
            posicionales.append(_parsear_valor(parte))
    return posicionales, nombrados


def invocar(nombre: str, texto_argumentos: str) -> Optional[ResultadoFormula]:
    """
    Busca `nombre` entre las fórmulas de circuitos e invoca la función con los
    argumentos dados en texto. Sintaxis: "clave=valor" separados por comas
    para la mayoría ("ley_ohm(v=12, i=2)"); valores por posición para
    resistencia_serie/paralelo ("resistencia_serie(10,20,30)"); valores por
    posición con "?" para la incógnita en Kirchhoff ("kirchhoff_corrientes(2,-1,?)").
    Retorna None si `nombre` no es una fórmula de circuitos conocida, para que
    el llamador pueda intentar otra ruta de evaluación (p. ej. SymPy).
    """
    if nombre not in NOMBRES_DISPONIBLES:
        return None
    try:
        posicionales, nombrados = _parsear_argumentos(texto_argumentos)
    except ValueError as e:
        return ResultadoFormula(error=f"Valor numérico inválido: {e}")

    try:
        if nombre in _FUNCIONES_KWARGS:
            if posicionales:
                return ResultadoFormula(error=f"{nombre}(...) usa solo clave=valor, ej: v=12, i=2")
            return _FUNCIONES_KWARGS[nombre](**nombrados)
        if nombre in _FUNCIONES_POSICIONALES:
            if nombrados:
                return ResultadoFormula(error=f"{nombre}(...) usa solo valores por posición, ej: 10, 20, 30")
            return _FUNCIONES_POSICIONALES[nombre](*posicionales)
        if nombrados:
            return ResultadoFormula(error=f"{nombre}(...) usa solo valores por posición")
        return _FUNCIONES_LISTA[nombre](posicionales)
    except TypeError as e:
        return ResultadoFormula(error=f"Argumentos inválidos para {nombre}: {e}")
