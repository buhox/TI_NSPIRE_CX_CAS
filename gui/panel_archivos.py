# =============================================================================
# PANEL DE ARCHIVOS — Transferencia PC ↔ Calculadora TI-Nspire
# =============================================================================
from __future__ import annotations

import logging
import os
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QTreeView, QTreeWidget, QTreeWidgetItem,
    QFileSystemModel, QGroupBox, QLineEdit, QTextEdit,
    QAbstractItemView, QHeaderView, QMessageBox, QFileDialog,
    QProgressBar, QFrame,
)
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon, QColor

logger = logging.getLogger("ti_nspire.panel_archivos")

import sys, os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))
from comunicacion.transferencia import GestorTransferencia, EntradaArchivo

# Extensiones conocidas de la TI-Nspire
_EXT_NSPIRE = {".tns", ".lua", ".py", ".lua", ".luac", ".8xp"}


# ── Señales thread-safe ───────────────────────────────────────────────────────

class _Senales(QObject):
    progreso          = pyqtSignal(str)
    calc_listada      = pyqtSignal(list, str)   # (entradas, error)
    transferido       = pyqtSignal(bool, str)   # (ok, mensaje)
    conectado         = pyqtSignal(bool, str)   # (ok, mensaje)
    eliminado         = pyqtSignal(bool, str)   # (ok, mensaje)
    info_dispositivo  = pyqtSignal(dict)        # info OS/batería/memoria


# ── Panel principal ───────────────────────────────────────────────────────────

class PanelArchivos(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gestor   = GestorTransferencia()
        self._senales  = _Senales()
        self._conectado = False
        self._entradas_calc: list[EntradaArchivo] = []
        self._construir_ui()
        self._conectar_senales()

    # ── Construcción UI ───────────────────────────────────────────────────────

    def _construir_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # ── Barra superior: conexión ──────────────────────────────────────────
        barra = QHBoxLayout()
        self._lbl_estado = QLabel("⚫  Calculadora no conectada")
        self._lbl_estado.setStyleSheet("color:#8b949e; font-size:12px;")
        barra.addWidget(self._lbl_estado)
        barra.addStretch()
        self._btn_conectar = QPushButton("🔌  Conectar calculadora")
        self._btn_conectar.setObjectName("btn_primary")
        self._btn_conectar.setFixedHeight(30)
        self._btn_conectar.clicked.connect(self._conectar)
        barra.addWidget(self._btn_conectar)
        self._btn_desconectar = QPushButton("⛔  Desconectar")
        self._btn_desconectar.setFixedHeight(30)
        self._btn_desconectar.clicked.connect(self._desconectar)
        self._btn_desconectar.setEnabled(False)
        barra.addWidget(self._btn_desconectar)
        root.addLayout(barra)

        # ── Splitter central ──────────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # Panel PC (izquierda)
        splitter.addWidget(self._construir_panel_pc())

        # Botones de transferencia (centro)
        mid = QWidget()
        mid.setFixedWidth(80)
        mid_lay = QVBoxLayout(mid)
        mid_lay.setContentsMargins(4, 0, 4, 0)
        mid_lay.setAlignment(Qt.AlignCenter)
        mid_lay.addStretch()

        self._btn_enviar = QPushButton("→")
        self._btn_enviar.setToolTip("Enviar archivo seleccionado a la calculadora")
        self._btn_enviar.setFixedSize(56, 40)
        self._btn_enviar.setFont(QFont("Consolas", 16, QFont.Bold))
        self._btn_enviar.setEnabled(False)
        self._btn_enviar.clicked.connect(self._enviar_a_calc)

        self._btn_recibir = QPushButton("←")
        self._btn_recibir.setToolTip("Recibir archivo seleccionado de la calculadora")
        self._btn_recibir.setFixedSize(56, 40)
        self._btn_recibir.setFont(QFont("Consolas", 16, QFont.Bold))
        self._btn_recibir.setEnabled(False)
        self._btn_recibir.clicked.connect(self._recibir_de_calc)

        mid_lay.addWidget(self._btn_enviar)
        mid_lay.addSpacing(12)
        mid_lay.addWidget(self._btn_recibir)
        mid_lay.addStretch()
        splitter.addWidget(mid)

        # Panel calculadora (derecha)
        splitter.addWidget(self._construir_panel_calc())

        splitter.setSizes([500, 80, 400])
        root.addWidget(splitter, 1)

        # ── Log de operaciones ────────────────────────────────────────────────
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(110)
        self._log.setFont(QFont("Consolas", 10))
        self._log.setStyleSheet(
            "QTextEdit { background:#0d1117; color:#7ee787; border:1px solid #21262d; "
            "border-radius:4px; padding:4px; }"
        )
        self._log.setPlaceholderText("— Registro de operaciones —")
        root.addWidget(self._log)

    def _construir_panel_pc(self) -> QWidget:
        w = QGroupBox("🖥️  Computador")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(4)

        # Barra de navegación
        nav = QHBoxLayout()
        self._lbl_ruta_pc = QLabel(os.path.expanduser("~"))
        self._lbl_ruta_pc.setStyleSheet("color:#8b949e; font-size:10px;")
        self._lbl_ruta_pc.setWordWrap(False)
        nav.addWidget(self._lbl_ruta_pc, 1)
        btn_home = QPushButton("🏠")
        btn_home.setFixedSize(28, 24)
        btn_home.setToolTip("Ir a carpeta personal")
        btn_home.clicked.connect(lambda: self._navegar_pc(os.path.expanduser("~")))
        nav.addWidget(btn_home)
        btn_sel = QPushButton("📂")
        btn_sel.setFixedSize(28, 24)
        btn_sel.setToolTip("Seleccionar carpeta")
        btn_sel.clicked.connect(self._seleccionar_carpeta_pc)
        nav.addWidget(btn_sel)
        lay.addLayout(nav)

        # Árbol de archivos
        self._modelo_pc = QFileSystemModel()
        self._modelo_pc.setRootPath(os.path.expanduser("~"))
        self._modelo_pc.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

        self._tree_pc = QTreeView()
        self._tree_pc.setModel(self._modelo_pc)
        self._tree_pc.setRootIndex(
            self._modelo_pc.index(os.path.expanduser("~"))
        )
        self._tree_pc.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tree_pc.setSortingEnabled(True)
        self._tree_pc.sortByColumn(0, Qt.AscendingOrder)
        self._tree_pc.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tree_pc.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tree_pc.setColumnWidth(2, 80)
        self._tree_pc.setColumnWidth(3, 120)
        self._tree_pc.setStyleSheet(
            "QTreeView { background:#0d1117; color:#c9d1d9; "
            "border:1px solid #21262d; alternate-background-color:#161b22; }"
            "QTreeView::item:selected { background:#1f6feb44; }"
        )
        self._tree_pc.setAlternatingRowColors(True)
        self._tree_pc.doubleClicked.connect(self._pc_doble_clic)
        lay.addWidget(self._tree_pc)
        return w

    def _construir_panel_calc(self) -> QWidget:
        w = QGroupBox("🔢  Calculadora TI-Nspire")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(4)

        # Barra de acciones
        nav = QHBoxLayout()
        self._btn_actualizar = QPushButton("🔄 Actualizar")
        self._btn_actualizar.setFixedHeight(26)
        self._btn_actualizar.setEnabled(False)
        self._btn_actualizar.clicked.connect(self._actualizar_calc)
        nav.addWidget(self._btn_actualizar)

        self._btn_eliminar_calc = QPushButton("🗑 Eliminar")
        self._btn_eliminar_calc.setObjectName("btn_danger")
        self._btn_eliminar_calc.setFixedHeight(26)
        self._btn_eliminar_calc.setEnabled(False)
        self._btn_eliminar_calc.setToolTip("Eliminar archivo seleccionado de la calculadora")
        self._btn_eliminar_calc.clicked.connect(self._eliminar_de_calc)
        nav.addWidget(self._btn_eliminar_calc)

        nav.addStretch()
        self._lbl_mem = QLabel("")
        self._lbl_mem.setStyleSheet("color:#8b949e; font-size:10px;")
        nav.addWidget(self._lbl_mem)
        lay.addLayout(nav)

        # Árbol de archivos de la calculadora
        self._tree_calc = QTreeWidget()
        self._tree_calc.setHeaderLabels(["Nombre", "Tamaño"])
        self._tree_calc.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tree_calc.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tree_calc.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tree_calc.setAlternatingRowColors(True)
        self._tree_calc.setStyleSheet(
            "QTreeWidget { background:#0d1117; color:#c9d1d9; "
            "border:1px solid #21262d; alternate-background-color:#161b22; }"
            "QTreeWidget::item:selected { background:#1f6feb44; }"
        )
        self._tree_calc.itemSelectionChanged.connect(self._calc_seleccion_cambio)

        # Placeholder cuando no hay conexión
        self._placeholder = QLabel(
            "Conecta la calculadora vía USB\ny pulsa  🔌 Conectar"
        )
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            "color:#6e7681; font-size:13px; padding:30px;"
        )

        lay.addWidget(self._placeholder)
        lay.addWidget(self._tree_calc)
        self._tree_calc.setVisible(False)
        return w

    # ── Señales ───────────────────────────────────────────────────────────────

    def _conectar_senales(self):
        self._senales.progreso.connect(self._agregar_log)
        self._senales.calc_listada.connect(self._mostrar_archivos_calc)
        self._senales.transferido.connect(self._on_transferido)
        self._senales.conectado.connect(self._on_conectado)
        self._senales.eliminado.connect(self._on_eliminado)
        self._senales.info_dispositivo.connect(self._on_info_dispositivo)

    # ── Acciones de conexión ──────────────────────────────────────────────────

    def _monitor_usb(self):
        """Devuelve el MonitorUSB de la ventana principal (si existe)."""
        win = self.window()
        return getattr(win, '_monitor', None)

    def _conectar(self):
        if not self._gestor.disponible:
            QMessageBox.warning(
                self, "Librerías no disponibles",
                "No se encontraron las librerías libticalcs2/libticables2.\n"
                "Instálalas con:\n  sudo dnf install tilp2"
            )
            return
        self._btn_conectar.setEnabled(False)
        self._agregar_log("Pausando monitor USB y conectando...")
        threading.Thread(target=self._hilo_conectar, daemon=True).start()

    def _hilo_conectar(self):
        monitor = self._monitor_usb()

        def pre_connect():
            if monitor:
                monitor.pausar()   # libera el handle pyusb del bucle de detección

        ok, msg = self._gestor.conectar(pre_connect_cb=pre_connect)
        # Emitir directamente — Qt AutoConnection detecta el hilo y usa QueuedConnection
        self._senales.conectado.emit(ok, msg)

    def _on_conectado(self, ok: bool, msg: str):
        self._conectado = ok
        if ok:
            self._lbl_estado.setText("✅  Calculadora conectada")
            self._lbl_estado.setStyleSheet("color:#3fb950; font-size:12px;")
            self._btn_conectar.setEnabled(False)
            self._btn_desconectar.setEnabled(True)
            self._btn_actualizar.setEnabled(True)
            self._btn_enviar.setEnabled(True)
            self._agregar_log(f"✓ {msg}")
            # Primero listar archivos; _hilo_info_dispositivo arrancará al terminar
            self._actualizar_calc()
        else:
            self._btn_conectar.setEnabled(True)
            self._lbl_estado.setText("⚫  No conectada")
            self._lbl_estado.setStyleSheet("color:#f85149; font-size:12px;")
            self._agregar_log(f"✗ {msg}")

    def _hilo_info_dispositivo(self):
        try:
            logger.info("Consultando info del dispositivo...")
            info = self._gestor.obtener_info_dispositivo()
            logger.info("Info dispositivo obtenida: %s", info)
        except Exception as e:
            logger.error("Error en _hilo_info_dispositivo: %s", e)
            info = {}
        self._senales.info_dispositivo.emit(info)

    def _on_info_dispositivo(self, info: dict):
        if not info:
            return
        # Mostrar en el log
        partes = []
        if info.get("os_version"):
            partes.append(f"OS {info['os_version']}")
        bat = info.get("battery")
        if bat is not None:
            carga = " (cargando)" if info.get("charging") else ""
            partes.append(f"Batería {bat}%{carga}")
        ram = info.get("mem_free_ram")
        if ram is not None:
            partes.append(f"RAM libre {self._fmt_tam(ram)}")
        flash = info.get("mem_free_flash")
        if flash is not None:
            partes.append(f"Flash libre {self._fmt_tam(flash)}")
        if partes:
            self._agregar_log("ℹ " + "  ·  ".join(partes))
        # Actualizar barra de estado de la ventana principal
        barra = getattr(self.window(), '_barra_conexion', None)
        if barra:
            barra.set_info_dispositivo(info)

    def _desconectar(self):
        self._gestor.desconectar()
        # Reanudar el monitor USB ahora que ticables liberó el dispositivo
        monitor = self._monitor_usb()
        if monitor:
            monitor.reanudar()
        self._conectado = False
        self._lbl_estado.setText("⚫  Calculadora no conectada")
        self._lbl_estado.setStyleSheet("color:#8b949e; font-size:12px;")
        self._btn_conectar.setEnabled(True)
        self._btn_desconectar.setEnabled(False)
        self._btn_actualizar.setEnabled(False)
        self._btn_enviar.setEnabled(False)
        self._btn_recibir.setEnabled(False)
        self._tree_calc.clear()
        self._tree_calc.setVisible(False)
        self._placeholder.setVisible(True)
        self._lbl_mem.setText("")
        self._agregar_log("Calculadora desconectada")

    # ── Listado de archivos de la calculadora ─────────────────────────────────

    def _actualizar_calc(self):
        if not self._conectado:
            return
        self._agregar_log("Listando archivos de la calculadora...")
        threading.Thread(target=self._hilo_listar, daemon=True).start()

    def _hilo_listar(self):
        try:
            logger.info("Iniciando listado de archivos de la calculadora...")
            entradas, error = self._gestor.listar_archivos()
            logger.info("Listado completado: %d entradas, error=%r", len(entradas), error)
        except Exception as e:
            logger.error("Error inesperado en _hilo_listar: %s", e)
            entradas, error = [], str(e)
        self._senales.calc_listada.emit(entradas, error)

    def _mostrar_archivos_calc(self, entradas: list, error: str):
        self._tree_calc.clear()
        if error:
            self._agregar_log(f"✗ Error listando: {error}")
            return

        self._entradas_calc = entradas
        self._placeholder.setVisible(False)
        self._tree_calc.setVisible(True)

        carpetas: dict[str, QTreeWidgetItem] = {}
        total_archivos = 0
        total_bytes = 0

        for e in entradas:
            if e.es_carpeta:
                item = QTreeWidgetItem(self._tree_calc)
                item.setText(0, f"📁  {e.nombre}")
                item.setForeground(0, QColor("#58a6ff"))
                item.setFont(0, QFont("Segoe UI", 10, QFont.Bold))
                item.setData(0, Qt.UserRole, None)
                carpetas[e.nombre] = item
                item.setExpanded(True)
            else:
                padre = carpetas.get(e.carpeta)
                item = QTreeWidgetItem(padre if padre else self._tree_calc)
                icon = self._icono_archivo(e.extension)
                item.setText(0, f"{icon}  {e.nombre}")
                item.setText(1, self._fmt_tam(e.tamanio))
                item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                item.setData(0, Qt.UserRole, e)
                total_archivos += 1
                total_bytes    += e.tamanio

        self._lbl_mem.setText(
            f"{total_archivos} archivos · {self._fmt_tam(total_bytes)}"
        )
        self._agregar_log(
            f"✓ {total_archivos} archivos encontrados "
            f"({self._fmt_tam(total_bytes)})"
        )
        # Consultar info del dispositivo DESPUÉS de que terminó el listado
        if self._conectado:
            threading.Thread(target=self._hilo_info_dispositivo, daemon=True).start()

    # ── Navegación en el PC ───────────────────────────────────────────────────

    def _navegar_pc(self, ruta: str):
        idx = self._modelo_pc.index(ruta)
        self._tree_pc.setRootIndex(idx)
        self._lbl_ruta_pc.setText(ruta)

    def _seleccionar_carpeta_pc(self):
        ruta = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta",
            self._modelo_pc.rootPath(),
        )
        if ruta:
            self._navegar_pc(ruta)

    def _pc_doble_clic(self, index):
        ruta = self._modelo_pc.filePath(index)
        if os.path.isdir(ruta):
            self._navegar_pc(ruta)

    # ── Transferencia PC → Calculadora ────────────────────────────────────────

    def _enviar_a_calc(self):
        idx = self._tree_pc.currentIndex()
        if not idx.isValid():
            self._agregar_log("Selecciona un archivo del PC primero.")
            return
        ruta = self._modelo_pc.filePath(idx)
        if not os.path.isfile(ruta):
            self._agregar_log("Selecciona un archivo (no una carpeta).")
            return
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in _EXT_NSPIRE:
            r = QMessageBox.question(
                self, "Extensión inusual",
                f"El archivo '{os.path.basename(ruta)}' no es un archivo típico "
                f"de la TI-Nspire.\n¿Continuar?",
            )
            if r != QMessageBox.Yes:
                return

        self._btn_enviar.setEnabled(False)
        threading.Thread(
            target=self._hilo_enviar,
            args=(ruta,),
            daemon=True,
        ).start()

    def _hilo_enviar(self, ruta: str):
        def cb(msg):
            self._senales.progreso.emit(msg)
        ok, msg = self._gestor.enviar_archivo(ruta, progreso_cb=cb)
        self._senales.transferido.emit(ok, msg)

    # ── Transferencia Calculadora → PC ────────────────────────────────────────

    def _recibir_de_calc(self):
        item = self._tree_calc.currentItem()
        if not item:
            self._agregar_log("Selecciona un archivo de la calculadora primero.")
            return
        entrada: EntradaArchivo = item.data(0, Qt.UserRole)
        if not entrada or entrada.es_carpeta:
            self._agregar_log("Selecciona un archivo (no una carpeta).")
            return

        directorio = self._modelo_pc.rootPath()
        self._btn_recibir.setEnabled(False)
        threading.Thread(
            target=self._hilo_recibir,
            args=(entrada, directorio),
            daemon=True,
        ).start()

    def _hilo_recibir(self, entrada: EntradaArchivo, directorio: str):
        def cb(msg):
            self._senales.progreso.emit(msg)
        ok, msg = self._gestor.recibir_archivo(entrada, directorio, progreso_cb=cb)
        self._senales.transferido.emit(ok, msg)

    # ── Eventos de finalización ───────────────────────────────────────────────

    def _on_transferido(self, ok: bool, msg: str):
        self._btn_enviar.setEnabled(self._conectado)
        self._btn_recibir.setEnabled(self._conectado and bool(
            self._tree_calc.currentItem()
        ))
        if ok:
            self._agregar_log(f"✓ Transferencia completada{': ' + msg if msg else ''}")
            # Refrescar lista PC
            self._modelo_pc.setRootPath(self._modelo_pc.rootPath())
        else:
            self._agregar_log(f"✗ Error: {msg}")

    def _calc_seleccion_cambio(self):
        item = self._tree_calc.currentItem()
        if item:
            entrada = item.data(0, Qt.UserRole)
            es_archivo = entrada is not None and not entrada.es_carpeta
            self._btn_recibir.setEnabled(self._conectado and es_archivo)
            self._btn_eliminar_calc.setEnabled(self._conectado and es_archivo)

    # ── Notificaciones de USB desde VentanaPrincipal ──────────────────────────

    def notificar_usb_detectada(self, info):
        """Llamado desde VentanaPrincipal cuando el monitor USB detecta la calculadora."""
        if not self._conectado:
            self._lbl_estado.setText(f"🟡  {info.modelo} detectada — pulsa Conectar")
            self._lbl_estado.setStyleSheet("color:#d29922; font-size:12px;")
            self._btn_conectar.setEnabled(True)

    def notificar_usb_perdida(self):
        """Llamado desde VentanaPrincipal cuando la calculadora se desenchufa."""
        if self._conectado:
            self._agregar_log("⚠ Calculadora desconectada físicamente")
            self._desconectar()

    # ── Eliminar archivo de la calculadora ────────────────────────────────────

    def _eliminar_de_calc(self):
        item = self._tree_calc.currentItem()
        if not item:
            return
        entrada: EntradaArchivo = item.data(0, Qt.UserRole)
        if not entrada or entrada.es_carpeta:
            self._agregar_log("Selecciona un archivo (no una carpeta).")
            return
        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar '{entrada.ruta_calc}' de la calculadora?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        self._btn_eliminar_calc.setEnabled(False)
        threading.Thread(
            target=self._hilo_eliminar,
            args=(entrada,),
            daemon=True,
        ).start()

    def _hilo_eliminar(self, entrada: EntradaArchivo):
        ok, msg = self._gestor.eliminar_archivo(entrada)
        self._senales.eliminado.emit(ok, msg)

    def _on_eliminado(self, ok: bool, msg: str):
        if ok:
            self._agregar_log(f"✓ Archivo eliminado de la calculadora")
            self._actualizar_calc()
        else:
            self._agregar_log(f"✗ Error al eliminar: {msg}")
            self._btn_eliminar_calc.setEnabled(True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _agregar_log(self, msg: str):
        self._log.append(msg)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _fmt_tam(n: int) -> str:
        if n >= 1_048_576:
            return f"{n/1_048_576:.1f} MB"
        if n >= 1024:
            return f"{n/1024:.1f} KB"
        return f"{n} B"

    @staticmethod
    def _icono_archivo(ext: str) -> str:
        return {
            ".tns":  "📄",
            ".py":   "🐍",
            ".lua":  "📜",
            ".luac": "📜",
            ".8xp":  "📐",
        }.get(ext, "📄")
