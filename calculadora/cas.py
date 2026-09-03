# =============================================================================
# MOTOR CAS — Funciones simbólicas y numéricas
# =============================================================================
# Implementa las funciones principales de la TI-Nspire CX CAS usando SymPy.
# Organizado igual que los menús de la calculadora:
#   Álgebra, Cálculo, Matrices, Estadística, Números
# =============================================================================

from __future__ import annotations
import logging
import re
from typing import Any

from . import campos, circuitos, movimiento, ondas   # se registran en formulas.REGISTRO al importarse
from .formulas import REGISTRO

logger = logging.getLogger("ti_nspire.cas")

_RE_LLAMADA = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)$", re.DOTALL)

try:
    import sympy as sp
    from sympy import (
        symbols, sympify, simplify, expand, factor, collect,
        solve, dsolve, Eq,
        diff, integrate, limit, series, Sum, Product,
        Matrix,
        sin, cos, tan, asin, acos, atan, atan2,
        sinh, cosh, tanh,
        exp, log, ln, sqrt, Abs, sign,
        pi, E, I, oo, zoo,
        Rational, Float, Integer,
        latex, pretty,
        nsolve, nsimplify,
        gcd, lcm, factorint, isprime, nextprime,
        binomial, factorial, fibonacci,
        re, im, conjugate, Abs as Modulo,
        floor, ceiling,
        apart, together, cancel,
        trigsimp, radsimp, ratsimp,
        zeros, ones, eye, diag,
    )
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
    _SYMPY_OK = True
except ImportError:
    _SYMPY_OK = False
    logger.error("SymPy no disponible. Instala con: pip install sympy")


# ── Variables simbólicas globales por defecto ─────────────────────────────────
# El usuario puede usar x, y, z, t, n, k, a, b, c directamente.
if _SYMPY_OK:
    x, y, z, t, n, k, a, b, c = symbols("x y z t n k a b c")
    _VARS_DEFAULT = {"x": x, "y": y, "z": z, "t": t, "n": n,
                     "k": k, "a": a, "b": b, "c": c,
                     "pi": pi, "e": E, "E": E, "i": I, "oo": oo,
                     "inf": oo}
    _TRANSFORMACIONES = (standard_transformations +
                         (implicit_multiplication_application, convert_xor))


# =============================================================================
# EVALUADOR DE EXPRESIONES
# =============================================================================

class ResultadoCAS:
    """Encapsula el resultado de una operación CAS."""

    def __init__(self, expresion=None, latex_str: str = "",
                 texto: str = "", error: str = ""):
        self.expresion  = expresion
        self.latex_str  = latex_str
        self.texto      = texto
        self.error      = error
        self.ok         = error == ""

    def __str__(self) -> str:
        return self.texto or self.error


def evaluar(entrada: str) -> ResultadoCAS:
    """
    Evalúa una expresión matemática en texto y retorna el resultado CAS.

    Ejemplos:
        evaluar("2+3")           → 5
        evaluar("diff(x^2, x)") → 2*x
        evaluar("solve(x^2-4)") → [-2, 2]
    """
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")

    entrada = entrada.strip()
    if not entrada:
        return ResultadoCAS(error="Entrada vacía")

    # Fórmulas de física invocadas por nombre, ej: ley_ohm(v=12, i=2)
    m = _RE_LLAMADA.match(entrada)
    if m:
        r = REGISTRO.invocar(m.group(1), m.group(2))
        if r is not None:
            return ResultadoCAS(texto=r.texto) if r.ok else ResultadoCAS(error=r.error)

    # Reemplazos de sintaxis TI → SymPy
    entrada = _normalizar_entrada(entrada)

    try:
        # Intentar parsear y evaluar
        expr = parse_expr(entrada, local_dict=_VARS_DEFAULT,
                          transformations=_TRANSFORMACIONES)
        resultado = expr

        return ResultadoCAS(
            expresion=resultado,
            latex_str=latex(resultado),
            texto=pretty(resultado, use_unicode=True),
        )
    except Exception as e:
        return ResultadoCAS(error=f"Error: {e}")


def _normalizar_entrada(s: str) -> str:
    """Convierte sintaxis TI-Nspire a sintaxis SymPy."""
    reemplazos = {
        "^":  "**",      # Potencia TI → Python
        "√":  "sqrt",
        "∞":  "oo",
        "π":  "pi",
        "→":  ",",       # store TI: a→b no aplica aquí
        "×":  "*",
        "÷":  "/",
        "–":  "-",       # Guión largo → menos
    }
    for viejo, nuevo in reemplazos.items():
        s = s.replace(viejo, nuevo)
    return s


# =============================================================================
# ÁLGEBRA
# =============================================================================

def simplificar(expr_str: str) -> ResultadoCAS:
    """Simplifica una expresión algebraica."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        res = simplify(r.expresion)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def expandir(expr_str: str) -> ResultadoCAS:
    """Expande productos y potencias."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        res = expand(r.expresion)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def factorizar(expr_str: str) -> ResultadoCAS:
    """Factoriza una expresión polinómica."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        res = factor(r.expresion)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def _dividir_nivel_superior(texto: str, separador: str = ",") -> list[str]:
    """Divide por `separador`, ignorando los que estén dentro de paréntesis."""
    partes, actual, profundidad = [], [], 0
    for ch in texto:
        if ch in "([{":
            profundidad += 1
        elif ch in ")]}":
            profundidad -= 1
        if ch == separador and profundidad == 0:
            partes.append("".join(actual))
            actual = []
        else:
            actual.append(ch)
    partes.append("".join(actual))
    return [p.strip() for p in partes if p.strip()]


def _parsear_ecuacion(texto: str):
    """Convierte "lhs = rhs" en Eq(lhs, rhs); sin "=", la expresión se iguala a 0."""
    if "=" in texto and "==" not in texto:
        izq, _, der = texto.partition("=")
        return Eq(parse_expr(izq, local_dict=_VARS_DEFAULT,
                             transformations=_TRANSFORMACIONES),
                  parse_expr(der, local_dict=_VARS_DEFAULT,
                             transformations=_TRANSFORMACIONES))
    return parse_expr(texto, local_dict=_VARS_DEFAULT,
                      transformations=_TRANSFORMACIONES)


def resolver(ecuacion_str: str, variable: str = "x") -> ResultadoCAS:
    """
    Resuelve una ecuación o un sistema.

    Formatos aceptados:
        "x^2 - 4"               → se iguala a cero, resuelve respecto a x
        "x^2 - 4 = 0"           → con igualdad explícita
        "x + y = 5, x - y = 1"  → sistema (ecuaciones separadas por comas)

    En un sistema, si `variable` no nombra tantas incógnitas como ecuaciones,
    se resuelve para todas las que aparezcan. `variable` también acepta varias
    separadas por comas ("x,y").
    """
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")
    try:
        ecuacion_str = _normalizar_entrada(ecuacion_str)
        ecuaciones = [_parsear_ecuacion(p)
                      for p in _dividir_nivel_superior(ecuacion_str)]
        if not ecuaciones:
            return ResultadoCAS(error="No hay ninguna ecuación que resolver")

        incognitas = [symbols(v) for v in _dividir_nivel_superior(variable or "x")]
        if len(ecuaciones) > 1 and len(incognitas) < len(ecuaciones):
            # Sistema sin incógnitas suficientes nombradas: usa las que aparezcan
            libres = set().union(*(ec.free_symbols for ec in ecuaciones))
            incognitas = sorted(libres, key=lambda s: s.name)

        objetivo = ecuaciones if len(ecuaciones) > 1 else ecuaciones[0]
        buscadas = incognitas if len(incognitas) > 1 else incognitas[0]
        sol = solve(objetivo, buscadas)

        return ResultadoCAS(sol, latex(sol), pretty(sol, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def fracciones_parciales(expr_str: str, variable: str = "x") -> ResultadoCAS:
    """Descompone en fracciones parciales."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        var = symbols(variable)
        res = apart(r.expresion, var)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


# =============================================================================
# CÁLCULO
# =============================================================================

def derivar(expr_str: str, variable: str = "x", orden: int = 1) -> ResultadoCAS:
    """Calcula la derivada de orden n."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        var = symbols(variable)
        res = diff(r.expresion, var, orden)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def integrar(expr_str: str, variable: str = "x",
             limite_inf=None, limite_sup=None) -> ResultadoCAS:
    """
    Calcula la integral indefinida o definida.

    Si se dan límites, calcula integral definida.
    """
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        var = symbols(variable)
        if limite_inf is not None and limite_sup is not None:
            a_val = parse_expr(str(limite_inf), local_dict=_VARS_DEFAULT,
                               transformations=_TRANSFORMACIONES)
            b_val = parse_expr(str(limite_sup), local_dict=_VARS_DEFAULT,
                               transformations=_TRANSFORMACIONES)
            res = integrate(r.expresion, (var, a_val, b_val))
        else:
            res = integrate(r.expresion, var)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def limite(expr_str: str, variable: str = "x", punto: str = "0",
           direccion: str = "+-") -> ResultadoCAS:
    """Calcula el límite de una expresión."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        var  = symbols(variable)
        pto  = parse_expr(_normalizar_entrada(punto),
                          local_dict=_VARS_DEFAULT,
                          transformations=_TRANSFORMACIONES)
        res  = limit(r.expresion, var, pto, direccion)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def serie_taylor(expr_str: str, variable: str = "x",
                 punto: int = 0, orden: int = 6) -> ResultadoCAS:
    """Calcula la serie de Taylor alrededor de un punto."""
    r = evaluar(expr_str)
    if not r.ok:
        return r
    try:
        var = symbols(variable)
        res = series(r.expresion, var, punto, orden)
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


# =============================================================================
# MATRICES
# =============================================================================

def crear_matriz(filas: list[list]) -> ResultadoCAS:
    """Crea una matriz desde una lista de listas."""
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")
    try:
        m = Matrix(filas)
        return ResultadoCAS(m, latex(m), pretty(m, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def determinante(filas: list[list]) -> ResultadoCAS:
    """Calcula el determinante de una matriz cuadrada."""
    r = crear_matriz(filas)
    if not r.ok:
        return r
    try:
        res = r.expresion.det()
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def inversa(filas: list[list]) -> ResultadoCAS:
    """Calcula la matriz inversa."""
    r = crear_matriz(filas)
    if not r.ok:
        return r
    try:
        res = r.expresion.inv()
        return ResultadoCAS(res, latex(res), pretty(res, use_unicode=True))
    except Exception as e:
        return ResultadoCAS(error=str(e))


def valores_propios(filas: list[list]) -> ResultadoCAS:
    """Calcula los valores propios (eigenvalues)."""
    r = crear_matriz(filas)
    if not r.ok:
        return r
    try:
        res = r.expresion.eigenvals()
        texto = "\n".join(f"λ = {v}  (mult. {m})" for v, m in res.items())
        return ResultadoCAS(res, str(res), texto)
    except Exception as e:
        return ResultadoCAS(error=str(e))


# =============================================================================
# NÚMEROS Y ARITMÉTICA
# =============================================================================

def factores_primos(n_str: str) -> ResultadoCAS:
    """Factorización en números primos."""
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")
    try:
        n_val = int(sympify(n_str))
        res   = factorint(n_val)
        texto = " × ".join(
            f"{p}^{e}" if e > 1 else str(p)
            for p, e in sorted(res.items())
        )
        return ResultadoCAS(res, texto, texto)
    except Exception as e:
        return ResultadoCAS(error=str(e))


def es_primo(n_str: str) -> ResultadoCAS:
    """Verifica si un número es primo."""
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")
    try:
        n_val  = int(sympify(n_str))
        result = isprime(n_val)
        texto  = f"{n_val} {'es' if result else 'no es'} primo"
        return ResultadoCAS(result, texto, texto)
    except Exception as e:
        return ResultadoCAS(error=str(e))


def combinatoria(n_str: str, r_str: str) -> ResultadoCAS:
    """Calcula C(n, r) — combinaciones."""
    if not _SYMPY_OK:
        return ResultadoCAS(error="SymPy no disponible")
    try:
        n_val = int(sympify(n_str))
        r_val = int(sympify(r_str))
        res   = binomial(n_val, r_val)
        return ResultadoCAS(res, str(res), str(res))
    except Exception as e:
        return ResultadoCAS(error=str(e))
