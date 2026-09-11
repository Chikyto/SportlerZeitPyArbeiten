#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente WebSocket para lector local de chips RFID
src/core/local_reader_scanner.py

Se conecta a un servicio local que expone ws://localhost:<puerto>
y reenvía las detecciones como señales PyQt.

Protocolo esperado del servicio:
  → enviar: {"action": "scan"}
  ← recibir: {"type": "chip_detected", "chip_id": "5959"}
  ← recibir: {"type": "status", "connected": true/false}
"""

import json
import logging
import threading
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class LocalReaderScanner(QObject):
    """
    Cliente WebSocket para un servicio lector local de chips RFID.
    Compatible con la interfaz de YR9011USBScanner (mismas señales).
    """

    tag_detected   = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(bool)   # True = lector físico conectado al servicio

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8765

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        super().__init__()
        self.host = host
        self.port = port
        self._ws = None
        self._thread: threading.Thread | None = None
        self.connected = False      # WebSocket conectado al servicio
        self.scanning  = False
        self.reader_ready = False   # El lector físico está listo según el servicio

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Conectar al servicio WebSocket local. Retorna True si OK."""
        try:
            import websockets.sync.client as _ws_sync
        except ImportError:
            logger.error("❌ Falta dependencia 'websockets'. Instalá con: pip install websockets")
            self.error_occurred.emit("Falta la librería 'websockets'. Instalá con: pip install websockets")
            return False

        try:
            uri = f"ws://{self.host}:{self.port}"
            logger.info(f"🔌 Conectando a lector local en {uri}...")
            self._ws = _ws_sync.connect(uri, open_timeout=3)
            self.connected = True
            logger.info("✅ Conectado al servicio de lector local")
            return True
        except Exception as e:
            logger.error(f"❌ No se pudo conectar al servicio local: {e}")
            self.error_occurred.emit(str(e))
            self.connected = False
            return False

    def disconnect(self):
        """Desconectar del servicio WebSocket."""
        self.scanning = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        self.connected = False
        logger.info("🔌 Desconectado del servicio de lector local")

    # ------------------------------------------------------------------
    # Escaneo
    # ------------------------------------------------------------------

    def start_continuous_reading(self):
        """Iniciar escaneo continuo en thread separado."""
        if self.scanning or not self.connected:
            return
        self.scanning = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info("🟢 Escaneo continuo iniciado (lector local)")

    def stop_continuous_reading(self):
        """Detener escaneo continuo."""
        if not self.scanning:
            return
        self.scanning = False
        try:
            if self._ws:
                self._ws.send(json.dumps({"action": "stop"}))
        except Exception:
            pass
        logger.info("🔴 Escaneo continuo detenido (lector local)")

    def _read_loop(self):
        """Thread de lectura — escucha mensajes del servicio."""
        try:
            # Activar escaneo en el servicio
            self._ws.send(json.dumps({"action": "scan"}))

            while self.scanning and self._ws:
                try:
                    raw = self._ws.recv(timeout=1.0)
                except TimeoutError:
                    continue
                except Exception as e:
                    if self.scanning:
                        logger.warning(f"⚠️ Error recibiendo mensaje: {e}")
                        self.error_occurred.emit(str(e))
                    break

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type", "")

                if msg_type == "chip_detected":
                    chip_id = str(msg.get("chip_id", "")).strip().upper()
                    if chip_id:
                        tag_data = {
                            "tag_id":  chip_id,
                            "epc":     chip_id,
                            "source":  "local_reader",
                        }
                        logger.info(f"📡 Chip detectado (local): {chip_id}")
                        self.tag_detected.emit(tag_data)

                elif msg_type == "status":
                    ready = bool(msg.get("connected", False))
                    self.reader_ready = ready
                    self.status_changed.emit(ready)

                elif msg_type in ("error", "disconnected"):
                    logger.warning(f"⚠️ Servicio reportó: {msg}")

        except Exception as e:
            if self.scanning:
                logger.error(f"❌ Error en loop de lectura local: {e}")
                self.error_occurred.emit(str(e))
        finally:
            self.scanning = False
