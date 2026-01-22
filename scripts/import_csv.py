#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Importar Atletas desde CSV de Firebase
scripts/import_csv.py

Uso:
    python scripts/import_csv.py inscriptos.csv

Features:
- Importa atletas con dorsales automáticos
- Genera lista de dorsales para imprimir
- Carga datos en RaceManager
- Guarda estado para usar en la app
"""

import sys
import os
import logging
import json
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.csv_importer import CSVAthleteImporter
from src.core.race_tracking.race_manager import RaceManager
from colorama import init, Fore, Style

# Inicializar colorama para colores en terminal
init(autoreset=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def print_banner():
    """Imprimir banner"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🏃 IMPORTADOR DE ATLETAS - Sistema RFID Athletics Timer")
    print(f"{Fore.CYAN}{'='*70}\n")


def print_success(message):
    """Imprimir mensaje de éxito"""
    print(f"{Fore.GREEN}✅ {message}")


def print_error(message):
    """Imprimir mensaje de error"""
    print(f"{Fore.RED}❌ {message}")


def print_info(message):
    """Imprimir información"""
    print(f"{Fore.YELLOW}ℹ️  {message}")


def import_and_process(csv_path: str):
    """
    Importar CSV y procesar

    Args:
        csv_path: Ruta al archivo CSV
    """
    # Verificar que existe el archivo
    if not os.path.exists(csv_path):
        print_error(f"Archivo no encontrado: {csv_path}")
        return False

    print_info(f"Importando desde: {csv_path}")
    print()

    try:
        # 1. Crear importador
        importer = CSVAthleteImporter()

        # 2. Importar desde CSV
        print("📥 Leyendo archivo CSV...")
        athletes_by_cat = importer.import_from_csv(
            csv_path=csv_path,
            encoding='utf-8',
            filter_approved=True  # Solo pago aprobado
        )

        if not athletes_by_cat:
            print_error("No se importó ningún atleta. Verifica el archivo.")
            return False

        # 3. Crear categorías
        print("\n📋 Creando categorías...")
        categories = importer.create_categories()

        # 4. Mostrar resumen
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}📊 RESUMEN DE IMPORTACIÓN")
        print(f"{Fore.CYAN}{'='*70}\n")

        total_athletes = 0

        for category in categories:
            total_athletes += len(category.participants)
            print(f"{Fore.WHITE}📁 {category.name}")
            print(f"   • Atletas: {len(category.participants)}")
            print(f"   • Distancia: {category.distance/1000:.1f} km")
            print(f"   • Checkpoints: {category.expected_checkpoints}")

            # Mostrar rango de dorsales
            if category.participants:
                min_bib = min(a.bib_number for a in category.participants)
                max_bib = max(a.bib_number for a in category.participants)
                print(f"   • Dorsales: {min_bib} - {max_bib}")

            print()

        print(f"{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ Total: {total_athletes} atletas en {len(categories)} categorías")
        print(f"{Fore.GREEN}{'='*70}\n")

        # 5. Mostrar algunos atletas de ejemplo
        print(f"{Fore.CYAN}👥 EJEMPLOS DE ATLETAS:\n")

        for category in categories[:2]:  # Primeras 2 categorías
            print(f"{Fore.WHITE}{category.name}:")
            for athlete in category.participants[:5]:  # Primeros 5
                print(f"   • #{athlete.bib_number:04d} - {athlete.name}")
            if len(category.participants) > 5:
                print(f"   ... y {len(category.participants) - 5} más")
            print()

        # 6. Exportar lista de dorsales
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        bib_list_path = output_dir / 'lista_dorsales.csv'
        print(f"📄 Generando lista de dorsales...")
        importer.export_bib_list(str(bib_list_path))
        print_success(f"Lista exportada: {bib_list_path}")

        # 7. Guardar datos para la app
        print(f"\n💾 Guardando datos para la aplicación...")

        # Crear RaceManager y cargar datos
        race_manager = RaceManager()

        for category in categories:
            race_manager.add_category(category)

        # Guardar estado (opcional - para persistencia)
        state = {
            'categories': [
                {
                    'category_id': cat.category_id,
                    'name': cat.name,
                    'distance': cat.distance,
                    'checkpoints': cat.expected_checkpoints,
                    'athlete_count': len(cat.participants)
                }
                for cat in categories
            ],
            'total_athletes': total_athletes,
            'import_date': str(Path(csv_path).stat().st_mtime)
        }

        state_path = output_dir / 'import_state.json'
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print_success(f"Estado guardado: {state_path}")

        # 8. Instrucciones
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}📝 PRÓXIMOS PASOS")
        print(f"{Fore.CYAN}{'='*70}\n")

        print(f"{Fore.WHITE}1. Imprimir lista de dorsales:")
        print(f"   📄 Archivo: {bib_list_path}")
        print(f"   Úsalo para entregar dorsales a los corredores\n")

        print(f"{Fore.WHITE}2. Ejecutar sistema de timing:")
        print(f"   python main.py\n")

        print(f"{Fore.WHITE}3. En la app, ir al tab '🏷️ Asignación de Chips':\n")
        print(f"   • Los atletas ya están cargados con dorsales")
        print(f"   • Seleccionar atleta")
        print(f"   • Escanear chip RFID")
        print(f"   • Asignar\n")

        print(f"{Fore.WHITE}4. Iniciar carrera:")
        print(f"   • Tab 'Gestión de Eventos'")
        print(f"   • Seleccionar categoría")
        print(f"   • Click en 'Iniciar Categoría'\n")

        print(f"{Fore.GREEN}¡Listo para el día del evento! 🏁\n")

        return True

    except Exception as e:
        print_error(f"Error durante importación: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print_banner()

    # Verificar argumentos
    if len(sys.argv) < 2:
        print_error("Uso: python scripts/import_csv.py <archivo.csv>")
        print()
        print(f"{Fore.YELLOW}Ejemplo:")
        print(f"  python scripts/import_csv.py inscriptos.csv")
        print()
        sys.exit(1)

    csv_path = sys.argv[1]

    # Importar y procesar
    success = import_and_process(csv_path)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
