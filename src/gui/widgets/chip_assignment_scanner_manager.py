#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Manager for Chip Assignment
src/gui/widgets/chip_assignment_scanner_manager.py

Manages network (YR8900) and USB (YR9011) scanners.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class ChipAssignmentScannerManager(QObject):
    """Manages RFID scanners for chip assignment"""

    # Signals
    scanner_mode_changed = pyqtSignal(str)  # "network" or "usb"
    scanner_connected = pyqtSignal(str)  # scanner type
    scanner_disconnected = pyqtSignal(str)
    scanning_started = pyqtSignal()
    scanning_stopped = pyqtSignal()

    def __init__(self, parent_widget):
        """
        Args:
            parent_widget: Parent QWidget for dialogs
        """
        super().__init__()
        self.parent = parent_widget
        self.scanner_mode = "network"  # "network" or "usb"
        self.network_scanner = None
        self.usb_scanner = None
        self.scanning = False

    def set_network_scanner(self, scanner):
        """Set YR8900 network scanner"""
        self.network_scanner = scanner
        logger.info("🌐 Network scanner configurado")

    def set_scanner_mode(self, mode: str):
        """
        Switch between network and USB scanner

        Args:
            mode: "network" for YR8900, "usb" for YR9011
        """
        if mode == self.scanner_mode:
            return

        self.scanner_mode = mode
        logger.info(f"🔄 Modo de scanner cambiado a: {mode}")

        if mode == "usb":
            # Connect USB scanner
            success = self.connect_usb_scanner()
            if not success:
                # Revert to network mode
                self.scanner_mode = "network"
                self.scanner_mode_changed.emit("network")
                return

        elif mode == "network":
            # Disconnect USB scanner if connected
            self.disconnect_usb_scanner()

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

        # Stop scanning if active
        if self.usb_scanner.scanning:
            logger.info("🔴 Deteniendo escaneo USB antes de desconectar...")
            self.usb_scanner.stop_continuous_reading()

        # Disconnect
        if self.usb_scanner.connected:
            logger.info("🔌 Desconectando lector USB...")
            self.usb_scanner.disconnect()

        self.scanner_disconnected.emit("usb")

    def start_scanning(self, athlete_name: str):
        """
        Start scanning mode

        Args:
            athlete_name: Name of athlete to assign chip to
        """
        self.scanning = True
        scanner_type = "YR9011 USB" if self.scanner_mode == "usb" else "YR8900 Network"

        logger.info(f"🔍 Modo de escaneo activado para: {athlete_name}")
        logger.info(f"   • Lector: {scanner_type}")
        logger.info(f"   • Esperando detección de chip...")

        # Start USB scanner if in USB mode
        if self.scanner_mode == "usb" and self.usb_scanner:
            logger.info("🟢 Iniciando escaneo continuo USB...")
            self.usb_scanner.start_continuous_reading()

        self.scanning_started.emit()

    def stop_scanning(self):
        """Stop scanning mode"""
        self.scanning = False
        logger.info("⏸️ Modo de escaneo desactivado")

        # Stop USB scanner if active
        if self.scanner_mode == "usb" and self.usb_scanner:
            logger.info("🔴 Deteniendo escaneo continuo USB...")
            self.usb_scanner.stop_continuous_reading()

        self.scanning_stopped.emit()

    def is_scanner_available(self) -> bool:
        """Check if a scanner is available for current mode"""
        if self.scanner_mode == "network":
            return self.network_scanner is not None

        elif self.scanner_mode == "usb":
            return self.usb_scanner is not None and self.usb_scanner.connected

        return False

    def get_scanner_status(self) -> dict:
        """Get scanner status information"""
        if self.scanner_mode == "network":
            return {
                'mode': 'network',
                'type': 'YR8900',
                'available': self.network_scanner is not None,
                'scanning': self.scanning
            }

        elif self.scanner_mode == "usb":
            return {
                'mode': 'usb',
                'type': 'YR9011',
                'available': self.usb_scanner is not None and self.usb_scanner.connected,
                'port': self.usb_scanner.port if self.usb_scanner else None,
                'scanning': self.usb_scanner.scanning if self.usb_scanner else False
            }

        return {}

    def cleanup(self):
        """Cleanup on widget destruction"""
        if self.usb_scanner:
            if self.usb_scanner.scanning:
                self.usb_scanner.stop_continuous_reading()
            if self.usb_scanner.connected:
                self.usb_scanner.disconnect()
