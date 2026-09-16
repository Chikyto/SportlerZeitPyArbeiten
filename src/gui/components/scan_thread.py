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
    Thread para scanning continuo sin bloquear UI.

    Rota entre todas las antenas disponibles lo más rápido posible.
    La pausa entre scans es mínima (SCAN_INTERVAL_MS) para maximizar
    el número de rondas de inventario EPC Gen2 por segundo, lo que
    mejora la captura en situaciones de alta densidad de chips
    (largada masiva con muchos corredores al mismo tiempo).
    """

    tag_detected  = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    # Pausa entre comandos de inventario — 50 ms es suficiente para que
    # el lector procese la respuesta anterior sin perder tiempo innecesario.
    # Durante la largada (muchos chips en campo) se reduce a BURST_INTERVAL_MS.
    SCAN_INTERVAL_MS  = 0.05   # 50 ms — modo normal
    BURST_INTERVAL_MS = 0.02   # 20 ms — modo densidad alta (largada)

    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner
        self.running = False
        self.burst_mode = False   # activar desde fuera para largada masiva

    def set_burst_mode(self, active: bool):
        """
        Activar/desactivar modo burst (mayor frecuencia de scan).
        Llamar con active=True justo antes de dar la largada,
        active=False cuando el último corredor cruzó la línea.
        """
        self.burst_mode = active
        logger.info(f"⚡ Burst mode {'ON' if active else 'OFF'}")

    def run(self):
        self.running = True
        scan_count = 0
        logger.info("🟢 ScanThread iniciado")

        while self.running:
            try:
                if not self.scanner.available_antennas:
                    time.sleep(1)
                    continue

                # Rotar entre antenas disponibles
                antenna_id = self.scanner.available_antennas[
                    scan_count % len(self.scanner.available_antennas)
                ]

                tags = self.scanner.scan_single_antenna(antenna_id)

                for tag in tags:
                    self.tag_detected.emit(tag)

                scan_count += 1
                interval = self.BURST_INTERVAL_MS if self.burst_mode else self.SCAN_INTERVAL_MS
                time.sleep(interval)

            except Exception as e:
                logger.error(f"❌ Error en scan: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)

        logger.info("🔴 ScanThread detenido")
    
    def stop(self):
        """
        Detener el thread de forma segura
        
        Establece la bandera running en False y espera
        a que el loop termine naturalmente
        """
        logger.info("⏸️  Deteniendo ScanThread...")
        self.running = False