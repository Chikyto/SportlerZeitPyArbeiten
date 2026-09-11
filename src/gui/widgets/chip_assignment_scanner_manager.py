#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Manager for Chip Assignment
src/gui/widgets/chip_assignment_scanner_manager.py

Manages USB (YR9011) and local WebSocket scanners for chip assignment.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class ChipAssignmentScannerManager(QObject):
    """Manages RFID scanners for chip assignment"""

    # Signals
    scanner_mode_changed = pyqtSignal(str)  # "none", "usb" or "local"
    scanner_connected = pyqtSignal(str)  # scanner type
    scanner_disconnected = pyqtSignal(str)
    scanning_started = pyqtSignal()
    scanning_stopped = pyqtSignal()

    def __init__(self, parent_widget):
        super().__init__()
        self.parent = parent_widget
        # Lectores para asignación de chips: USB (YR9011) o local
        # (WebSocket). Las antenas de competencia (YR8900) NO se usan
        # acá: sus lecturas son de carrera, no de asignación.
        self.scanner_mode = "none"  # "none", "usb" or "local"
        self.usb_scanner = None
        self.local_scanner = None
        self.scanning = False

    def set_scanner_mode(self, mode: str):
        """
        Switch between USB and local scanner

        Args:
            mode: "usb" for YR9011, "local" for WebSocket reader,
                  "none" for manual-only assignment
        """
        if mode == self.scanner_mode:
            return

        self.scanner_mode = mode
        logger.info(f"🔄 Modo de scanner cambiado a: {mode}")

        if mode == "usb":
            success = self.connect_usb_scanner()
            if not success:
                self.scanner_mode = "none"
                self.scanner_mode_changed.emit("none")
                return

        elif mode == "local":
            success = self.connect_local_scanner()
            if not success:
                self.scanner_mode = "none"
                self.scanner_mode_changed.emit("none")
                return

        elif mode == "none":
            self.disconnect_usb_scanner()
            self.disconnect_local_scanner()

        self.scanner_mode_changed.emit(mode)

    def connect_usb_scanner(self) -> bool:
        """Connect to USB scanner with configuration dialog"""
        try:
            from src.core.yr9011_usb_scanner import YR9011USBScanner
            from src.gui.usb_scanner_config_dialog import USBScannerConfigDialog

            logger.info("📡 Abriendo configuración de lector USB...")

            # Show configuration dialog
            dialog = USBScannerConfigDialog(self.parent)

            if dialog.exec() != dialog.DialogCode.Accepted:
                logger.info("⏭️ Usuario canceló configuración USB")
                return False

            config = dialog.get_config()

            if not config['port']:
                logger.warning("❌ No se seleccionó puerto")
                return False

            logger.info(f"📡 Conectando a {config['port']} @ {config['baudrate']} bps...")

            # Create USB scanner
            self.usb_scanner = YR9011USBScanner(port=config['port'])

            # Connect to scanner
            if not self.usb_scanner.connect():
                QMessageBox.warning(
                    self.parent,
                    "Conexión Fallida",
                    f"No se pudo conectar al puerto {config['port']}.\n\n"
                    "Verifica que:\n"
                    "• El puerto sea el correcto\n"
                    "• No esté siendo usado por otra aplicación\n"
                    "• El lector esté encendido"
                )
                return False

            # CRITICAL: Ensure NOT in continuous scan mode on connect
            self.usb_scanner.stop_continuous_reading()

            logger.info(f"✅ Lector USB conectado en {config['port']}")
            logger.info(f"💡 Lector USB listo. Escaneo iniciará al presionar 'Escanear Chip'")

            self.scanner_connected.emit("usb")
            return True

        except ImportError as e:
            logger.error(f"❌ Error importando YR9011USBScanner: {e}")
            QMessageBox.critical(
                self.parent,
                "Error",
                f"No se pudo cargar el driver del lector USB:\n{str(e)}"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Error conectando lector USB: {e}")
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Error conectando lector USB:\n{str(e)}"
            )
            return False

    def disconnect_usb_scanner(self):
        """Disconnect USB scanner"""
        if not self.usb_scanner:
            return
        if self.usb_scanner.scanning:
            self.usb_scanner.stop_continuous_reading()
        if self.usb_scanner.connected:
            self.usb_scanner.disconnect()
        self.scanner_disconnected.emit("usb")

    def connect_local_scanner(self) -> bool:
        """Connect to local WebSocket reader service"""
        try:
            from src.core.local_reader_scanner import LocalReaderScanner
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QDialogButtonBox, QFormLayout

            # Simple dialog to confirm host/port
            dlg = QDialog(self.parent)
            dlg.setWindowTitle("Lector Local — Configuración")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Conectar al servicio WebSocket del lector local:"))
            form = QFormLayout()
            host_input = QLineEdit("localhost")
            port_input = QSpinBox()
            port_input.setRange(1, 65535)
            port_input.setValue(8765)
            form.addRow("Host:", host_input)
            form.addRow("Puerto WebSocket:", port_input)
            layout.addLayout(form)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)
            layout.addWidget(buttons)

            if dlg.exec() != QDialog.DialogCode.Accepted:
                return False

            scanner = LocalReaderScanner(host=host_input.text().strip(), port=port_input.value())
            if not scanner.connect():
                QMessageBox.warning(
                    self.parent,
                    "Sin conexión",
                    f"No se pudo conectar a ws://{host_input.text()}:{port_input.value()}\n\n"
                    "Verificá que el servicio lector local esté corriendo."
                )
                return False

            self.local_scanner = scanner
            self.scanner_connected.emit("local")
            logger.info(f"✅ Lector local conectado en ws://{scanner.host}:{scanner.port}")
            return True

        except Exception as e:
            logger.error(f"❌ Error conectando lector local: {e}")
            QMessageBox.critical(self.parent, "Error", f"Error conectando lector local:\n{str(e)}")
            return False

    def disconnect_local_scanner(self):
        """Disconnect local WebSocket scanner"""
        if not self.local_scanner:
            return
        if self.local_scanner.scanning:
            self.local_scanner.stop_continuous_reading()
        if self.local_scanner.connected:
            self.local_scanner.disconnect()
        self.local_scanner = None
        self.scanner_disconnected.emit("local")

    def start_scanning(self, athlete_name: str):
        """
        Start scanning mode

        Args:
            athlete_name: Name of athlete to assign chip to
        """
        self.scanning = True
        logger.info(f"🔍 Escaneo activado para: {athlete_name} (modo: {self.scanner_mode})")

        if self.scanner_mode == "usb" and self.usb_scanner:
            self.usb_scanner.start_continuous_reading()
        elif self.scanner_mode == "local" and self.local_scanner:
            self.local_scanner.start_continuous_reading()

        self.scanning_started.emit()

    def stop_scanning(self):
        """Stop scanning mode"""
        self.scanning = False
        if self.scanner_mode == "usb" and self.usb_scanner:
            self.usb_scanner.stop_continuous_reading()
        elif self.scanner_mode == "local" and self.local_scanner:
            self.local_scanner.stop_continuous_reading()
        self.scanning_stopped.emit()

    def is_scanner_available(self) -> bool:
        """Check if a scanner is available for current mode"""
        if self.scanner_mode == "usb":
            return self.usb_scanner is not None and self.usb_scanner.connected
        elif self.scanner_mode == "local":
            return self.local_scanner is not None and self.local_scanner.connected
        return False

    def get_scanner_status(self) -> dict:
        """Get scanner status information"""
        if self.scanner_mode == "usb":
            return {
                'mode': 'usb',
                'type': 'YR9011',
                'available': self.usb_scanner is not None and self.usb_scanner.connected,
                'port': self.usb_scanner.port if self.usb_scanner else None,
                'scanning': self.usb_scanner.scanning if self.usb_scanner else False
            }

        elif self.scanner_mode == "local":
            return {
                'mode': 'local',
                'type': 'LocalReader',
                'available': self.local_scanner is not None and self.local_scanner.connected,
                'host': self.local_scanner.host if self.local_scanner else None,
                'port': self.local_scanner.port if self.local_scanner else None,
                'scanning': self.local_scanner.scanning if self.local_scanner else False
            }

        return {}

    def cleanup(self):
        """Cleanup on widget destruction"""
        if self.usb_scanner:
            if self.usb_scanner.scanning:
                self.usb_scanner.stop_continuous_reading()
            if self.usb_scanner.connected:
                self.usb_scanner.disconnect()
        self.disconnect_local_scanner()
