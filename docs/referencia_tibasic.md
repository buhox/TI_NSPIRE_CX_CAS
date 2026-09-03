# Referencia de TI-Basic (TI-Nspire)

El intérprete (`calculadora/ti_basic.py`) ejecuta el TI-Basic de la TI-Nspire
CX / CX CAS: `Define … Func/Prgm`, `→` para guardar, bloques `EndIf`/`EndFor`,
listas indexadas desde 1 y comentarios con `©`.

**Los programas se ejecutan en el PC, no en la calculadora.** Un `.tns` es un
formato de documento que libtifiles trata como un bloque opaco: se puede
transferir, pero no crear. Así que lo que escribas aquí no se puede subir a la
calculadora; sirve para escribir, probar y depurar antes de teclearlo allí.
Además la aritmética es la de Python, no la del CAS: los resultados numéricos
coinciden, pero una expresión simbólica no se simplifica igual.

## Definir funciones y programas

```
Define f(x)=Func
  Return x^2+1
EndFunc

Define saluda()=Prgm
  Disp "hola"
EndPrgm

Define g(x)=2*x+1          © forma de una línea
```

Una `Func` devuelve un valor con `Return`; un `Prgm` no devuelve nada y se
ejecuta por sus efectos. Si el código solo tiene definiciones, el panel ejecuta
`main()` si existe, y si no el último `Prgm` definido.

## Variables

| Qué | Sintaxis |
|---|---|
| Guardar | `expr→var` · `var:=expr` |
| Guardar en una lista | `valor→l[3]` |
| Declarar local | `Local a,b,c` |
| Borrar | `DelVar a,b` |

Los nombres no distinguen mayúsculas de minúsculas: `Total`, `total` y `TOTAL`
son la misma variable. Sin `Local`, una variable es global.

## Control de flujo

```
If cond Then          If cond              For i,1,10,2        While cond
  ...                   sentencia            ...                 ...
ElseIf cond Then                            EndFor              EndWhile
  ...
Else                  Loop                  Try
  ...                   ...                   ...
EndIf                   Exit                Else
                      EndLoop                 ...
                                            EndTry
```

- `Exit` sale del bucle; `Cycle` pasa a la siguiente vuelta.
- `Lbl nombre` y `Goto nombre` para saltos.
- `Return [expr]` sale de la función; `Stop` termina el programa.
- Dentro de `Try`, un error salta al `Else`. `ClrErr` limpia el error y
  `PassErr` lo vuelve a lanzar.

## Entrada y salida

| Comando | Qué hace |
|---|---|
| `Disp expr[,expr…]` | Muestra los valores |
| `Text expr` | Igual que `Disp` en este panel |
| `Request "texto",var` | Pide un valor y lo evalúa como expresión |
| `RequestStr "texto",var` | Pide un valor y lo guarda como cadena |
| `Input [prompt,]var` | Como `Request` |
| `Pause [expr]` | Muestra y espera |
| `ClrIO` · `ClrHome` | Limpia la pantalla |

## Operadores

| Categoría | Símbolos |
|---|---|
| Aritméticos | `+ - * / ^` · `√(x)` · `x²` |
| Comparación | `= ≠ < > ≤ ≥` — ojo: `=` **compara**, para guardar se usa `→` |
| Lógicos | `and or not xor` |
| Cadenas | `&` concatena |

## Listas, cadenas y matrices

**Se indexan desde 1**, como en la calculadora, no desde 0.

```
{4,8,15}→l
Disp l[1]              © 4
Disp dim(l)            © 3
99→l[2]                © {4,99,15}

"Nspire"→s
Disp s[1]              © N
Disp mid(s,2,3)        © spi

[[1,2][3,4]]→m
Disp m[2,1]            © 3
Disp m[1]              © {1,2}
```

## Funciones disponibles

- **Números**: `abs root ln log exp int iPart fPart round floor ceiling sign
  mod remain gcd lcm nCr nPr factorial approx`
- **Trigonometría** (en radianes): `sin cos tan arcsin arccos arctan sinh cosh
  tanh`. También se aceptan `sin⁻¹`, `cos⁻¹`, `tan⁻¹`.
- **Listas**: `dim sum product mean max min augment sortA sortD left right`
- **Cadenas**: `dim left right mid inString char ord`
- **Otras**: `when(cond,a,b)` · `rand([n])` · `randInt(a,b[,n])`
- **Constantes**: `pi` (o `π`), `e`, `true`, `false`, `undef`, `infinity` (`∞`)

## Comentarios

`©` comienza un comentario hasta el final de la línea (el panel también acepta
`//`). El separador `:` permite varias sentencias en una línea.

## Lo que no está implementado

No hay CAS simbólico (`solve`, `expand`, `factor`, `∫`, `d/dx`), ni gráficos,
ni acceso a las variables del documento de la calculadora, ni `DispAt` con
posicionamiento, ni bibliotecas `LibPub` compartidas entre documentos. Para
álgebra simbólica están los paneles CAS y Gráficas, que usan SymPy.
