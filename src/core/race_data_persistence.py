#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Race Data Persistence Manager
src/core/race_data_persistence.py

Handles automatic saving/loading of race data to prevent data loss.
Saves athlete registrations and chip assignments locally.
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RaceDataPersistence:
    """
    Manages automatic persistence of race data to local storage

    Features:
    - Auto-save on every chip assignment
    - Auto-load on app startup
    - Backup files (.bak)
    - JSON format for readability
    """

    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: Directory for storing race data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.data_file = self.data_dir / "race_data.json"
        self.backup_file = self.data_dir / "race_data.bak"

        logger.info(f"💾 Persistencia configurada: {self.data_file}")

    def save_race_data(self, race_manager) -> bool:
        """
        Save complete race data to JSON file

        Args:
            race_manager: RaceManager instance with all categories and athletes

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build data structure
            data = {
                'metadata': {
                    'saved_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'app': 'SportlerZeit RFID'
                },
                'categories': [],
                'statistics': {
                    'total_athletes': 0,
                    'total_categories': 0,
                    'chips_assigned': 0
                }
            }

            total_athletes = 0
            chips_assigned = 0

            # Serialize categories and athletes
            for category in race_manager.get_all_categories():
                category_data = {
                    'distance_id': category.distance_id,
                    'name': category.name,
                    'distance_meters': category.distance_meters,
                    'expected_checkpoints': category.expected_checkpoints,
                    'notes': category.notes,
                    'start_time': category.start_time.isoformat() if category.start_time else None,
                    'athletes': []
                }

                for athlete in category.participants:
                    athlete_data = {
                        'athlete_id': athlete.athlete_id,
                        'bib_number': athlete.bib_number,
                        'name': athlete.name,
                        'tag_id': athlete.tag_id,
                        'team': athlete.team,
                        'notes': athlete.notes
                    }
                    category_data['athletes'].append(athlete_data)
                    total_athletes += 1

                    if athlete.has_chip_assigned():
                        chips_assigned += 1

                data['categories'].append(category_data)

            # Update statistics
            data['statistics']['total_athletes'] = total_athletes
            data['statistics']['total_categories'] = len(data['categories'])
            data['statistics']['chips_assigned'] = chips_assigned

            # Create backup of existing file
            if self.data_file.exists():
                shutil.copy2(self.data_file, self.backup_file)
                logger.debug(f"📦 Backup creado: {self.backup_file}")

            # Write to file with indentation for readability
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Datos guardados: {total_athletes} atletas, {chips_assigned} chips asignados")
            return True

        except Exception as e:
            logger.error(f"❌ Error guardando datos: {e}")
            return False

    def load_race_data(self, race_manager) -> bool:
        """
        Load race data from JSON file and populate race_manager

        Args:
            race_manager: RaceManager instance to populate

        Returns:
            True if data was loaded, False if no data exists or error
        """
        if not self.data_file.exists():
            logger.info("ℹ️  No hay datos guardados previos")
            return False

        try:
            logger.info(f"📂 Cargando datos desde: {self.data_file}")

            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate data structure
            if 'categories' not in data:
                logger.warning("⚠️  Archivo de datos inválido")
                return False

            # Import categories and athletes
            from .race_tracking.models import RaceDistance, Athlete

            total_athletes = 0
            chips_assigned = 0

            for cat_data in data['categories']:
                # Create category (soporta ambos: distance_id y category_id por compatibilidad)
                category = RaceDistance(
                    distance_id=cat_data.get('distance_id', cat_data.get('category_id', '')),
                    name=cat_data['name'],
                    distance_meters=cat_data.get('distance_meters', cat_data.get('distance', 0.0)),
                    expected_checkpoints=cat_data.get('expected_checkpoints', 0),
                    notes=cat_data.get('notes')
                )

                # Add athletes
                for athlete_data in cat_data['athletes']:
                    athlete = Athlete(
                        athlete_id=athlete_data['athlete_id'],
                        bib_number=athlete_data['bib_number'],
                        name=athlete_data['name'],
                        distance_id=cat_data.get('distance_id', cat_data.get('category_id', '')),
                        tag_id=athlete_data.get('tag_id', ''),
                        team=athlete_data.get('team'),
                        notes=athlete_data.get('notes')
                    )

                    category.add_participant(athlete)
                    total_athletes += 1

                    if athlete.has_chip_assigned():
                        chips_assigned += 1

                # Add category to race manager
                race_manager.add_category(category)

            # Log metadata if available
            if 'metadata' in data:
                saved_at = data['metadata'].get('saved_at', 'unknown')
                logger.info(f"📅 Datos del: {saved_at}")

            logger.info(f"✅ Datos cargados: {total_athletes} atletas, {chips_assigned} chips asignados")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error leyendo JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            return False

    def has_saved_data(self) -> bool:
        """Check if there is saved data available"""
        return self.data_file.exists()

    def get_last_save_time(self) -> Optional[datetime]:
        """Get timestamp of last save"""
        if not self.data_file.exists():
            return None

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'metadata' in data and 'saved_at' in data['metadata']:
                return datetime.fromisoformat(data['metadata']['saved_at'])

        except Exception as e:
            logger.debug(f"Error obteniendo timestamp: {e}")

        return None

    def restore_from_backup(self, race_manager) -> bool:
        """
        Restore data from backup file

        Args:
            race_manager: RaceManager instance to populate

        Returns:
            True if backup was restored successfully
        """
        if not self.backup_file.exists():
            logger.warning("⚠️  No hay archivo de backup disponible")
            return False

        try:
            logger.info(f"🔄 Restaurando desde backup: {self.backup_file}")

            # Copy backup to main file
            shutil.copy2(self.backup_file, self.data_file)

            # Load from restored file
            return self.load_race_data(race_manager)

        except Exception as e:
            logger.error(f"❌ Error restaurando backup: {e}")
            return False

    def clear_data(self) -> bool:
        """Delete saved data files (use with caution!)"""
        try:
            if self.data_file.exists():
                self.data_file.unlink()
                logger.info("🗑️  Datos borrados")

            if self.backup_file.exists():
                self.backup_file.unlink()
                logger.info("🗑️  Backup borrado")

            return True

        except Exception as e:
            logger.error(f"❌ Error borrando datos: {e}")
            return False
