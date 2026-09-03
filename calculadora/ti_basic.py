# =============================================================================
# INTÉRPRETE DE TI-BASIC DE TI-NSPIRE
#
# Implementa el lenguaje de la TI-Nspire CX / CX CAS:
#   Define f(x)=Func ... EndFunc      Define p()=Prgm ... EndPrgm
#   Local · → (guardar) · If/Then/ElseIf/Else/EndIf · For/EndFor
#   While/EndWhile · Loop/EndLoop · Exit · Cycle · Try/Else/EndTry
#   Lbl/Goto · Return · Stop · Disp · Request · Pause · DelVar · ©
#
# Detalles del lenguaje que NO son los de Python y aquí se respetan:
#   - Las listas y cadenas se indexan desde 1, no desde 0.
#   - Los identificadores no distinguen mayúsculas de minúsculas.
#   - `=` es comparación; para guardar se usa `→` (o `:=`).
#   - El comentario es `©`.
#
# El programa se ejecuta en el PC, no en la calculadora: los resultados son de
# Python, así que una expresión simbólica no se resuelve como lo haría el CAS.
# =============================================================================
from __future__ import annotations

import math
import random
import re
import threading
from typing import Callable, Optional


# ── Excepciones de control ────────────────────────────────────────────────────

class TIBasicError(Exception):
    """Error del programa del usuario (equivale a un error de la calculadora)."""


class _Detener(Exception):
    """Stop, o el usuario pulsó Detener."""


class _Retornar(Exception):
    def __init__(self, valor=None):
        self.valor = valor


class _Salir(Exception):
    """Exit"""


class _Ciclo(Exception):
    """Cycle"""


class _Saltar(Exception):
    def __init__(self, etiqueta: str):
        self.etiqueta = etiqueta


# ── Tipos del lenguaje ────────────────────────────────────────────────────────

class TIList(list):
    """
    Lista de la Nspire: se indexa desde 1.
    `l[1]` es el primer elemento; `l[0]` es un error, como en la calculadora.
    """

    def _idx(self, i):
        if isinstance(i, slice):
            return i
        i = int(i)
        if i < 1 or i > len(self):
            raise TIBasicError(f"Índice {i} fuera de rango (1..{len(self)})")
        return i - 1

    def __getitem__(self, i):
        if isinstance(i, tuple):        # m[1,2] es el elemento fila 1, columna 2
            valor = self
            for k in i:
                valor = valor[k]
            return valor
        return list.__getitem__(self, self._idx(i))

    def __setitem__(self, i, v):
        if isinstance(i, tuple):
            destino = self
            for k in i[:-1]:
                destino = destino[k]
            destino[i[-1]] = v
            return
        # asignar más allá del final hace crecer la lista, como en la Nspire
        if not isinstance(i, slice):
            n = int(i)
            if n > len(self):
                self.extend([0] * (n - len(self)))
                list.__setitem__(self, n - 1, v)
                return
        list.__setitem__(self, self._idx(i), v)

    def __call__(self, i):
        # en la Nspire l(1) y l[1] son equivalentes
        return self[i]

    def __repr__(self):
        return "{" + ",".join(_formatear(v) for v in self) + "}"


class TICadena(str):
    """Cadena indexada desde 1 (mid/left/right son las funciones normales)."""

    def __getitem__(self, i):
        if isinstance(i, slice):
            return TICadena(str.__getitem__(self, i))
        n = int(i)
        if n < 1 or n > len(self):
            raise TIBasicError(f"Índice {n} fuera de rango (1..{len(self)})")
        return TICadena(str.__getitem__(self, n - 1))


def _formatear(v) -> str:
    """Convierte un valor al texto que mostraría la calculadora."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, TIList) or isinstance(v, list):
        return "{" + ",".join(_formatear(x) for x in v) + "}"
    if isinstance(v, float):
        if math.isnan(v):
            return "undef"
        if math.isinf(v):
            return "∞" if v > 0 else "-∞"
        if v == int(v) and abs(v) < 1e14:
            return str(int(v))
        return f"{v:.12g}"
    if isinstance(v, int):
        return str(v)
    return str(v)


# ── Biblioteca de funciones ───────────────────────────────────────────────────

def _dim(x):
    return len(x)


def _mid(s, inicio, cuenta=None):
    s = str(s)
    i = int(inicio) - 1
    if i < 0:
        raise TIBasicError("mid(): el inicio empieza en 1")
    return TICadena(s[i:i + int(cuenta)] if cuenta is not None else s[i:])


def _left(x, n=None):
    if isinstance(x, list):
        return TIList(x[:int(n)] if n is not None else x)
    s = str(x)
    return TICadena(s[:int(n)] if n is not None else s)


def _right(x, n=None):
    if isinstance(x, list):
        return TIList(x[-int(n):] if n is not None else x)
    s = str(x)
    return TICadena(s[-int(n):] if n is not None else s)


def _instring(origen, patron, inicio=1):
    idx = str(origen).find(str(patron), int(inicio) - 1)
    return idx + 1 if idx >= 0 else 0


def _when(cond, si_true, si_false=None, si_undef=None):
    if cond is None:
        return si_undef
    return si_true if cond else si_false


def _seq(expr_fn, var, low, high, paso=1):
    # seq() se resuelve en el intérprete porque necesita evaluar una expresión;
    # aquí solo se recibe ya convertido en función.
    salida = TIList()
    x = low
    while (paso > 0 and x <= high) or (paso < 0 and x >= high):
        salida.append(expr_fn(x))
        x += paso
    return salida


def _augment(a, b):
    return TIList(list(a) + list(b))


def _sortd(l):
    return TIList(sorted(l, reverse=True))


def _signo(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def _mod(a, b):
    return a - b * math.floor(a / b) if b else a


def _ncr(n, r):
    return math.comb(int(n), int(r))


def _npr(n, r):
    return math.perm(int(n), int(r))


def _root(x, n=2):
    return x ** (1.0 / n)


def _exp(x):
    return math.exp(x)


def _raiz(x):
    if isinstance(x, (int, float)) and x < 0:
        raise TIBasicError("√ de un número negativo (aquí no hay aritmética compleja)")
    return math.sqrt(x)


def _redondear(x, n=None):
    return round(x, int(n)) if n is not None else round(x)


def _entero(x):
    return int(math.floor(x))


def _fpart(x):
    return x - math.trunc(x)


def _xor(a, b):
    return bool(a) != bool(b)


_BIBLIOTECA: dict = {
    "__builtins__": {},
    # trigonometría (la Nspire trabaja en radianes salvo que se diga otra cosa)
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "sin⁻¹": math.asin, "cos⁻¹": math.acos, "tan⁻¹": math.atan,
    "arcsin": math.asin, "arccos": math.acos, "arctan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    # aritmética
    "abs": abs, "sqrt": _raiz, "root": _root,
    "ln": math.log, "log": math.log10, "e^": _exp, "exp": _exp,
    "int": _entero, "ipart": math.trunc, "fpart": _fpart,
    "round": _redondear, "floor": lambda x: int(math.floor(x)),
    "ceiling": lambda x: int(math.ceil(x)), "sign": _signo,
    "mod": _mod, "remain": lambda a, b: math.fmod(a, b),
    "gcd": lambda a, b: math.gcd(int(a), int(b)),
    "lcm": lambda a, b: math.lcm(int(a), int(b)),
    "ncr": _ncr, "npr": _npr, "factorial": lambda n: math.factorial(int(n)),
    "max": max, "min": min,
    "sum": lambda l: sum(l), "product": lambda l: math.prod(l),
    "mean": lambda l: sum(l) / len(l),
    "approx": float,
    # listas y cadenas
    "dim": _dim, "augment": _augment,
    "left": _left, "right": _right, "mid": _mid,
    "instring": _instring, "sortd": _sortd,
    "sorta": lambda l: TIList(sorted(l)),
    "char": lambda n: TICadena(chr(int(n))),
    "ord": lambda s: ord(str(s)[0]) if s else 0,
    "when": _when,
    # aleatoriedad
    "rand": lambda n=None: (TIList([random.random() for _ in range(int(n))])
                            if n is not None else random.random()),
    "randint": lambda a, b, n=None: (
        TIList([random.randint(int(a), int(b)) for _ in range(int(n))])
        if n is not None else random.randint(int(a), int(b))),
    # lógica
    "not": lambda x: not bool(x),
    "xor": _xor,
    # constantes
    "pi": math.pi, "e": math.e, "true": True, "false": False,
    "undef": None, "infinity": math.inf,
    # ayudas internas del traductor
    "_tilist": TIList, "_ticadena": TICadena,
}


# ── Traducción de expresiones Nspire → Python ─────────────────────────────────

_RE_CADENA = re.compile(r'"[^"]*"')
_RE_IDENT  = re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*\b')
_RE_IGUAL  = re.compile(r'(?<![!<>=≠≤≥])=(?!=)')

# palabras que en Python significan otra cosa o no deben tocarse
_RESERVADAS_PY = {
    "and", "or", "not", "if", "else", "in", "is", "none", "true", "false",
    "lambda", "for", "while",
}


def _proteger_cadenas(s: str) -> tuple[str, list[str]]:
    """Saca los literales de cadena para que las sustituciones no los toquen."""
    guardadas: list[str] = []

    def _sacar(m):
        guardadas.append(m.group(0))
        return f"\x00{len(guardadas) - 1}\x00"

    return _RE_CADENA.sub(_sacar, s), guardadas


def _restaurar_cadenas(s: str, guardadas: list[str]) -> str:
    for i, lit in enumerate(guardadas):
        s = s.replace(f"\x00{i}\x00", f"_ticadena({lit})")
    return s


def _convertir_agrupadores(s: str) -> str:
    """
    `{1,2,3}` → `_tilist([1,2,3])` y `[[1,2][3,4]]` → matriz de TIList,
    distinguiendo un corchete de literal de uno de subíndice.
    """
    s = re.sub(r'\]\s*\[', '],[', s)      # separador de filas de matriz
    salida: list[str] = []
    pila: list[str] = []
    anterior = ''
    for c in s:
        if c == '{':
            pila.append('llave')
            salida.append('_tilist([')
        elif c == '}':
            if pila and pila[-1] == 'llave':
                pila.pop()
                salida.append('])')
            else:
                salida.append(c)
        elif c == '[':
            if anterior and (anterior.isalnum() or anterior in '_)]'):
                pila.append('sub')        # a[1] es un subíndice
                salida.append('[')
            else:
                pila.append('lit')        # [[1,2],[3,4]] es un literal
                salida.append('_tilist([')
        elif c == ']':
            salida.append(']' if (pila and pila.pop() == 'sub') else '])')
        else:
            salida.append(c)
        if not c.isspace():
            anterior = c
    return ''.join(salida)


def traducir(expr: str) -> str:
    """Convierte una expresión de TI-Basic de Nspire en una de Python."""
    s, cadenas = _proteger_cadenas(expr)

    # funciones trigonométricas inversas escritas con el superíndice de la calculadora
    for base in ("sin", "cos", "tan"):
        s = s.replace(f"{base}⁻¹", f"arc{base}")

    # símbolos de la calculadora
    s = (s.replace("≠", "!=").replace("≤", "<=").replace("≥", ">=")
          .replace("π", "pi").replace("∞", "infinity")
          .replace("√", "sqrt").replace("−", "-"))
    s = s.replace("²", "**2").replace("³", "**3")
    s = s.replace("&", "+")               # concatenación de cadenas
    s = s.replace("^", "**")

    # `=` es comparación en Nspire (para guardar se usa →, que se trata aparte)
    s = _RE_IGUAL.sub("==", s)

    s = _convertir_agrupadores(s)

    # los identificadores no distinguen mayúsculas
    def _bajar(m):
        palabra = m.group(0)
        return palabra if palabra.lower() in _RESERVADAS_PY else palabra.lower()

    s = _RE_IDENT.sub(_bajar, s)

    return _restaurar_cadenas(s, cadenas)


# ── Ámbito de variables ───────────────────────────────────────────────────────

class _Ambito:
    """Un marco de variables. Los `Local` viven aquí; el resto va a globales."""

    def __init__(self, globales: dict, locales: Optional[dict] = None):
        self.globales = globales
        self.locales = locales if locales is not None else {}
        self.declaradas: set[str] = set()

    def declarar(self, nombre: str):
        self.declaradas.add(nombre)
        self.locales.setdefault(nombre, None)

    def obtener(self, nombre: str):
        if nombre in self.declaradas:
            return self.locales.get(nombre)
        if nombre in self.globales:
            return self.globales[nombre]
        raise TIBasicError(f"Variable «{nombre}» sin definir")

    def asignar(self, nombre: str, valor):
        if nombre in self.declaradas:
            self.locales[nombre] = valor
        else:
            self.globales[nombre] = valor

    def borrar(self, nombre: str):
        self.declaradas.discard(nombre)
        self.locales.pop(nombre, None)
        self.globales.pop(nombre, None)

    def como_dict(self) -> dict:
        d = dict(self.globales)
        for k in self.declaradas:
            d[k] = self.locales.get(k)
        return d


# ── Utilidades de análisis ────────────────────────────────────────────────────

def _clave(sentencia: str) -> str:
    m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)', sentencia)
    return m.group(1).lower() if m else ""


def _partir_fuera_de_cadenas(s: str, sep: str) -> list[str]:
    """Parte por `sep` ignorando lo que haya dentro de comillas."""
    partes, actual, en_cadena, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == '"':
            en_cadena = not en_cadena
            actual.append(c)
        elif not en_cadena and s.startswith(sep, i):
            partes.append(''.join(actual))
            actual = []
            i += len(sep)
            continue
        else:
            actual.append(c)
        i += 1
    partes.append(''.join(actual))
    return partes


def _partir_argumentos(s: str) -> list[str]:
    """Parte por comas respetando paréntesis, corchetes, llaves y comillas."""
    args, actual, prof, en_cadena = [], [], 0, False
    for c in s:
        if c == '"':
            en_cadena = not en_cadena
            actual.append(c)
        elif en_cadena:
            actual.append(c)
        elif c in '([{':
            prof += 1
            actual.append(c)
        elif c in ')]}':
            prof -= 1
            actual.append(c)
        elif c == ',' and prof == 0:
            args.append(''.join(actual).strip())
            actual = []
        else:
            actual.append(c)
    if ''.join(actual).strip():
        args.append(''.join(actual).strip())
    return args


# ── Intérprete ────────────────────────────────────────────────────────────────

class TIBasicInterpreter:
    """
    Intérprete de TI-Basic de TI-Nspire.

    Interfaz que usa el panel:
        set_callbacks(salida, entrada, limpiar)
        ejecutar(codigo)
        detener()
    """

    PROFUNDIDAD_MAX = 60

    def __init__(self):
        self._globales: dict = {}
        self._funcs: dict[str, tuple] = {}     # nombre → (params, cuerpo, es_func)
        self._salida_cb:  Optional[Callable[[str], None]] = None
        self._entrada_cb: Optional[Callable[[str], str]]  = None
        self._limpiar_cb: Optional[Callable[[], None]]    = None
        self._parar = threading.Event()
        self._profundidad = 0
        self._ultimo_error = ""

    # ── Interfaz del panel ────────────────────────────────────────────────────

    def set_callbacks(self, output_cb, input_cb, clrhome_cb=None):
        self._salida_cb  = output_cb
        self._entrada_cb = input_cb
        self._limpiar_cb = clrhome_cb

    def detener(self):
        self._parar.set()

    # ── Entrada / salida ──────────────────────────────────────────────────────

    def _mostrar(self, texto: str):
        if self._salida_cb:
            self._salida_cb(str(texto))

    def _preguntar(self, prompt: str) -> str:
        return self._entrada_cb(prompt) if self._entrada_cb else ""

    # ── Evaluación ────────────────────────────────────────────────────────────

    def _espacio_nombres(self, ambito: _Ambito) -> dict:
        ns = dict(_BIBLIOTECA)
        for nombre, (params, cuerpo, es_func) in self._funcs.items():
            ns[nombre] = self._crear_invocable(nombre, params, cuerpo, es_func)
        ns.update(ambito.como_dict())
        return ns

    def _evaluar(self, expr: str, ambito: _Ambito):
        texto = expr.strip()
        if not texto:
            return None
        codigo = traducir(texto)
        try:
            valor = eval(codigo, self._espacio_nombres(ambito))
        except TIBasicError:
            raise
        except (_Detener, _Retornar):
            raise
        except ZeroDivisionError:
            raise TIBasicError(f"División entre cero en «{texto}»")
        except NameError as exc:
            falta = str(exc).split("'")[1] if "'" in str(exc) else "?"
            raise TIBasicError(f"«{falta}» no está definido")
        except Exception as exc:
            raise TIBasicError(f"Error en «{texto}»: {exc}")
        if isinstance(valor, str) and not isinstance(valor, TICadena):
            valor = TICadena(valor)
        if type(valor) is list:
            valor = TIList(valor)
        return valor

    # ── Guardar (operador →) ──────────────────────────────────────────────────

    def _guardar(self, destino: str, valor, ambito: _Ambito):
        destino = destino.strip()
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\[(.+)\]$', destino)
        if m:
            nombre = m.group(1).lower()
            indices = [self._evaluar(a, ambito) for a in _partir_argumentos(m.group(2))]
            contenedor = ambito.obtener(nombre)
            try:
                if len(indices) == 1:
                    contenedor[indices[0]] = valor
                else:
                    destino_fila = contenedor[indices[0]]
                    destino_fila[indices[1]] = valor
            except TIBasicError:
                raise
            except Exception as exc:
                raise TIBasicError(f"No se pudo guardar en «{destino}»: {exc}")
            return
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', destino):
            raise TIBasicError(f"«{destino}» no es un destino válido para →")
        ambito.asignar(destino.lower(), valor)

    # ── Preparación del código ────────────────────────────────────────────────

    def _partir(self, codigo: str) -> list[str]:
        """Convierte el texto en una lista de sentencias, sin comentarios."""
        sentencias: list[str] = []
        for linea in codigo.splitlines():
            # comentarios: © de la calculadora y // por comodidad
            sin_com, cadenas = _proteger_cadenas(linea)
            for marca in ("©", "//"):
                pos = sin_com.find(marca)
                if pos >= 0:
                    sin_com = sin_com[:pos]
            linea = _restaurar_cadenas(sin_com, cadenas)
            linea = re.sub(r'_ticadena\((".*?")\)', r'\1', linea)
            linea = linea.strip()
            if not linea:
                continue
            # `:` separa sentencias, pero `:=` es asignación
            linea = linea.replace(":=", "\x01")
            for trozo in _partir_fuera_de_cadenas(linea, ":"):
                trozo = trozo.replace("\x01", ":=").strip()
                if trozo:
                    sentencias.append(trozo)
        return sentencias

    def _extraer_definiciones(self, sentencias: list[str]) -> list[str]:
        """Registra los Define y devuelve las sentencias de nivel superior."""
        sueltas: list[str] = []
        i = 0
        while i < len(sentencias):
            st = sentencias[i]
            m = re.match(
                r'^\s*Define\s+(?:LibPub\s+|LibPriv\s+)?'
                r'([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*=\s*(.*)$',
                st, re.IGNORECASE)
            if not m:
                sueltas.append(st)
                i += 1
                continue

            nombre = m.group(1).lower()
            params = [p.strip().lower() for p in m.group(2).split(',') if p.strip()]
            resto = m.group(3).strip()

            if resto.lower() in ("func", "prgm"):
                es_func = resto.lower() == "func"
                cierre = "endfunc" if es_func else "endprgm"
                apertura = resto.lower()
                cuerpo: list[str] = []
                nivel = 1
                i += 1
                while i < len(sentencias):
                    actual = sentencias[i]
                    clave = _clave(actual)
                    if clave == apertura:
                        nivel += 1
                    elif clave == cierre:
                        nivel -= 1
                        if nivel == 0:
                            break
                    cuerpo.append(actual)
                    i += 1
                if i >= len(sentencias):
                    raise TIBasicError(
                        f"Falta {cierre.capitalize()} para Define {nombre}()")
                i += 1
                self._funcs[nombre] = (params, cuerpo, es_func)
            else:
                # Define f(x)=expresión  — función de una línea
                self._funcs[nombre] = (params, [f"Return {resto}"], True)
                i += 1
        return sueltas

    # ── Mapa de bloques ───────────────────────────────────────────────────────

    def _mapear(self, sentencias: list[str]) -> dict:
        fin: dict[int, int] = {}
        abre: dict[int, int] = {}
        alt: dict[int, int] = {}
        rescate: dict[int, int] = {}
        etiquetas: dict[str, int] = {}
        pila: list[list] = []

        for i, st in enumerate(sentencias):
            clave = _clave(st)
            if clave == "if" and re.search(r'\bthen\s*$', st, re.IGNORECASE):
                pila.append(["if", i, [i]])
            elif clave == "for":
                pila.append(["for", i, []])
            elif clave == "while":
                pila.append(["while", i, []])
            elif clave == "loop":
                pila.append(["loop", i, []])
            elif clave == "try":
                pila.append(["try", i, []])
            elif clave in ("elseif", "else"):
                if not pila:
                    raise TIBasicError(f"{st!r} sin bloque que lo contenga")
                tipo, apertura, ramas = pila[-1]
                if tipo == "try" and clave == "else":
                    rescate[apertura] = i
                elif tipo == "if":
                    alt[ramas[-1]] = i
                    ramas.append(i)
                else:
                    raise TIBasicError(f"{clave.capitalize()} inesperado")
            elif clave in ("endif", "endfor", "endwhile", "endloop", "endtry"):
                if not pila:
                    raise TIBasicError(f"{st!r} sin apertura")
                tipo, apertura, ramas = pila.pop()
                esperado = {"if": "endif", "for": "endfor", "while": "endwhile",
                            "loop": "endloop", "try": "endtry"}[tipo]
                if clave != esperado:
                    raise TIBasicError(
                        f"Se esperaba {esperado.capitalize()} y hay {st!r}")
                fin[apertura] = i
                abre[i] = apertura
                if tipo == "if":
                    alt[ramas[-1]] = i
                    for rama in ramas:      # ElseIf/Else también saltan al EndIf
                        fin[rama] = i
                if tipo == "try":
                    rescate.setdefault(apertura, i)
                    # si el cuerpo terminó sin error, su Else salta al EndTry
                    if rescate[apertura] != i:
                        fin[rescate[apertura]] = i
            elif clave == "lbl":
                etiqueta = st.split(None, 1)[1].strip().lower() if len(st.split(None, 1)) > 1 else ""
                if not etiqueta:
                    raise TIBasicError("Lbl sin nombre")
                etiquetas[etiqueta] = i

        if pila:
            tipo, apertura, _ = pila[-1]
            falta = {"if": "EndIf", "for": "EndFor", "while": "EndWhile",
                     "loop": "EndLoop", "try": "EndTry"}[tipo]
            raise TIBasicError(f"Falta {falta} (bloque abierto en «{sentencias[apertura]}»)")

        return {"fin": fin, "abre": abre, "alt": alt,
                "rescate": rescate, "etiquetas": etiquetas}

    # ── Bucle de ejecución ────────────────────────────────────────────────────

    def _correr(self, sentencias: list[str], mapa: dict, ambito: _Ambito):
        pc = 0
        n = len(sentencias)
        pila_bucles: list[int] = []
        estados_for: dict[int, tuple] = {}
        pila_try: list[tuple[int, int]] = []

        while pc < n:
            if self._parar.is_set():
                raise _Detener()
            try:
                pc = self._sentencia(sentencias, pc, mapa, ambito,
                                     pila_bucles, estados_for, pila_try)
            except _Saltar as salto:
                destino = mapa["etiquetas"].get(salto.etiqueta)
                if destino is None:
                    raise TIBasicError(f"Lbl «{salto.etiqueta}» no existe")
                pila_bucles.clear()
                estados_for.clear()
                pc = destino + 1
            except TIBasicError as err:
                if not pila_try:
                    raise
                _apertura, rescate = pila_try.pop()
                self._ultimo_error = str(err)
                ambito.globales["errcode"] = 1
                pc = rescate + 1

    def _sentencia(self, sentencias, pc, mapa, ambito,
                   pila_bucles, estados_for, pila_try) -> int:
        st = sentencias[pc]
        clave = _clave(st)
        resto = st[len(clave):].strip() if clave else st

        # ── Declaraciones ─────────────────────────────────────────────────────
        if clave == "local":
            for nombre in _partir_argumentos(resto):
                ambito.declarar(nombre.strip().lower())
            return pc + 1

        if clave == "delvar":
            for nombre in _partir_argumentos(resto):
                ambito.borrar(nombre.strip().lower())
            return pc + 1

        # ── Salida ────────────────────────────────────────────────────────────
        if clave in ("disp", "text", "output"):
            if not resto:
                self._mostrar("")
            else:
                partes = [_formatear(self._evaluar(a, ambito))
                          for a in _partir_argumentos(resto)]
                self._mostrar(" ".join(partes))
            return pc + 1

        if clave in ("clrio", "clrhome"):
            if self._limpiar_cb:
                self._limpiar_cb()
            return pc + 1

        if clave == "pause":
            if resto:
                self._mostrar(_formatear(self._evaluar(resto, ambito)))
            self._preguntar("Pause — pulsa Aceptar para continuar")
            return pc + 1

        # ── Entrada ───────────────────────────────────────────────────────────
        if clave in ("request", "requeststr", "input", "inputstr"):
            args = _partir_argumentos(resto)
            if not args:
                raise TIBasicError(f"{clave.capitalize()} necesita una variable")
            if len(args) == 1:
                prompt, destino = f"{args[0].strip()}?", args[0].strip()
            else:
                prompt = str(self._evaluar(args[0], ambito))
                destino = args[1].strip()
            texto = self._preguntar(prompt)
            if clave in ("requeststr", "inputstr"):
                valor = TICadena(texto)
            else:
                try:
                    valor = self._evaluar(texto, ambito) if texto.strip() else 0
                except TIBasicError:
                    valor = TICadena(texto)
            self._guardar(destino, valor, ambito)
            return pc + 1

        # ── Condicionales ─────────────────────────────────────────────────────
        if clave == "if":
            if re.search(r'\bthen\s*$', st, re.IGNORECASE):
                return self._resolver_if(sentencias, pc, mapa, ambito)
            # forma corta: `If cond` y la sentencia siguiente es el cuerpo
            cond = self._evaluar(resto, ambito)
            return pc + 1 if cond else pc + 2

        if clave in ("elseif", "else"):
            # se llega aquí al terminar una rama tomada: saltar al EndIf
            return mapa["fin"].get(pc, pc) + 1

        if clave == "endif":
            return pc + 1

        # ── Bucles ────────────────────────────────────────────────────────────
        if clave == "for":
            args = _partir_argumentos(resto)
            if len(args) < 3:
                raise TIBasicError("For necesita variable, inicio y fin")
            var = args[0].strip().lower()
            if pc not in estados_for:
                inicio = self._evaluar(args[1], ambito)
                limite = self._evaluar(args[2], ambito)
                paso = self._evaluar(args[3], ambito) if len(args) > 3 else 1
                if paso == 0:
                    raise TIBasicError("El paso de For no puede ser 0")
                estados_for[pc] = (limite, paso)
                ambito.asignar(var, inicio)
                pila_bucles.append(pc)
            limite, paso = estados_for[pc]
            actual = ambito.obtener(var)
            if (paso > 0 and actual > limite) or (paso < 0 and actual < limite):
                estados_for.pop(pc, None)
                if pila_bucles and pila_bucles[-1] == pc:
                    pila_bucles.pop()
                return mapa["fin"][pc] + 1
            return pc + 1

        if clave == "endfor":
            apertura = mapa["abre"][pc]
            args = _partir_argumentos(sentencias[apertura][3:].strip())
            var = args[0].strip().lower()
            _limite, paso = estados_for[apertura]
            ambito.asignar(var, ambito.obtener(var) + paso)
            return apertura

        if clave == "while":
            if self._evaluar(resto, ambito):
                if not pila_bucles or pila_bucles[-1] != pc:
                    pila_bucles.append(pc)
                return pc + 1
            if pila_bucles and pila_bucles[-1] == pc:
                pila_bucles.pop()
            return mapa["fin"][pc] + 1

        if clave == "endwhile":
            return mapa["abre"][pc]

        if clave == "loop":
            if not pila_bucles or pila_bucles[-1] != pc:
                pila_bucles.append(pc)
            return pc + 1

        if clave == "endloop":
            return mapa["abre"][pc]

        if clave == "exit":
            if not pila_bucles:
                raise TIBasicError("Exit fuera de un bucle")
            apertura = pila_bucles.pop()
            estados_for.pop(apertura, None)
            return mapa["fin"][apertura] + 1

        if clave == "cycle":
            if not pila_bucles:
                raise TIBasicError("Cycle fuera de un bucle")
            return mapa["fin"][pila_bucles[-1]]

        # ── Try ───────────────────────────────────────────────────────────────
        if clave == "try":
            pila_try.append((pc, mapa["rescate"].get(pc, mapa["fin"][pc])))
            return pc + 1

        if clave == "endtry":
            if pila_try and pila_try[-1][0] == mapa["abre"][pc]:
                pila_try.pop()
            return pc + 1

        if clave == "clrerr":
            ambito.globales["errcode"] = 0
            self._ultimo_error = ""
            return pc + 1

        if clave == "passerr":
            raise TIBasicError(self._ultimo_error or "error propagado con PassErr")

        # ── Saltos y fin ──────────────────────────────────────────────────────
        if clave == "lbl":
            return pc + 1

        if clave == "goto":
            raise _Saltar(resto.strip().lower())

        if clave == "return":
            raise _Retornar(self._evaluar(resto, ambito) if resto else None)

        if clave == "stop":
            raise _Detener()

        if clave in ("endfunc", "endprgm"):
            raise _Retornar(None)

        # ── Guardar y expresiones sueltas ─────────────────────────────────────
        partes = _partir_fuera_de_cadenas(st, "→")
        if len(partes) > 1:
            valor = self._evaluar(partes[0], ambito)
            for destino in partes[1:]:
                self._guardar(destino, valor, ambito)
                valor = self._evaluar(destino, ambito)
            return pc + 1

        partes = _partir_fuera_de_cadenas(st, ":=")
        if len(partes) == 2:
            self._guardar(partes[0], self._evaluar(partes[1], ambito), ambito)
            return pc + 1

        # llamada a un programa o expresión cuyo valor se descarta
        self._evaluar(st, ambito)
        return pc + 1

    def _resolver_if(self, sentencias, pc, mapa, ambito) -> int:
        """Recorre la cadena If/ElseIf/Else y devuelve dónde seguir."""
        idx = pc
        while True:
            st = sentencias[idx]
            clave = _clave(st)
            if clave in ("if", "elseif"):
                cond_txt = re.sub(r'\bthen\s*$', '', st[len(clave):].strip(),
                                  flags=re.IGNORECASE).strip()
                if self._evaluar(cond_txt, ambito):
                    return idx + 1
                siguiente = mapa["alt"].get(idx)
                if siguiente is None:
                    raise TIBasicError("Bloque If mal formado")
                idx = siguiente
            elif clave == "else":
                return idx + 1
            else:                       # endif
                return idx + 1

    # ── Funciones y programas del usuario ─────────────────────────────────────

    def _crear_invocable(self, nombre, params, cuerpo, es_func):
        def _llamar(*args):
            return self._invocar(nombre, params, cuerpo, args, es_func)
        _llamar.__name__ = nombre
        return _llamar

    def _invocar(self, nombre, params, cuerpo, args, es_func):
        if len(args) != len(params):
            raise TIBasicError(
                f"{nombre}() espera {len(params)} argumento(s) y recibió {len(args)}")
        if self._profundidad >= self.PROFUNDIDAD_MAX:
            raise TIBasicError(f"Demasiada recursión en {nombre}()")

        ambito = _Ambito(self._globales)
        for p, v in zip(params, args):
            ambito.declarar(p)
            ambito.locales[p] = v

        self._profundidad += 1
        try:
            self._correr(cuerpo, self._mapear(cuerpo), ambito)
            return None
        except _Retornar as r:
            return r.valor
        finally:
            self._profundidad -= 1

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def ejecutar(self, codigo: str):
        self._parar.clear()
        self._globales = {}
        self._funcs = {}
        self._profundidad = 0
        self._ultimo_error = ""
        try:
            sentencias = self._partir(codigo)
            sueltas = self._extraer_definiciones(sentencias)

            if sueltas:
                ambito = _Ambito(self._globales)
                self._correr(sueltas, self._mapear(sueltas), ambito)
            else:
                # Solo hay definiciones: se ejecuta el programa principal, igual
                # que si lo llamaras por su nombre desde la calculadora.
                programas = [n for n, (_p, _c, f) in self._funcs.items() if not f]
                if not programas:
                    self._mostrar("(solo hay definiciones; nada que ejecutar)")
                    return
                principal = "main" if "main" in programas else programas[-1]
                params = self._funcs[principal][0]
                if params:
                    self._mostrar(
                        f"«{principal}()» necesita {len(params)} argumento(s); "
                        f"llámalo tú desde el programa.")
                    return
                self._mostrar(f"— ejecutando {principal}() —")
                self._invocar(principal, [], self._funcs[principal][1], (), False)

        except _Detener:
            self._mostrar("— detenido —")
        except _Retornar:
            pass
        except TIBasicError as err:
            self._mostrar(f"⚠ {err}")
        except RecursionError:
            self._mostrar("⚠ Demasiada recursión")
        except Exception as err:                       # red de seguridad
            self._mostrar(f"⚠ Error interno: {type(err).__name__}: {err}")
