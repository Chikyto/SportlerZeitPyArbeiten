#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thread de escaneo RFID separado
src/gui/tabs/scan_thread.py

Responsabilidad única: Ejecutar scanning en background sin bloquear UI
"""

import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ScanThread(QThread):
    """
    Thread para scanning continuo sin bloquear UI
    
    Signals:
        tag_detected: Emitido cuando se detecta un tag
        error_occurred: Emitido cuando hay un error en el scan
    """
    
    tag_detected = pyqtSignal(dict)  # Emite dict con info del tag
    error_occurred = pyqtSignal(str)  # Emite mensaje de error
    
    def __init__(self, scanner):
        """
        Inicializar thread de scanning
        
        Args:
            scanner: Instancia de AdvancedYR8900Scanner
        """
        super().__init__()
        self.scanner = scanner
        self.running = False
    
    def run(self):
        """
        Loop principal de scanning
        
        Ejecuta en background, rotando entre antenas disponibles
        y emitiendo señales cuando detecta tags
        """
        self.running = True
        scan_count = 0
        
        logger.info("🟢 ScanThread iniciado")
        
        while self.running:
            try:
                # Verificar que hay antenas disponibles
                if not self.scanner.available_antennas:
                    time.sleep(1)
                    continue
                
                # Rotar entre antenas disponibles
                antenna_id = self.scanner.available_antennas[
                    scan_count % len(self.scanner.available_antennas)
                ]
                
                # Escanear antena actual
                tags = self.scanner.scan_single_antenna(antenna_id)
                
                # Emitir cada tag detectado
                for tag in tags:
                    self.tag_detected.emit(tag)
                
                scan_count += 1
                time.sleep(0.3)  # Pausa entre scans
                
            except Exception as e:
                logger.error(f"❌ Error en scan: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)  # Pausa más larga en caso de error
        
        logger.info("🔴 ScanThread detenido")
    
    def stop(self):
        """
        Detener el thread de forma segura
        
        Establece la bandera running en False y espera
        a que el loop termine naturalmente
        """
        logger.info("⏸️  Deteniendo ScanThread...")
        self.running = False