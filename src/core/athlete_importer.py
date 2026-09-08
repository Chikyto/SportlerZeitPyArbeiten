#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador de atletas desde el backend SportlerZeit
src/core/athlete_importer.py
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10


class AthleteImporter:
    """
    Importa atletas desde el backend SportlerZeit.

    Args:
        base_url: URL base de la API, ej. "https://api.sportlerzeit.com.ar/api/v1"
                  NO debe terminar en "/".
        api_key:  Token de autenticación (Bearer), si corresponde.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.session.headers.update({"Content-Type": "application/json"})

    def import_athletes(self, event_id: str) -> Dict[str, List[dict]]:
        """
        Importar atletas de un evento agrupados por distance_id.

        Args:
            event_id: ID del evento en el backend.

        Returns:
            Dict {distance_id: [athlete_dict, ...]}.
            Cada athlete_dict tiene al menos: tag_id, bib_number, name,
            distance_id y opcionalmente gender, category, team.

        Raises:
            requests.HTTPError: si el servidor responde con 4xx/5xx.
            requests.ConnectionError: si no hay red.
        """
        # base_url ya contiene /api/v1; el path correcto es /events/... (sin /api/ extra)
        url = f"{self.base_url}/events/{event_id}/athletes"
        logger.info(f"Importando atletas desde {url}")

        response = self.session.get(url, timeout=_DEFAULT_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # El backend puede devolver una lista directa o {"athletes": [...]}
        if isinstance(data, dict):
            athletes_list = data.get("athletes", data.get("data", []))
        else:
            athletes_list = data

        athletes_by_dist: Dict[str, List[dict]] = {}
        for athlete in athletes_list:
            dist_id = str(athlete.get("distance_id", athlete.get("category_id", "default")))
            athletes_by_dist.setdefault(dist_id, []).append(athlete)

        total = sum(len(v) for v in athletes_by_dist.values())
        logger.info(
            f"✅ {total} atletas importados en {len(athletes_by_dist)} distancia(s)"
        )
        return athletes_by_dist

    def fetch_event_info(self, event_id: str) -> dict:
        """
        Obtener metadatos del evento (nombre, fecha, distancias).

        Returns:
            dict con la información del evento o {} si falla.
        """
        url = f"{self.base_url}/events/{event_id}"
        try:
            response = self.session.get(url, timeout=_DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning(f"No se pudo obtener info del evento: {exc}")
            return {}

    def close(self):
        self.session.close()
