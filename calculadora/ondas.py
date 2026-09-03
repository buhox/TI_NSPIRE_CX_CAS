# =============================================================================
# MOVIMIENTO ONDULATORIO — librería FX-880P, sección 2 de física (pág. 272)
# Las 16 fórmulas de esa sección, en forma estándar SI.
#
# Igual que en campos.py y movimiento.py: el OCR del manual llegó ilegible en
# la columna de fórmulas, así que están en su forma estándar de física, con las
# constantes (h, c, masa del electrón) desde `scipy.constants`. La única que se
# conserva tal cual del manual es la aproximación lineal de la velocidad del
# sonido, v = 331.5 + 0.61·T.
# =============================================================================

from __future__ import annotations
import logging
import math
from typing import Optional

from scipy import constants

from .formulas import REGISTRO, ResultadoFormula

logger = logging.getLogger("ti_nspire.ondas")

H_PLANCK  = constants.h              # constante de Planck, J·s
H_BARRA   = constants.hbar           # h/2π
C_LUZ     = constants.c              # velocidad de la luz, m/s
MASA_E    = constants.m_e            # masa del electrón, kg
CARGA_E   = constants.e              # carga elemental, C (y el julio por eV)


def _falta_una(pares) -> list:
    return [n for n, val in pares if val is None]


# ── 1. Onda: relación v = λ·f ────────────────────────────────────────────────

def onda(v: Optional[float] = None, longitud_onda: Optional[float] = None,
          frecuencia: Optional[float] = None) -> ResultadoFormula:
    """Onda: v = λ·f (y T = 1/f). Da dos valores y deja el tercero en None."""
    faltantes = _falta_una((("v", v), ("longitud_onda", longitud_onda),
                            ("frecuencia", frecuencia)))
    if len(faltantes) != 1:
        return ResultadoFormula(
            error="Da dos valores (v, longitud_onda, frecuencia) y deja el tercero en None")
    try:
        if v is None:
            v = longitud_onda * frecuencia
        elif longitud_onda is None:
            longitud_onda = v / frecuencia
        else:
            frecuencia = v / longitud_onda
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    periodo = 1 / frecuencia if frecuencia else float("inf")
    return ResultadoFormula({"v": v, "longitud_onda": longitud_onda,
                              "frecuencia": frecuencia, "periodo": periodo},
                             texto=(f"v = λ·f = {v:.6g} m/s (λ={longitud_onda:.6g} m, "
                                    f"f={frecuencia:.6g} Hz, T={periodo:.6g} s)"))


def onda_viajera(amplitud: float, longitud_onda: float, periodo: float,
                  x: float, t: float) -> ResultadoFormula:
    """Onda viajera: y(x,t) = A·sen[2π·(t/T − x/λ)]."""
    if longitud_onda == 0 or periodo == 0:
        return ResultadoFormula(error="λ y T deben ser distintos de cero")
    fase = 2 * math.pi * (t / periodo - x / longitud_onda)
    y = amplitud * math.sin(fase)
    return ResultadoFormula({"y": y, "fase": fase, "amplitud": amplitud,
                              "longitud_onda": longitud_onda, "periodo": periodo,
                              "x": x, "t": t},
                             texto=f"y(x={x:.6g} m, t={t:.6g} s) = {y:.6g} m")


# ── 2. Velocidad de una onda transversal en una cuerda ──────────────────────

def velocidad_cuerda(tension: Optional[float] = None,
                      densidad_lineal: Optional[float] = None,
                      v: Optional[float] = None) -> ResultadoFormula:
    """Onda transversal en una cuerda: v = √(F/μ), μ = masa/longitud (kg/m)."""
    faltantes = _falta_una((("tension", tension), ("densidad_lineal", densidad_lineal), ("v", v)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (tension, densidad_lineal, v) y deja el tercero en None")
    try:
        if v is None:
            v = math.sqrt(tension / densidad_lineal)
        elif tension is None:
            tension = densidad_lineal * v ** 2
        else:
            densidad_lineal = tension / v ** 2
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos (deben ser positivos)")
    return ResultadoFormula({"tension": tension, "densidad_lineal": densidad_lineal, "v": v},
                             texto=f"v = √(F/μ) = {v:.6g} m/s (F={tension:.6g} N, μ={densidad_lineal:.6g} kg/m)")


# ── 3. Interferencia ─────────────────────────────────────────────────────────

def interferencia(diferencia_camino: Optional[float] = None,
                   longitud_onda: Optional[float] = None,
                   n: Optional[float] = None,
                   tipo: str = "constructiva") -> ResultadoFormula:
    """
    Interferencia entre dos ondas según la diferencia de camino Δl:
      constructiva (en fase):    Δl = n·λ
      destructiva (en oposición): Δl = (n+½)·λ
    Si das Δl y λ, deduce el orden n y de qué tipo es la interferencia.
    """
    tipo = (tipo or "constructiva").strip().lower()
    if tipo not in ("constructiva", "destructiva"):
        return ResultadoFormula(error='tipo debe ser "constructiva" o "destructiva"')

    if diferencia_camino is not None and longitud_onda:
        cociente = diferencia_camino / longitud_onda
        n_cerca = round(cociente)
        if abs(cociente - n_cerca) < 1e-6:
            clase, orden = "constructiva", float(n_cerca)
        elif abs(abs(cociente - math.floor(cociente)) - 0.5) < 1e-6:
            clase, orden = "destructiva", float(math.floor(cociente))
        else:
            clase, orden = "parcial (ni máximo ni mínimo)", cociente
        return ResultadoFormula(
            {"diferencia_camino": diferencia_camino, "longitud_onda": longitud_onda,
             "n": orden, "tipo": clase, "cociente": cociente},
            texto=(f"Δl/λ = {cociente:.6g}  →  interferencia {clase}"
                   + (f" de orden n = {orden:.0f}" if isinstance(clase, str)
                      and clase != "parcial (ni máximo ni mínimo)" else "")))

    faltantes = _falta_una((("diferencia_camino", diferencia_camino),
                            ("longitud_onda", longitud_onda), ("n", n)))
    if len(faltantes) != 1:
        return ResultadoFormula(
            error="Da dos valores (diferencia_camino, longitud_onda, n) y deja el tercero en None")
    factor = n if tipo == "constructiva" else (n if n is None else n + 0.5)
    try:
        if diferencia_camino is None:
            diferencia_camino = factor * longitud_onda
        elif longitud_onda is None:
            longitud_onda = diferencia_camino / factor
        else:
            cociente = diferencia_camino / longitud_onda
            n = cociente if tipo == "constructiva" else cociente - 0.5
    except (ZeroDivisionError, TypeError):
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"diferencia_camino": diferencia_camino,
                              "longitud_onda": longitud_onda, "n": n, "tipo": tipo},
                             texto=(f"Interferencia {tipo}: Δl = {diferencia_camino:.6g} m "
                                    f"(λ={longitud_onda:.6g} m, n={n:.6g})"))


# ── 4. Onda estacionaria ─────────────────────────────────────────────────────

def onda_estacionaria(longitud: Optional[float] = None,
                       longitud_onda: Optional[float] = None,
                       n: float = 1, extremos: str = "fijos",
                       v: Optional[float] = None) -> ResultadoFormula:
    """
    Onda estacionaria en el armónico n:
      extremos "fijos"  — cuerda fija en los dos extremos (o tubo abierto-abierto):
                          L = n·λ/2
      extremos "libre"  — un extremo libre (tubo abierto-cerrado):
                          L = (2n−1)·λ/4  → solo armónicos impares
    Con la velocidad v calcula además la frecuencia del armónico.
    """
    extremos = (extremos or "fijos").strip().lower()
    if extremos not in ("fijos", "libre"):
        return ResultadoFormula(error='extremos debe ser "fijos" o "libre"')
    if n < 1:
        return ResultadoFormula(error="El armónico n debe ser 1 o mayor")
    if (longitud is None) == (longitud_onda is None):
        return ResultadoFormula(error="Da exactamente uno: la longitud o la longitud de onda")

    if extremos == "fijos":
        relacion = "L = n·λ/2"
        if longitud_onda is None:
            longitud_onda = 2 * longitud / n
        else:
            longitud = n * longitud_onda / 2
    else:
        relacion = "L = (2n−1)·λ/4"
        if longitud_onda is None:
            longitud_onda = 4 * longitud / (2 * n - 1)
        else:
            longitud = (2 * n - 1) * longitud_onda / 4

    valores = {"longitud": longitud, "longitud_onda": longitud_onda,
               "n": n, "extremos": extremos}
    lineas = [f"{relacion} (armónico n={n:.0f}, extremos {extremos})",
              f"L = {longitud:.6g} m,  λ = {longitud_onda:.6g} m"]
    if v is not None:
        frecuencia = v / longitud_onda
        valores.update(v=v, frecuencia=frecuencia)
        lineas.append(f"f = v/λ = {frecuencia:.6g} Hz")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 5. Refracción (ley de Snell) ─────────────────────────────────────────────

def refraccion(theta1: Optional[float] = None, theta2: Optional[float] = None,
                n1: float = 1.0, n2: Optional[float] = None,
                v1: Optional[float] = None) -> ResultadoFormula:
    """
    Ley de Snell: n₁·sen(θ₁) = n₂·sen(θ₂), con los ángulos en grados.
    Deja en None el que quieras despejar (θ₁, θ₂ o n₂). Si das v₁, calcula
    también v₂ = v₁·n₁/n₂ y la razón de longitudes de onda.
    """
    faltantes = _falta_una((("theta1", theta1), ("theta2", theta2), ("n2", n2)))
    if len(faltantes) != 1:
        return ResultadoFormula(error="Da dos valores (theta1, theta2, n2) y deja el tercero en None")
    try:
        if theta2 is None:
            sen2 = n1 * math.sin(math.radians(theta1)) / n2
            if abs(sen2) > 1:
                return ResultadoFormula(
                    error="Reflexión total interna: no hay rayo refractado con ese ángulo")
            theta2 = math.degrees(math.asin(sen2))
        elif theta1 is None:
            sen1 = n2 * math.sin(math.radians(theta2)) / n1
            if abs(sen1) > 1:
                return ResultadoFormula(error="No hay solución: el seno saldría mayor que 1")
            theta1 = math.degrees(math.asin(sen1))
        else:
            sen2 = math.sin(math.radians(theta2))
            if sen2 == 0:
                return ResultadoFormula(error="θ₂ no puede ser 0 para despejar n₂")
            n2 = n1 * math.sin(math.radians(theta1)) / sen2
    except (ZeroDivisionError, ValueError):
        return ResultadoFormula(error="Valores inválidos")

    valores = {"theta1": theta1, "theta2": theta2, "n1": n1, "n2": n2,
               "n_relativo": n2 / n1}
    lineas = [f"n₁·sen(θ₁) = n₂·sen(θ₂):  θ₁={theta1:.6g}°, θ₂={theta2:.6g}°, "
              f"n₁={n1:.6g}, n₂={n2:.6g}"]
    if v1 is not None:
        v2 = v1 * n1 / n2
        valores.update(v1=v1, v2=v2)
        lineas.append(f"v₂ = v₁·n₁/n₂ = {v2:.6g} m/s  (λ₁/λ₂ = {n2 / n1:.6g})")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 6. Frecuencia natural de una cuerda ─────────────────────────────────────

def frecuencia_natural_cuerda(longitud: float, tension: float,
                               densidad_lineal: float, n: float = 1
                               ) -> ResultadoFormula:
    """Armónico n de una cuerda fija en ambos extremos: f = (n/2L)·√(F/μ)."""
    if longitud <= 0 or densidad_lineal <= 0 or tension <= 0:
        return ResultadoFormula(error="L, F y μ deben ser mayores que cero")
    v = math.sqrt(tension / densidad_lineal)
    f = n * v / (2 * longitud)
    return ResultadoFormula({"longitud": longitud, "tension": tension,
                              "densidad_lineal": densidad_lineal, "n": n,
                              "v": v, "frecuencia": f, "longitud_onda": 2 * longitud / n},
                             texto=(f"f = (n/2L)·√(F/μ) = {f:.6g} Hz  "
                                    f"(armónico n={n:.0f}, v={v:.6g} m/s)"))


# ── 7. Velocidad del sonido en el aire ──────────────────────────────────────

def velocidad_sonido(temperatura: float = 20.0) -> ResultadoFormula:
    """
    Velocidad del sonido en el aire: v = 331.5 + 0.61·T (T en °C), la
    aproximación lineal del manual. Se muestra también la forma exacta
    v = 331.3·√(1+T/273.15) para comparar.
    """
    v_lineal = 331.5 + 0.61 * temperatura
    if temperatura <= -273.15:
        return ResultadoFormula(error="La temperatura debe ser mayor que el cero absoluto")
    v_exacta = 331.3 * math.sqrt(1 + temperatura / 273.15)
    return ResultadoFormula({"temperatura": temperatura, "v": v_lineal, "v_exacta": v_exacta},
                             texto=(f"v = 331.5 + 0.61·T = {v_lineal:.6g} m/s a {temperatura:.6g} °C\n"
                                    f"(forma exacta: {v_exacta:.6g} m/s)"))


# ── 8. Efecto Doppler ────────────────────────────────────────────────────────

def efecto_doppler(f_fuente: float, v_observador: float = 0.0,
                    v_fuente: float = 0.0, v_sonido: Optional[float] = None,
                    temperatura: Optional[float] = None) -> ResultadoFormula:
    """
    Efecto Doppler: f' = f·(v + v_obs)/(v − v_fuente).
    Los signos siguen el convenio de acercamiento: v_observador positivo si el
    observador se acerca a la fuente, v_fuente positivo si la fuente se acerca
    al observador. Si no das v_sonido, se calcula del aire a `temperatura`
    (20 °C por defecto).
    """
    if v_sonido is None:
        t = 20.0 if temperatura is None else temperatura
        v_sonido = 331.5 + 0.61 * t
    denominador = v_sonido - v_fuente
    if denominador == 0:
        return ResultadoFormula(error="La fuente viaja a la velocidad del sonido: f' → ∞")
    f_observada = f_fuente * (v_sonido + v_observador) / denominador
    desplazamiento = f_observada - f_fuente
    return ResultadoFormula({"f_fuente": f_fuente, "f_observada": f_observada,
                              "v_sonido": v_sonido, "v_observador": v_observador,
                              "v_fuente": v_fuente, "desplazamiento": desplazamiento},
                             texto=(f"f' = f·(v+v_obs)/(v−v_fuente) = {f_observada:.6g} Hz "
                                    f"(f={f_fuente:.6g} Hz, Δf={desplazamiento:+.6g} Hz, "
                                    f"v_sonido={v_sonido:.6g} m/s)"))


# ── 9. Batido (pulsación) ────────────────────────────────────────────────────

def batido(f1: float, f2: float) -> ResultadoFormula:
    """Batido entre dos ondas: f_batido = |f₁ − f₂|."""
    f_batido = abs(f1 - f2)
    return ResultadoFormula({"f1": f1, "f2": f2, "f_batido": f_batido,
                              "f_media": (f1 + f2) / 2},
                             texto=(f"f_batido = |f₁ − f₂| = {f_batido:.6g} Hz "
                                    f"(se oye un tono de {(f1 + f2) / 2:.6g} Hz pulsando)"))


# ── 10. Reflectividad de la luz ──────────────────────────────────────────────

def reflectividad(n1: float, n2: float) -> ResultadoFormula:
    """Reflectividad en incidencia normal: R = ((n₁−n₂)/(n₁+n₂))², T = 1−R."""
    if n1 + n2 == 0:
        return ResultadoFormula(error="n₁+n₂ no puede ser 0")
    r = ((n1 - n2) / (n1 + n2)) ** 2
    return ResultadoFormula({"n1": n1, "n2": n2, "r": r, "t": 1 - r},
                             texto=(f"R = ((n₁−n₂)/(n₁+n₂))² = {r:.6g} ({r * 100:.4g} % reflejado, "
                                    f"{(1 - r) * 100:.4g} % transmitido)"))


# ── 11. Ángulo crítico ───────────────────────────────────────────────────────

def angulo_critico(n1: float, n2: float = 1.0) -> ResultadoFormula:
    """Ángulo crítico de reflexión total: sen(θc) = n₂/n₁ (requiere n₁ > n₂)."""
    if n1 <= 0 or n2 <= 0:
        return ResultadoFormula(error="Los índices deben ser mayores que cero")
    if n1 <= n2:
        return ResultadoFormula(
            error=f"No hay reflexión total: hace falta n₁ > n₂ (n₁={n1:.6g}, n₂={n2:.6g})")
    theta_c = math.degrees(math.asin(n2 / n1))
    return ResultadoFormula({"n1": n1, "n2": n2, "theta_c": theta_c},
                             texto=f"θc = arcsen(n₂/n₁) = {theta_c:.6g}°")


# ── 12. Onda de De Broglie ───────────────────────────────────────────────────

def onda_de_broglie(masa: Optional[float] = None, velocidad: Optional[float] = None,
                     longitud_onda: Optional[float] = None) -> ResultadoFormula:
    """
    Longitud de onda de De Broglie: λ = h/(m·v). Si no das la masa, usa la del
    electrón. Deja en None la incógnita (λ o la velocidad).
    """
    masa = MASA_E if masa is None else masa
    if masa <= 0:
        return ResultadoFormula(error="La masa debe ser mayor que cero")
    if (velocidad is None) == (longitud_onda is None):
        return ResultadoFormula(error="Da exactamente uno: la velocidad o la longitud de onda")
    try:
        if longitud_onda is None:
            longitud_onda = H_PLANCK / (masa * velocidad)
        else:
            velocidad = H_PLANCK / (masa * longitud_onda)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    momento = masa * velocidad
    return ResultadoFormula({"masa": masa, "velocidad": velocidad,
                              "longitud_onda": longitud_onda, "momento": momento},
                             texto=(f"λ = h/(m·v) = {longitud_onda:.6g} m "
                                    f"(v={velocidad:.6g} m/s, p={momento:.6g} kg·m/s)"))


# ── 13. Condición cuántica (Bohr) ────────────────────────────────────────────

def condicion_cuantica(n: float = 1, masa: Optional[float] = None,
                        velocidad: Optional[float] = None,
                        r: Optional[float] = None) -> ResultadoFormula:
    """
    Condición cuántica de Bohr: 2π·r = n·λ, o m·v·r = n·ħ (momento angular
    cuantizado). Da la masa (por defecto la del electrón) y dos de (v, r).
    """
    masa = MASA_E if masa is None else masa
    if n < 1:
        return ResultadoFormula(error="El número cuántico n debe ser 1 o mayor")
    momento_angular = n * H_BARRA
    valores = {"n": n, "masa": masa, "momento_angular": momento_angular}
    lineas = [f"L = n·ħ = {momento_angular:.6g} kg·m²/s"]
    try:
        if velocidad is not None and r is None:
            r = momento_angular / (masa * velocidad)
        elif r is not None and velocidad is None:
            velocidad = momento_angular / (masa * r)
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    if velocidad is not None and r is not None:
        longitud_onda = 2 * math.pi * r / n
        valores.update(velocidad=velocidad, r=r, longitud_onda=longitud_onda)
        lineas.append(f"r = {r:.6g} m,  v = {velocidad:.6g} m/s")
        lineas.append(f"λ = 2πr/n = {longitud_onda:.6g} m")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 14. Efecto fotoeléctrico ─────────────────────────────────────────────────

def efecto_fotoelectrico(trabajo_ev: float, longitud_onda: Optional[float] = None,
                          frecuencia: Optional[float] = None) -> ResultadoFormula:
    """
    Efecto fotoeléctrico: h·ν = W + Ek_máx. `trabajo_ev` es la función de
    trabajo en eV. Da la longitud de onda (m) o la frecuencia (Hz) de la luz.
    Calcula la energía cinética máxima, el potencial de frenado y el umbral.
    """
    if (longitud_onda is None) == (frecuencia is None):
        return ResultadoFormula(error="Da exactamente uno: la longitud de onda o la frecuencia")
    if longitud_onda is not None:
        if longitud_onda <= 0:
            return ResultadoFormula(error="La longitud de onda debe ser mayor que cero")
        frecuencia = C_LUZ / longitud_onda
    else:
        longitud_onda = C_LUZ / frecuencia

    energia_foton = H_PLANCK * frecuencia
    trabajo_j = trabajo_ev * CARGA_E
    ek = energia_foton - trabajo_j
    f_umbral = trabajo_j / H_PLANCK
    lambda_umbral = C_LUZ / f_umbral
    valores = {"trabajo_ev": trabajo_ev, "frecuencia": frecuencia,
               "longitud_onda": longitud_onda, "energia_foton": energia_foton,
               "energia_foton_ev": energia_foton / CARGA_E, "ek": ek,
               "ek_ev": ek / CARGA_E, "f_umbral": f_umbral,
               "lambda_umbral": lambda_umbral, "hay_emision": ek > 0}
    lineas = [f"E del fotón = h·ν = {energia_foton / CARGA_E:.6g} eV "
              f"(λ={longitud_onda:.6g} m, f={frecuencia:.6g} Hz)",
              f"Umbral: f₀ = {f_umbral:.6g} Hz, λ₀ = {lambda_umbral:.6g} m"]
    if ek > 0:
        lineas.append(f"Ek_máx = h·ν − W = {ek / CARGA_E:.6g} eV "
                       f"(potencial de frenado V₀ = {ek / CARGA_E:.6g} V)")
    else:
        lineas.append("No hay emisión: el fotón no llega a la función de trabajo")
    return ResultadoFormula(valores, texto="\n".join(lineas))


# ── 15. Condición de frecuencia (salto entre niveles) ───────────────────────

def condicion_frecuencia(em_ev: Optional[float] = None, en_ev: Optional[float] = None,
                          frecuencia: Optional[float] = None,
                          longitud_onda: Optional[float] = None) -> ResultadoFormula:
    """
    Salto entre niveles de energía: h·ν = Em − En (energías en eV, con Em > En).
    Da los dos niveles para obtener la frecuencia y la longitud de onda del
    fotón emitido, o da uno de los niveles y el fotón para despejar el otro.
    """
    if em_ev is not None and en_ev is not None:
        delta_ev = em_ev - en_ev
        if delta_ev <= 0:
            return ResultadoFormula(error="Em debe ser mayor que En para que se emita un fotón")
        frecuencia = delta_ev * CARGA_E / H_PLANCK
        longitud_onda = C_LUZ / frecuencia
    else:
        if frecuencia is None:
            if longitud_onda is None or longitud_onda <= 0:
                return ResultadoFormula(
                    error="Da los dos niveles (em_ev, en_ev) o el fotón (frecuencia o longitud_onda)")
            frecuencia = C_LUZ / longitud_onda
        else:
            longitud_onda = C_LUZ / frecuencia
        delta_ev = H_PLANCK * frecuencia / CARGA_E
        if em_ev is not None:
            en_ev = em_ev - delta_ev
        elif en_ev is not None:
            em_ev = en_ev + delta_ev
    return ResultadoFormula({"em_ev": em_ev, "en_ev": en_ev, "delta_ev": delta_ev,
                              "frecuencia": frecuencia, "longitud_onda": longitud_onda},
                             texto=(f"h·ν = Em − En = {delta_ev:.6g} eV\n"
                                    f"f = {frecuencia:.6g} Hz,  λ = {longitud_onda:.6g} m "
                                    f"({longitud_onda * 1e9:.6g} nm)"))


# ── 16. Onda luminosa ────────────────────────────────────────────────────────

def onda_luminosa(longitud_onda: Optional[float] = None,
                   frecuencia: Optional[float] = None,
                   energia_ev: Optional[float] = None) -> ResultadoFormula:
    """
    Luz en el vacío: λ = c/ν y E = h·ν. Da uno cualquiera de los tres
    (longitud de onda en m, frecuencia en Hz o energía del fotón en eV).
    """
    dados = [x for x in (longitud_onda, frecuencia, energia_ev) if x is not None]
    if len(dados) != 1:
        return ResultadoFormula(
            error="Da exactamente uno: longitud_onda, frecuencia o energia_ev")
    try:
        if longitud_onda is not None:
            frecuencia = C_LUZ / longitud_onda
        elif energia_ev is not None:
            frecuencia = energia_ev * CARGA_E / H_PLANCK
        longitud_onda = C_LUZ / frecuencia
        energia_ev = H_PLANCK * frecuencia / CARGA_E
    except ZeroDivisionError:
        return ResultadoFormula(error="División por cero")
    return ResultadoFormula({"longitud_onda": longitud_onda, "frecuencia": frecuencia,
                              "energia_ev": energia_ev,
                              "energia_j": energia_ev * CARGA_E},
                             texto=(f"λ = {longitud_onda:.6g} m ({longitud_onda * 1e9:.6g} nm),  "
                                    f"f = {frecuencia:.6g} Hz,  E = {energia_ev:.6g} eV"))


# ── Registro para invocar estas fórmulas desde la consola CAS ───────────────

REGISTRO.registrar(
    kwargs={
        "onda": onda,
        "onda_viajera": onda_viajera,
        "velocidad_cuerda": velocidad_cuerda,
        "interferencia": interferencia,
        "onda_estacionaria": onda_estacionaria,
        "refraccion": refraccion,
        "frecuencia_natural_cuerda": frecuencia_natural_cuerda,
        "velocidad_sonido": velocidad_sonido,
        "efecto_doppler": efecto_doppler,
        "batido": batido,
        "reflectividad": reflectividad,
        "angulo_critico": angulo_critico,
        "onda_de_broglie": onda_de_broglie,
        "condicion_cuantica": condicion_cuantica,
        "efecto_fotoelectrico": efecto_fotoelectrico,
        "condicion_frecuencia": condicion_frecuencia,
        "onda_luminosa": onda_luminosa,
    },
)
