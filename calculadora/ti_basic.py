# =============================================================================
# INTÉRPRETE TI-BASIC / TI-BASIC EXTENDIDO
# Compatible con TI-Nspire CX CAS y TI-99/4A Extended Basic
# =============================================================================
from __future__ import annotations

import re
import math
import random
import threading
from typing import Callable, Optional


class _Stop(Exception):
    def __init__(self, silent: bool = False):
        self.silent = silent

class _Return(Exception):
    pass

class _GotoInline(Exception):
    def __init__(self, target: int):
        self.target = target

class TIBasicError(Exception):
    pass


# ---------------------------------------------------------------------------
# Wrapper para arrays: A(i) evaluable desde eval()
# ---------------------------------------------------------------------------
class _ArrayVar:
    def __init__(self, data: list):
        self.data = data

    def __call__(self, *idx):
        if len(idx) == 1:
            return self.data[int(idx[0])]
        return self.data[int(idx[0])][int(idx[1])]

    def __len__(self): return len(self.data)
    def __getitem__(self, i): return self.data[i]
    def __setitem__(self, i, v): self.data[int(i)] = v


# ---------------------------------------------------------------------------
# Namespace matemático
# ---------------------------------------------------------------------------
def _sgn(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)

def _pos(haystack: str, needle: str, start: int = 1) -> int:
    idx = haystack.find(needle, start - 1)
    return idx + 1 if idx >= 0 else 0

def _seg(s: str, start: int, length: int) -> str:
    return s[int(start) - 1: int(start) - 1 + int(length)]

def _rpt(s: str, n) -> str:
    return str(s) * int(n)

def _val(s) -> float:
    try:
        return float(str(s).strip())
    except Exception:
        return 0.0

def _str(x) -> str:
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)

_MATH_NS: dict = {
    '__builtins__': {},
    # Trigonometría
    'sin': math.sin,  'cos': math.cos,  'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'ATN': math.atan,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    # Álgebra
    'sqrt': math.sqrt, 'SQR': math.sqrt,
    'abs': abs,  'ABS': abs,
    'log': math.log10, 'LOG': math.log10,
    'ln': math.log,
    'EXP': math.exp, 'exp': math.exp,
    'int': lambda x: int(math.floor(x)), 'INT': lambda x: int(math.floor(x)),
    'iPart': math.trunc,
    'frac': lambda x: x - math.floor(x),
    'round': round,
    'max': max, 'MAX': max,
    'min': min, 'MIN': min,
    'SGN': _sgn, 'sgn': _sgn,
    # Constantes
    'pi': math.pi, 'PI': math.pi, 'e': math.e,
    # Aleatoriedad
    'rand': random.random,
    'RND': random.random,
    'randInt': lambda a, b: random.randint(int(a), int(b)),
    # Lógica
    'not': lambda x: int(not bool(x)),
    'True': 1, 'False': 0,
    # Cadenas
    'LEN': len,  'len': len,
    'ASC': lambda s: ord(str(s)[0]) if s else 0,
    'CHR': chr,
    'STR': _str,
    'VAL': _val, 'val': _val,
    'SEG': _seg,
    'RPT': _rpt,
    'POS': _pos,
    # Misc
    'TAB': lambda n: ' ' * int(n),
}


def _normalizar(expr: str) -> str:
    """Convierte sintaxis TI-Basic a Python evaluable."""
    s = expr
    # Funciones con $ (TI-99/4A) → sin $ para que Python las acepte
    s = re.sub(r'\b(CHR|STR|SEG|RPT)\$\s*\(', r'\1(', s, flags=re.IGNORECASE)
    s = s.replace('^', '**')
    s = s.replace('√(', 'sqrt(')
    s = s.replace('√', 'sqrt')
    s = s.replace('π', 'pi')
    s = s.replace('≠', '!=')
    s = s.replace('≤', '<=')
    s = s.replace('≥', '>=')
    # := (TI-Nspire) → == para comparación (en contexto de eval)
    s = s.replace(':=', '==__ASSIGN__')   # placeholder para no confundir
    # = suelto → == (comparación)
    s = re.sub(r'(?<![!<>=])=(?!=)', '==', s)
    s = s.replace('==__ASSIGN__', '')  # quitar placeholder (ya se evaluó el lado derecho)
    # Operadores lógicos
    s = re.sub(r'\bXOR\b', '!=',  s, flags=re.IGNORECASE)
    s = re.sub(r'\band\b', ' and ', s, flags=re.IGNORECASE)
    s = re.sub(r'\bor\b',  ' or ',  s, flags=re.IGNORECASE)
    return s


# ---------------------------------------------------------------------------
# Intérprete
# ---------------------------------------------------------------------------
class TIBasicInterpreter:
    """
    Intérprete TI-Basic compatible con:
    - TI-Nspire CX CAS  (sin números de línea, →, :=, For()/End)
    - TI-99/4A Extended (números de línea, LET, FOR/NEXT, GOSUB)
    """

    def __init__(self):
        self._vars:   dict[str, object] = {}
        self._strs:   dict[str, str]    = {}
        self._lists:  dict[str, list]   = {}
        self._arrays: dict[str, list]   = {}
        self._defs:   dict[str, tuple]  = {}
        self._data:   list              = []
        self._data_ptr: int             = 0
        self._output_cb:  Optional[Callable[[str], None]] = None
        self._input_cb:   Optional[Callable[[str], str]]  = None
        self._clrhome_cb: Optional[Callable[[], None]]    = None
        self._stop_flag = threading.Event()
        self._gosub_stack: list[int] = []
        self._line_num_map: dict[int, int] = {}

    def set_callbacks(self, output_cb, input_cb, clrhome_cb=None):
        self._output_cb  = output_cb
        self._input_cb   = input_cb
        self._clrhome_cb = clrhome_cb

    def detener(self):
        self._stop_flag.set()

    # ── I/O ──────────────────────────────────────────────────────────────────

    def _emit(self, text: str):
        if self._output_cb:
            self._output_cb(str(text))

    def _pedir(self, prompt: str) -> str:
        return self._input_cb(prompt) if self._input_cb else ""

    # ── Evaluación ────────────────────────────────────────────────────────────

    def _ns(self) -> dict:
        ns = dict(_MATH_NS)
        ns.update(self._vars)
        ns.update(self._strs)
        for k, v in self._lists.items():
            ns[k] = v
        for k, v in self._arrays.items():
            ns[k] = _ArrayVar(v)     # callable wrapper: A(i) funciona en eval()
        for fname, (param, expr) in self._defs.items():
            p = param
            e = expr
            ns[fname] = eval(f'lambda {p}: {e}', ns)
        return ns

    def _eval(self, expr: str):
        s = expr.strip()
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        s = _normalizar(s)
        try:
            return eval(s, self._ns())
        except Exception as exc:
            raise TIBasicError(f"Error en «{expr}»: {exc}")

    def _fmt(self, val) -> str:
        if isinstance(val, bool):
            return "1" if val else "0"
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            if val == int(val) and abs(val) < 1e15:
                return str(int(val))
            return f"{val:.10g}"
        if isinstance(val, list):
            return "{" + ",".join(self._fmt(v) for v in val) + "}"
        return str(val)

    # ── Parseo ────────────────────────────────────────────────────────────────

    def _parsear(self, codigo: str) -> list[str]:
        stmts: list[str] = []
        self._line_num_map = {}

        for raw in codigo.splitlines():
            m = re.match(r'^(\d+)\s+(.*)', raw.strip())
            if m:
                line_num = int(m.group(1))
                self._line_num_map[line_num] = len(stmts)
                raw = m.group(2)

            # Dividir por ':' respetando cadenas y ':=' (operador de asignación)
            current: list[str] = []
            in_str = False
            i_ch = 0
            while i_ch < len(raw):
                c = raw[i_ch]
                if c == '"':
                    in_str = not in_str
                    current.append(c)
                elif c == ':' and not in_str:
                    # ':=' es asignación (TI-Nspire), no separador de sentencias
                    if i_ch + 1 < len(raw) and raw[i_ch + 1] == '=':
                        current.append(':=')
                        i_ch += 2
                        continue
                    s = ''.join(current).strip()
                    if s:
                        stmts.append(s)
                    current = []
                else:
                    current.append(c)
                i_ch += 1
            s = ''.join(current).strip()
            if s:
                stmts.append(s)

        # Pre-procesar DATA
        self._data = []
        self._data_ptr = 0
        for st in stmts:
            if self._kw(st) == 'DATA':
                for val in self._split_args(st[4:].strip()):
                    v = val.strip()
                    if v.startswith('"') and v.endswith('"'):
                        self._data.append(v[1:-1])
                    else:
                        try:
                            self._data.append(float(v))
                        except Exception:
                            self._data.append(v)

        return stmts

    def _kw(self, line: str) -> str:
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_$]*)', line.strip())
        return m.group(1).upper() if m else ""

    # ── Tabla de saltos ───────────────────────────────────────────────────────

    def _construir_mapa(self, stmts: list[str]):
        stack: list[tuple[str, int]] = []
        end_map:      dict[int, int] = {}
        else_map:     dict[int, int] = {}
        else_end_map: dict[int, int] = {}
        loop_map:     dict[int, int] = {}

        for i, line in enumerate(stmts):
            kw    = self._kw(line)
            upper = line.strip().upper()

            if kw in ('FOR', 'WHILE', 'REPEAT'):
                stack.append((kw, i))
            elif kw == 'IF':
                j = i + 1
                while j < len(stmts) and not stmts[j].strip():
                    j += 1
                if j < len(stmts) and self._kw(stmts[j]) == 'THEN':
                    stack.append(('IF', i))
            elif upper == 'ELSE':
                for k in range(len(stack) - 1, -1, -1):
                    if stack[k][0] == 'IF':
                        else_map[stack[k][1]] = i
                        break
            elif kw in ('END', 'NEXT', 'SUBEND', 'WEND',
                        'ENDWHILE', 'ENDFOR', 'ENDLOOP', 'ENDIF'):
                if stack:
                    entry_kw, start = stack.pop()
                    end_map[start] = i
                    if entry_kw in ('FOR', 'WHILE', 'REPEAT'):
                        loop_map[i] = start

        for if_idx, else_idx in else_map.items():
            if if_idx in end_map:
                else_end_map[else_idx] = end_map[if_idx]

        # Conjunto de posiciones que cierran un bloque (no terminan el programa)
        block_end_set: set[int] = set(end_map.values())

        return end_map, else_map, else_end_map, loop_map, block_end_set

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar(self, codigo: str):
        self._stop_flag.clear()
        self._vars.clear()
        self._strs.clear()
        self._lists.clear()
        self._arrays.clear()
        self._defs.clear()
        self._gosub_stack.clear()

        stmts = self._parsear(codigo)
        end_map, else_map, else_end_map, loop_map, block_end_set = \
            self._construir_mapa(stmts)

        lbl_map: dict[str, int] = {}
        for i, s in enumerate(stmts):
            kw = self._kw(s)
            if kw == 'LBL':
                lbl_map[s[3:].strip().upper()] = i

        ip = 0
        try:
            while ip < len(stmts):
                if self._stop_flag.is_set():
                    raise _Stop(silent=False)
                ip = self._stmt(stmts[ip], ip, stmts,
                                end_map, else_map, else_end_map,
                                loop_map, lbl_map, block_end_set)
        except _Stop as e:
            if not e.silent:
                self._emit("■ Programa detenido")
        except _Return:
            pass
        except TIBasicError as e:
            self._emit(f"  ERR: {e}")
        except Exception as e:
            self._emit(f"  ERR inesperado: {type(e).__name__}: {e}")
        self._emit("")

    # ── Ejecución de un statement ──────────────────────────────────────────

    def _stmt(self, s: str, ip: int, stmts: list[str],
              end_map, else_map, else_end_map,
              loop_map, lbl_map, block_end_set) -> int:
        s = s.strip()
        if not s:
            return ip + 1

        upper = s.upper().strip()
        kw    = self._kw(s)

        # ── Comentarios ──────────────────────────────────────────────────────
        if kw in ('REM', 'COMMENT') or s.startswith('//') or s.startswith("'"):
            return ip + 1

        # ── Asignación := (TI-Nspire) ─────────────────────────────────────────
        if ':=' in s:
            idx = s.index(':=')
            var  = s[:idx].strip().upper()
            expr = s[idx + 2:].strip()
            self._asignar(var, self._eval(expr))
            return ip + 1

        # ── Marcadores de bloque ─────────────────────────────────────────────
        if upper == 'THEN':
            return ip + 1

        if upper == 'ELSE':
            return else_end_map.get(ip, ip) + 1

        if kw in ('END', 'SUBEND'):
            if ip in loop_map:
                start = loop_map[ip]
                sk = self._kw(stmts[start])
                if sk == 'FOR':
                    return self._for_end(stmts[start], start, ip)
                elif sk == 'WHILE':
                    return start
                elif sk == 'REPEAT':
                    return self._repeat_end(stmts[start], start, ip)
            if ip in block_end_set:
                return ip + 1          # cierra bloque IF
            raise _Stop(silent=True)   # END standalone = fin normal del programa

        # WEND / ENDWHILE / ENDFOR / ENDLOOP
        if kw in ('WEND', 'ENDWHILE', 'ENDFOR', 'ENDLOOP'):
            if ip in loop_map:
                start = loop_map[ip]
                sk = self._kw(stmts[start])
                if sk == 'FOR':
                    return self._for_end(stmts[start], start, ip)
                elif sk in ('WHILE',):
                    return start       # re-evalúa condición del WHILE
                elif sk == 'REPEAT':
                    return self._repeat_end(stmts[start], start, ip)
            return ip + 1

        # ENDIF
        if kw == 'ENDIF':
            return ip + 1

        if kw == 'NEXT':
            if ip in loop_map:
                return self._for_end(stmts[loop_map[ip]], loop_map[ip], ip)
            return ip + 1

        if upper in ('LBL', 'DATA', 'SUB'):
            return ip + 1

        # ── Terminación ──────────────────────────────────────────────────────
        if upper in ('STOP', 'BYE'):
            raise _Stop(silent=False)

        if upper in ('RETURN', 'SUBEXIT'):
            if self._gosub_stack:
                return self._gosub_stack.pop()
            raise _Return()

        # ── Asignación TI-Nspire: expr→Var ───────────────────────────────────
        if '→' in s:
            arrow = s.rfind('→')
            expr_part = s[:arrow].strip()
            var_part  = s[arrow + 1:].strip().upper()
            self._asignar(var_part, self._eval(expr_part))
            return ip + 1

        # ── Asignación TI-99/4A: LET var = expr ──────────────────────────────
        if kw == 'LET':
            rest = s[3:].strip()
            return self._asignar_let(rest, ip)

        # ── Asignación a elemento de array: A(I) = expr ───────────────────────
        m_arr = re.match(r'^([A-Za-z_][A-Za-z0-9_$]*)\s*\((.+)\)\s*=\s*(.*)', s)
        if m_arr and m_arr.group(1).upper() in self._arrays:
            name = m_arr.group(1).upper()
            idx_list = [int(self._eval(x)) for x in self._split_args(m_arr.group(2))]
            val = self._eval(m_arr.group(3))
            arr = self._arrays[name]
            if len(idx_list) == 1:
                arr[idx_list[0]] = float(val)
            elif len(idx_list) == 2:
                arr[idx_list[0]][idx_list[1]] = float(val)
            return ip + 1

        # ── Asignación implícita: VAR = expr (sin LET) ───────────────────────
        if re.match(r'^[A-Za-z_][A-Za-z0-9_$]*\s*=\s*', s) and kw not in (
                'IF','FOR','WHILE','REPEAT','PRINT','DISPLAY','ACCEPT',
                'INPUT','PROMPT','DISP','OUTPUT','GOSUB','GOTO','ON','DEF',
                'DIM','CALL','READ','RESTORE','RANDOMIZE','OPEN','CLOSE'):
            eq = s.index('=')
            var = s[:eq].strip().upper()
            expr = s[eq+1:].strip()
            if not expr.startswith('=') and '(' not in var:
                self._asignar(var, self._eval(expr))
                return ip + 1

        # ── DEF fn(x) = expr ─────────────────────────────────────────────────
        if kw == 'DEF':
            m = re.match(r'DEF\s+(\w+)\s*\((\w+)\)\s*=\s*(.+)', s, re.IGNORECASE)
            if m:
                fname  = m.group(1).upper()
                param  = m.group(2).upper()
                expr   = _normalizar(m.group(3))
                self._defs[fname] = (param, expr)
            return ip + 1

        # ── DIM var(n[,m]) ────────────────────────────────────────────────────
        if kw == 'DIM':
            for decl in self._split_args(s[3:].strip()):
                decl = decl.strip()
                m = re.match(r'(\w+)\s*\((.+)\)', decl, re.IGNORECASE)
                if m:
                    name = m.group(1).upper()
                    dims = [int(self._eval(d)) for d in self._split_args(m.group(2))]
                    if len(dims) == 1:
                        self._arrays[name] = [0.0] * (dims[0] + 1)
                    else:
                        self._arrays[name] = [[0.0] * (dims[1]+1)
                                               for _ in range(dims[0]+1)]
            return ip + 1

        # ── RANDOMIZE ─────────────────────────────────────────────────────────
        if kw == 'RANDOMIZE':
            rest = s[9:].strip()
            seed = int(self._eval(rest)) if rest else None
            random.seed(seed)
            return ip + 1

        # ── CLRHOME / CALL CLEAR ──────────────────────────────────────────────
        if upper == 'CLRHOME':
            if self._clrhome_cb: self._clrhome_cb()
            return ip + 1

        if upper in ('CALL CLEAR', 'NEW'):
            if self._clrhome_cb: self._clrhome_cb()
            return ip + 1

        # ── CALL (subprogramas TI-99/4A) ─────────────────────────────────────
        if kw == 'CALL':
            return self._call(s[4:].strip(), ip)

        # ── PRINT / DISP ─────────────────────────────────────────────────────
        if kw in ('PRINT', 'DISP'):
            rest = s[len(kw):].strip()
            if rest.upper().startswith('USING'):
                rest = rest[5:].strip().lstrip('"').strip()
            linea = ''
            for arg in self._split_args_print(rest):
                arg = arg.strip()
                if arg == ';':
                    continue
                if arg == ',':
                    linea += '\t'
                    continue
                if arg.startswith('"') and arg.endswith('"'):
                    linea += arg[1:-1]
                else:
                    linea += self._fmt(self._eval(arg))
            self._emit(linea)
            return ip + 1

        # ── PAUSE ─────────────────────────────────────────────────────────────
        if kw == 'PAUSE':
            rest = s[5:].strip()
            if rest:
                self._emit(self._fmt(self._eval(rest)))
            self._pedir("[PAUSA — Enter para continuar]")
            return ip + 1

        # ── INPUT / LINPUT ────────────────────────────────────────────────────
        if kw in ('INPUT', 'LINPUT'):
            parts = self._split_args(s[len(kw):].strip())
            if len(parts) >= 2:
                prompt = parts[0].strip().strip('"')
                var = parts[1].strip().upper()
            elif parts:
                var = parts[0].strip().upper()
                prompt = f"{var}? "
            else:
                return ip + 1
            raw = self._pedir(prompt)
            try:
                self._asignar(var, float(self._eval(raw)))
            except Exception:
                self._asignar(var, raw)
            return ip + 1

        # ── PROMPT ────────────────────────────────────────────────────────────
        if kw == 'PROMPT':
            for var in self._split_args(s[6:].strip()):
                var = var.strip().upper()
                raw = self._pedir(f"{var}=? ")
                try:
                    self._asignar(var, float(self._eval(raw)))
                except Exception:
                    self._asignar(var, raw)
            return ip + 1

        # ── OUTPUT / DISPLAY AT ───────────────────────────────────────────────
        if kw in ('OUTPUT', 'DISPLAY'):
            m = re.match(r'(?:Output|Display)\s*AT\s*\(([^)]+)\)\s*.*?:\s*(.*)',
                         s, re.IGNORECASE)
            if m:
                val = self._eval(m.group(2).strip()) if m.group(2).strip() else ''
                self._emit(self._fmt(val))
            else:
                m2 = re.match(r'Output\s*\((.+)\)', s, re.IGNORECASE)
                if m2:
                    parts = self._split_args(m2.group(1))
                    if len(parts) >= 3:
                        self._emit(self._fmt(self._eval(parts[2].strip())))
            return ip + 1

        # ── READ ──────────────────────────────────────────────────────────────
        if kw == 'READ':
            for var in self._split_args(s[4:].strip()):
                var = var.strip().upper()
                if self._data_ptr < len(self._data):
                    val = self._data[self._data_ptr]
                    self._data_ptr += 1
                    self._asignar(var, val)
                else:
                    raise TIBasicError("READ: sin más datos")
            return ip + 1

        if upper == 'RESTORE':
            self._data_ptr = 0
            return ip + 1

        # ── IF ────────────────────────────────────────────────────────────────
        if kw == 'IF':
            return self._if_stmt(s, ip, stmts,
                                 end_map, else_map, else_end_map,
                                 loop_map, lbl_map, block_end_set)

        # ── FOR ───────────────────────────────────────────────────────────────
        if kw == 'FOR':
            if re.match(r'For\s*\(', s, re.IGNORECASE):
                return self._for_nspire(s, ip, end_map)
            else:
                return self._for_tibasic(s, ip, end_map)

        # ── WHILE ─────────────────────────────────────────────────────────────
        if kw == 'WHILE':
            cond = bool(self._eval(s[5:].strip()))
            return (ip + 1) if cond else (end_map.get(ip, ip) + 1)

        # ── REPEAT ────────────────────────────────────────────────────────────
        if kw == 'REPEAT':
            return ip + 1

        # ── GOTO ──────────────────────────────────────────────────────────────
        if kw == 'GOTO':
            return self._saltar(s[4:].strip(), lbl_map)

        if kw == 'LBL':
            return ip + 1

        # ── GOSUB ─────────────────────────────────────────────────────────────
        if kw == 'GOSUB':
            self._gosub_stack.append(ip + 1)
            return self._saltar(s[5:].strip(), lbl_map)

        # ── ON...GOTO / ON...GOSUB ────────────────────────────────────────────
        if kw == 'ON':
            return self._on_stmt(s, ip, lbl_map)

        # ── Expresión numérica sola ───────────────────────────────────────────
        try:
            val = self._eval(s)
            self._emit(f"  {self._fmt(val)}")
        except TIBasicError:
            pass

        return ip + 1

    # ── Helpers de asignación ─────────────────────────────────────────────────

    def _asignar(self, var: str, val):
        if re.match(r'^STR[1-9]$', var):
            self._strs[var] = self._fmt(val)
        elif re.match(r'^L[1-6]$', var):
            self._lists[var] = val if isinstance(val, list) else [val]
        elif var.endswith('$'):
            self._strs[var] = str(val)
        elif var in self._arrays:
            pass
        else:
            try:
                self._vars[var] = float(val)
            except (TypeError, ValueError):
                self._strs[var] = str(val)

    def _asignar_let(self, rest: str, ip: int) -> int:
        m = re.match(r'(\w+)\s*\((.+)\)\s*=\s*(.+)', rest)
        if m:
            name = m.group(1).upper()
            idx  = [int(self._eval(x)) for x in self._split_args(m.group(2))]
            val  = self._eval(m.group(3))
            if name in self._arrays:
                arr = self._arrays[name]
                if len(idx) == 1:
                    arr[idx[0]] = float(val)
                elif len(idx) == 2:
                    arr[idx[0]][idx[1]] = float(val)
        else:
            eq = rest.index('=')
            var = rest[:eq].strip().upper()
            expr = rest[eq+1:].strip()
            self._asignar(var, self._eval(expr))
        return ip + 1

    # ── Helpers de control de flujo ───────────────────────────────────────────

    def _saltar(self, destino: str, lbl_map: dict) -> int:
        destino = destino.strip()
        if destino.isdigit():
            n = int(destino)
            if n in self._line_num_map:
                return self._line_num_map[n]
            raise TIBasicError(f"Línea {n} no encontrada")
        lbl = destino.upper()
        if lbl in lbl_map:
            return lbl_map[lbl]
        raise TIBasicError(f"Etiqueta '{destino}' no encontrada")

    def _if_stmt(self, s: str, ip: int, stmts,
                 end_map, else_map, else_end_map,
                 loop_map, lbl_map, block_end_set) -> int:
        cond_str = s[2:].strip()

        # Detectar IF inline: IF cond THEN stmt [ELSE stmt]
        m_inline = re.match(r'(.+?)\s+THEN\s+(.*)', cond_str, re.IGNORECASE)
        if m_inline:
            cond = bool(self._eval(m_inline.group(1).strip()))
            then_part = m_inline.group(2).strip()
            m_else = re.split(r'\s+ELSE\s+', then_part, maxsplit=1, flags=re.IGNORECASE)
            try:
                if cond:
                    self._ejecutar_inline(m_else[0].strip(), ip, stmts,
                                          end_map, else_map, else_end_map,
                                          loop_map, lbl_map, block_end_set)
                elif len(m_else) > 1:
                    self._ejecutar_inline(m_else[1].strip(), ip, stmts,
                                          end_map, else_map, else_end_map,
                                          loop_map, lbl_map, block_end_set)
            except _GotoInline as e:
                return e.target
            return ip + 1

        # Bloque IF con THEN en línea siguiente (TI-Nspire / TI-99/4A estilo bloque)
        j = ip + 1
        while j < len(stmts) and not stmts[j].strip():
            j += 1
        is_block = j < len(stmts) and self._kw(stmts[j]) == 'THEN'
        cond = bool(self._eval(cond_str))
        if is_block:
            if cond:
                return ip + 1
            if ip in else_map:
                return else_map[ip] + 1
            return end_map.get(ip, ip) + 1
        else:
            return (ip + 1) if cond else (ip + 2)

    def _ejecutar_inline(self, stmt: str, ip: int, stmts,
                         end_map, else_map, else_end_map,
                         loop_map, lbl_map, block_end_set):
        """Ejecuta un statement inline (consecuencia de IF de una línea)."""
        if not stmt:
            return
        kw = self._kw(stmt)
        if kw == 'GOTO':
            raise _GotoInline(self._saltar(stmt[4:].strip(), lbl_map))
        if kw == 'GOSUB':
            self._gosub_stack.append(ip + 1)
            raise _GotoInline(self._saltar(stmt[5:].strip(), lbl_map))
        # Cualquier otro statement se ejecuta normalmente
        self._stmt(stmt, ip, stmts,
                   end_map, else_map, else_end_map,
                   loop_map, lbl_map, block_end_set)

    def _on_stmt(self, s: str, ip: int, lbl_map: dict) -> int:
        """ON expr GOTO/GOSUB dest1, dest2, ..."""
        m = re.match(r'ON\s+(.+?)\s+(GOTO|GOSUB)\s+(.+)', s, re.IGNORECASE)
        if not m:
            return ip + 1
        idx  = int(self._eval(m.group(1))) - 1
        mode = m.group(2).upper()
        dests = [d.strip() for d in m.group(3).split(',')]
        if 0 <= idx < len(dests):
            if mode == 'GOSUB':
                self._gosub_stack.append(ip + 1)
            return self._saltar(dests[idx], lbl_map)
        return ip + 1

    # ── Helpers de FOR ────────────────────────────────────────────────────────

    def _for_nspire(self, s: str, ip: int, end_map: dict) -> int:
        m = re.match(r'For\s*\((.+)\)', s, re.IGNORECASE)
        if not m:
            raise TIBasicError(f"Sintaxis For: {s}")
        parts = self._split_args(m.group(1))
        var   = parts[0].strip().upper()
        start = float(self._eval(parts[1]))
        stop  = float(self._eval(parts[2]))
        step  = float(self._eval(parts[3])) if len(parts) > 3 else 1.0
        self._vars[var] = start
        in_range = (step > 0 and start <= stop) or (step < 0 and start >= stop)
        return (ip + 1) if in_range else (end_map.get(ip, ip) + 1)

    def _for_tibasic(self, s: str, ip: int, end_map: dict) -> int:
        m = re.match(r'FOR\s+(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+))?$',
                     s, re.IGNORECASE)
        if not m:
            raise TIBasicError(f"Sintaxis FOR: {s}")
        var   = m.group(1).upper()
        start = float(self._eval(m.group(2)))
        stop  = float(self._eval(m.group(3)))
        step  = float(self._eval(m.group(4))) if m.group(4) else 1.0
        self._vars[var] = start
        in_range = (step > 0 and start <= stop) or (step < 0 and start >= stop)
        return (ip + 1) if in_range else (end_map.get(ip, ip) + 1)

    def _for_end(self, for_stmt: str, start: int, end: int) -> int:
        if re.match(r'For\s*\(', for_stmt, re.IGNORECASE):
            m = re.match(r'For\s*\((.+)\)', for_stmt, re.IGNORECASE)
            parts = self._split_args(m.group(1))
            var  = parts[0].strip().upper()
            stop = float(self._eval(parts[2]))
            step = float(self._eval(parts[3])) if len(parts) > 3 else 1.0
        else:
            m = re.match(r'FOR\s+(\w+)\s*=\s*.+?\s+TO\s+(.+?)(?:\s+STEP\s+(.+))?$',
                         for_stmt, re.IGNORECASE)
            if not m:
                return end + 1
            var  = m.group(1).upper()
            stop = float(self._eval(m.group(2)))
            step = float(self._eval(m.group(3))) if m.group(3) else 1.0

        self._vars[var] = self._vars.get(var, 0) + step
        cur = self._vars[var]
        in_range = (step > 0 and cur <= stop) or (step < 0 and cur >= stop)
        return (start + 1) if in_range else (end + 1)

    def _repeat_end(self, repeat_stmt: str, start: int, end: int) -> int:
        cond_str = repeat_stmt[6:].strip()
        return (end + 1) if bool(self._eval(cond_str)) else (start + 1)

    # ── CALL subprogramas ─────────────────────────────────────────────────────

    def _call(self, rest: str, ip: int) -> int:
        kw = self._kw(rest).upper()
        if kw == 'CLEAR':
            if self._clrhome_cb: self._clrhome_cb()
        elif kw == 'KEY':
            m = re.match(r'KEY\s*\((.+)\)', rest, re.IGNORECASE)
            if m:
                parts = self._split_args(m.group(1))
                if len(parts) >= 2:
                    self._asignar(parts[1].strip().upper(), 0.0)
                if len(parts) >= 3:
                    self._asignar(parts[2].strip().upper(), 0.0)
        elif kw == 'SOUND':
            pass
        elif kw == 'SAY':
            pass
        elif kw in ('CHAR','CHARSET','COLOR','SCREEN','HCHAR','VCHAR',
                    'SPRITE','DELSPRITE','MOTION','PATTERN','LOCATE',
                    'MAGNIFY','COINC','DISTANCE','POSITION'):
            pass
        elif kw == 'ERR':
            pass
        elif kw == 'VERSION':
            m = re.match(r'VERSION\s*\((.+)\)', rest, re.IGNORECASE)
            if m:
                self._asignar(m.group(1).strip().upper(), 200.0)
        return ip + 1

    # ── Split de print (respeta ; y ,) ────────────────────────────────────────

    def _split_args_print(self, s: str) -> list[str]:
        tokens, depth, in_q, cur = [], 0, False, []
        for c in s:
            if c == '"':
                in_q = not in_q; cur.append(c)
            elif not in_q and c == '(':
                depth += 1; cur.append(c)
            elif not in_q and c == ')':
                depth -= 1; cur.append(c)
            elif not in_q and c in (',', ';') and depth == 0:
                tokens.append(''.join(cur).strip())
                tokens.append(c)
                cur = []
            else:
                cur.append(c)
        if cur:
            tokens.append(''.join(cur).strip())
        return [t for t in tokens if t]

    # ── Split genérico ────────────────────────────────────────────────────────

    def _split_args(self, s: str) -> list[str]:
        args, depth, in_q, cur = [], 0, False, []
        for c in s:
            if c == '"':
                in_q = not in_q; cur.append(c)
            elif not in_q and c == '(':
                depth += 1; cur.append(c)
            elif not in_q and c == ')':
                depth -= 1; cur.append(c)
            elif not in_q and c == ',' and depth == 0:
                args.append(''.join(cur)); cur = []
            else:
                cur.append(c)
        if cur:
            args.append(''.join(cur))
        return args
