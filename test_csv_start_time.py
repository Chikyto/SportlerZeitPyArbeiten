#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de extracción de hora de largada desde CSV
Verifica que los datos de hora se importen correctamente
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.csv_importer import CSVAthleteImporter
from datetime import datetime


def test_with_start_time():
    """Test con CSV que incluye hora de largada"""
    print("=" * 60)
    print("TEST: CSV CON HORA DE LARGADA")
    print("=" * 60)
    print()

    # CSV con hora de largada
    csv_data = """Nombre,Apellido,Email,DNI,Fecha Nacimiento,Género,Distancia,N° Pecho,Hora Largada
Juan,Pérez,juan@test.com,12345678,01/01/1990,M,5K,1,28/01/2026 08:00:00
María,González,maria@test.com,87654321,15/06/1992,F,5K,2,28/01/2026 08:00:00
Pedro,López,pedro@test.com,11223344,20/03/1988,M,10K,1001,28/01/2026 09:30:00"""

    print("1. Importando CSV con hora de largada...")
    importer = CSVAthleteImporter()

    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_data)
        temp_path = f.name

    try:
        athletes_by_cat = importer.import_from_csv(temp_path, filter_approved=False)
        imported = sum(len(athletes) for athletes in athletes_by_cat.values())
        print(f"   ✅ {imported} atletas importados")
        print()
    finally:
        Path(temp_path).unlink()  # Cleanup

    print("2. Verificando horas de largada capturadas...")
    if '5k' in importer.category_start_times:
        start_5k = importer.category_start_times['5k']
        print(f"   ✅ 5K: {start_5k}")

        # Verificar que es datetime
        if isinstance(start_5k, datetime):
            print(f"   ✅ Tipo correcto: datetime")
            expected = datetime(2026, 1, 28, 8, 0, 0)
            if start_5k == expected:
                print(f"   ✅ Hora correcta: 08:00:00")
            else:
                print(f"   ❌ Error: esperaba {expected}, obtuvo {start_5k}")
                return False
        else:
            print(f"   ❌ Error: tipo incorrecto {type(start_5k)}")
            return False
    else:
        print("   ❌ Error: no se capturó hora de largada para 5K")
        return False

    if '10k' in importer.category_start_times:
        start_10k = importer.category_start_times['10k']
        print(f"   ✅ 10K: {start_10k}")

        expected = datetime(2026, 1, 28, 9, 30, 0)
        if start_10k == expected:
            print(f"   ✅ Hora correcta: 09:30:00")
        else:
            print(f"   ❌ Error: esperaba {expected}, obtuvo {start_10k}")
            return False
    else:
        print("   ❌ Error: no se capturó hora de largada para 10K")
        return False

    print()
    print("3. Creando categorías con hora de largada...")
    categories = importer.create_categories()

    if len(categories) != 2:
        print(f"   ❌ Error: esperaba 2 categorías, obtuvo {len(categories)}")
        return False

    cat_5k = next((c for c in categories if c.category_id == '5k'), None)
    cat_10k = next((c for c in categories if c.category_id == '10k'), None)

    if not cat_5k:
        print("   ❌ Error: no se encontró categoría 5K")
        return False

    if not cat_10k:
        print("   ❌ Error: no se encontró categoría 10K")
        return False

    if cat_5k.start_time:
        print(f"   ✅ 5K tiene start_time: {cat_5k.start_time.strftime('%H:%M')}")
    else:
        print("   ❌ Error: 5K no tiene start_time")
        return False

    if cat_10k.start_time:
        print(f"   ✅ 10K tiene start_time: {cat_10k.start_time.strftime('%H:%M')}")
    else:
        print("   ❌ Error: 10K no tiene start_time")
        return False

    print()
    print("=" * 60)
    print("✅ TEST EXITOSO - CSV CON HORA DE LARGADA")
    print("=" * 60)
    return True


def test_without_start_time():
    """Test con CSV que NO incluye hora de largada"""
    print()
    print("=" * 60)
    print("TEST: CSV SIN HORA DE LARGADA")
    print("=" * 60)
    print()

    # CSV sin hora de largada
    csv_data = """Nombre,Apellido,Email,DNI,Fecha Nacimiento,Género,Distancia,N° Pecho
Carlos,Ramírez,carlos@test.com,99887766,10/10/1985,M,5K,3
Ana,Martínez,ana@test.com,66778899,25/12/1995,F,5K,4"""

    print("1. Importando CSV sin hora de largada...")
    importer = CSVAthleteImporter()

    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_data)
        temp_path = f.name

    try:
        athletes_by_cat = importer.import_from_csv(temp_path, filter_approved=False)
        imported = sum(len(athletes) for athletes in athletes_by_cat.values())
        print(f"   ✅ {imported} atletas importados")
        print()
    finally:
        Path(temp_path).unlink()  # Cleanup

    print("2. Verificando que no se capturó hora de largada...")
    if '5k' in importer.category_start_times:
        start_time = importer.category_start_times['5k']
        if start_time is None:
            print(f"   ✅ 5K sin hora de largada (None)")
        else:
            print(f"   ❌ Error: esperaba None, obtuvo {start_time}")
            return False
    print()

    print("3. Creando categorías sin hora de largada...")
    categories = importer.create_categories()

    cat_5k = next((c for c in categories if c.category_id == '5k'), None)

    if not cat_5k:
        print("   ❌ Error: no se encontró categoría 5K")
        return False

    if cat_5k.start_time is None:
        print(f"   ✅ 5K sin start_time (debe configurarse manualmente)")
    else:
        print(f"   ❌ Error: esperaba None, obtuvo {cat_5k.start_time}")
        return False

    print()
    print("=" * 60)
    print("✅ TEST EXITOSO - CSV SIN HORA DE LARGADA")
    print("=" * 60)
    return True


def test_different_formats():
    """Test con diferentes formatos de fecha"""
    print()
    print("=" * 60)
    print("TEST: DIFERENTES FORMATOS DE FECHA")
    print("=" * 60)
    print()

    formats_to_test = [
        ("dd/mm/yyyy HH:MM:SS", "28/01/2026 08:00:00", datetime(2026, 1, 28, 8, 0, 0)),
        ("dd/mm/yyyy HH:MM", "28/01/2026 08:00", datetime(2026, 1, 28, 8, 0, 0)),
        ("yyyy-mm-dd HH:MM:SS", "2026-01-28 08:00:00", datetime(2026, 1, 28, 8, 0, 0)),
        ("yyyy-mm-dd HH:MM", "2026-01-28 08:00", datetime(2026, 1, 28, 8, 0, 0)),
    ]

    for format_name, date_str, expected_dt in formats_to_test:
        print(f"Probando formato: {format_name}")

        csv_data = f"""Nombre,Apellido,Email,DNI,Fecha Nacimiento,Género,Distancia,N° Pecho,Hora Largada
Test,User,test@test.com,12345678,01/01/1990,M,5K,1,{date_str}"""

        importer = CSVAthleteImporter()

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            athletes_by_cat = importer.import_from_csv(temp_path, filter_approved=False)
        finally:
            Path(temp_path).unlink()  # Cleanup

        if '5k' in importer.category_start_times:
            start_time = importer.category_start_times['5k']
            if start_time == expected_dt:
                print(f"   ✅ {format_name}: {start_time}")
            else:
                print(f"   ❌ Error: esperaba {expected_dt}, obtuvo {start_time}")
                return False
        else:
            print(f"   ❌ Error: no se capturó hora para formato {format_name}")
            return False

    print()
    print("=" * 60)
    print("✅ TEST EXITOSO - DIFERENTES FORMATOS")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = True

    success = test_with_start_time() and success
    success = test_without_start_time() and success
    success = test_different_formats() and success

    print()
    print("=" * 60)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print()
        print("La extracción de hora de largada funciona correctamente!")
        print("- Extrae hora cuando está presente")
        print("- Maneja múltiples formatos de fecha")
        print("- Devuelve None cuando no hay hora")
        print("- Pasa hora a RaceCategory correctamente")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("=" * 60)

    sys.exit(0 if success else 1)
