# Referencia TI-Basic

El intérprete (`calculadora/ti_basic.py`) ejecuta programas TI-Basic con dos
estilos compatibles:

- **TI-Nspire CX CAS** — sin números de línea, asignación con `→` o `:=`,
  bloques `For ... EndFor`, `If ... EndIf`.
- **TI-99/4A Extended Basic** — con números de línea, `LET`, `FOR/NEXT`,
  `GOSUB/RETURN`.

## Asignación de variables

| Estilo | Sintaxis | Ejemplo |
|---|---|---|
| TI-Nspire (flecha) | `expr → Var` | `5 → A` |
| TI-Nspire (`:=`) | `Var := expr` | `A := 5` |
| TI-99/4A | `LET Var = expr` | `LET A = 5` |
| Implícita | `Var = expr` | `A = 5` |

## Entrada / salida

| Comando | Descripción |
|---|---|
| `PRINT` / `DISP` | Muestra texto y valores (separadores `;` y `,`) |
| `INPUT` / `LINPUT` | Pide un valor al usuario (con mensaje opcional) |
| `PROMPT` | Pide uno o más valores (`PROMPT A, B`) |
| `OUTPUT` / `DISPLAY AT` | Salida en una posición dada |
| `PAUSE` | Pausa hasta que el usuario presiona Enter |
| `CLRHOME` / `CALL CLEAR` / `NEW` | Limpia la pantalla |

## Control de flujo

| Estructura | Palabras clave |
|---|---|
| Condicional | `IF ... THEN ... ELSE ... ENDIF` |
| Bucle contador | `FOR ... NEXT` / `FOR ... ENDFOR` |
| Bucle condicional | `WHILE ... ENDWHILE` (`WEND`) |
| Bucle repetir | `REPEAT ... END` |
| Salto | `GOTO` + etiqueta `LBL` |
| Subrutina | `GOSUB` / `RETURN` |
| Terminación | `STOP` / `BYE` / `RETURN` / `SUBEXIT` |

## Datos y estructuras

| Comando | Descripción |
|---|---|
| `DATA` / `READ` | Define y lee datos secuenciales |
| `DIM var(n[,m])` | Declara un array de 1 o 2 dimensiones |
| `DEF fn(x) = expr` | Define una función |
| `CALL` | Llama a un subprograma (TI-99/4A) |
| `RANDOMIZE [semilla]` | Inicializa el generador aleatorio |

## Funciones matemáticas incorporadas

- **Trigonometría**: `sin`, `cos`, `tan`, `asin`, `acos`, `atan` (`ATN`),
  `sinh`, `cosh`, `tanh`
- **Álgebra**: `sqrt` (`SQR`), `abs`, `log` (base 10), `ln`, `exp`,
  `int` (parte entera), `iPart`, `frac`, `round`, `max`, `min`, `sgn`
- **Aleatoriedad**: `rand` / `RND`, `randInt(a, b)`
- **Cadenas**: `LEN`, `ASC`, `CHR`, `STR`, `VAL`, `SEG` (subcadena),
  `RPT` (repetir), `POS` (buscar), `TAB`
- **Constantes**: `pi` / `π`, `e`

## Operadores

| Notación TI | Significado |
|---|---|
| `^` | Potencia |
| `=` | Igualdad (comparación) |
| `≠` | Distinto (`!=`) |
| `≤`, `≥` | Menor/mayor o igual |
| `and`, `or`, `not`, `XOR` | Operadores lógicos |

## Comentarios

Se ignoran las líneas que empiezan por `REM`, `//` o `'`.

## Ejemplo

```
"Hola desde TI-Basic" → msg
Disp msg
For i, 1, 5
  Disp i, i^2
EndFor
```
