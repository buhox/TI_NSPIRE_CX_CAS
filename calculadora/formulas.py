# =============================================================================
# FÓRMULAS — tipo de resultado y registro compartidos
#
# ResultadoFormula: lo que devuelve toda fórmula física o geométrica portada
# de la librería científica de calculadoras de bolsillo. Distinto de
# ResultadoCAS: aquí los valores son numéricos, no expresiones simbólicas.
#
# REGISTRO: permite invocar cualquiera de esas fórmulas por su nombre desde la
# consola CAS, ej. "ley_ohm(v=12, i=2)". Cada módulo de fórmulas (circuitos,
# campos, ...) registra sus funciones al importarse.
# =============================================================================

from __future__ import annotations

from typing import Callable, Optional


class ResultadoFormula:
    """Encapsula el resultado de evaluar una fórmula física o geométrica."""

    def __init__(self, valores: dict | None = None, texto: str = "", error: str = ""):
        self.valores = valores or {}
        self.texto   = texto
        self.error   = error
        self.ok      = error == ""

    def __str__(self) -> str:
        return self.texto or self.error

    def __repr__(self) -> str:
        return f"ResultadoFormula(ok={self.ok}, valores={self.valores!r})"


# ── Invocación por nombre desde la consola CAS ───────────────────────────────

def _parsear_valor(token: str):
    """Convierte un token de la consola a float, o lo deja como texto (para
    parámetros no numéricos como orden="RC"). Vacío o "?" significa incógnita."""
    token = token.strip()
    if token in ("", "?", "none", "None"):
        return None
    try:
        return float(token)
    except ValueError:
        return token.strip("\"'")


def _parsear_argumentos(texto: str) -> tuple[list, dict]:
    """Separa "r=1000, c=1e-6" en ([], {"r":1000.0, "c":1e-06}) y "10,20,30"
    en ([10.0,20.0,30.0], {})."""
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


class RegistroFormulas:
    """
    Índice de las fórmulas invocables por nombre desde la consola CAS.

    Cada función se registra según cómo recibe sus argumentos:
      kwargs       — "clave=valor" (la mayoría): ley_ohm(v=12, i=2)
      posicionales — valores sueltos: resistencia_serie(10,20,30)
      lista        — valores sueltos como una lista, con "?" en la incógnita:
                     kirchhoff_corrientes(2,-1,?)
    """

    def __init__(self):
        self._kwargs: dict[str, Callable] = {}
        self._posicionales: dict[str, Callable] = {}
        self._lista: dict[str, Callable] = {}

    def registrar(self, kwargs: dict | None = None,
                  posicionales: dict | None = None,
                  lista: dict | None = None) -> None:
        self._kwargs.update(kwargs or {})
        self._posicionales.update(posicionales or {})
        self._lista.update(lista or {})

    @property
    def nombres(self) -> list[str]:
        return sorted(set(self._kwargs) | set(self._posicionales) | set(self._lista))

    def invocar(self, nombre: str, texto_argumentos: str) -> Optional[ResultadoFormula]:
        """
        Invoca la fórmula `nombre` con los argumentos dados en texto. Retorna
        None si `nombre` no es una fórmula registrada, para que el llamador
        pueda intentar otra ruta de evaluación (p. ej. SymPy).
        """
        if nombre not in self.nombres:
            return None
        posicionales, nombrados = _parsear_argumentos(texto_argumentos)
        try:
            if nombre in self._kwargs:
                if posicionales:
                    return ResultadoFormula(
                        error=f"{nombre}(...) usa solo clave=valor, ej: v=12, i=2")
                return self._kwargs[nombre](**nombrados)
            if nombre in self._posicionales:
                if nombrados:
                    return ResultadoFormula(
                        error=f"{nombre}(...) usa solo valores por posición, ej: 10, 20, 30")
                return self._posicionales[nombre](*posicionales)
            if nombrados:
                return ResultadoFormula(error=f"{nombre}(...) usa solo valores por posición")
            return self._lista[nombre](posicionales)
        except TypeError as e:
            return ResultadoFormula(error=f"Argumentos inválidos para {nombre}: {e}")


REGISTRO = RegistroFormulas()
