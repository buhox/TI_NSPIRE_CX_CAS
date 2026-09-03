#!/usr/bin/env python3
# =============================================================================
# BANCO DE PRUEBAS — TI-Nspire CX CAS
# Ejercita el backend de comunicación paso a paso, con la calculadora conectada.
#
#   python3 pruebas_calc.py                 → solo lectura (seguro)
#   python3 pruebas_calc.py --enviar X.tns  → prueba el envío PC → calculadora
#   python3 pruebas_calc.py --recibir       → baja el primer archivo a /tmp
#   python3 pruebas_calc.py --eliminar NOM  → DESTRUCTIVO, pide confirmación
#   python3 pruebas_calc.py -v              → log detallado de ctypes
# =============================================================================
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comunicacion.transferencia import (      # noqa: E402
    GestorTransferencia, EntradaArchivo,
    FTS_SILENT, FTS_FOLDER, FTS_MEMFREE, FTS_NONSILENT,
    OPS_ISREADY, OPS_DIRLIST, OPS_VARS, OPS_VERSION, OPS_DELVAR,
    OPS_SCREEN, OPS_NEWFLD, OPS_OS, OPS_RENAME,
)

VERDE, ROJO, GRIS, AMAR, FIN = "\033[32m", "\033[31m", "\033[90m", "\033[33m", "\033[0m"


def titulo(t):
    print(f"\n{GRIS}{'─' * 66}{FIN}\n  {t}\n{GRIS}{'─' * 66}{FIN}")


def ok(t):    print(f"  {VERDE}✓{FIN} {t}")
def fallo(t): print(f"  {ROJO}✗{FIN} {t}")
def nota(t):  print(f"  {GRIS}·{FIN} {t}")


def fmt(n):
    if n >= 1_048_576:
        return f"{n / 1_048_576:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def main():
    ap = argparse.ArgumentParser(description="Banco de pruebas TI-Nspire CX CAS")
    ap.add_argument("--enviar",   metavar="RUTA", help="archivo del PC a enviar")
    ap.add_argument("--recibir",  action="store_true",
                    help="descargar el primer archivo listado a /tmp")
    ap.add_argument("--eliminar", metavar="NOMBRE",
                    help="eliminar ese archivo de la calculadora (destructivo)")
    ap.add_argument("--captura", nargs="?", const="/tmp/nspire.png", metavar="RUTA",
                    help="capturar la pantalla a un PNG (por defecto /tmp/nspire.png)")
    ap.add_argument("--carpeta", metavar="NOMBRE",
                    help="crear una carpeta con ese nombre en la calculadora")
    ap.add_argument("--renombrar", metavar="VIEJO:NUEVO",
                    help="renombrar un archivo de la calculadora")
    ap.add_argument("--validar-os", metavar="RUTA",
                    help="comprobar si un archivo es una imagen de OS válida "
                         "(NO la envía, no toca la calculadora)")
    ap.add_argument("--actualizar-os", metavar="RUTA",
                    help="DESTRUCTIVO: flashear el sistema operativo")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="    %(levelname)s %(name)s: %(message)s",
    )

    g = GestorTransferencia()

    # ── 1. Librerías ──────────────────────────────────────────────────────────
    titulo("1. Librerías")
    if not g.disponible:
        fallo(f"no se cargaron: {g._error_init}")
        return 1
    ok("libticalcs2 / libticables2 / libtifiles2 cargadas")

    import ctypes
    from comunicacion.transferencia import VarEntry, CalcInfos
    if ctypes.sizeof(VarEntry) == 2072 and VarEntry.data.offset == 2056:
        ok("layout de VarEntry correcto (2072 B, data@2056)")
    else:
        fallo(f"VarEntry mide {ctypes.sizeof(VarEntry)} B — ABI distinto, ¡no continúes!")
        return 1
    if CalcInfos.os_version.offset == 210:
        ok("layout de CalcInfos correcto (os_version@210)")
    else:
        fallo(f"CalcInfos.os_version en {CalcInfos.os_version.offset}, se esperaba 210")

    # ── 2. Conexión ───────────────────────────────────────────────────────────
    titulo("2. Conexión USB")
    conectado, msg = g.conectar()
    if not conectado:
        fallo(msg)
        nota("¿está encendida, desbloqueada y en la pantalla principal?")
        nota("¿hay otro programa (TiLP) usando el cable?")
        return 1
    ok(msg)

    try:
        # ── 3. Capacidades ────────────────────────────────────────────────────
        titulo("3. Capacidades que declara la librería para este modelo")
        print(f"  features = 0x{g.features & 0xffffffff:08x}")
        for nombre, bit in (
            ("OPS_ISREADY  (isready)",        OPS_ISREADY),
            ("OPS_DIRLIST  (listar)",         OPS_DIRLIST),
            ("OPS_VARS     (enviar/recibir)", OPS_VARS),
            ("OPS_DELVAR   (eliminar)",       OPS_DELVAR),
            ("OPS_VERSION  (info OS)",        OPS_VERSION),
            ("OPS_SCREEN   (captura)",        OPS_SCREEN),
            ("OPS_NEWFLD   (crear carpeta)",  OPS_NEWFLD),
            ("OPS_RENAME   (renombrar)",      OPS_RENAME),
            ("OPS_OS       (actualizar OS)",  OPS_OS),
            ("FTS_SILENT   (transf. silenciosa)", FTS_SILENT),
            ("FTS_FOLDER   (carpetas)",       FTS_FOLDER),
            ("FTS_MEMFREE  (memoria libre)",  FTS_MEMFREE),
            ("FTS_NONSILENT (variantes _ns)", FTS_NONSILENT),
        ):
            marca = f"{VERDE}sí{FIN}" if g.soporta(bit) else f"{AMAR}no{FIN}"
            print(f"    {nombre:36} {marca}")
        if g.soporta(FTS_NONSILENT):
            nota("ojo: esta calculadora SÍ soporta _ns; el código usa las silenciosas igual")

        # ── 4. Listado ────────────────────────────────────────────────────────
        titulo("4. Listado de archivos")
        entradas, err = g.listar_archivos()
        if err:
            fallo(err)
        else:
            archivos = [e for e in entradas if not e.es_carpeta]
            carpetas = [e for e in entradas if e.es_carpeta]
            ok(f"{len(archivos)} archivos en {len(carpetas)} carpetas")
            for e in entradas[:25]:
                if e.es_carpeta:
                    print(f"    📁 {e.nombre}/")
                else:
                    print(f"       {e.ruta_calc:<44} {fmt(e.tamanio):>10}  tipo=0x{e.tipo:02x}")
            if len(entradas) > 25:
                nota(f"... y {len(entradas) - 25} más")

        # ── 5. Info del dispositivo ───────────────────────────────────────────
        titulo("5. Info del dispositivo (CalcInfos)")
        info = g.obtener_info_dispositivo()
        if not info:
            fallo("no devolvió nada — revisa el log con -v")
        else:
            for k, v in info.items():
                if k.startswith(("mem_", "ram_", "flash_")) and isinstance(v, int):
                    v = fmt(v)
                print(f"    {k:18} = {v}")
            if isinstance(info.get("os_version"), str) and info["os_version"][:1].isdigit():
                ok("os_version tiene pinta de versión real → layout confirmado")
            else:
                fallo("os_version no parece una versión — revisar el layout de CalcInfos")

        # ── 6. Envío ──────────────────────────────────────────────────────────
        if args.enviar:
            titulo(f"6. Envío PC → calculadora: {args.enviar}")
            if not os.path.isfile(args.enviar):
                fallo("ese archivo no existe")
            else:
                bien, m = g.enviar_archivo(args.enviar, progreso_cb=nota)
                (ok if bien else fallo)(m or "enviado")

        # ── 7. Recepción ──────────────────────────────────────────────────────
        if args.recibir:
            titulo("7. Recepción calculadora → PC")
            candidatos = [e for e in entradas if not e.es_carpeta]
            if not candidatos:
                fallo("no hay archivos que descargar")
            else:
                e = candidatos[0]
                nota(f"descargando {e.ruta_calc} a /tmp")
                bien, m = g.recibir_archivo(e, "/tmp", progreso_cb=nota)
                if bien:
                    ok(f"guardado en {m} ({fmt(os.path.getsize(m))})")
                else:
                    fallo(m)

        # ── 8. Eliminación ────────────────────────────────────────────────────
        if args.eliminar:
            titulo(f"8. Eliminar de la calculadora: {args.eliminar}")
            objetivo = next(
                (e for e in entradas
                 if not e.es_carpeta
                 and args.eliminar in (e.nombre, e.ruta_calc)), None)
            if not objetivo:
                fallo("no encontré ese archivo en el listado")
            else:
                r = input(f"  {AMAR}¿Eliminar '{objetivo.ruta_calc}'? "
                          f"esto NO se deshace [escribe SI]: {FIN}")
                if r.strip() == "SI":
                    bien, m = g.eliminar_archivo(objetivo)
                    (ok if bien else fallo)(m or "eliminado")
                else:
                    nota("cancelado")

        # ── 9. Captura de pantalla ────────────────────────────────────────────
        if args.captura:
            titulo(f"9. Captura de pantalla → {args.captura}")
            cap, m = g.capturar_pantalla()
            if cap is None:
                fallo(m)
            else:
                ok(f"recibida {cap.ancho}x{cap.alto} px "
                   f"({len(cap.rgb888)} B en RGB888)")
                cap.guardar_png(args.captura)
                ok(f"guardada en {args.captura} "
                   f"({fmt(os.path.getsize(args.captura))})")

        # ── 10. Crear carpeta ─────────────────────────────────────────────────
        if args.carpeta:
            titulo(f"10. Crear carpeta: {args.carpeta}")
            bien, m = g.crear_carpeta(args.carpeta)
            if bien:
                ok("creada — comprobando en el listado...")
                entradas2, err2 = g.listar_archivos()
                if any(e.es_carpeta and e.nombre == args.carpeta for e in entradas2):
                    ok(f"'{args.carpeta}' aparece en la calculadora")
                else:
                    fallo(f"la librería dijo OK pero '{args.carpeta}' no está "
                          f"en el listado (¿carpeta vacía no se lista?)")
            else:
                fallo(m)

        # ── 11. Renombrar ─────────────────────────────────────────────────────
        if args.renombrar:
            titulo(f"11. Renombrar: {args.renombrar}")
            if ":" not in args.renombrar:
                fallo("formato: --renombrar VIEJO:NUEVO")
            else:
                viejo_n, nuevo_n = args.renombrar.split(":", 1)
                objetivo = next(
                    (e for e in entradas if not e.es_carpeta
                     and viejo_n in (e.nombre, e.ruta_calc)), None)
                if not objetivo:
                    fallo(f"'{viejo_n}' no está en el listado")
                else:
                    bien, m = g.renombrar(objetivo, nuevo_n)
                    if bien:
                        ok("renombrado — comprobando...")
                        e2, _ = g.listar_archivos()
                        nombres = [x.nombre for x in e2 if not x.es_carpeta]
                        if nuevo_n in nombres and viejo_n not in nombres:
                            ok(f"'{viejo_n}' → '{nuevo_n}' confirmado")
                        else:
                            fallo(f"el listado no lo refleja: {nombres}")
                    else:
                        fallo(m)

        # ── 12. Validar imagen de OS (no toca la calculadora) ─────────────────
        if args.validar_os:
            titulo(f"12. Validar imagen de OS: {args.validar_os}")
            bien, m = g.validar_archivo_os(args.validar_os)
            (ok if bien else fallo)(m)

        # ── 13. Flasheo del OS ────────────────────────────────────────────────
        if args.actualizar_os:
            titulo(f"13. ACTUALIZAR EL SISTEMA OPERATIVO: {args.actualizar_os}")
            bien, m = g.validar_archivo_os(args.actualizar_os)
            if not bien:
                fallo(m)
            else:
                ok(m)
                print(f"\n  {ROJO}Esto reescribe el firmware de la calculadora.{FIN}")
                print(f"  {ROJO}Si se interrumpe (cable suelto, batería baja) puede")
                print(f"  quedar inutilizable y habría que recuperarla por el modo")
                print(f"  de emergencia.{FIN}")
                r = input(f"  {AMAR}Escribe ACTUALIZAR para continuar: {FIN}")
                if r.strip() != "ACTUALIZAR":
                    nota("cancelado")
                else:
                    def barra(texto, pct):
                        if pct >= 0:
                            print(f"\r    {texto[:40]:<40} {pct:5.1f}%",
                                  end="", flush=True)
                        elif texto:
                            print(f"\r    {texto[:60]:<60}", end="", flush=True)
                    bien, m = g.actualizar_os(args.actualizar_os, progreso_cb=barra)
                    print()
                    (ok if bien else fallo)(m)

    finally:
        titulo("Cierre")
        g.cerrar()
        ok("sesión cerrada")

    return 0


if __name__ == "__main__":
    sys.exit(main())
