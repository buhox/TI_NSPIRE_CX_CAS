# Guía de usuario

La aplicación se organiza en pestañas, cada una dedicada a una función de la
calculadora. En la parte inferior, la **barra de estado** muestra si hay una
TI-Nspire CX CAS conectada por USB.

## Iniciar la aplicación

```bash
python3 main.py      # o bien:  ./lanzar.sh
```

## Panel CAS / Álgebra

Cálculo simbólico y numérico con SymPy. Escribe una expresión y aplica la
operación deseada (evaluar, simplificar, expandir, factorizar, derivar,
integrar, resolver, etc.).

- La sintaxis de entrada admite notación de la calculadora (`^`, `√`, `π`, `∞`).
- Consulta la [referencia CAS](referencia_cas.md) para la lista completa de
  funciones y la sintaxis aceptada.

## Panel de Gráficas

Representación de funciones matemáticas con Matplotlib:

- **Funciones 2D**: introduce una o varias funciones de `x`.
- **Superficies 3D**: funciones de dos variables.
- **Puntos**: nubes de puntos a partir de listas de datos.

## Panel de Matrices

Operaciones matriciales: determinante, matriz inversa y valores propios
(*eigenvalues*). Introduce la matriz por filas.

## Panel TI-Basic

Editor y ejecutor de programas TI-Basic con entrada/salida interactiva.
Soporta tanto el estilo TI-Nspire (`:=`, `→`, `For ... EndFor`) como
TI-99/4A Extended Basic (números de línea, `LET`, `FOR/NEXT`, `GOSUB`).
Consulta la [referencia TI-Basic](referencia_tibasic.md).

## Panel de Archivos

Transferencia de archivos entre el PC y la calculadora:

- Listar los archivos de la calculadora.
- **Enviar** un archivo del PC a la calculadora (se añade la extensión `.tns`
  automáticamente si falta).
- **Recibir** un archivo de la calculadora al PC.
- **Eliminar** un archivo de la calculadora.

Requiere una calculadora conectada por USB. Ver [conexión USB](conexion_usb.md).
