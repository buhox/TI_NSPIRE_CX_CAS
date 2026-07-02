# Referencia CAS

El motor CAS (`calculadora/cas.py`) implementa cálculo simbólico y numérico
sobre **SymPy**, organizado como los menús de la calculadora.

## Sintaxis de entrada

Las expresiones se escriben en texto. El motor traduce automáticamente la
notación de la calculadora a la de SymPy:

| Símbolo TI | Se traduce a | Significado |
|---|---|---|
| `^` | `**` | Potencia |
| `√` | `sqrt` | Raíz cuadrada |
| `π` | `pi` | Pi |
| `∞` | `oo` | Infinito |
| `×` | `*` | Multiplicación |
| `÷` | `/` | División |
| `–` | `-` | Signo menos (guión largo) |

Además:

- La **multiplicación implícita** está activada: `2x` equivale a `2*x`.
- Variables disponibles por defecto: `x, y, z, t, n, k, a, b, c`.
- Constantes: `pi`, `e`, `E`, `i` (unidad imaginaria), `oo`/`inf` (infinito).

## Álgebra

| Función | Descripción | Ejemplo de entrada |
|---|---|---|
| `evaluar` | Evalúa una expresión | `2+3` → `5` |
| `simplificar` | Simplifica | `sin(x)^2 + cos(x)^2` → `1` |
| `expandir` | Expande productos y potencias | `(x+1)^2` → `x**2 + 2*x + 1` |
| `factorizar` | Factoriza polinomios | `x^2 - 4` → `(x-2)(x+2)` |
| `resolver` | Resuelve ecuaciones | `x^2 - 4 = 0` → `[-2, 2]` |
| `fracciones_parciales` | Descompone en fracciones parciales | `1/(x^2-1)` |

**Formatos aceptados por `resolver`:**

- `x^2 - 4` — se iguala a cero implícitamente
- `x^2 - 4 = 0` — con igualdad explícita
- `x + y = 5, x - y = 1` — sistema (ecuaciones separadas por comas)

## Cálculo

| Función | Descripción | Parámetros |
|---|---|---|
| `derivar` | Derivada de orden *n* | variable, orden |
| `integrar` | Integral indefinida o definida | variable, límites opcionales |
| `limite` | Límite en un punto | variable, punto, dirección (`+`, `-`, `+-`) |
| `serie_taylor` | Serie de Taylor | variable, punto, orden (por defecto 6) |

Si a `integrar` se le dan límite inferior y superior, calcula la integral
definida; si no, la indefinida.

## Matrices

| Función | Descripción |
|---|---|
| `crear_matriz` | Crea una matriz desde filas |
| `determinante` | Determinante de una matriz cuadrada |
| `inversa` | Matriz inversa |
| `valores_propios` | Valores propios (*eigenvalues*) con multiplicidad |

## Números y aritmética

| Función | Descripción | Ejemplo |
|---|---|---|
| `factores_primos` | Factorización en primos | `360` → `2^3 × 3^2 × 5` |
| `es_primo` | Test de primalidad | `17` → `17 es primo` |
| `combinatoria` | Combinaciones C(n, r) | `C(5, 2)` → `10` |

## Formato de resultado

Cada operación devuelve un objeto `ResultadoCAS` con:

- `expresion` — el objeto SymPy resultante
- `latex_str` — representación en LaTeX
- `texto` — representación legible (pretty-print Unicode)
- `error` — mensaje de error si la operación falló
- `ok` — `True` si no hubo error
