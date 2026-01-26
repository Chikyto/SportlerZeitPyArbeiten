#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador CSV para Sistema de Pre-Registro Firebase
src/core/csv_importer.py

Lee archivos CSV exportados desde Firebase y genera dorsales automáticamente.
"""

import csv
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from src.core.race_tracking.models import Athlete, RaceCategory

logger = logging.getLogger(__name__)


class CSVAthleteImporter:
    """
    Importador de atletas desde CSV exportado de Firebase

    Estructura esperada del CSV:
    - Nombre, Apellido, Email, DNI, Fecha Nacimiento, Género, Teléfono
    - Distancia, Estado Pago, Precio Total, Pagado Online
    - Pendiente Presencial, Presencial, Fecha Inscripción, N°, Pecho

    Features:
    - Lee CSV con múltiples categorías (distancias)
    - Genera dorsales automáticamente por categoría
    - Asigna rango de dorsales por distancia
    - Valida datos y estado de pago
    """

    # Mapeo de distancias a categorías
    DISTANCE_MAPPING = {
        '5K': {'category_id': '5k', 'name': '5 Kilómetros', 'distance_m': 5000, 'checkpoints': 0},
        '10K': {'category_id': '10k', 'name': '10 Kilómetros', 'distance_m': 10000, 'checkpoints': 1},
        '21K': {'category_id': '21k', 'name': 'Media Maratón 21K', 'distance_m': 21000, 'checkpoints': 2},
        '30K': {'category_id': '30k', 'name': 'Mountain 30K', 'distance_m': 30000, 'checkpoints': 2},
        '42K': {'category_id': '42k', 'name': 'Maratón 42K', 'distance_m': 42000, 'checkpoints': 3},
        '50K': {'category_id': '50k', 'name': 'Trail 50K', 'distance_m': 50000, 'checkpoints': 3},
        '100K': {'category_id': '100k', 'name': 'Ultra 100K', 'distance_m': 100000, 'checkpoints': 5},
    }

    # Rangos de dorsales por categoría (inicio)
    BIB_RANGES = {
        '5k': 1,      # 1-999
        '10k': 1000,  # 1000-1999
        '21k': 2000,  # 2000-2999
        '30k': 3000,  # 3000-3999
        '42k': 4000,  # 4000-4999
        '50k': 5000,  # 5000-5999
        '100k': 6000, # 6000-6999
    }

    def __init__(self):
        """Inicializar importador"""
        self.athletes_by_category: Dict[str, List[Athlete]] = {}
        self.bib_counters: Dict[str, int] = {}  # Contador de dorsales por categoría

    def import_from_csv(
        self,
        csv_path: str,
        encoding: str = 'utf-8',
        delimiter: str = ',',
        filter_approved: bool = True
    ) -> Dict[str, List[Athlete]]:
        """
        Importar atletas desde archivo CSV

        Args:
            csv_path: Ruta al archivo CSV
            encoding: Codificación del archivo (default: utf-8)
            delimiter: Delimitador (default: ,)
            filter_approved: Solo importar atletas con pago aprobado

        Returns:
            Dict[category_id, List[Athlete]]: Atletas agrupados por categoría

        Example:
            >>> importer = CSVAthleteImporter()
            >>> athletes = importer.import_from_csv('inscriptos.csv')
            >>> for cat_id, athletes_list in athletes.items():
            ...     print(f"{cat_id}: {len(athletes_list)} atletas")
        """
        try:
            logger.info(f"📥 Importando desde {csv_path}...")

            # Limpiar contadores
            self.athletes_by_category = {}
            self.bib_counters = {}

            # Leer CSV
            with open(csv_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                # Log columnas detectadas
                if reader.fieldnames:
                    logger.info(f"📋 Columnas detectadas en CSV: {', '.join(reader.fieldnames)}")
                else:
                    logger.warning("⚠️  No se detectaron columnas en el CSV")

                row_count = 0
                imported_count = 0
                skipped_count = 0
                skipped_payment = 0
                skipped_error = 0

                for row in reader:
                    row_count += 1

                    try:
                        # Filtrar por estado de pago si se requiere
                        if filter_approved:
                            estado_pago = row.get('Estado Pago', '').strip().lower()
                            if estado_pago not in ['approved', 'aprobado', 'confirmado']:
                                if row_count <= 5:  # Log las primeras 5
                                    logger.info(f"⏭️  Fila {row_count}: Pago no aprobado ('{estado_pago}')")
                                skipped_payment += 1
                                continue

                        # Crear atleta
                        athlete = self._parse_row(row, row_count)

                        if athlete:
                            # Agrupar por categoría
                            cat_id = athlete.category_id
                            if cat_id not in self.athletes_by_category:
                                self.athletes_by_category[cat_id] = []

                            self.athletes_by_category[cat_id].append(athlete)
                            imported_count += 1
                        else:
                            skipped_error += 1

                    except Exception as e:
                        logger.error(f"❌ Error en fila {row_count}: {e}")
                        skipped_error += 1
                        continue

            logger.info(f"✅ Importación completa:")
            logger.info(f"   • Total filas: {row_count}")
            logger.info(f"   • Importados: {imported_count}")
            logger.info(f"   • Omitidos por pago: {skipped_payment}")
            logger.info(f"   • Omitidos por error: {skipped_error}")

            for cat_id, athletes in self.athletes_by_category.items():
                logger.info(f"   • {cat_id}: {len(athletes)} atletas")

            return self.athletes_by_category

        except FileNotFoundError:
            logger.error(f"❌ Archivo no encontrado: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Error importando CSV: {e}")
            raise

    def _parse_row(self, row: dict, row_number: int) -> Optional[Athlete]:
        """
        Parsear fila del CSV a objeto Athlete

        Args:
            row: Diccionario con datos de la fila
            row_number: Número de fila (para logging)

        Returns:
            Athlete o None si hay error
        """
        try:
            # Extraer campos
            nombre = row.get('Nombre', '').strip()
            apellido = row.get('Apellido', '').strip()
            email = row.get('Email', '').strip()
            dni = row.get('DNI', '').strip()
            fecha_nacimiento = row.get('Fecha Nacimiento', '').strip()
            genero = row.get('Género', '').strip()
            telefono = row.get('Teléfono', '').strip()
            distancia = row.get('Distancia', '').strip().upper()

            # Validar campos obligatorios
            if not nombre or not apellido:
                logger.warning(f"⚠️  Fila {row_number}: Nombre o apellido vacío")
                return None

            if not distancia:
                logger.warning(f"⚠️  Fila {row_number}: Sin distancia/categoría")
                return None

            # Mapear distancia a categoría
            if distancia not in self.DISTANCE_MAPPING:
                logger.warning(f"⚠️  Fila {row_number}: Distancia desconocida '{distancia}'")
                # Intentar mapeo flexible
                if 'K' in distancia:
                    distancia = distancia.replace('KM', 'K').replace('km', 'K')
                    if distancia not in self.DISTANCE_MAPPING:
                        return None
                else:
                    return None

            category_info = self.DISTANCE_MAPPING[distancia]
            category_id = category_info['category_id']

            # Intentar leer dorsal del CSV (columna "N°")
            bib_from_csv = row.get('N°', '').strip() or row.get('Nº', '').strip() or row.get('Pecho', '').strip()

            if bib_from_csv and bib_from_csv.isdigit():
                # Usar dorsal del CSV
                bib_number = int(bib_from_csv)
                logger.debug(f"✓ Fila {row_number}: Usando dorsal del CSV: {bib_number}")
            else:
                # Generar dorsal automáticamente
                bib_number = self._generate_bib_number(category_id)
                logger.debug(f"⚙️  Fila {row_number}: Generando dorsal automático: {bib_number}")

            # Calcular edad
            edad = self._calculate_age(fecha_nacimiento)

            # Construir nombre completo
            full_name = f"{nombre} {apellido}"

            # Crear ID único
            athlete_id = f"{category_id}_{bib_number}"

            # Construir notas con información adicional
            notes_parts = []

            if edad:
                notes_parts.append(f"Edad: {edad}")

            if genero:
                notes_parts.append(f"Género: {genero}")

            if dni:
                notes_parts.append(f"DNI: {dni}")

            if email:
                notes_parts.append(f"Email: {email}")

            if telefono:
                telefono_clean = self._clean_phone(telefono)
                if telefono_clean:
                    notes_parts.append(f"Tel: {telefono_clean}")

            # Estado de pago
            estado_pago = row.get('Estado Pago', '').strip()
            if estado_pago:
                notes_parts.append(f"Pago: {estado_pago}")

            # Precio
            precio = row.get('Precio Total', '').strip()
            if precio:
                notes_parts.append(f"Precio: ${precio}")

            notes = " | ".join(notes_parts)

            # Crear atleta
            athlete = Athlete(
                athlete_id=athlete_id,
                tag_id='',  # Se asignará después con el chip físico
                bib_number=bib_number,
                name=full_name,
                category_id=category_id,
                team='',  # Agregar si lo tienes en tu CSV
                notes=notes
            )

            logger.debug(f"✓ Atleta creado: {full_name} (#{bib_number}) - {category_id}")

            return athlete

        except Exception as e:
            logger.error(f"❌ Error parseando fila {row_number}: {e}")
            return None

    def _generate_bib_number(self, category_id: str) -> int:
        """
        Generar número de dorsal automático para una categoría

        Usa rangos predefinidos:
        - 5K: 1-999
        - 10K: 1000-1999
        - 21K: 2000-2999
        - etc.

        Args:
            category_id: ID de la categoría

        Returns:
            int: Número de dorsal único
        """
        # Inicializar contador si no existe
        if category_id not in self.bib_counters:
            base = self.BIB_RANGES.get(category_id, 1)
            self.bib_counters[category_id] = base

        # Obtener siguiente número
        bib_number = self.bib_counters[category_id]

        # Incrementar contador
        self.bib_counters[category_id] += 1

        return bib_number

    def _calculate_age(self, fecha_nacimiento: str) -> Optional[int]:
        """
        Calcular edad desde fecha de nacimiento

        Formatos soportados:
        - DD/MM/YYYY
        - YYYY-MM-DD
        - DD-MM-YYYY

        Args:
            fecha_nacimiento: Fecha en string

        Returns:
            int: Edad en años o None si no se puede parsear
        """
        if not fecha_nacimiento:
            return None

        try:
            # Intentar diferentes formatos
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    birth_date = datetime.strptime(fecha_nacimiento, fmt)
                    age = (datetime.now() - birth_date).days // 365
                    return age
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.debug(f"No se pudo parsear fecha: {fecha_nacimiento}")
            return None

    def _clean_phone(self, telefono: str) -> Optional[str]:
        """
        Limpiar número de teléfono

        Maneja formato científico de Excel (5.4266E+11)

        Args:
            telefono: Teléfono en string

        Returns:
            str: Teléfono limpio o None
        """
        if not telefono:
            return None

        try:
            # Si está en notación científica
            if 'E' in telefono or 'e' in telefono:
                # Convertir a número
                phone_num = float(telefono)
                # Convertir a string sin decimales
                telefono = f"{int(phone_num)}"

            # Limpiar caracteres no numéricos (excepto +)
            telefono = ''.join(c for c in telefono if c.isdigit() or c == '+')

            # Si empieza con código de país, dejarlo
            if telefono.startswith('+'):
                return telefono

            # Si es número argentino (empieza con 54)
            if telefono.startswith('54') and len(telefono) >= 12:
                return f"+{telefono}"

            return telefono if telefono else None

        except Exception as e:
            logger.debug(f"No se pudo limpiar teléfono: {telefono}")
            return None

    def create_categories(self) -> List[RaceCategory]:
        """
        Crear objetos RaceCategory basados en los atletas importados

        Returns:
            List[RaceCategory]: Lista de categorías con participantes
        """
        categories = []

        for category_id, athletes in self.athletes_by_category.items():
            if not athletes:
                continue

            # Obtener info de la categoría
            # Buscar en el mapeo de distancias
            cat_info = None
            for dist, info in self.DISTANCE_MAPPING.items():
                if info['category_id'] == category_id:
                    cat_info = info
                    break

            if not cat_info:
                logger.warning(f"⚠️  No se encontró info para categoría {category_id}")
                continue

            # Crear categoría
            category = RaceCategory(
                category_id=category_id,
                name=cat_info['name'],
                distance=cat_info['distance_m'],
                expected_checkpoints=cat_info['checkpoints'],
                participants=athletes.copy(),  # Copiar lista de atletas
                notes=f"Importado desde CSV - {len(athletes)} participantes"
            )

            categories.append(category)
            logger.info(f"✅ Categoría creada: {category.name} ({len(athletes)} atletas)")

        return categories

    def export_bib_list(self, output_path: str):
        """
        Exportar lista de dorsales asignados

        Útil para imprimir lista o para control

        Args:
            output_path: Ruta del archivo de salida (CSV)
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(['Dorsal', 'Nombre', 'Categoría', 'Email', 'Teléfono'])

                # Ordenar por dorsal
                all_athletes = []
                for athletes in self.athletes_by_category.values():
                    all_athletes.extend(athletes)

                all_athletes.sort(key=lambda a: a.bib_number)

                # Escribir filas
                for athlete in all_athletes:
                    # Extraer email y tel de notes
                    email = ''
                    tel = ''
                    if athlete.notes:
                        parts = athlete.notes.split(' | ')
                        for part in parts:
                            if part.startswith('Email: '):
                                email = part.replace('Email: ', '')
                            elif part.startswith('Tel: '):
                                tel = part.replace('Tel: ', '')

                    writer.writerow([
                        athlete.bib_number,
                        athlete.name,
                        athlete.category_id.upper(),
                        email,
                        tel
                    ])

            logger.info(f"✅ Lista de dorsales exportada: {output_path}")

        except Exception as e:
            logger.error(f"❌ Error exportando lista: {e}")
            raise


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear importador
    importer = CSVAthleteImporter()

    # Importar desde CSV
    athletes = importer.import_from_csv(
        csv_path='inscriptos.csv',
        encoding='utf-8',
        filter_approved=True  # Solo pago aprobado
    )

    print(f"\n✅ Importación completa:")
    print(f"{'='*60}")

    for cat_id, athletes_list in athletes.items():
        print(f"\n📋 {cat_id.upper()}: {len(athletes_list)} atletas")
        print(f"   Dorsales: {athletes_list[0].bib_number} - {athletes_list[-1].bib_number}")

        # Mostrar primeros 3
        for athlete in athletes_list[:3]:
            print(f"   • #{athlete.bib_number:04d} - {athlete.name}")

        if len(athletes_list) > 3:
            print(f"   ... y {len(athletes_list) - 3} más")

    # Crear categorías
    categories = importer.create_categories()

    print(f"\n✅ {len(categories)} categorías creadas")

    # Exportar lista de dorsales
    importer.export_bib_list('lista_dorsales.csv')
    print(f"\n✅ Lista de dorsales exportada: lista_dorsales.csv")
