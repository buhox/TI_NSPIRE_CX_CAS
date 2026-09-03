# =============================================================================
# RESULTADO DE FÓRMULA — tipo compartido por los módulos de fórmulas
# (circuitos, geometría, física...) portados de la librería científica de
# calculadoras de bolsillo. Distinto de ResultadoCAS: aquí los valores son
# numéricos, no expresiones simbólicas.
# =============================================================================

from __future__ import annotations


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
