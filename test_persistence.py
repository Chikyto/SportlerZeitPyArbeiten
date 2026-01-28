#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de persistencia de datos
Verifica que los datos se guarden y carguen correctamente
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.race_tracking.race_manager import RaceManager
from src.core.race_tracking.models import RaceCategory, Athlete
from src.core.race_data_persistence import RaceDataPersistence


def test_save_load():
    """Test básico de guardar y cargar"""
    print("=" * 60)
    print("TEST DE PERSISTENCIA")
    print("=" * 60)
    print()

    # Crear race manager con datos de prueba
    print("1. Creando datos de prueba...")
    race_manager = RaceManager()

    # Crear categoría
    cat = RaceCategory(
        category_id="5k",
        name="5 Kilómetros",
        distance=5000.0
    )

    # Agregar atletas
    athlete1 = Athlete(
        athlete_id="1",
        bib_number=1,
        name="Juan Pérez",
        category_id="5k",
        tag_id="8587"  # Chip asignado
    )

    athlete2 = Athlete(
        athlete_id="2",
        bib_number=2,
        name="María González",
        category_id="5k",
        tag_id=""  # Sin chip
    )

    cat.add_participant(athlete1)
    cat.add_participant(athlete2)
    race_manager.add_category(cat)

    print(f"   ✅ Creados: 1 categoría, 2 atletas")
    print(f"   ✅ Atleta 1: {athlete1.name} - Chip: {athlete1.tag_id}")
    print(f"   ✅ Atleta 2: {athlete2.name} - Chip: {athlete2.tag_id or 'Sin asignar'}")
    print()

    # Guardar
    print("2. Guardando datos...")
    persistence = RaceDataPersistence(data_dir="data_test")
    success = persistence.save_race_data(race_manager)

    if success:
        print(f"   ✅ Datos guardados en: {persistence.data_file}")
    else:
        print("   ❌ Error guardando")
        return False
    print()

    # Cargar en nuevo race manager
    print("3. Cargando datos en nuevo RaceManager...")
    race_manager2 = RaceManager()
    success = persistence.load_race_data(race_manager2)

    if not success:
        print("   ❌ Error cargando")
        return False
    print()

    # Verificar datos
    print("4. Verificando datos cargados...")
    categories = race_manager2.get_all_categories()

    if len(categories) != 1:
        print(f"   ❌ Error: esperaba 1 categoría, encontró {len(categories)}")
        return False

    cat = categories[0]
    if len(cat.participants) != 2:
        print(f"   ❌ Error: esperaba 2 atletas, encontró {len(cat.participants)}")
        return False

    athlete1_loaded = cat.participants[0]
    athlete2_loaded = cat.participants[1]

    print(f"   ✅ Categoría: {cat.name}")
    print(f"   ✅ Atleta 1: {athlete1_loaded.name} - Chip: {athlete1_loaded.tag_id}")
    print(f"   ✅ Atleta 2: {athlete2_loaded.name} - Chip: {athlete2_loaded.tag_id or 'Sin asignar'}")
    print()

    # Verificar chips
    if athlete1_loaded.tag_id != "8587":
        print(f"   ❌ Error: chip de atleta 1 no coincide")
        return False

    if athlete2_loaded.has_chip_assigned():
        print(f"   ❌ Error: atleta 2 no debería tener chip")
        return False

    print("=" * 60)
    print("✅ TEST EXITOSO")
    print("=" * 60)
    print()
    print("La persistencia funciona correctamente!")
    print("- Datos guardados en JSON")
    print("- Datos cargados correctamente")
    print("- Chips asignados preservados")
    print()

    # Limpiar archivos de test
    import shutil
    if os.path.exists("data_test"):
        shutil.rmtree("data_test")
        print("🗑️  Archivos de test limpiados")

    return True


if __name__ == "__main__":
    success = test_save_load()
    sys.exit(0 if success else 1)
