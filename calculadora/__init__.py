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
from .campos import (
    ley_coulomb_electrica, campo_electrico, capacidad_electrica, capacidad_placas,
    capacidad_paralelo, capacidad_serie, constante_dielectrica,
    energia_electrostatica, electron_campo_electrico,
    ley_coulomb_magnetica, campo_magnetico_hilo, campo_magnetico_solenoide,
    flujo_magnetico, fuerza_lorentz, electron_campo_magnetico,
    ley_faraday, induccion_electromagnetica, induccion_mutua, autoinduccion,
)
from .movimiento import (
    movimiento_acelerado, segunda_ley_newton, movimiento_circular,
    oscilacion_armonica, ley_hooke, oscilacion_resorte, pendulo_simple,
    energia_potencial, energia_elastica, energia_cinetica,
    coeficiente_friccion, trabajo, ley_kepler, gravitacion_universal,
    energia_potencial_gravitatoria, velocidad_orbital,
    momento_inercia, momento_angular, conservacion_momento,
)
