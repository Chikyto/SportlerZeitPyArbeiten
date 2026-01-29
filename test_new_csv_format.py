#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del nuevo formato CSV con distancias en minúscula
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.csv_importer import CSVAthleteImporter


def test_new_csv_format():
    """Test con el CSV nuevo que tiene 24k, 14k, 7k en minúscula"""
    print("=" * 60)
    print("TEST: NUEVO FORMATO CSV (24k, 14k, 7k)")
    print("=" * 60)
    print()

    csv_data = """Nombre,Apellido,Email,DNI,Fecha Nacimiento,Género,Teléfono,Distancia,Estado Pago,Precio Total,Pagado Online,Pendiente Presencial,Presencial Pagado,Fecha Inscripción,N° Pecho
Adriana ,Bengolea ,adribengolea@hotmail.com,25755124,22/01/1977,F,5.43E+11,24k,approved,110000,58300,55000,No,27/01/2026,4
Adrian ,Bengo ,adribengolea@hotmail.com,25755124,22/01/1987,M,5.43E+11,14k,approved,110000,58300,55000,No,27/01/2026,2
Mariana ,Bengolea ,adribengolea@hotmail.com,25755124,22/01/1977,F,5.43E+11,7k,approved,110000,58300,55000,No,27/01/2026,3"""

    print("1. Importando CSV con distancias en minúscula (24k, 14k, 7k)...")
    importer = CSVAthleteImporter()

    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_data)
        temp_path = f.name

    try:
        athletes_by_cat = importer.import_from_csv(temp_path, filter_approved=True)
        imported = sum(len(athletes) for athletes in athletes_by_cat.values())

        print(f"   ✅ {imported} atletas importados")
        print()

        if imported == 0:
            print("   ❌ ERROR: No se importó ningún atleta!")
            return False

        print("2. Verificando categorías creadas...")
        for cat_id, athletes in athletes_by_cat.items():
            print(f"   - {cat_id}: {len(athletes)} atleta(s)")
            for athlete in athletes:
                print(f"     • {athlete.name} - Dorsal: {athlete.bib_number}")

        print()

        # Verificar que se crearon las 3 categorías
        if '24k' not in athletes_by_cat:
            print("   ❌ ERROR: Falta categoría 24k")
            return False
        if '14k' not in athletes_by_cat:
            print("   ❌ ERROR: Falta categoría 14k")
            return False
        if '7k' not in athletes_by_cat:
            print("   ❌ ERROR: Falta categoría 7k")
            return False

        print("   ✅ Todas las categorías creadas correctamente")
        print()

        print("3. Verificando dorsales del CSV...")
        athlete_24k = athletes_by_cat['24k'][0]
        athlete_14k = athletes_by_cat['14k'][0]
        athlete_7k = athletes_by_cat['7k'][0]

        if athlete_24k.bib_number == 4:
            print("   ✅ 24K: Dorsal 4 correcto")
        else:
            print(f"   ❌ 24K: Esperaba dorsal 4, obtuvo {athlete_24k.bib_number}")
            return False

        if athlete_14k.bib_number == 2:
            print("   ✅ 14K: Dorsal 2 correcto")
        else:
            print(f"   ❌ 14K: Esperaba dorsal 2, obtuvo {athlete_14k.bib_number}")
            return False

        if athlete_7k.bib_number == 3:
            print("   ✅ 7K: Dorsal 3 correcto")
        else:
            print(f"   ❌ 7K: Esperaba dorsal 3, obtuvo {athlete_7k.bib_number}")
            return False

        print()
        print("=" * 60)
        print("✅ TEST EXITOSO - NUEVO FORMATO CSV")
        print("=" * 60)
        return True

    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    success = test_new_csv_format()
    sys.exit(0 if success else 1)
