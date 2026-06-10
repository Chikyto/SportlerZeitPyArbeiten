#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Worker de sincronización con el backend
src/core/cloud_sync_worker.py

Vacía la cola de envíos pendientes (sync_outbox en la base SQLite)
hacia el backend, en orden y con confirmación:

- Cada envío se marca 'sent' solo cuando el servidor respondió 2xx.
- Si se corta internet, los envíos quedan 'pending' en disco y se
  reintentan automáticamente cada `interval_seconds` hasta que vuelva
  la conexión. Sobreviven también a reinicios de la aplicación.
- El orden se respeta estrictamente: ante un fallo de red se corta el
  ciclo (no se saltean envíos), se reintenta todo desde ahí.
- Errores permanentes del servidor (400, 404, 422...) se marcan 'dead'
  para no bloquear la cola, y quedan en la base para diagnóstico.
"""

import logging
import threading

import requests

logger = logging.getLogger(__name__)


class CloudSyncWorker:
    """
    Hilo en segundo plano que envía la cola de sincronización.

    Example:
        >>> worker = CloudSyncWorker(persistence)
        >>> worker.start()
        >>> persistence.enqueue_sync('detection', url, payload, headers)
        >>> worker.notify()  # intento inmediato (sin esperar al intervalo)
    """

    # Errores del servidor que no tiene sentido reintentar
    DEAD_STATUS_CODES = {400, 404, 405, 409, 410, 422}

    def __init__(self, persistence, interval_seconds: float = 10.0,
                 request_timeout: float = 10.0):
        self.persistence = persistence
        self.interval_seconds = interval_seconds
        self.request_timeout = request_timeout

        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None

        # Resultado del último intento de envío (para indicador en UI):
        # None = aún sin intentos | True = conexión OK | False = sin conexión
        self.last_flush_ok = None

    def start(self):
        """Iniciar el hilo de envío"""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="CloudSyncWorker", daemon=True
        )
        self._thread.start()
        logger.info(f"☁️ CloudSyncWorker iniciado (reintento cada {self.interval_seconds}s)")

    def notify(self):
        """Despertar al worker para intentar enviar ya mismo"""
        self._wake.set()

    def stop(self, timeout: float = 3.0):
        """Detener el hilo (al cerrar la aplicación)"""
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self):
        while not self._stop.is_set():
            self._wake.wait(timeout=self.interval_seconds)
            self._wake.clear()
            if self._stop.is_set():
                break
            try:
                self.flush()
            except Exception as e:
                # El worker nunca debe morir por un error inesperado
                logger.error(f"❌ Error en ciclo de sincronización: {e}", exc_info=True)

    def flush(self) -> tuple:
        """
        Intentar enviar todos los pendientes, en orden.

        Returns:
            (enviados, pendientes_restantes)
        """
        sent = 0
        pending_rows = self.persistence.get_pending_sync()
        if not pending_rows:
            return 0, 0

        logger.info(f"☁️ Sincronizando: {len(pending_rows)} envío(s) pendiente(s)")

        for row in pending_rows:
            if self._stop.is_set():
                break
            try:
                r = requests.post(
                    row['url'],
                    json=row['payload'],
                    headers=row['headers'],
                    timeout=self.request_timeout,
                )

                if 200 <= r.status_code < 300:
                    self.persistence.mark_sync_sent(row['id'])
                    sent += 1
                    logger.info(f"☁️ Enviado OK [{row['kind']}] id={row['id']}")
                elif r.status_code in self.DEAD_STATUS_CODES:
                    # Error permanente: no bloquear la cola reintentando
                    self.persistence.mark_sync_failed(
                        row['id'],
                        f"HTTP {r.status_code}: {r.text[:200]}",
                        dead=True,
                    )
                    logger.warning(
                        f"⚠️ Envío [{row['kind']}] id={row['id']} descartado "
                        f"(HTTP {r.status_code}): {r.text[:150]}"
                    )
                else:
                    # Error transitorio del servidor (5xx, 429...):
                    # reintentar más tarde, sin saltear los siguientes.
                    # El servidor respondió → hay conexión.
                    self.last_flush_ok = True
                    self.persistence.mark_sync_failed(
                        row['id'], f"HTTP {r.status_code}: {r.text[:200]}"
                    )
                    logger.warning(
                        f"⚠️ Backend respondió {r.status_code} para id={row['id']}, "
                        f"se reintenta en el próximo ciclo"
                    )
                    break

            except requests.RequestException as e:
                # Sin conexión: queda todo pendiente para el próximo ciclo
                self.persistence.mark_sync_failed(row['id'], f"{type(e).__name__}: {e}")
                self.last_flush_ok = False
                logger.info(
                    f"☁️ Sin conexión ({type(e).__name__}) — "
                    f"los envíos quedan en cola y se reintentan automáticamente"
                )
                break
        else:
            # El ciclo terminó sin errores de red
            self.last_flush_ok = True

        remaining = self.persistence.pending_sync_count()
        if sent:
            logger.info(f"☁️ Sincronización: {sent} enviado(s), {remaining} pendiente(s)")
        return sent, remaining
