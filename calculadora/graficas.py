# =============================================================================
# MÓDULO DE GRÁFICAS — TI-Nspire CX CAS
# Soporta gráficas 2D y(x) y 3D z(x,y) con Matplotlib + SymPy
# =============================================================================

from __future__ import annotations
import logging
import numpy as np
import matplotlib
matplotlib.use("qtagg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D          # registra la proyección '3d'
from typing import Optional

logger = logging.getLogger("ti_nspire.graficas")

try:
    import sympy as sp
    from sympy import symbols, lambdify, parse_expr
    from sympy.parsing.sympy_parser import (
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
    _SYMPY_OK = True
    _TRANS = standard_transformations + (implicit_multiplication_application, convert_xor)
    _x, _y = symbols("x y")
    _VARS = {"x": _x, "y": _y, "pi": sp.pi, "e": sp.E, "E": sp.E}
except ImportError:
    _SYMPY_OK = False

# Paleta clara (fondo blanco)
COLORES = ["#0550ae", "#c0392b", "#1a6e2e", "#b8860b",
           "#8e44ad", "#16a085", "#d35400", "#2980b9"]
CMAPS_3D = ["Blues_r", "Reds_r", "Greens_r", "YlOrBr",
            "Purples_r", "GnBu", "Oranges_r", "PuBu"]
FONDO  = "#ffffff"
EJES   = "#f5f7fa"
TEXTO  = "#1a1a2e"
GRILLA = "#d0d7de"


def _parsear(expr_str: str):
    s = (expr_str
         .replace("^", "**")
         .replace("√", "sqrt")
         .replace("π", "pi"))
    return parse_expr(s, local_dict=_VARS, transformations=_TRANS)


class WidgetGrafica(FigureCanvas):
    """Widget Matplotlib embebido en PyQt5, soporta modo 2D y 3D."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(7, 5), facecolor=FONDO)
        self._modo_3d = False
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._aplicar_estilo_2d()

    # ── Gestión de ejes ───────────────────────────────────────────────────────

    def _crear_ejes(self, modo_3d: bool = False):
        self.fig.clear()
        if modo_3d:
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax = self.fig.add_subplot(111)
        self._modo_3d = modo_3d

    def _aplicar_estilo_2d(self):
        self.ax.set_facecolor(EJES)
        self.fig.patch.set_facecolor(FONDO)
        self.ax.tick_params(colors=TEXTO)
        self.ax.xaxis.label.set_color(TEXTO)
        self.ax.yaxis.label.set_color(TEXTO)
        self.ax.title.set_color(TEXTO)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(GRILLA)
        self.ax.grid(True, color=GRILLA, linestyle="--", alpha=0.6)

    def _aplicar_estilo_3d(self):
        self.fig.patch.set_facecolor(FONDO)
        self.ax.tick_params(colors=TEXTO, labelsize=8)
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor(GRILLA)
        self.ax.yaxis.pane.set_edgecolor(GRILLA)
        self.ax.zaxis.pane.set_edgecolor(GRILLA)
        self.ax.grid(True, color=GRILLA, linestyle="--", alpha=0.4)
        self.ax.xaxis.label.set_color(TEXTO)
        self.ax.yaxis.label.set_color(TEXTO)
        self.ax.zaxis.label.set_color(TEXTO)

    # ── Gráfica 2D ────────────────────────────────────────────────────────────

    def graficar_funciones(self, funciones: list[str],
                           x_min: float = -10, x_max: float = 10,
                           y_min: Optional[float] = None,
                           y_max: Optional[float] = None) -> str:
        if not _SYMPY_OK:
            return "SymPy no disponible"

        self._crear_ejes(False)
        self._aplicar_estilo_2d()
        x_vals = np.linspace(x_min, x_max, 1000)
        graficadas = 0

        for i, fn_str in enumerate(funciones):
            if not fn_str.strip():
                continue
            try:
                expr   = _parsear(fn_str)
                fn     = lambdify(_x, expr, modules=["numpy"])
                y_vals = np.asarray(fn(x_vals), dtype=float)
                y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)
                color  = COLORES[i % len(COLORES)]
                self.ax.plot(x_vals, y_vals, color=color,
                             linewidth=2, label=f"f{i+1}(x) = {fn_str}")
                graficadas += 1
            except Exception as e:
                logger.warning("Error graficando '%s': %s", fn_str, e)
                return f"Error en f{i+1}: {e}"

        if graficadas == 0:
            return "No se pudo graficar ninguna función"

        self.ax.axhline(0, color=TEXTO, linewidth=0.8, alpha=0.5)
        self.ax.axvline(0, color=TEXTO, linewidth=0.8, alpha=0.5)

        if y_min is not None and y_max is not None:
            self.ax.set_ylim(y_min, y_max)

        self.ax.set_xlim(x_min, x_max)
        self.ax.set_xlabel("x", color=TEXTO)
        self.ax.set_ylabel("y", color=TEXTO)
        self.ax.legend(facecolor=EJES, edgecolor=GRILLA,
                       labelcolor=TEXTO, fontsize=9)
        self.fig.tight_layout(pad=1.5)
        self.draw()
        return ""

    # ── Gráfica 3D ────────────────────────────────────────────────────────────

    def graficar_3d(self, funciones: list[str],
                    x_min: float = -5, x_max: float = 5,
                    y_min: float = -5, y_max: float = 5,
                    resolucion: int = 45) -> str:
        """
        Grafica superficies z = f(x, y).

        Args:
            funciones   : Expresiones en texto, ej: ["x^2 + y^2", "sin(x)*cos(y)"]
            x_min/max   : Rango del eje X (horizontal)
            y_min/max   : Rango del eje Y (profundidad)
            resolucion  : Puntos de la malla (resolucion × resolucion)
        """
        if not _SYMPY_OK:
            return "SymPy no disponible"

        self._crear_ejes(True)

        x_arr = np.linspace(x_min, x_max, resolucion)
        y_arr = np.linspace(y_min, y_max, resolucion)
        X, Y  = np.meshgrid(x_arr, y_arr)

        graficadas = 0
        for i, fn_str in enumerate(funciones):
            if not fn_str.strip():
                continue
            try:
                expr = _parsear(fn_str)
                fn   = lambdify((_x, _y), expr, modules=["numpy"])
                Z    = fn(X, Y)
                # Garantizar array 2D con la forma del meshgrid
                if np.isscalar(Z):
                    Z = np.full(X.shape, float(Z))
                else:
                    Z = np.asarray(Z, dtype=float)
                    if Z.shape != X.shape:
                        Z = np.broadcast_to(Z, X.shape).copy()
                Z = np.where(np.isfinite(Z), Z, np.nan)

                cmap  = CMAPS_3D[i % len(CMAPS_3D)]
                surf  = self.ax.plot_surface(
                    X, Y, Z,
                    cmap=cmap, alpha=0.85,
                    linewidth=0, antialiased=True,
                    label=f"f{i+1}(x,y) = {fn_str}",
                )
                surf._facecolors2d = surf._facecolor3d
                surf._edgecolors2d = surf._edgecolor3d
                graficadas += 1
            except Exception as e:
                logger.warning("Error graficando 3D '%s': %s", fn_str, e)
                return f"Error en f{i+1}: {e}"

        if graficadas == 0:
            return "No se pudo graficar ninguna función"

        self._aplicar_estilo_3d()
        self.ax.set_xlabel("x", labelpad=6)
        self.ax.set_ylabel("y", labelpad=6)
        self.ax.set_zlabel("z", labelpad=6)
        if graficadas > 0:
            try:
                self.ax.legend(facecolor=EJES, edgecolor=GRILLA,
                               labelcolor=TEXTO, fontsize=8,
                               loc='upper left')
            except Exception:
                pass
        self.fig.tight_layout(pad=1.5)
        self.draw()
        return ""

    # ── Dispersión 2D ─────────────────────────────────────────────────────────

    def graficar_puntos(self, xs: list, ys: list, etiqueta: str = "Datos") -> str:
        self._crear_ejes(False)
        self._aplicar_estilo_2d()
        try:
            self.ax.scatter(xs, ys, color=COLORES[0], s=60,
                            edgecolors=FONDO, linewidths=0.8, label=etiqueta)
            self.ax.axhline(0, color=TEXTO, linewidth=0.6, alpha=0.4)
            self.ax.axvline(0, color=TEXTO, linewidth=0.6, alpha=0.4)
            self.ax.legend(facecolor=EJES, edgecolor=GRILLA,
                           labelcolor=TEXTO, fontsize=9)
            self.fig.tight_layout(pad=1.5)
            self.draw()
            return ""
        except Exception as e:
            return str(e)

    # ── Limpiar ───────────────────────────────────────────────────────────────

    def limpiar(self):
        self._crear_ejes(False)
        self._aplicar_estilo_2d()
        self.draw()
