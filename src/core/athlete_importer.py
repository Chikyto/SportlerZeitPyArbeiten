#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador de Atletas desde Sistema Web
src/core/athlete_importer.py

Importa atletas pre-registrados desde el backend Cloud Run
y los convierte al formato del sistema de timing local.
"""

import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import asdict

from src.core.race_tracking.models import Athlete, RaceDistance

logger = logging.getLogger(__name__)


class AthleteImporter:
    """
    Importador de atletas desde sistema web de pre-registro

    Conecta con el backend Cloud Run para obtener atletas registrados
    y los sincroniza con el sistema de timing local.

    Example:
        >>> importer = AthleteImporter("https://your-api.run.app")
        >>> athletes = await importer.import_athletes(event_id="ultra-2025")
        >>> for athlete in athletes:
        ...     category.add_participant(athlete)
    """

    def _parse_birth_date(self, fecha: str):
        if not fecha or not fecha.strip():
            return None
        from datetime import datetime
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                return datetime.strptime(fecha.strip(), fmt)
            except ValueError:
                continue
        return None

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Inicializar importador

        Args:
            api_url: URL del backend Cloud Run (ej: "https://api.run.app")
            api_key: API key para autenticación (opcional)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

        logger.info(f"🔌 AthleteImporter inicializado: {self.api_url}")

    def import_athletes(
        self,
        event_id: str,
        category_filter: Optional[str] = None
    ) -> Dict[str, List[Athlete]]:
        """
        Importar atletas desde el sistema web

        Args:
            event_id: ID del evento en el sistema web
            category_filter: Filtrar por categoría específica (opcional)

        Returns:
            Dict[category_id, List[Athlete]]: Atletas agrupados por categoría

        Raises:
            requests.RequestException: Si falla la conexión
            ValueError: Si los datos son inválidos
        """
        try:
            logger.info(f"📥 Importando atletas del evento {event_id}...")

            # Endpoint de tu API existente (ajustar según tu estructura)
            url = f"{self.api_url}/api/events/{event_id}/athletes"

            params = {}
            if category_filter:
                params['category'] = category_filter

            # Llamar a tu API
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Convertir respuesta a objetos Athlete
            athletes_by_category = self._parse_athletes(data)

            total_count = sum(len(athletes) for athletes in athletes_by_category.values())
            logger.info(f"✅ {total_count} atletas importados en {len(athletes_by_category)} categorías")

            return athletes_by_category

        except requests.RequestException as e:
            logger.error(f"❌ Error conectando a API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error importando atletas: {e}")
            raise

    def _parse_athletes(self, data: Any) -> Dict[str, List[Athlete]]:
        """
        Parsear respuesta de API a objetos Athlete

        Ajusta esta función según la estructura de tu API existente
        """
        athletes_by_category = {}

        # AJUSTAR SEGÚN TU ESTRUCTURA DE API
        # Ejemplo si tu API retorna: {"athletes": [...]}
        if isinstance(data, dict) and 'athletes' in data:
            athletes_data = data['athletes']
        elif isinstance(data, list):
            athletes_data = data
        else:
            raise ValueError(f"Formato de respuesta no esperado: {type(data)}")
        if athletes_data:
            logger.info(f"🔍 Raw primer atleta: {athletes_data[0]}")
        for athlete_data in athletes_data:
            try:
                # Extraer datos del atleta (ajustar campos según tu API)
                athlete = Athlete(
                    # ID único del atleta
                    athlete_id=athlete_data.get('id') or athlete_data.get('athlete_id'),

                    # Chip RFID (puede venir vacío si no fue asignado aún)
                    tag_id=athlete_data.get('chip_code') or athlete_data.get('chip_id') or athlete_data.get('rfid_tag') or '',

                    # Número de dorsal
                    bib_number=athlete_data.get('bib_number') or athlete_data.get('bib') or 0,

                    # Nombre completo
                    name=f"{athlete_data.get('first_name', '')} {athlete_data.get('last_name', '')}".strip()
                          or athlete_data.get('name', 'Unknown'),

                    # Categoría
                    distance_id=(athlete_data.get('category_id') or athlete_data.get('category') or '').lower(),

                    # Equipo (opcional)
                    team=athlete_data.get('team') or athlete_data.get('club'),

                    # Género (opcional)
                    gender=athlete_data.get('gender') or None,
                    
                    # Fecha de nacimiento (opcional, parsear si viene como string)
                    birth_date=self._parse_birth_date(athlete_data.get('birth_date', '')) if athlete_data.get('birth_date') else None,

                    # Notas adicionales (puedes guardar más info aquí)
                    notes=self._build_notes(athlete_data)
                    
                )

                # Agrupar por categoría
                category_id = athlete.distance_id
                if category_id not in athletes_by_category:
                    athletes_by_category[category_id] = []

                athletes_by_category[category_id].append(athlete)

                logger.debug(f"✓ Atleta importado: {athlete.name} (#{athlete.bib_number})")

            except Exception as e:
                logger.error(f"❌ Error parseando atleta {athlete_data}: {e}")
                continue

        return athletes_by_category

    def _build_notes(self, athlete_data: dict) -> str:
        """
        Construir notas con información adicional del atleta

        Puedes incluir: edad, género, distancia elegida, teléfono, etc.
        """
        notes_parts = []

        # Edad
        if 'age' in athlete_data:
            notes_parts.append(f"Edad: {athlete_data['age']}")
        elif 'birth_date' in athlete_data:
            # Calcular edad si tienes fecha de nacimiento
            try:
                birth_date = datetime.fromisoformat(athlete_data['birth_date'])
                age = (datetime.now() - birth_date).days // 365
                notes_parts.append(f"Edad: {age}")
            except:
                pass

        # Género
        if 'gender' in athlete_data:
            notes_parts.append(f"Género: {athlete_data['gender']}")

        # Email
        if 'email' in athlete_data:
            notes_parts.append(f"Email: {athlete_data['email']}")

        # Teléfono
        if 'phone' in athlete_data:
            notes_parts.append(f"Tel: {athlete_data['phone']}")

        # Contacto de emergencia
        if 'emergency_contact' in athlete_data:
            notes_parts.append(f"Emergencia: {athlete_data['emergency_contact']}")

        # Estado de pago
        if 'payment_status' in athlete_data:
            status = athlete_data['payment_status']
            notes_parts.append(f"Pago: {status}")

        # Cualquier otro dato relevante
        if 'medical_info' in athlete_data:
            notes_parts.append(f"Info médica: {athlete_data['medical_info']}")

        return " | ".join(notes_parts)

    def import_categories(self, event_id: str) -> List[RaceDistance]:
        """
        Importar categorías desde el sistema web

        Args:
            event_id: ID del evento

        Returns:
            List[RaceCategory]: Lista de categorías
        """
        try:
            logger.info(f"📥 Importando categorías del evento {event_id}...")

            url = f"{self.api_url}/api/events/{event_id}/categories"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            categories = []

            # Parsear categorías (ajustar según tu API)
            categories_data = data if isinstance(data, list) else data.get('categories', [])

            for cat_data in categories_data:
                try:
                    category = RaceDistance(
                        distance_id=cat_data.get('id') or cat_data.get('category_id'),
                        name=cat_data.get('name'),
                        distance=float(cat_data.get('distance_meters', 0) or cat_data.get('distance', 0)),
                        expected_checkpoints=int(cat_data.get('checkpoints', 0)),
                        participants=[],  # Se llenarán con import_athletes()
                        notes=cat_data.get('description') or cat_data.get('notes')
                    )
                    categories.append(category)
                    logger.debug(f"✓ Categoría importada: {category.name}")

                except Exception as e:
                    logger.error(f"❌ Error parseando categoría {cat_data}: {e}")
                    continue

            logger.info(f"✅ {len(categories)} categorías importadas")
            return categories

        except requests.RequestException as e:
            logger.error(f"❌ Error conectando a API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error importando categorías: {e}")
            raise

    def get_event_info(self, event_id: str) -> Dict[str, Any]:
        """
        Obtener información general del evento

        Args:
            event_id: ID del evento

        Returns:
            dict: Información del evento
        """
        try:
            url = f"{self.api_url}/api/events/{event_id}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Error obteniendo info del evento: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Probar conexión con el backend

        Returns:
            bool: True si la conexión funciona
        """
        try:
            # Endpoint de health check (ajustar según tu API)
            url = f"{self.api_url}/health"

            response = self.session.get(url, timeout=5)
            response.raise_for_status()

            logger.info("✅ Conexión con backend exitosa")
            return True

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Inicializar importador
    importer = AthleteImporter(
        api_url="https://your-backend.run.app",
        api_key="your-api-key-here"  # Si tu API requiere autenticación
    )

    # Probar conexión
    if importer.test_connection():
        # Importar categorías
        categories = importer.import_categories(event_id="ultra-2025")
        print(f"\n📋 Categorías importadas: {len(categories)}")
        for cat in categories:
            print(f"  - {cat.name} ({cat.distance}m)")

        # Importar atletas
        athletes_by_cat = importer.import_athletes(event_id="ultra-2025")
        print(f"\n👥 Atletas importados:")
        for cat_id, athletes in athletes_by_cat.items():
            print(f"  - {cat_id}: {len(athletes)} atletas")
            for athlete in athletes[:3]:  # Mostrar primeros 3
                print(f"    • {athlete.name} (#{athlete.bib_number})")
