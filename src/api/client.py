#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente API para enviar resultados a servidor web
src/api/client.py

Envía detecciones y resultados en tiempo real a un backend web
para que los espectadores puedan ver los resultados online.
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RaceAPIClient:
    """
    Cliente asíncrono para enviar datos a servidor web

    Características:
    - Cola de mensajes con procesamiento asíncrono
    - Retry automático con exponential backoff
    - No bloquea el sistema de timing local
    - Continúa funcionando si el servidor está caído

    Example:
        >>> client = RaceAPIClient("https://api.example.com", "event-2025-01")
        >>> await client.start()
        >>> await client.send_detection(detection_event)
        >>> await client.stop()
    """

    def __init__(
        self,
        api_url: str,
        event_id: str,
        api_key: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Inicializar cliente API

        Args:
            api_url: URL base del servidor (ej: "https://api.example.com")
            event_id: ID del evento actual
            api_key: API key para autenticación (opcional)
            enabled: Si False, no envía nada (modo offline)
        """
        self.api_url = api_url.rstrip('/')
        self.event_id = event_id
        self.api_key = api_key
        self.enabled = enabled

        self.session: Optional[aiohttp.ClientSession] = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None

        self.stats = {
            'sent': 0,
            'failed': 0,
            'queued': 0
        }

    async def start(self):
        """Iniciar cliente y worker"""
        if not self.enabled:
            logger.info("🌐 API Client deshabilitado (modo offline)")
            return

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        self.session = aiohttp.ClientSession(headers=headers)
        self.worker_task = asyncio.create_task(self._worker())

        logger.info(f"🌐 API Client iniciado: {self.api_url}")
        logger.info(f"📡 Event ID: {self.event_id}")

    async def stop(self):
        """Detener cliente y cerrar conexiones"""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info(f"🌐 API Client detenido. Stats: {self.stats}")

    async def send_detection(self, detection_event) -> bool:
        """
        Enviar detección al servidor

        Args:
            detection_event: DetectionEvent del RaceManager

        Returns:
            bool: True si se agregó a la cola exitosamente
        """
        if not self.enabled:
            return False

        try:
            data = {
                'tag_id': detection_event.tag_id,
                'timestamp': detection_event.timestamp.isoformat(),
                'antenna_port': detection_event.antenna_port,
                'event_type': detection_event.event_type.value,
                'checkpoint_number': detection_event.checkpoint_number,
                'category_id': detection_event.category_id,
                'athlete_name': detection_event.athlete.name if detection_event.athlete else None,
                'bib_number': detection_event.athlete.bib_number if detection_event.athlete else None
            }

            await self.queue.put({
                'type': 'detection',
                'endpoint': f'/api/events/{self.event_id}/detection',
                'data': data
            })

            self.stats['queued'] += 1
            logger.debug(f"📤 Detección agregada a cola: {detection_event.tag_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error agregando detección a cola: {e}")
            return False

    async def send_result(self, athlete_result) -> bool:
        """
        Enviar resultado actualizado al servidor

        Args:
            athlete_result: AthleteResult del RaceManager

        Returns:
            bool: True si se agregó a la cola exitosamente
        """
        if not self.enabled:
            return False

        try:
            data = {
                'athlete_id': athlete_result.athlete.athlete_id,
                'tag_id': athlete_result.athlete.tag_id,
                'bib_number': athlete_result.athlete.bib_number,
                'name': athlete_result.athlete.name,
                'category_id': athlete_result.category_id,
                'status': athlete_result.status.value,
                'start_time': athlete_result.start_time.isoformat() if athlete_result.start_time else None,
                'finish_time': athlete_result.finish_time.isoformat() if athlete_result.finish_time else None,
                'total_time': athlete_result.total_time.total_seconds() if athlete_result.total_time else None,
                'position': athlete_result.position,
                'checkpoint_times': {
                    str(k): v.isoformat() for k, v in athlete_result.checkpoint_times.items()
                },
                'splits': {
                    str(k): v.total_seconds() for k, v in athlete_result.splits.items()
                }
            }

            await self.queue.put({
                'type': 'result',
                'endpoint': f'/api/events/{self.event_id}/result',
                'data': data
            })

            self.stats['queued'] += 1
            logger.debug(f"📤 Resultado agregado a cola: {athlete_result.athlete.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error agregando resultado a cola: {e}")
            return False

    async def _worker(self):
        """
        Worker que procesa la cola de envíos

        Features:
        - Retry con exponential backoff (2s, 4s, 8s)
        - Continúa procesando si un envío falla
        - No bloquea el sistema local
        """
        logger.info("🔄 Worker de API iniciado")

        while True:
            try:
                # Esperar mensaje de la cola
                item = await self.queue.get()

                endpoint = item['endpoint']
                data = item['data']
                url = f"{self.api_url}{endpoint}"

                # Intentar enviar con retry
                success = False
                for attempt in range(3):
                    try:
                        async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status in [200, 201]:
                                self.stats['sent'] += 1
                                logger.debug(f"✓ Enviado a API: {item['type']} (intento {attempt + 1})")
                                success = True
                                break
                            else:
                                error_text = await response.text()
                                logger.warning(f"⚠️ API retornó {response.status}: {error_text}")

                    except asyncio.TimeoutError:
                        logger.warning(f"⏱️ Timeout enviando a API (intento {attempt + 1})")
                    except aiohttp.ClientError as e:
                        logger.warning(f"⚠️ Error de red (intento {attempt + 1}): {e}")
                    except Exception as e:
                        logger.error(f"❌ Error inesperado (intento {attempt + 1}): {e}")

                    if attempt < 2:
                        # Exponential backoff: 2s, 4s
                        await asyncio.sleep(2 ** (attempt + 1))

                if not success:
                    self.stats['failed'] += 1
                    logger.error(f"❌ Falló después de 3 intentos: {item['type']}")

                self.queue.task_done()

            except asyncio.CancelledError:
                logger.info("🛑 Worker de API cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error crítico en worker de API: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)  # Evitar loop infinito en caso de error

    async def sync_categories(self, categories: list) -> bool:
        """
        Sincronizar categorías al inicio del evento

        Args:
            categories: Lista de RaceCategory

        Returns:
            bool: True si se sincronizó exitosamente
        """
        if not self.enabled:
            return False

        try:
            data = {
                'event_id': self.event_id,
                'categories': [
                    {
                        'category_id': cat.category_id,
                        'name': cat.name,
                        'distance': cat.distance,
                        'expected_checkpoints': cat.expected_checkpoints,
                        'status': cat.status.value
                    }
                    for cat in categories
                ]
            }

            url = f"{self.api_url}/api/events/{self.event_id}/categories"

            async with self.session.post(url, json=data) as response:
                if response.status in [200, 201]:
                    logger.info("✅ Categorías sincronizadas con API")
                    return True
                else:
                    logger.error(f"❌ Error sincronizando categorías: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error sincronizando categorías: {e}")
            return False

    async def sync_athletes(self, category_id: str, athletes: list) -> bool:
        """
        Sincronizar atletas de una categoría

        Args:
            category_id: ID de la categoría
            athletes: Lista de Athlete

        Returns:
            bool: True si se sincronizó exitosamente
        """
        if not self.enabled:
            return False

        try:
            data = {
                'category_id': category_id,
                'athletes': [
                    {
                        'athlete_id': athlete.athlete_id,
                        'tag_id': athlete.tag_id,
                        'bib_number': athlete.bib_number,
                        'name': athlete.name,
                        'team': athlete.team
                    }
                    for athlete in athletes
                ]
            }

            url = f"{self.api_url}/api/events/{self.event_id}/athletes"

            async with self.session.post(url, json=data) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Atletas sincronizados con API: {len(athletes)} en {category_id}")
                    return True
                else:
                    logger.error(f"❌ Error sincronizando atletas: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error sincronizando atletas: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cliente

        Returns:
            dict: Estadísticas de envío
        """
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'enabled': self.enabled,
            'connected': self.session is not None and not self.session.closed
        }
