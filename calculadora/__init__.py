from .cas import evaluar, simplificar, expandir, factorizar, resolver
from .cas import derivar, integrar, limite, serie_taylor
from .cas import crear_matriz, determinante, inversa, valores_propios
from .cas import factores_primos, es_primo, combinatoria
from .formulas import ResultadoFormula
from .circuitos import (
    ley_ohm, resistencia_serie, resistencia_paralelo, circuito_dc,
    potencia_dc, calor_joule, conductancia,
    kirchhoff_corrientes, kirchhoff_voltajes, puente_wheatstone,
    valor_instantaneo, valor_efectivo, potencia_ac, factor_potencia,
    transformador, reactancia_inductiva, reactancia_capacitiva,
    impedancia, frecuencia_natural, oscilacion_electrica,
    circuito_rc_primer_orden, circuito_rlc_segundo_orden,
)
