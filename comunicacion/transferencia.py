# =============================================================================
# GESTOR DE TRANSFERENCIA DE ARCHIVOS — TI-Nspire CX CAS
# Usa libticalcs2 + libticables2 + libtifiles2 vía ctypes
#
# Los layouts de VarEntry/CalcInfos y las firmas de las funciones están
# verificados contra libticalcs 1.19 / libtifiles 1.19 (Fedora):
#   - sizeof(VarEntry)  = 2072  (folder[1024], name[1024], ...)
#   - sizeof(CalcInfos) =  344  (model, mask, ..., os_version en offset 210)
#   - la Nspire NO soporta FTS_NONSILENT → hay que usar send_var/recv_var
#     (silenciosas), NO las variantes *_ns / *_ns2.
# =============================================================================
from __future__ import annotations

import ctypes
import logging
import os
import struct
import tempfile
import threading
import zlib
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger("ti_nspire.transferencia")

# ── Constantes de protocolo ───────────────────────────────────────────────────
CALC_NSPIRE = 15   # CalcModel: tifiles_model_to_string(15) == "Nspire"
CALC_NSP    = CALC_NSPIRE   # alias histórico
CABLE_USB   = 5    # DirectLink USB
PORT_1      = 1
MODE_NORMAL = 0

# tifiles.h
FLDNAME_MAX = 1024
VARNAME_MAX = 1024

# ticalcs.h — CalcFeatures (bitmask devuelto por ticalcs_calc_features)
OPS_ISREADY   = 1 << 0
OPS_SCREEN    = 1 << 2
OPS_DIRLIST   = 1 << 3
OPS_VARS      = 1 << 5
OPS_VERSION   = 1 << 10
OPS_NEWFLD    = 1 << 11
OPS_DELVAR    = 1 << 12
OPS_OS        = 1 << 13
OPS_RENAME    = 1 << 14
FTS_SILENT    = 1 << 15
FTS_FOLDER    = 1 << 16
FTS_MEMFREE   = 1 << 17
FTS_NONSILENT = 1 << 22

# Extensiones de imagen de OS de la familia Nspire. libtifiles solo tiene un
# CalcModel para toda la familia (15 = "Nspire"), así que no puede distinguir
# una imagen CAS de una no-CAS: eso hay que deducirlo de la extensión.
EXT_OS_NSPIRE = {
    ".tno": ("Nspire",     False),   # (familia, ¿es CAS?)
    ".tnc": ("Nspire",     True),
    ".tco": ("Nspire CX",  False),
    ".tcc": ("Nspire CX",  True),
}

# ticalcs.h — CalcScreenFormat / CalcPixelFormat
SCREEN_FULL    = 0
SCREEN_CLIPPED = 1
CALC_PIXFMT_MONO       = 1
CALC_PIXFMT_GRAY_4     = 2
CALC_PIXFMT_RGB_565_LE = 3

# ticalcs.h — InfosMask (qué campos de CalcInfos rellenó get_version)
INFOS_PRODUCT_NAME   = 1 << 1
INFOS_HW_VERSION     = 1 << 3
INFOS_BOOT_VERSION   = 1 << 7
INFOS_OS_VERSION     = 1 << 8
INFOS_RAM_PHYS       = 1 << 9
INFOS_RAM_FREE       = 1 << 11
INFOS_FLASH_PHYS     = 1 << 12
INFOS_FLASH_FREE     = 1 << 14
INFOS_BATTERY        = 1 << 17
INFOS_BOOT2_VERSION  = 1 << 18
INFOS_PRODUCT_ID     = 1 << 22
INFOS_PYTHON_ON_BOARD = 1 << 26


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
    tifiles.h — VarEntry (== VarRequest, es un alias).
    Layout confirmado sobre la librería instalada:
      malloc_usable_size(tifiles_ve_create()) == 2072
      campo 'data' en offset 2056
    """
    _fields_ = [
        ('folder',  ctypes.c_char * FLDNAME_MAX),   # off 0
        ('name',    ctypes.c_char * VARNAME_MAX),   # off 1024
        ('type',    ctypes.c_uint8),                # off 2048
        ('attr',    ctypes.c_uint8),                # off 2049
        ('version', ctypes.c_uint8),                # off 2050
        ('size',    ctypes.c_uint32),               # off 2052
        ('data',    ctypes.POINTER(ctypes.c_uint8)),# off 2056
        ('action',  ctypes.c_int),                  # off 2064
    ]

VarRequest = VarEntry
SIZEOF_VARENTRY_ESPERADO = 2072


class CalcInfos(ctypes.Structure):
    """
    ticalcs.h — CalcInfos. `mask` indica qué campos son válidos tras
    ticalcs_calc_get_version. Se añade relleno final por si una versión
    posterior de la librería crece: así nunca escribe fuera del buffer.
    """
    _fields_ = [
        ('model',           ctypes.c_int),          # off   0  (CalcModel)
        ('mask',            ctypes.c_uint32),       # off   4  (InfosMask)
        ('product_name',    ctypes.c_char * 64),    # off   8
        ('product_id',      ctypes.c_char * 32),    # off  72
        ('product_number',  ctypes.c_uint32),       # off 104
        ('main_calc_id',    ctypes.c_char * 32),    # off 108
        ('hw_version',      ctypes.c_uint16),       # off 140
        ('language_id',     ctypes.c_uint8),        # off 142
        ('sub_lang_id',     ctypes.c_uint8),        # off 143
        ('device_type',     ctypes.c_uint16),       # off 144
        ('boot_version',    ctypes.c_char * 32),    # off 146
        ('boot2_version',   ctypes.c_char * 32),    # off 178
        ('os_version',      ctypes.c_char * 32),    # off 210
        ('ram_phys',        ctypes.c_uint64),       # off 248
        ('ram_user',        ctypes.c_uint64),
        ('ram_free',        ctypes.c_uint64),
        ('flash_phys',      ctypes.c_uint64),
        ('flash_user',      ctypes.c_uint64),
        ('flash_free',      ctypes.c_uint64),       # off 288
        ('lcd_width',       ctypes.c_uint16),       # off 296
        ('lcd_height',      ctypes.c_uint16),
        ('battery',         ctypes.c_uint8),        # off 300 — flag, NO porcentaje
        ('run_level',       ctypes.c_uint8),
        ('bits_per_pixel',  ctypes.c_uint16),
        ('clock_speed',     ctypes.c_uint16),
        ('exact_math',      ctypes.c_uint8),
        ('clock_support',   ctypes.c_uint8),
        ('color_screen',    ctypes.c_uint8),
        ('python_on_board', ctypes.c_uint8),
        ('user_defined_id', ctypes.c_char * 32),    # off 310, fin en 342
        ('_pad_compat',     ctypes.c_uint8 * 256),  # margen de seguridad
    ]

SIZEOF_CALCINFOS_ESPERADO = 344   # sin el relleno _pad_compat


def _verificar_layouts():
    """Avisa en el log si el ABI de la librería no coincide con lo asumido."""
    real_ve = ctypes.sizeof(VarEntry)
    if real_ve != SIZEOF_VARENTRY_ESPERADO:
        logger.error("sizeof(VarEntry)=%d, se esperaba %d — ABI distinto",
                     real_ve, SIZEOF_VARENTRY_ESPERADO)
    off_data = VarEntry.data.offset
    if off_data != 2056:
        logger.error("VarEntry.data en offset %d, se esperaba 2056", off_data)
    off_os = CalcInfos.os_version.offset
    if off_os != 210:
        logger.error("CalcInfos.os_version en offset %d, se esperaba 210", off_os)

_verificar_layouts()


class CalcUpdate(ctypes.Structure):
    """
    ticalcs.h — canal de progreso. Se registra con ticalcs_update_set y la
    librería lo va rellenando y llama a los punteros a función durante las
    operaciones largas (envío de OS, transferencias grandes).
    Lleva relleno al final por si una versión posterior de la librería crece.
    """
    _fields_ = [
        ('text',    ctypes.c_char * 256),
        ('cancel',  ctypes.c_int),
        ('rate',    ctypes.c_float),
        ('cnt1',    ctypes.c_int), ('max1', ctypes.c_int),
        ('cnt2',    ctypes.c_int), ('max2', ctypes.c_int),
        ('cnt3',    ctypes.c_int), ('max3', ctypes.c_int),
        ('mask',    ctypes.c_int),
        ('type',    ctypes.c_int),
        ('start',   ctypes.CFUNCTYPE(None)),
        ('stop',    ctypes.CFUNCTYPE(None)),
        ('refresh', ctypes.CFUNCTYPE(None)),
        ('pbar',    ctypes.CFUNCTYPE(None)),
        ('label',   ctypes.CFUNCTYPE(None)),
        ('_pad_compat', ctypes.c_uint8 * 256),
    ]

_CB_VOID = ctypes.CFUNCTYPE(None)


class CalcScreenCoord(ctypes.Structure):
    """ticalcs.h — dimensiones y formato de la captura de pantalla."""
    _fields_ = [
        ('format',         ctypes.c_int),    # SCREEN_FULL / SCREEN_CLIPPED
        ('width',          ctypes.c_uint),
        ('height',         ctypes.c_uint),
        ('clipped_width',  ctypes.c_uint),
        ('clipped_height', ctypes.c_uint),
        ('pixel_format',   ctypes.c_int),    # CalcPixelFormat
    ]


@dataclass
class Captura:
    """Captura de pantalla ya convertida a RGB888 (3 bytes por píxel)."""
    ancho: int
    alto: int
    rgb888: bytes

    def guardar_png(self, ruta: str) -> str:
        guardar_png(ruta, self.ancho, self.alto, self.rgb888)
        return ruta


def guardar_png(ruta: str, ancho: int, alto: int, rgb888: bytes) -> None:
    """
    Escribe un PNG RGB de 8 bits sin dependencias externas (solo zlib).
    Se hace aquí y no con Qt para que el backend no dependa de la GUI.
    """
    paso = ancho * 3
    filas = bytearray()
    for y in range(alto):
        filas.append(0)                      # filtro "None" por fila
        filas += rgb888[y * paso:(y + 1) * paso]

    def _chunk(tipo: bytes, datos: bytes) -> bytes:
        return (struct.pack(">I", len(datos)) + tipo + datos
                + struct.pack(">I", zlib.crc32(tipo + datos) & 0xffffffff))

    with open(ruta, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)))
        f.write(_chunk(b"IDAT", zlib.compress(bytes(filas), 9)))
        f.write(_chunk(b"IEND", b""))


@dataclass
class EntradaArchivo:
    carpeta: str
    nombre: str
    tamanio: int        # bytes
    es_carpeta: bool = False
    tipo: int = 0       # tipo de variable (0x01 para carpeta en el dirlist)

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
        self._glib     = None
        self._error_init: str = ""
        self._features: int = 0
        # El canal de progreso y sus callbacks tienen que seguir vivos mientras
        # el handle los use: si Python los recolecta, la librería salta a
        # memoria liberada. Por eso se guardan como atributos.
        self._update: Optional[CalcUpdate] = None
        self._update_cbs: list = []
        self._progreso_cb: Optional[Callable[[str, float], None]] = None
        self._cancelar_op = False
        self._lock = threading.RLock()  # serializa TODAS las llamadas USB y la desconexión
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
            return
        # glib solo para liberar el char* que devuelve tifiles_file_write_regular
        try:
            self._glib = ctypes.cdll.LoadLibrary("libglib-2.0.so.0")
            self._glib.g_free.restype  = None
            self._glib.g_free.argtypes = [ctypes.c_void_p]
        except Exception:
            self._glib = None   # sin glib solo se filtran unos bytes por transferencia

    def _configurar_prototipos(self):
        tc = self._ticalcs
        tb = self._ticables
        tf = self._tifiles

        # ── ticables ──
        tb.ticables_handle_new.restype  = ctypes.c_void_p
        tb.ticables_handle_new.argtypes = [ctypes.c_int, ctypes.c_int]
        tb.ticables_handle_del.restype  = ctypes.c_int
        tb.ticables_handle_del.argtypes = [ctypes.c_void_p]
        # NOTA: ticables_cable_open/close NO se declaran a propósito —
        # ticalcs_cable_attach/detach ya los llaman internamente. Abrir el
        # cable por separado reclama la interfaz dos veces y da EBUSY.

        # ── ticalcs: sesión ──
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
        tc.ticalcs_calc_features.restype  = ctypes.c_int
        tc.ticalcs_calc_features.argtypes = [ctypes.c_void_p]
        tc.ticalcs_error_get.restype  = ctypes.c_int
        tc.ticalcs_error_get.argtypes = [ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_char_p)]
        tb.ticables_error_get.restype  = ctypes.c_int
        tb.ticables_error_get.argtypes = [ctypes.c_int,
                                           ctypes.POINTER(ctypes.c_char_p)]
        tf.tifiles_error_get.restype  = ctypes.c_int
        tf.tifiles_error_get.argtypes = [ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_char_p)]

        # ── ticalcs: listado ──
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

        # ── ticalcs: variables (variantes SILENCIOSAS — las que soporta la Nspire) ──
        #   int ticalcs_calc_send_var(CalcHandle*, CalcMode, FileContent*);
        #   int ticalcs_calc_recv_var(CalcHandle*, CalcMode, FileContent*, VarRequest*);
        tc.ticalcs_calc_send_var.restype  = ctypes.c_int
        tc.ticalcs_calc_send_var.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p
        ]
        tc.ticalcs_calc_recv_var.restype  = ctypes.c_int
        tc.ticalcs_calc_recv_var.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
            ctypes.POINTER(VarEntry),
        ]
        tc.ticalcs_calc_del_var.restype  = ctypes.c_int
        tc.ticalcs_calc_del_var.argtypes = [ctypes.c_void_p,
                                             ctypes.POINTER(VarEntry)]

        # ── ticalcs: captura de pantalla y carpetas ──
        #   int ticalcs_calc_recv_screen_rgb888(CalcHandle*, CalcScreenCoord*, uint8_t**);
        #   void ticalcs_free_screen(uint8_t*);
        #   int ticalcs_calc_new_fld(CalcHandle*, VarRequest*);
        tc.ticalcs_calc_recv_screen_rgb888.restype  = ctypes.c_int
        tc.ticalcs_calc_recv_screen_rgb888.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(CalcScreenCoord),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
        ]
        tc.ticalcs_free_screen.restype  = None
        tc.ticalcs_free_screen.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        tc.ticalcs_calc_new_fld.restype  = ctypes.c_int
        tc.ticalcs_calc_new_fld.argtypes = [ctypes.c_void_p,
                                             ctypes.POINTER(VarEntry)]

        # ── ticalcs: renombrar y actualizar el OS ──
        #   int ticalcs_calc_rename_var(CalcHandle*, VarRequest* orig, VarRequest* nuevo);
        #   int ticalcs_calc_send_os2(CalcHandle*, const char* fichero);
        #   int ticalcs_update_set(CalcHandle*, CalcUpdate*);
        tc.ticalcs_calc_rename_var.restype  = ctypes.c_int
        tc.ticalcs_calc_rename_var.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(VarEntry), ctypes.POINTER(VarEntry)
        ]
        tc.ticalcs_calc_send_os2.restype  = ctypes.c_int
        tc.ticalcs_calc_send_os2.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        tc.ticalcs_update_set.restype  = ctypes.c_int
        tc.ticalcs_update_set.argtypes = [ctypes.c_void_p,
                                           ctypes.POINTER(CalcUpdate)]

        # ── tifiles: validación de archivos de sistema operativo ──
        for _f in ("tifiles_file_is_ti", "tifiles_file_is_os",
                   "tifiles_file_is_tno", "tifiles_file_is_regular"):
            getattr(tf, _f).restype  = ctypes.c_int
            getattr(tf, _f).argtypes = [ctypes.c_char_p]
        tf.tifiles_file_get_model.restype  = ctypes.c_int
        tf.tifiles_file_get_model.argtypes = [ctypes.c_char_p]
        tf.tifiles_model_to_string.restype  = ctypes.c_char_p
        tf.tifiles_model_to_string.argtypes = [ctypes.c_int]

        # ── ticalcs: info del dispositivo ──
        tc.ticalcs_calc_get_version.restype  = ctypes.c_int
        tc.ticalcs_calc_get_version.argtypes = [ctypes.c_void_p,
                                                 ctypes.POINTER(CalcInfos)]
        tc.ticalcs_calc_get_memfree.restype  = ctypes.c_int
        tc.ticalcs_calc_get_memfree.argtypes = [ctypes.c_void_p,
                                                 ctypes.POINTER(ctypes.c_uint32),
                                                 ctypes.POINTER(ctypes.c_uint32)]

        # ── tifiles ──
        #   FileContent* tifiles_content_create_regular(CalcModel);
        #   int tifiles_file_read_regular(const char*, FileContent*);
        #   int tifiles_file_write_regular(const char*, FileContent*, char**);
        tf.tifiles_content_create_regular.restype  = ctypes.c_void_p
        tf.tifiles_content_create_regular.argtypes = [ctypes.c_int]
        tf.tifiles_content_delete_regular.restype  = ctypes.c_int
        tf.tifiles_content_delete_regular.argtypes = [ctypes.c_void_p]
        tf.tifiles_file_read_regular.restype  = ctypes.c_int
        tf.tifiles_file_read_regular.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
        tf.tifiles_file_write_regular.restype  = ctypes.c_int
        tf.tifiles_file_write_regular.argtypes = [
            ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)
        ]

    # ── Utilidades de error ───────────────────────────────────────────────────

    def _msg_error(self, codigo: int) -> str:
        """
        Traduce un código de error a texto legible, en una sola línea.
        Los códigos >= 256 son de ticalcs; los más bajos vienen de
        ticables/tifiles, así que se prueban las tres librerías.
        """
        if codigo == 0:
            return ""
        for lib, fn in (
            (self._ticalcs,  "ticalcs_error_get"),
            (self._ticables, "ticables_error_get"),
            (self._tifiles,  "tifiles_error_get"),
        ):
            if lib is None:
                continue
            try:
                buf = ctypes.c_char_p(None)
                if getattr(lib, fn)(codigo, ctypes.byref(buf)) == 0 and buf.value:
                    texto = buf.value.decode("utf-8", errors="replace")
                    if self._glib:
                        self._glib.g_free(buf)
                    # el mensaje trae saltos de línea y un prefijo "Msg: "
                    texto = " ".join(texto.split()).removeprefix("Msg: ").strip()
                    return f"{texto} (código {codigo})"
            except Exception:
                continue
        return f"código {codigo}"

    # ── Conexión / desconexión ────────────────────────────────────────────────

    @property
    def disponible(self) -> bool:
        return self._ticalcs is not None

    @property
    def conectado(self) -> bool:
        return self._conectado

    @property
    def features(self) -> int:
        return self._features

    def soporta(self, bit: int) -> bool:
        return bool(self._features & bit)

    def conectar(self, pre_connect_cb=None) -> tuple[bool, str]:
        """
        Abre cable USB y verifica que la calculadora responda.
        pre_connect_cb: llamado justo antes de abrir el cable (para pausar
                        el MonitorUSB y liberar el handle pyusb).
        """
        if not self.disponible:
            return False, f"Librerías no disponibles: {self._error_init}"

        with self._lock:
            try:
                if pre_connect_cb:
                    pre_connect_cb()

                # Secuencia correcta: ticables_handle_new → ticalcs_handle_new
                # → ticalcs_cable_attach (que abre el cable internamente).
                # NO llamar ticables_cable_open por separado.
                self._cable_h = self._ticables.ticables_handle_new(CABLE_USB, PORT_1)
                logger.info("ticables_handle_new → %s", self._cable_h)
                if not self._cable_h:
                    return False, "No se pudo crear el handle del cable USB (handle NULL)"

                self._calc_h = self._ticalcs.ticalcs_handle_new(CALC_NSPIRE)
                logger.info("ticalcs_handle_new → %s", self._calc_h)
                if not self._calc_h:
                    self._ticables.ticables_handle_del(self._cable_h)
                    self._cable_h = None
                    return False, "No se pudo crear el handle de la calculadora"

                self._features = self._ticalcs.ticalcs_calc_features(self._calc_h)
                logger.info("ticalcs_calc_features → 0x%08x (silent=%s, folder=%s, "
                            "vars=%s, delvar=%s, version=%s, memfree=%s)",
                            self._features & 0xffffffff,
                            self.soporta(FTS_SILENT), self.soporta(FTS_FOLDER),
                            self.soporta(OPS_VARS), self.soporta(OPS_DELVAR),
                            self.soporta(OPS_VERSION), self.soporta(FTS_MEMFREE))

                self._instalar_progreso()

                ret = self._ticalcs.ticalcs_cable_attach(self._calc_h, self._cable_h)
                logger.info("ticalcs_cable_attach → %d", ret)
                if ret != 0:
                    self._ticalcs.ticalcs_handle_del(self._calc_h)
                    self._ticables.ticables_handle_del(self._cable_h)
                    self._calc_h = self._cable_h = None
                    return False, f"No se pudo adjuntar el cable ({self._msg_error(ret)})"

                ret = self._ticalcs.ticalcs_calc_isready(self._calc_h)
                logger.info("ticalcs_calc_isready → %d", ret)
                if ret != 0:
                    self._desconectar_sin_lock()
                    return False, "La calculadora no responde"

                self._conectado = True
                logger.info("Calculadora TI-Nspire conectada y lista")
                return True, "Calculadora conectada"

            except Exception as e:
                logger.error("Error al conectar: %s", e)
                self._desconectar_sin_lock()
                return False, str(e)

    def desconectar(self):
        """
        Cierra la sesión. Toma el lock para no liberar los handles mientras
        otro hilo está dentro de una llamada USB (use-after-free).
        """
        with self._lock:
            self._desconectar_sin_lock()

    def _desconectar_sin_lock(self):
        # ticalcs_cable_detach cierra el cable internamente
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
        self._features = 0
        self._update = None
        self._update_cbs = []
        self._progreso_cb = None
        self._cancelar_op = False

    # ── Listado de archivos ───────────────────────────────────────────────────

    def listar_archivos(self) -> tuple[list[EntradaArchivo], str]:
        """Devuelve (lista, mensaje_error)."""
        with self._lock:
            if not self._conectado:
                return [], "No conectada"

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
                return [], f"Error al listar archivos ({self._msg_error(ret)})"

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
        """
        Redirige el fd 1 a un archivo temporal, llama ticalcs_dirlist_display
        y devuelve el texto. Se usa un archivo y no un pipe: un pipe se llena
        a los 64 KB y bloquearía a la librería para siempre con muchos archivos.
        """
        import sys
        sys.stdout.flush()
        fd, ruta = tempfile.mkstemp(prefix="ti_dirlist_", suffix=".txt")
        saved_fd1 = os.dup(1)
        try:
            os.dup2(fd, 1)
            os.close(fd)
            self._ticalcs.ticalcs_dirlist_display(gnode_ptr)
            ctypes.CDLL(None).fflush(None)   # fflush(NULL) — vacía el buffer de C
        finally:
            os.dup2(saved_fd1, 1)
            os.close(saved_fd1)
        try:
            with open(ruta, "rb") as f:
                data = f.read()
        finally:
            try:
                os.unlink(ruta)
            except OSError:
                pass
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
                            carpeta="", nombre=t_name, tamanio=0,
                            es_carpeta=True, tipo=tipo
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
        """
        Lee el archivo con tifiles y lo envía con ticalcs_calc_send_var
        (transferencia silenciosa — la Nspire no soporta las variantes _ns).
        """
        def log(msg):
            logger.info(msg)
            if progreso_cb:
                progreso_cb(msg)

        with self._lock:
            if not self._conectado:
                return False, "No conectada"

            content = None
            try:
                # tifiles_file_read_regular espera un FileContent YA asignado
                content = self._tifiles.tifiles_content_create_regular(CALC_NSPIRE)
                if not content:
                    return False, "No se pudo asignar el FileContent"

                ret = self._tifiles.tifiles_file_read_regular(
                    ruta_pc.encode("utf-8"), content
                )
                if ret != 0:
                    return False, f"Error al leer el archivo (código {ret})"

                log(f"Enviando {os.path.basename(ruta_pc)}...")
                ret = self._ticalcs.ticalcs_calc_send_var(
                    self._calc_h, MODE_NORMAL, content
                )
                if ret != 0:
                    return False, f"Error al enviar ({self._msg_error(ret)})"

                log(f"✓ {os.path.basename(ruta_pc)} enviado")
                return True, ""

            except Exception as e:
                logger.exception("Error en enviar_archivo")
                return False, str(e)
            finally:
                if content:
                    try:
                        self._tifiles.tifiles_content_delete_regular(content)
                    except Exception:
                        pass

    # ── Recepción Calculadora → PC ────────────────────────────────────────────

    def recibir_archivo(self, entrada: EntradaArchivo, directorio_pc: str,
                        progreso_cb: Optional[Callable[[str], None]] = None
                        ) -> tuple[bool, str]:
        """
        Pide el archivo con ticalcs_calc_recv_var(handle, mode, content, request)
        y lo escribe con tifiles_file_write_regular (3 parámetros).
        """
        def log(msg):
            logger.info(msg)
            if progreso_cb:
                progreso_cb(msg)

        with self._lock:
            if not self._conectado:
                return False, "No conectada"
            if entrada.es_carpeta:
                return False, "No se puede recibir una carpeta"

            content = None
            try:
                ve = VarEntry()
                ve.folder = entrada.carpeta.encode("utf-8")[:FLDNAME_MAX - 1]
                ve.name   = entrada.nombre.encode("utf-8")[:VARNAME_MAX - 1]
                ve.type   = entrada.tipo
                ve.attr   = 0
                logger.info("recv_var → folder=%r name=%r type=0x%02x",
                            entrada.carpeta, entrada.nombre, entrada.tipo)

                content = self._tifiles.tifiles_content_create_regular(CALC_NSPIRE)
                if not content:
                    return False, "No se pudo asignar el FileContent"

                log(f"Recibiendo {entrada.ruta_calc}...")
                ret = self._ticalcs.ticalcs_calc_recv_var(
                    self._calc_h, MODE_NORMAL, content, ctypes.byref(ve)
                )
                if ret != 0:
                    return False, f"Error al recibir ({self._msg_error(ret)})"

                nombre_pc = entrada.nombre
                if not os.path.splitext(nombre_pc)[1]:
                    nombre_pc += ".tns"
                ruta_destino = os.path.join(directorio_pc, nombre_pc)

                # El 3er parámetro es de salida: la ruta real que escribió
                # tifiles (puede corregir la extensión). Hay que pasarlo:
                # omitirlo dejaba basura en RDX y la librería escribía ahí.
                real = ctypes.c_char_p(None)
                ret = self._tifiles.tifiles_file_write_regular(
                    ruta_destino.encode("utf-8"), content, ctypes.byref(real)
                )
                if ret != 0:
                    return False, f"Error al escribir el archivo (código {ret})"
                if real.value:
                    ruta_destino = real.value.decode("utf-8", errors="replace")
                    if self._glib:
                        self._glib.g_free(real)

                log(f"✓ {entrada.ruta_calc} → {ruta_destino}")
                return True, ruta_destino

            except Exception as e:
                logger.exception("Error en recibir_archivo")
                return False, str(e)
            finally:
                if content:
                    try:
                        self._tifiles.tifiles_content_delete_regular(content)
                    except Exception:
                        pass

    # ── Info del dispositivo ──────────────────────────────────────────────────

    def obtener_info_dispositivo(self) -> dict:
        """
        Consulta OS, batería y memoria libre.
        Solo devuelve las claves que la máscara de CalcInfos marca como válidas.
        Ojo: `battery` es un FLAG (batería suficiente sí/no), no un porcentaje.
        """
        resultado: dict = {}
        with self._lock:
            if not self._conectado:
                return resultado

            # — Versión, modelo y batería —
            infos = CalcInfos()
            ret = self._ticalcs.ticalcs_calc_get_version(
                self._calc_h, ctypes.byref(infos)
            )
            if ret == 0:
                mask = infos.mask

                def _txt(campo: str) -> str:
                    return getattr(infos, campo).decode("utf-8", errors="replace").strip()

                if mask & INFOS_OS_VERSION:
                    resultado["os_version"] = _txt("os_version")
                if mask & INFOS_BOOT_VERSION:
                    resultado["boot_version"] = _txt("boot_version")
                if mask & INFOS_BOOT2_VERSION:
                    resultado["boot2_version"] = _txt("boot2_version")
                if mask & INFOS_PRODUCT_NAME:
                    resultado["product_name"] = _txt("product_name")
                if mask & INFOS_PRODUCT_ID:
                    resultado["product_id"] = _txt("product_id")
                if mask & INFOS_HW_VERSION:
                    resultado["hw_version"] = int(infos.hw_version)
                if mask & INFOS_BATTERY:
                    resultado["bateria_ok"] = bool(infos.battery)
                if mask & INFOS_PYTHON_ON_BOARD:
                    resultado["python_on_board"] = bool(infos.python_on_board)
                if mask & INFOS_RAM_PHYS:
                    resultado["ram_total"] = int(infos.ram_phys)
                if mask & INFOS_RAM_FREE:
                    resultado["mem_free_ram"] = int(infos.ram_free)
                if mask & INFOS_FLASH_PHYS:
                    resultado["flash_total"] = int(infos.flash_phys)
                if mask & INFOS_FLASH_FREE:
                    resultado["mem_free_flash"] = int(infos.flash_free)
                logger.info("get_version OK — mask=0x%08x → %s", mask, resultado)
            else:
                logger.warning("ticalcs_calc_get_version → %s", self._msg_error(ret))

            # — Memoria libre (si get_version no la trajo) —
            if "mem_free_ram" not in resultado and self.soporta(FTS_MEMFREE):
                ram   = ctypes.c_uint32(0)
                flash = ctypes.c_uint32(0)
                ret2 = self._ticalcs.ticalcs_calc_get_memfree(
                    self._calc_h, ctypes.byref(ram), ctypes.byref(flash)
                )
                if ret2 == 0:
                    resultado["mem_free_ram"]   = int(ram.value)
                    resultado["mem_free_flash"] = int(flash.value)
                else:
                    logger.warning("ticalcs_calc_get_memfree → %s", self._msg_error(ret2))

            return resultado

    # ── Eliminación de archivo en la calculadora ──────────────────────────────

    def eliminar_archivo(self, entrada: EntradaArchivo) -> tuple[bool, str]:
        with self._lock:
            if not self._conectado:
                return False, "No conectada"
            if entrada.es_carpeta:
                return False, "No se puede eliminar una carpeta desde aquí"
            try:
                ve = VarEntry()
                ve.folder = entrada.carpeta.encode("utf-8")[:FLDNAME_MAX - 1]
                ve.name   = entrada.nombre.encode("utf-8")[:VARNAME_MAX - 1]
                ve.type   = entrada.tipo
                ve.attr   = 0
                logger.info("del_var → folder=%r name=%r type=0x%02x",
                            entrada.carpeta, entrada.nombre, entrada.tipo)
                ret = self._ticalcs.ticalcs_calc_del_var(
                    self._calc_h, ctypes.byref(ve)
                )
                if ret != 0:
                    return False, f"Error al eliminar ({self._msg_error(ret)})"
                return True, ""
            except Exception as e:
                logger.exception("Error en eliminar_archivo")
                return False, str(e)

    # ── Canal de progreso ─────────────────────────────────────────────────────

    def _instalar_progreso(self):
        """
        Registra un CalcUpdate en el handle. La librería lo rellena y llama a
        los callbacks durante las operaciones largas (sobre todo el flasheo
        del OS, que tarda minutos).
        """
        upd = CalcUpdate()
        upd.cancel = 0
        ultimo = [-1.0, ""]

        def _emitir():
            # Se invoca desde C: una excepción aquí volvería al llamador
            # nativo, así que nunca puede propagarse.
            try:
                cb = self._progreso_cb
                if cb is None:
                    return
                texto = upd.text.decode("utf-8", errors="replace").strip()
                m1 = int(upd.max1)
                pct = (int(upd.cnt1) * 100.0 / m1) if m1 > 0 else -1.0
                # se filtra el ruido: solo cambios de 1 % o de texto
                if texto == ultimo[1] and abs(pct - ultimo[0]) < 1.0:
                    return
                ultimo[0], ultimo[1] = pct, texto
                cb(texto, pct)
            except Exception:
                pass

        def _nada():
            pass

        cbs = [_CB_VOID(_nada), _CB_VOID(_nada), _CB_VOID(_emitir),
               _CB_VOID(_emitir), _CB_VOID(_emitir)]
        upd.start, upd.stop, upd.refresh, upd.pbar, upd.label = cbs
        self._update = upd
        self._update_cbs = cbs      # mantener vivas las trampolines de ctypes
        ret = self._ticalcs.ticalcs_update_set(self._calc_h, ctypes.byref(upd))
        logger.info("ticalcs_update_set → %d", ret)

    def cancelar_operacion(self):
        """Pide a la librería que aborte la operación larga en curso."""
        if self._update is not None:
            self._update.cancel = 1
            logger.info("cancelación solicitada")

    # ── Renombrar en la calculadora ───────────────────────────────────────────

    def renombrar(self, entrada: EntradaArchivo,
                  nuevo_nombre: str) -> tuple[bool, str]:
        """Renombra un archivo dejándolo en la misma carpeta."""
        nuevo_nombre = nuevo_nombre.strip()
        with self._lock:
            if not self._conectado:
                return False, "No conectada"
            if not self.soporta(OPS_RENAME):
                return False, "Este modelo no soporta renombrar"
            if entrada.es_carpeta:
                return False, "Renombrar carpetas no está soportado"
            if not nuevo_nombre:
                return False, "El nombre no puede estar vacío"
            if any(c in nuevo_nombre for c in '/\\:*?"<>|'):
                return False, "El nombre tiene caracteres no permitidos"
            if nuevo_nombre == entrada.nombre:
                return False, "Es el mismo nombre"
            try:
                orig = VarEntry()
                orig.folder = entrada.carpeta.encode("utf-8")[:FLDNAME_MAX - 1]
                orig.name   = entrada.nombre.encode("utf-8")[:VARNAME_MAX - 1]
                orig.type   = entrada.tipo

                dest = VarEntry()
                dest.folder = entrada.carpeta.encode("utf-8")[:FLDNAME_MAX - 1]
                dest.name   = nuevo_nombre.encode("utf-8")[:VARNAME_MAX - 1]
                dest.type   = entrada.tipo

                logger.info("rename_var → %r/%r → %r/%r",
                            entrada.carpeta, entrada.nombre,
                            entrada.carpeta, nuevo_nombre)
                ret = self._ticalcs.ticalcs_calc_rename_var(
                    self._calc_h, ctypes.byref(orig), ctypes.byref(dest)
                )
                if ret != 0:
                    return False, f"Error al renombrar ({self._msg_error(ret)})"
                return True, ""
            except Exception as e:
                logger.exception("Error en renombrar")
                return False, str(e)

    # ── Actualización del sistema operativo ───────────────────────────────────

    def validar_archivo_os(self, ruta: str) -> tuple[bool, str]:
        """
        Comprueba, SIN tocar la calculadora, que el archivo es una imagen de
        sistema operativo válida para este modelo. Se llama antes de flashear.
        """
        if not os.path.isfile(ruta):
            return False, "El archivo no existe"
        p = ruta.encode("utf-8")
        try:
            if not self._tifiles.tifiles_file_is_ti(p):
                return False, "No es un archivo de Texas Instruments"
            es_os  = bool(self._tifiles.tifiles_file_is_os(p))
            es_tno = bool(self._tifiles.tifiles_file_is_tno(p))
            if not (es_os or es_tno):
                return False, ("No es una imagen de sistema operativo "
                               "(parece un documento o una aplicación)")
            modelo = self._tifiles.tifiles_file_get_model(p)
            nombre = self._tifiles.tifiles_model_to_string(modelo)
            nombre = nombre.decode() if nombre else str(modelo)
            if modelo != CALC_NSPIRE:
                return False, (f"La imagen es para {nombre}, no para Nspire "
                               f"— NO la envíes")
            return True, f"Imagen de OS válida para {nombre}"
        except Exception as e:
            return False, f"No se pudo validar: {e}"

    def actualizar_os(self, ruta_os: str,
                      progreso_cb: Optional[Callable[[str, float], None]] = None
                      ) -> tuple[bool, str]:
        """
        Envía una imagen de sistema operativo a la calculadora.

        OPERACIÓN DE RIESGO: reescribe el firmware. Si se interrumpe (cable
        suelto, batería baja) la calculadora puede quedar inutilizable y hay
        que recuperarla por el modo de emergencia. El llamador DEBE confirmar
        con el usuario antes de invocar esto.
        """
        with self._lock:
            if not self._conectado:
                return False, "No conectada"
            if not self.soporta(OPS_OS):
                return False, "Este modelo no soporta actualizar el OS"

            valido, detalle = self.validar_archivo_os(ruta_os)
            if not valido:
                return False, detalle
            logger.warning("FLASHEO DE OS: %s (%s)", ruta_os, detalle)

            # Batería: un corte a media escritura deja la calculadora inservible
            info = {}
            try:
                infos = CalcInfos()
                if self._ticalcs.ticalcs_calc_get_version(
                        self._calc_h, ctypes.byref(infos)) == 0:
                    if infos.mask & INFOS_BATTERY:
                        info["bateria_ok"] = bool(infos.battery)
                    if infos.mask & INFOS_PRODUCT_NAME:
                        info["product_name"] = infos.product_name.decode(
                            "utf-8", errors="replace").strip()
            except Exception:
                pass
            if info.get("bateria_ok") is False:
                return False, ("La batería está baja: no se puede flashear el "
                               "OS con riesgo de que se apague a mitad")

            # CAS vs no-CAS: libtifiles no lo distingue (todo es modelo 15),
            # así que se compara la extensión con el modelo real conectado.
            ext = os.path.splitext(ruta_os)[1].lower()
            if ext in EXT_OS_NSPIRE:
                _fam, img_es_cas = EXT_OS_NSPIRE[ext]
                calc_es_cas = "CAS" in info.get("product_name", "").upper()
                if calc_es_cas and not img_es_cas:
                    return False, (
                        f"La imagen '{ext}' es de una Nspire SIN CAS y la "
                        f"calculadora conectada es {info['product_name']}. "
                        f"Instalarla le quitaría el CAS. Para una CX CAS el "
                        f"archivo debe ser .tcc")
                if img_es_cas and not calc_es_cas and info.get("product_name"):
                    return False, (
                        f"La imagen '{ext}' es de una Nspire CAS y la "
                        f"calculadora conectada es {info['product_name']}")

            self._progreso_cb = progreso_cb
            if self._update is not None:
                self._update.cancel = 0
            try:
                ret = self._ticalcs.ticalcs_calc_send_os2(
                    self._calc_h, ruta_os.encode("utf-8")
                )
                if ret != 0:
                    return False, f"Error al enviar el OS ({self._msg_error(ret)})"
                return True, ("OS enviado. La calculadora se reiniciará e "
                              "instalará la actualización; no la desconectes.")
            except Exception as e:
                logger.exception("Error en actualizar_os")
                return False, str(e)
            finally:
                self._progreso_cb = None

    # ── Captura de pantalla ───────────────────────────────────────────────────

    def capturar_pantalla(self) -> tuple[Optional[Captura], str]:
        """
        Pide la pantalla a la calculadora y la devuelve en RGB888.
        La librería hace la conversión desde el formato nativo (RGB565 en la
        CX CAS), así que aquí solo se copia el búfer y se libera el suyo.
        """
        with self._lock:
            if not self._conectado:
                return None, "No conectada"
            if not self.soporta(OPS_SCREEN):
                return None, "Este modelo no soporta captura de pantalla"

            sc = CalcScreenCoord()
            sc.format = SCREEN_FULL
            bitmap = ctypes.POINTER(ctypes.c_uint8)()
            try:
                ret = self._ticalcs.ticalcs_calc_recv_screen_rgb888(
                    self._calc_h, ctypes.byref(sc), ctypes.byref(bitmap)
                )
                if ret != 0:
                    return None, f"Error al capturar ({self._msg_error(ret)})"
                if not bitmap:
                    return None, "La calculadora no devolvió imagen"

                # clipped_* nunca es mayor que width/height: leer esas
                # dimensiones es seguro sea cual sea el tamaño que asignó.
                ancho = int(sc.clipped_width) or int(sc.width)
                alto  = int(sc.clipped_height) or int(sc.height)
                logger.info("recv_screen → %dx%d (completa %dx%d, pixfmt=%d)",
                            ancho, alto, sc.width, sc.height, sc.pixel_format)
                if ancho <= 0 or alto <= 0:
                    return None, f"Dimensiones inválidas ({ancho}x{alto})"

                datos = bytes(ctypes.string_at(bitmap, ancho * alto * 3))
                return Captura(ancho, alto, datos), ""
            except Exception as e:
                logger.exception("Error en capturar_pantalla")
                return None, str(e)
            finally:
                if bitmap:
                    try:
                        self._ticalcs.ticalcs_free_screen(bitmap)
                    except Exception:
                        pass

    # ── Crear carpeta en la calculadora ───────────────────────────────────────

    def crear_carpeta(self, nombre: str) -> tuple[bool, str]:
        """Crea una carpeta en la raíz de la calculadora."""
        nombre = nombre.strip().strip("/")
        with self._lock:
            if not self._conectado:
                return False, "No conectada"
            if not self.soporta(OPS_NEWFLD):
                return False, "Este modelo no soporta crear carpetas"
            if not nombre:
                return False, "El nombre no puede estar vacío"
            if any(c in nombre for c in '/\\:*?"<>|'):
                return False, "El nombre tiene caracteres no permitidos"
            try:
                ve = VarEntry()
                ve.folder = nombre.encode("utf-8")[:FLDNAME_MAX - 1]
                ve.name   = b""
                logger.info("new_fld → folder=%r", nombre)
                ret = self._ticalcs.ticalcs_calc_new_fld(
                    self._calc_h, ctypes.byref(ve)
                )
                if ret != 0:
                    return False, f"Error al crear la carpeta ({self._msg_error(ret)})"
                return True, ""
            except Exception as e:
                logger.exception("Error en crear_carpeta")
                return False, str(e)

    # ── Cierre explícito ──────────────────────────────────────────────────────

    def cerrar(self):
        """Llamar al cerrar la aplicación. Sustituye al viejo __del__."""
        try:
            self.desconectar()
        except Exception:
            pass
