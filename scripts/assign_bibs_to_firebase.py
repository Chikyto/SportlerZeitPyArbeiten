#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Asignar Dorsales en Firebase
scripts/assign_bibs_to_firebase.py

IMPORTANTE: Ejecutar UNA VEZ antes del evento para asignar dorsales
a todos los atletas registrados en Firebase.

Uso:
    python scripts/assign_bibs_to_firebase.py

Requiere:
    pip install firebase-admin requests

Este script:
1. Se conecta a Firebase via Cloud Run API
2. Obtiene todos los atletas registrados
3. Asigna dorsales automáticamente por categoría
4. Actualiza Firebase con los dorsales
5. Genera lista imprimible
"""

import sys
import os
import logging
import json
import requests
from pathlib import Path
from typing import Dict, List
from colorama import init, Fore, Style

# Inicializar colorama
init(autoreset=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


class BibNumberAssigner:
    """
    Asignador de dorsales para Firebase

    Conecta con Cloud Run API, asigna dorsales y actualiza Firebase
    """

    # Rangos de dorsales por categoría
    BIB_RANGES = {
        '5K': 1,      # 1-999
        '10K': 1000,  # 1000-1999
        '21K': 2000,  # 2000-2999
        '30K': 3000,  # 3000-3999
        '42K': 4000,  # 4000-4999
        '50K': 5000,  # 5000-5999
        '100K': 6000, # 6000-6999
    }

    def __init__(self, api_url: str, api_key: str = None):
        """
        Inicializar asignador

        Args:
            api_url: URL de Cloud Run (ej: https://your-api.run.app)
            api_key: API key para autenticación (opcional)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def get_athletes(self, event_id: str) -> List[Dict]:
        """
        Obtener atletas desde Firebase via Cloud Run

        Args:
            event_id: ID del evento

        Returns:
            List[Dict]: Lista de atletas
        """
        print(f"{Fore.CYAN}📥 Obteniendo atletas desde Cloud Run...")

        url = f"{self.api_url}/api/events/{event_id}/athletes"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Ajustar según estructura de tu API
            if isinstance(data, dict) and 'athletes' in data:
                athletes = data['athletes']
            elif isinstance(data, dict) and 'data' in data and 'athletes' in data['data']:
                athletes = data['data']['athletes']
            elif isinstance(data, list):
                athletes = data
            else:
                raise ValueError(f"Formato de respuesta no esperado: {type(data)}")

            print(f"{Fore.GREEN}✅ {len(athletes)} atletas obtenidos")
            return athletes

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Error conectando a API: {e}")
            raise

    def assign_bib_numbers(self, athletes: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Asignar dorsales a atletas

        Args:
            athletes: Lista de atletas

        Returns:
            Dict: Atletas agrupados por categoría con dorsales asignados
        """
        print(f"\n{Fore.CYAN}🔢 Asignando dorsales...")

        # Agrupar por categoría/distancia
        by_category = {}
        bib_counters = {}

        for athlete in athletes:
            # Obtener categoría/distancia
            # AJUSTAR según los campos de tu Firebase
            distancia = athlete.get('Distancia', athlete.get('distancia', athlete.get('category', ''))).strip().upper()

            if not distancia:
                print(f"{Fore.YELLOW}⚠️  Atleta sin distancia: {athlete.get('Nombre', 'Unknown')}")
                continue

            # Normalizar distancia
            if 'KM' in distancia:
                distancia = distancia.replace('KM', 'K').replace('km', 'K')

            # Inicializar categoría
            if distancia not in by_category:
                by_category[distancia] = []
                # Obtener base de dorsales
                bib_counters[distancia] = self.BIB_RANGES.get(distancia, 1)

            # Asignar dorsal si no tiene
            current_bib = athlete.get('Pecho', athlete.get('pecho', athlete.get('bib_number', '')))

            if not current_bib or current_bib == '':
                # Asignar nuevo dorsal
                new_bib = bib_counters[distancia]
                athlete['bib_number'] = new_bib
                athlete['needs_update'] = True
                bib_counters[distancia] += 1
            else:
                # Ya tiene dorsal
                athlete['bib_number'] = int(current_bib)
                athlete['needs_update'] = False

            by_category[distancia].append(athlete)

        # Ordenar por dorsal
        for category in by_category.values():
            category.sort(key=lambda a: a['bib_number'])

        print(f"{Fore.GREEN}✅ Dorsales asignados\n")

        # Mostrar resumen
        for category, athletes_list in by_category.items():
            needs_update = sum(1 for a in athletes_list if a.get('needs_update'))
            print(f"  {Fore.WHITE}• {category}: {len(athletes_list)} atletas")
            print(f"    Dorsales: {athletes_list[0]['bib_number']} - {athletes_list[-1]['bib_number']}")
            if needs_update > 0:
                print(f"    {Fore.YELLOW}Nuevos: {needs_update}")

        return by_category

    def update_firebase(self, event_id: str, athletes_by_category: Dict) -> bool:
        """
        Actualizar Firebase con dorsales asignados

        Args:
            event_id: ID del evento
            athletes_by_category: Atletas con dorsales

        Returns:
            bool: True si exitoso
        """
        print(f"\n{Fore.CYAN}💾 Actualizando Firebase...")

        # Endpoint para actualizar dorsales
        # AJUSTAR según tu API - puede ser:
        # POST /api/events/{event_id}/assign-bibs
        # PATCH /api/athletes/bulk-update
        # etc.

        url = f"{self.api_url}/api/events/{event_id}/assign-bibs"

        # Preparar datos
        updates = []
        for category, athletes in athletes_by_category.items():
            for athlete in athletes:
                if athlete.get('needs_update'):
                    updates.append({
                        'id': athlete.get('id'),  # AJUSTAR campo ID según tu Firebase
                        'bib_number': athlete['bib_number'],
                        'pecho': athlete['bib_number']  # Actualizar campo "Pecho"
                    })

        if not updates:
            print(f"{Fore.GREEN}✅ No hay dorsales para actualizar (todos ya asignados)")
            return True

        print(f"  Actualizando {len(updates)} atletas...")

        try:
            response = self.session.post(
                url,
                json={'updates': updates},
                timeout=60
            )

            response.raise_for_status()

            print(f"{Fore.GREEN}✅ Firebase actualizado exitosamente")
            return True

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Error actualizando Firebase: {e}")
            print(f"\n{Fore.YELLOW}IMPORTANTE:")
            print(f"  El endpoint de actualización debe existir en tu Cloud Run:")
            print(f"  POST {url}")
            print(f"\n  Estructura esperada:")
            print(f"  {{'updates': [{{'id': '...', 'bib_number': 123}}]}}")
            return False

    def export_bib_list(self, athletes_by_category: Dict, output_path: str):
        """
        Exportar lista de dorsales

        Args:
            athletes_by_category: Atletas con dorsales
            output_path: Ruta del archivo
        """
        import csv

        print(f"\n{Fore.CYAN}📄 Generando lista de dorsales...")

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(['Dorsal', 'Nombre', 'Apellido', 'Categoría', 'Email', 'Teléfono'])

            # Ordenar todos por dorsal
            all_athletes = []
            for category, athletes in athletes_by_category.items():
                for athlete in athletes:
                    athlete['_category'] = category
                    all_athletes.append(athlete)

            all_athletes.sort(key=lambda a: a['bib_number'])

            # Escribir filas
            for athlete in all_athletes:
                writer.writerow([
                    athlete['bib_number'],
                    athlete.get('Nombre', athlete.get('nombre', '')),
                    athlete.get('Apellido', athlete.get('apellido', '')),
                    athlete['_category'],
                    athlete.get('Email', athlete.get('email', '')),
                    athlete.get('Teléfono', athlete.get('telefono', ''))
                ])

        print(f"{Fore.GREEN}✅ Lista exportada: {output_path}")


def main():
    """Main function"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🔢 ASIGNADOR DE DORSALES - Firebase/Cloud Run")
    print(f"{Fore.CYAN}{'='*70}\n")

    # Cargar configuración
    config_path = Path('config/firebase_config.json')

    if not config_path.exists():
        print(f"{Fore.RED}❌ No se encontró config/firebase_config.json")
        print(f"\n{Fore.YELLOW}Crear archivo con:")
        print(f"""
{{
  "cloud_run_url": "https://your-backend.run.app",
  "event_id": "ultra-2025",
  "api_key": null
}}
        """)
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Crear asignador
    assigner = BibNumberAssigner(
        api_url=config['cloud_run_url'],
        api_key=config.get('api_key')
    )

    try:
        # 1. Obtener atletas
        athletes = assigner.get_athletes(event_id=config['event_id'])

        if not athletes:
            print(f"{Fore.RED}❌ No se obtuvieron atletas")
            sys.exit(1)

        # 2. Asignar dorsales
        athletes_by_category = assigner.assign_bib_numbers(athletes)

        # 3. Actualizar Firebase
        success = assigner.update_firebase(config['event_id'], athletes_by_category)

        if not success:
            print(f"\n{Fore.YELLOW}⚠️  No se actualizó Firebase automáticamente")
            print(f"   Opción 1: Implementar endpoint de actualización en Cloud Run")
            print(f"   Opción 2: Actualizar manualmente desde Firebase Console")

        # 4. Exportar lista
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        bib_list_path = output_dir / 'lista_dorsales.csv'
        assigner.export_bib_list(athletes_by_category, str(bib_list_path))

        # 5. Resumen final
        total = sum(len(a) for a in athletes_by_category.values())

        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ PROCESO COMPLETO")
        print(f"{Fore.GREEN}{'='*70}\n")
        print(f"  • {total} atletas procesados")
        print(f"  • {len(athletes_by_category)} categorías")
        print(f"  • Lista generada: {bib_list_path}")
        print()

        if success:
            print(f"{Fore.GREEN}✅ Firebase actualizado - Dorsales guardados")
        else:
            print(f"{Fore.YELLOW}⚠️  Revisar actualización de Firebase")

        print()

    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
