# =============================================================================
# GESTOR DE TRANSFERENCIA DE ARCHIVOS — TI-Nspire CX CAS
# Usa libticalcs2 + libticables2 + libtifiles2 vía ctypes
# =============================================================================
from __future__ import annotations

import ctypes
import logging
import os
import threading
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger("ti_nspire.transferencia")

# ── Constantes de protocolo ───────────────────────────────────────────────────
CALC_NSP   = 15   # TI-Nspire (ticalcs_model_to_string → "Nspire")
CABLE_USB  = 5    # DirectLink USB
PORT_1     = 1
MODE_NORMAL = 0


# ── Estructuras ctypes ────────────────────────────────────────────────────────

class GNode(ctypes.Structure):
    pass

GNode._fields_ = [
    ('data',     ctypes.c_void_p),
    ('next',     ctypes.POINTER(GNode)),
    ('prev',     ctypes.POINTER(GNode)),
    ('parent',   ctypes.POINTER(GNode)),
    ('children', ctypes.POINTER(GNode)),
]


class VarEntry(ctypes.Structure):
    """
    Layout verificado experimentalmente (x86_64):
      offset  0: folder[41]
      offset 41: name[41]
      offset 82: type (uint8)
      offset 83: attr (uint8)
      offset 84: size (uint32)   ← confirmado offset 84
      offset 88: data (void*)
      offset 96: data_name (char*)
      offset 104: data_ext (char*)
    """
    _fields_ = [
        ('folder',    ctypes.c_char * 41),
        ('name',      ctypes.c_char * 41),
        ('type',      ctypes.c_uint8),
        ('attr',      ctypes.c_uint8),
        ('size',      ctypes.c_uint32),
        ('data',      ctypes.c_void_p),
        ('data_name', ctypes.c_void_p),
        ('data_ext',  ctypes.c_void_p),
    ]


class CalcInfos(ctypes.Structure):
    """
    Mapa de CalcInfos de libticalcs2 (x86_64).
    Contiene versión OS, batería y memoria — llenado por ticalcs_calc_get_version.
    """
    _fields_ = [
        ('os_version',    ctypes.c_char * 64),
        ('boot_version',  ctypes.c_char * 64),
        ('product_name',  ctypes.c_char * 65),
        ('product_id',    ctypes.c_uint8),
        ('language_id',   ctypes.c_uint8),
        ('mcu',           ctypes.c_uint8),
        ('_pad',          ctypes.c_uint8),
        ('hw_ver',        ctypes.c_uint32),
        ('mem_ram',       ctypes.c_uint32),
        ('mem_flash',     ctypes.c_uint32),
        ('mem_free_ram',  ctypes.c_uint32),
        ('mem_free_flash',ctypes.c_uint32),
        ('battery',       ctypes.c_uint8),
        ('charging',      ctypes.c_uint8),
        ('_reserved',     ctypes.c_uint8 * 256),
    ]


@dataclass
class EntradaArchivo:
    carpeta: str
    nombre: str
    tamanio: int        # bytes
    es_carpeta: bool = False
    tipo: int = 0       # tipo de variable (0x73 para .tns NSP, 0x01 para carpeta)

    @property
    def ruta_calc(self) -> str:
        if self.carpeta:
            return f"{self.carpeta}/{self.nombre}"
        return self.nombre

    @property
    def extension(self) -> str:
        _, ext = os.path.splitext(self.nombre)
        return ext.lower()


# ── Backend ctypes ────────────────────────────────────────────────────────────

class GestorTransferencia:
    """
    Gestiona la conexión y transferencia de archivos con la calculadora
    TI-Nspire CX CAS a través de las librerías libticalcs2/libticables2.
    """

    def __init__(self):
        self._calc_h:   ctypes.c_void_p = None
        self._cable_h:  ctypes.c_void_p = None
        self._conectado = False
        self._ticalcs  = None
        self._ticables = None
        self._tifiles  = None
        self._error_init: str = ""
        self._lock = threading.Lock()   # serializa todas las llamadas USB a ticalcs
        self._cargar_libs()

    # ── Carga de librerías ────────────────────────────────────────────────────

    def _cargar_libs(self):
        try:
            self._ticalcs  = ctypes.cdll.LoadLibrary("libticalcs2.so.13")
            self._ticables = ctypes.cdll.LoadLibrary("libticables2.so.8")
            self._tifiles  = ctypes.cdll.LoadLibrary("libtifiles2.so.11")
            self._configurar_prototipos()
            self._ticalcs.ticalcs_library_init()
            self._ticables.ticables_library_init()
            self._tifiles.tifiles_library_init()
            logger.info("Librerías TI cargadas OK")
        except Exception as e:
            self._error_init = str(e)
            logger.warning("No se pudieron cargar las librerías TI: %s", e)
            self._ticalcs = self._ticables = self._tifiles = None

    def _configurar_prototipos(self):
        tc = self._ticalcs
        tb = self._ticables
        tf = self._tifiles

        # ticables
        tb.ticables_handle_new.restype  = ctypes.c_void_p
        tb.ticables_handle_new.argtypes = [ctypes.c_int, ctypes.c_int]
        tb.ticables_handle_del.restype  = ctypes.c_int
        tb.ticables_handle_del.argtypes = [ctypes.c_void_p]
        tb.ticables_cable_open.restype  = ctypes.c_int
        tb.ticables_cable_open.argtypes = [ctypes.c_void_p]
        tb.ticables_cable_close.restype = ctypes.c_int
        tb.ticables_cable_close.argtypes = [ctypes.c_void_p]

        # ticalcs
        tc.ticalcs_handle_new.restype  = ctypes.c_void_p
        tc.ticalcs_handle_new.argtypes = [ctypes.c_int]
        tc.ticalcs_handle_del.restype  = ctypes.c_int
        tc.ticalcs_handle_del.argtypes = [ctypes.c_void_p]
        tc.ticalcs_cable_attach.restype  = ctypes.c_int
        tc.ticalcs_cable_attach.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        tc.ticalcs_cable_detach.restype  = ctypes.c_int
        tc.ticalcs_cable_detach.argtypes = [ctypes.c_void_p]
        tc.ticalcs_calc_isready.restype  = ctypes.c_int
        tc.ticalcs_calc_isready.argtypes = [ctypes.c_void_p]
        tc.ticalcs_calc_get_dirlist.restype  = ctypes.c_int
        tc.ticalcs_calc_get_dirlist.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        tc.ticalcs_dirlist_destroy.restype  = ctypes.c_int
        tc.ticalcs_dirlist_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        tc.ticalcs_dirlist_display.restype  = None
        tc.ticalcs_dirlist_display.argtypes = [ctypes.c_void_p]
        tc.ticalcs_calc_send_var_ns2.restype  = ctypes.c_int
        tc.ticalcs_calc_send_var_ns2.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p
        ]
        tc.ticalcs_calc_recv_var_ns2.restype  = ctypes.c_int
        tc.ticalcs_calc_recv_var_ns2.argtypes = [
            ctypes.c_void_p, ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(VarEntry),
        ]

        # eliminar variable
        tc.ticalcs_calc_del_var.restype  = ctypes.c_int
        tc.ticalcs_calc_del_var.argtypes = [ctypes.c_void_p, ctypes.POINTER(VarEntry)]

        # info del dispositivo
        tc.ticalcs_calc_get_version.restype  = ctypes.c_int
        tc.ticalcs_calc_get_version.argtypes = [ctypes.c_void_p,
                                                 ctypes.POINTER(CalcInfos)]
        tc.ticalcs_calc_get_memfree.restype  = ctypes.c_int
        tc.ticalcs_calc_get_memfree.argtypes = [ctypes.c_void_p,
                                                 ctypes.POINTER(ctypes.c_uint32),
                                                 ctypes.POINTER(ctypes.c_uint32)]

        # tifiles
        tf.tifiles_file_read_regular.restype  = ctypes.c_int
        tf.tifiles_file_read_regular.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)
        ]
        tf.tifiles_file_write_regular.restype  = ctypes.c_int
        tf.tifiles_file_write_regular.argtypes = [
            ctypes.c_char_p, ctypes.c_void_p
        ]
        tf.tifiles_content_delete_regular.restype  = ctypes.c_int
        tf.tifiles_content_delete_regular.argtypes = [ctypes.c_void_p]
        tf.tifiles_ve_create.restype  = ctypes.POINTER(VarEntry)
        tf.tifiles_ve_create.argtypes = []
        tf.tifiles_ve_free_data.restype  = None
        tf.tifiles_ve_free_data.argtypes = [ctypes.POINTER(VarEntry)]

    # ── Conexión / desconexión ────────────────────────────────────────────────

    @property
    def disponible(self) -> bool:
        return self._ticalcs is not None

    @property
    def conectado(self) -> bool:
        return self._conectado

    def conectar(self, pre_connect_cb=None) -> tuple[bool, str]:
        """
        Abre cable USB y verifica que la calculadora responda.
        pre_connect_cb: llamado justo antes de abrir el cable (para pausar
                        el MonitorUSB y liberar el handle pyusb).
        """
        if not self.disponible:
            return False, f"Librerías no disponibles: {self._error_init}"

        try:
            if pre_connect_cb:
                pre_connect_cb()

            # Secuencia correcta: ticables_handle_new → ticalcs_handle_new
            # → ticalcs_cable_attach (que abre el cable internamente)
            # NO llamar ticables_cable_open por separado — ticalcs_cable_attach lo hace.
            self._cable_h = self._ticables.ticables_handle_new(CABLE_USB, PORT_1)
            logger.info("ticables_handle_new → %s", self._cable_h)
            if not self._cable_h:
                return False, "No se pudo crear el handle del cable USB (handle NULL)"

            self._calc_h = self._ticalcs.ticalcs_handle_new(CALC_NSP)
            logger.info("ticalcs_handle_new → %s", self._calc_h)
            if not self._calc_h:
                self._ticables.ticables_handle_del(self._cable_h)
                self._cable_h = None
                return False, "No se pudo crear el handle de la calculadora"

            # ticalcs_cable_attach abre el cable USB internamente
            ret = self._ticalcs.ticalcs_cable_attach(self._calc_h, self._cable_h)
            logger.info("ticalcs_cable_attach → %d", ret)
            if ret != 0:
                self._ticalcs.ticalcs_handle_del(self._calc_h)
                self._ticables.ticables_handle_del(self._cable_h)
                self._calc_h = self._cable_h = None
                return False, f"No se pudo adjuntar el cable (código {ret})"

            ret = self._ticalcs.ticalcs_calc_isready(self._calc_h)
            logger.info("ticalcs_calc_isready → %d", ret)
            if ret != 0:
                self.desconectar()
                return False, "La calculadora no responde"

            self._conectado = True
            logger.info("Calculadora TI-Nspire conectada y lista")
            return True, "Calculadora conectada"

        except Exception as e:
            logger.error("Error al conectar: %s", e)
            self.desconectar()
            return False, str(e)

    def desconectar(self):
        # ticalcs_cable_detach cierra el cable internamente — no llamar ticables_cable_close
        if self._calc_h:
            try:
                self._ticalcs.ticalcs_cable_detach(self._calc_h)
            except Exception:
                pass
            try:
                self._ticalcs.ticalcs_handle_del(self._calc_h)
            except Exception:
                pass
            self._calc_h = None
        if self._cable_h:
            try:
                self._ticables.ticables_handle_del(self._cable_h)
            except Exception:
                pass
            self._cable_h = None
        self._conectado = False

    # ── Listado de archivos ───────────────────────────────────────────────────

    def listar_archivos(self) -> tuple[list[EntradaArchivo], str]:
        """Devuelve (lista, mensaje_error)."""
        if not self._conectado:
            return [], "No conectada"

        with self._lock:
            vars_ptr = ctypes.c_void_p(None)
            apps_ptr = ctypes.c_void_p(None)
            logger.info("ticalcs_calc_get_dirlist → iniciando...")
            ret = self._ticalcs.ticalcs_calc_get_dirlist(
                self._calc_h,
                ctypes.byref(vars_ptr),
                ctypes.byref(apps_ptr),
            )
            logger.info("ticalcs_calc_get_dirlist → %d", ret)
            if ret != 0:
                return [], f"Error al listar archivos (código {ret})"

            entradas: list[EntradaArchivo] = []
            try:
                if vars_ptr.value:
                    texto = self._capturar_dirlist(vars_ptr)
                    entradas = self._parsear_dirlist(texto)
            except Exception as e:
                logger.warning("Error al parsear dirlist: %s", e)

            if vars_ptr.value:
                self._ticalcs.ticalcs_dirlist_destroy(ctypes.byref(vars_ptr))
            if apps_ptr.value:
                self._ticalcs.ticalcs_dirlist_destroy(ctypes.byref(apps_ptr))

            return entradas, ""

    def _capturar_dirlist(self, gnode_ptr: ctypes.c_void_p) -> str:
        """Redirige stdout a un pipe, llama ticalcs_dirlist_display y devuelve el texto."""
        import sys, fcntl
        sys.stdout.flush()
        r_fd, w_fd = os.pipe()
        saved_fd1 = os.dup(1)
        try:
            os.dup2(w_fd, 1)
            os.close(w_fd)
            self._ticalcs.ticalcs_dirlist_display(gnode_ptr)
            # Forzar flush del buffer de C (fflush(NULL))
            ctypes.CDLL(None).fflush(None)
        finally:
            os.dup2(saved_fd1, 1)
            os.close(saved_fd1)
        # Leer todo lo que haya en el pipe (no-bloqueante)
        flags = fcntl.fcntl(r_fd, fcntl.F_GETFL)
        fcntl.fcntl(r_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        data = b""
        try:
            while True:
                chunk = os.read(r_fd, 4096)
                if not chunk:
                    break
                data += chunk
        except (BlockingIOError, OSError):
            pass
        os.close(r_fd)
        return data.decode("utf-8", errors="replace")

    def _parsear_dirlist(self, texto: str) -> list[EntradaArchivo]:
        """Parsea la tabla que imprime ticalcs_dirlist_display."""
        entradas: list[EntradaArchivo] = []
        carpetas_vistas: set[str] = set()
        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea.startswith('|'):
                continue
            partes = [p.strip() for p in linea.split('|')]
            # partes: ['', B_name, T_name, Attr, Type, Size, Folder, '']
            if len(partes) < 8:
                continue
            if 'B. name' in partes[1] or '---' in partes[1]:
                continue
            if 'No ' in partes[1]:   # "No variables" / "No applications"
                continue
            try:
                t_name = partes[2].strip()
                tipo   = int(partes[4].strip(), 16)   # 01=carpeta, 00=archivo
                size_h = partes[5].strip()
                tamanio = int(size_h, 16) if size_h else 0
                carpeta = partes[6].strip()
                if not t_name:
                    continue
                if tipo == 0x01:
                    if t_name not in carpetas_vistas:
                        carpetas_vistas.add(t_name)
                        entradas.append(EntradaArchivo(
                            carpeta="", nombre=t_name, tamanio=0, es_carpeta=True, tipo=tipo
                        ))
                else:
                    entradas.append(EntradaArchivo(
                        carpeta=carpeta, nombre=t_name, tamanio=tamanio, tipo=tipo
                    ))
            except (ValueError, IndexError):
                continue
        return entradas

    # ── Envío PC → Calculadora ────────────────────────────────────────────────

    def enviar_archivo(self, ruta_pc: str,
                       progreso_cb: Optional[Callable[[str], None]] = None
                       ) -> tuple[bool, str]:
        if not self._conectado:
            return False, "No conectada"

        def log(msg):
            logger.info(msg)
            if progreso_cb:
                progreso_cb(msg)

        try:
            content = ctypes.c_void_p(None)
            ret = self._tifiles.tifiles_file_read_regular(
                ruta_pc.encode(), ctypes.byref(content)
            )
            if ret != 0 or not content:
                return False, f"Error al leer archivo (código {ret})"

            log(f"Enviando {os.path.basename(ruta_pc)}...")
            with self._lock:
                ret = self._ticalcs.ticalcs_calc_send_var_ns2(
                    self._calc_h, MODE_NORMAL, content
                )
            self._tifiles.tifiles_content_delete_regular(content)

            if ret != 0:
                return False, f"Error al enviar (código {ret})"

            log(f"✓ {os.path.basename(ruta_pc)} enviado")
            return True, ""

        except Exception as e:
            return False, str(e)

    # ── Recepción Calculadora → PC ────────────────────────────────────────────

    def recibir_archivo(self, entrada: EntradaArchivo, directorio_pc: str,
                        progreso_cb: Optional[Callable[[str], None]] = None
                        ) -> tuple[bool, str]:
        if not self._conectado:
            return False, "No conectada"

        def log(msg):
            logger.info(msg)
            if progreso_cb:
                progreso_cb(msg)

        try:
            ve = VarEntry()
            ve.folder = entrada.carpeta.encode()[:40]
            ve.name   = entrada.nombre.encode()[:40]
            ve.type   = entrada.tipo   # necesario para que NSP sepa qué tipo de archivo pedir
            logger.info("recv_var_ns2 → folder=%r name=%r type=0x%02x",
                        entrada.carpeta, entrada.nombre, entrada.tipo)

            content = ctypes.c_void_p(None)
            log(f"Recibiendo {entrada.ruta_calc}...")
            with self._lock:
                ret = self._ticalcs.ticalcs_calc_recv_var_ns2(
                    self._calc_h, MODE_NORMAL,
                    ctypes.byref(content),
                    ctypes.byref(ve),
                )
            if ret != 0 or not content:
                return False, f"Error al recibir (código {ret})"

            nombre_pc = entrada.nombre
            if not nombre_pc.lower().endswith(".tns"):
                nombre_pc += ".tns"
            ruta_destino = os.path.join(directorio_pc, nombre_pc)

            ret = self._tifiles.tifiles_file_write_regular(
                ruta_destino.encode(), content
            )
            self._tifiles.tifiles_content_delete_regular(content)

            if ret != 0:
                return False, f"Error al escribir archivo (código {ret})"

            log(f"✓ {entrada.ruta_calc} → {ruta_destino}")
            return True, ruta_destino

        except Exception as e:
            return False, str(e)

    # ── Info del dispositivo ──────────────────────────────────────────────────

    def obtener_info_dispositivo(self) -> dict:
        """
        Consulta OS, batería y memoria libre vía ticalcs_calc_get_version
        y ticalcs_calc_get_memfree.
        Retorna dict con claves: os_version, boot_version, battery, charging,
        mem_free_ram, mem_free_flash.
        """
        resultado = {}
        if not self._conectado:
            return resultado

        with self._lock:
            # — Versión y batería —
            infos = CalcInfos()
            ret = self._ticalcs.ticalcs_calc_get_version(
                self._calc_h, ctypes.byref(infos)
            )
            if ret == 0:
                resultado["os_version"]   = infos.os_version.decode("ascii", errors="replace").strip("\x00") or "—"
                resultado["boot_version"] = infos.boot_version.decode("ascii", errors="replace").strip("\x00") or "—"
                resultado["battery"]      = int(infos.battery)
                resultado["charging"]     = bool(infos.charging)
            else:
                logger.warning("ticalcs_calc_get_version error %d", ret)

            # — Memoria libre —
            ram   = ctypes.c_uint32(0)
            flash = ctypes.c_uint32(0)
            ret2 = self._ticalcs.ticalcs_calc_get_memfree(
                self._calc_h, ctypes.byref(ram), ctypes.byref(flash)
            )
            if ret2 == 0:
                resultado["mem_free_ram"]   = int(ram.value)
                resultado["mem_free_flash"] = int(flash.value)
            else:
                logger.warning("ticalcs_calc_get_memfree error %d", ret2)

            return resultado

    # ── Eliminación de archivo en la calculadora ──────────────────────────────

    def eliminar_archivo(self, entrada: EntradaArchivo) -> tuple[bool, str]:
        if not self._conectado:
            return False, "No conectada"
        try:
            ve = VarEntry()
            ve.folder = entrada.carpeta.encode()[:40]
            ve.name   = entrada.nombre.encode()[:40]
            with self._lock:
                ret = self._ticalcs.ticalcs_calc_del_var(self._calc_h, ctypes.byref(ve))
            if ret != 0:
                return False, f"Error al eliminar (código {ret})"
            return True, ""
        except Exception as e:
            return False, str(e)

    def __del__(self):
        self.desconectar()
