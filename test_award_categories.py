#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el sistema de categorías de premiación
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.race_tracking.models import (
    Athlete, RaceCategory, AthleteResult, AthleteStatus,
    AwardCategory, create_iaaf_award_categories
)
from src.core.race_tracking.race_manager import RaceManager

def test_award_categories():
    """Prueba del sistema de categorías de premiación"""

    print("=" * 80)
    print("PRUEBA: Sistema de Categorías de Premiación")
    print("=" * 80)

    # 1. Crear Race Manager (carga IAAF por defecto)
    print("\n1️⃣  Creando RaceManager con categorías IAAF...")
    manager = RaceManager(load_iaaf_categories=True)

    award_cats = manager.get_all_award_categories()
    print(f"   ✅ {len(award_cats)} categorías IAAF cargadas")

    # Mostrar algunas categorías IAAF
    print("\n   📋 Categorías IAAF de muestra:")
    for cat in award_cats[:5]:
        print(f"      - {cat.award_category_id}: {cat.name} ({cat.get_age_range_str()} años)")
    print(f"      ... y {len(award_cats) - 5} más")

    # 2. Crear una categoría de carrera (21K)
    print("\n2️⃣  Creando categoría de carrera (21K)...")

    # Crear atletas de ejemplo con género y edad
    athletes = [
        Athlete(
            tag_id="1001",
            bib_number=101,
            name="Juan Pérez",
            category_id="21k",
            gender="M",
            birth_date=datetime(1990, 5, 15),  # 35 años
            team="Club A"
        ),
        Athlete(
            tag_id="1002",
            bib_number=102,
            name="María González",
            category_id="21k",
            gender="F",
            birth_date=datetime(1995, 8, 20),  # 30 años
            team="Club B"
        ),
        Athlete(
            tag_id="1003",
            bib_number=103,
            name="Carlos López",
            category_id="21k",
            gender="M",
            birth_date=datetime(1985, 3, 10),  # 40 años
            team="Club A"
        ),
        Athlete(
            tag_id="1004",
            bib_number=104,
            name="Ana Martínez",
            category_id="21k",
            gender="F",
            birth_date=datetime(1988, 11, 5),  # 37 años
            team="Club C"
        ),
        Athlete(
            tag_id="1005",
            bib_number=105,
            name="Pedro Sánchez",
            category_id="21k",
            gender="M",
            birth_date=datetime(2005, 7, 25),  # 20 años
            team="Club D"
        ),
    ]

    race_category = RaceCategory(
        category_id="21k",
        name="Media Maratón 21K",
        distance=21000.0,
        expected_checkpoints=2,
        participants=athletes
    )

    manager.add_category(race_category)
    print(f"   ✅ Categoría de carrera creada: {race_category.name}")
    print(f"   👥 {len(athletes)} atletas registrados")

    # Mostrar atletas y su categoría IAAF
    print("\n   📋 Atletas y sus categorías de premiación:")
    for athlete in athletes:
        age = athlete.get_age()
        award_cat_id = athlete.get_award_category()
        print(f"      - {athlete.name} ({athlete.gender}, {age} años) → {award_cat_id}")

    # 3. Simular una carrera
    print("\n3️⃣  Simulando carrera...")
    manager.start_category("21k")

    # Simular tiempos de llegada
    start_time = datetime.now()
    finish_times = [
        (athletes[0], timedelta(hours=1, minutes=45, seconds=30)),  # Juan
        (athletes[1], timedelta(hours=1, minutes=52, seconds=15)),  # María
        (athletes[2], timedelta(hours=1, minutes=58, seconds=45)),  # Carlos
        (athletes[3], timedelta(hours=2, minutes=5, seconds=10)),   # Ana
        (athletes[4], timedelta(hours=1, minutes=42, seconds=5)),   # Pedro (más rápido)
    ]

    for athlete, delta in finish_times:
        result = manager.results["21k"][athlete.athlete_id]
        result.record_start(start_time)
        result.record_finish(start_time + delta)

    print("   ✅ Carrera simulada, todos los atletas finalizaron")

    # 4. Obtener clasificación general
    print("\n4️⃣  Clasificación General:")
    results = manager.get_results("21k")
    for i, result in enumerate(results[:5], 1):
        print(f"      {i}. {result.athlete.name} - {result.get_formatted_time()}")

    # 5. Obtener podios por categoría de premiación
    print("\n5️⃣  Podios por Categoría de Premiación:")
    podiums = manager.get_podium_by_award_category("21k", top_n=3)

    for award_cat_id, podium in sorted(podiums.items()):
        if len(podium) == 0:
            continue

        award_cat = manager.get_award_category(award_cat_id)
        print(f"\n   🏆 {award_cat.name}:")

        for position, result in podium:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(position, f"{position}°")
            print(f"      {medal} {result.athlete.name} - {result.get_formatted_time()}")

    # 6. Crear una categoría personalizada
    print("\n6️⃣  Creando categoría personalizada...")

    custom_cat = AwardCategory(
        award_category_id="M30-40-21K",
        name="Masculino Master Especial 30-40 (solo 21K)",
        gender="M",
        min_age=30,
        max_age=40,
        race_category_ids=["21k"],  # Solo para 21K
        is_iaaf=False,
        description="Categoría personalizada para hombres de 30 a 40 años en 21K"
    )

    manager.add_award_category(custom_cat)
    print(f"   ✅ Categoría personalizada creada: {custom_cat.name}")

    # Ver podio de categoría personalizada
    podiums_custom = manager.get_podium_by_award_category("21k", top_n=3)
    if custom_cat.award_category_id in podiums_custom:
        podium = podiums_custom[custom_cat.award_category_id]
        print(f"\n   🏆 Podio de categoría personalizada:")
        for position, result in podium:
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(position, f"{position}°")
            print(f"      {medal} {result.athlete.name} - {result.get_formatted_time()}")

    # 7. Estadísticas finales
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL")
    print("=" * 80)
    print(f"Categorías de carrera: {len(manager.get_all_categories())}")
    print(f"Categorías de premiación: {len(manager.get_all_award_categories())}")
    print(f"  - IAAF: {sum(1 for c in manager.get_all_award_categories() if c.is_iaaf)}")
    print(f"  - Personalizadas: {sum(1 for c in manager.get_all_award_categories() if not c.is_iaaf)}")
    print(f"Atletas totales: {len(athletes)}")
    print(f"Categorías de premiación con podios: {len([p for p in podiums.values() if len(p) > 0])}")

    print("\n" + "=" * 80)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 80)


if __name__ == "__main__":
    test_award_categories()
