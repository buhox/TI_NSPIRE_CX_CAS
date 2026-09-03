# TI-Nspire CX CAS — PC

Aplicación de escritorio PyQt5 para gestionar la calculadora TI-Nspire CX CAS.

## Rutas
- Proyecto: `/home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS/`
- Lanzador: `lanzar.sh`
- Acceso directo escritorio: `~/.local/share/applications/ti-nspire-cx-cas.desktop`

## Estructura del proyecto
- `main.py` — Punto de entrada
- `gui/ventana_principal.py` — Ventana principal, pestañas, tema visual
- `gui/panel_cas.py` — Panel CAS / Álgebra
- `gui/panel_graficas.py` — Panel de Gráficas
- `gui/panel_matriz.py` — Panel de Matrices
- `gui/panel_tibasic.py` — Panel TI-Basic
- `gui/panel_archivos.py` — Panel de transferencia de archivos
- `gui/barra_estado.py` — Barra de conexión USB
- `comunicacion/detector.py` — Detección USB via /sys/bus/usb/devices (sin libusb)
- `comunicacion/transferencia.py` — Transferencia de archivos (ctypes → libticalcs2)
- `pruebas_calc.py` — Banco de pruebas del backend con la calculadora conectada
- `calculadora/cas.py` — Cálculos CAS con SymPy
- `calculadora/graficas.py` — Gráficas matemáticas con Matplotlib
- `calculadora/ti_basic.py` — Intérprete de TI-Basic de TI-Nspire

## Dependencias
```
PyQt5>=5.15
sympy>=1.12
numpy>=1.24
matplotlib>=3.7
pyusb>=1.2
scipy>=1.10
```

## Lo que se hizo en la sesión
- Se creó `lanzar.sh` — script bash que lanza la app con `python3 main.py`
- Se creó `~/.local/share/applications/ti-nspire-cx-cas.desktop` — acceso directo en el menú de aplicaciones de Fedora
- La instalación en Fedora es Opción A (lanzador de escritorio, sin compilar)

## Comandos para activar la app en Fedora
```bash
# Instalar dependencias
pip install PyQt5 sympy numpy matplotlib pyusb scipy

# Dar permisos al lanzador
chmod +x /home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS/lanzar.sh

# Actualizar menú de aplicaciones
update-desktop-database ~/.local/share/applications/

# Ejecutar directamente
cd /home/jbotero/Documentos/proyecto_freebuff/TI_NSPIRE_CX_CAS
python3 main.py
```

## ABI de las librerías TI (verificado sobre libticalcs/libtifiles 1.19)
Los layouts y firmas de `comunicacion/transferencia.py` están comprobados contra
las librerías instaladas, no supuestos. Si se tocan, revalidar con `pruebas_calc.py`.

- `sizeof(VarEntry) == 2072` — `folder[1024]`, `name[1024]`, `type`, `attr`,
  `version`, `size`@2052, `data`@2056, `action`@2064. `VarRequest` es un alias.
- `sizeof(CalcInfos) == 344` — empieza por `model` y `mask`; `os_version` está en
  el **offset 210**, no al principio. `mask` (InfosMask) dice qué campos son válidos.
  `battery` es un **flag** de "batería suficiente", NO un porcentaje, y no existe
  ningún campo `charging`.
- La Nspire **no** declara `FTS_NONSILENT`: las funciones `*_var_ns` / `*_var_ns2`
  no le sirven. Hay que usar las silenciosas:
  `ticalcs_calc_send_var(h, mode, FileContent*)` y
  `ticalcs_calc_recv_var(h, mode, FileContent*, VarRequest*)`.
- `tifiles_file_read_regular(const char*, FileContent*)` recibe un FileContent
  **ya asignado** con `tifiles_content_create_regular(CALC_NSPIRE)` — no es un
  parámetro de salida.
- `tifiles_file_write_regular(const char*, FileContent*, char**)` tiene **3**
  parámetros; el tercero es de salida y hay que pasarlo sí o sí.
- `CALC_NSPIRE == 15` (`tifiles_model_to_string(15)` → "Nspire").
- `ticalcs_calc_features(handle)` funciona sin cable conectado: sirve para saber
  qué operaciones soporta el modelo antes de intentarlas.
- Códigos de error: `ticalcs_error_get` cubre los >= 256; los más bajos son de
  `ticables_error_get` / `tifiles_error_get`. `_msg_error()` prueba las tres.
- Captura: `ticalcs_calc_recv_screen_rgb888(h, CalcScreenCoord*, uint8_t**)` +
  `ticalcs_free_screen`. En la CX CAS devuelve 320x240 RGB888 (230.400 B).
  `sizeof(CalcScreenCoord) == 24`. Leer `clipped_width/height`, nunca mayores
  que `width/height`, así la lectura es segura sea cual sea el búfer asignado.
- Crear carpeta: `ticalcs_calc_new_fld(h, VarRequest*)` con el nombre en el
  campo **`folder`** y `name` vacío. Se llama `new_fld`, no `new_folder`.
- **Borrar carpetas no está en la API pública** (solo el `nsp_cmd_s_del_folder`
  de bajo nivel). Hay que borrarlas desde la calculadora.
- Renombrar: `ticalcs_calc_rename_var(h, VarRequest* orig, VarRequest* nuevo)`.
  Los dos VarEntry llevan la MISMA carpeta; solo cambia `name`.
- Actualizar el OS: `ticalcs_calc_send_os2(h, const char* ruta)` (el sufijo `2`
  significa "recibe un nombre de archivo", igual que en el resto de la familia).
- Progreso: `ticalcs_update_set(h, CalcUpdate*)`. `sizeof(CalcUpdate) == 336`.
  **Los callbacks de ctypes y el propio struct hay que guardarlos como atributos**
  del gestor: si Python los recolecta, la librería salta a memoria liberada.
  Un callback invocado desde C nunca puede dejar escapar una excepción.
- **libtifiles solo tiene un CalcModel para toda la familia Nspire (15)**, así que
  NO distingue una imagen de OS con CAS de una sin CAS. Eso se deduce de la
  extensión: `.tno`=Nspire, `.tnc`=Nspire CAS, `.tco`=CX, `.tcc`=CX CAS. Antes de
  flashear se compara con el `product_name` real de la calculadora conectada,
  porque instalar un `.tco` en una CX CAS le quitaría el CAS.

## Estado de las operaciones (probado con la calculadora el 2026-09-02)
Todo verificado contra una CX CAS con OS 3.60.0550:
conectar · listar · info (OS/batería/RAM/Flash) · enviar · recibir · eliminar ·
captura de pantalla · crear carpeta · **renombrar**. Repetir con
`python3 pruebas_calc.py`.

## PENDIENTE: flasheo del OS (nunca ejecutado contra hardware real)
`actualizar_os()` en `comunicacion/transferencia.py:1032` está implementado pero
**nunca se ha ejecutado de punta a punta**. Falta lo único que no se puede
fabricar en el código: una imagen `.tcc` real (Nspire CX CAS) de TI. Es una
operación de riesgo (línea 1038): una interrupción a mitad de escritura —cable
suelto, batería agotada— puede dejar la calculadora en modo de emergencia o
inutilizarla.

Lo que sí está probado (por lógica, sin escritura real):
- Rechaza archivos que no son de Texas Instruments (`tifiles_file_is_ti`).
- Rechaza archivos que no son imagen de OS (`tifiles_file_is_os`/`is_tno`).
- Rechaza imágenes de otro modelo que no sea Nspire.
- Compara la extensión (`.tcc`/`.tco`/`.tnc`/`.tno`) contra el `product_name`
  real de la calculadora para no instalar una imagen sin CAS sobre una CAS.
- Aborta si el flag de batería (`INFOS_BATTERY`) indica batería baja.

Para poder marcarlo como probado hace falta: conseguir una imagen `.tcc`
oficial, probar con batería alta y cable estable, ejecutar el flasheo una vez
y confirmar que la calculadora arranca normal después.

## Panel TI-Basic
`calculadora/ti_basic.py` interpreta el TI-Basic **de la TI-Nspire**: `Define …
Func/Prgm`, `Local`, `→`, `EndIf`/`EndFor`/`EndWhile`/`EndLoop`, `Try/Else/EndTry`,
`Exit`/`Cycle`, `Lbl`/`Goto`, `Disp`/`Request`, comentarios con `©`.

Tres detalles del lenguaje que no son los de Python y el intérprete respeta:
- **Listas y cadenas se indexan desde 1** (clases `TIList` y `TICadena`).
- **Los identificadores no distinguen mayúsculas**: se normalizan a minúsculas.
- **`=` compara**; para guardar se usa `→` o `:=`.

Las expresiones se traducen a Python y se evalúan (`traducir()` en ese módulo).
Los programas **corren en el PC y no se pueden subir a la calculadora**: un
`.tns` es un documento que libtifiles trata como bloque opaco, se transfiere
pero no se crea. Tampoco hay CAS simbólico aquí. Referencia del lenguaje y lo
que falta: `docs/referencia_tibasic.md`.

Antes había un intérprete de BASIC de TI-99/4A y TI-8x (`LET`, `GOSUB`,
`CALL SOUND`, `L1..L6`) que no tenía nada que ver con la Nspire. Se eliminó.

## Notas técnicas
- El detector USB lee `/sys/bus/usb/devices` directamente, sin libusb/pyusb, para evitar conflictos con ticables
- Todas las llamadas USB (incluida la desconexión) se serializan con un `RLock`:
  desconectar sin el lock mientras otro hilo transfiere provoca use-after-free
- Vendor ID Texas Instruments: 0x0451
- PIDs soportados: 0xE022 (CX CAS), 0xE012 (CX), 0xE008 (Nspire), 0xE003 (CAS)
- No modificar código sin aprobación explícita del usuario
