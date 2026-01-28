#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV Import/Export Handler for Chip Assignment
src/gui/widgets/chip_assignment_csv_handler.py

Handles all CSV operations for chip assignment widget.
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox
import logging
import csv

logger = logging.getLogger(__name__)


class ChipAssignmentCSVHandler:
    """Handles CSV import/export for chip assignments"""

    def __init__(self, parent_widget, race_manager):
        """
        Args:
            parent_widget: Parent QWidget for dialogs
            race_manager: RaceManager instance
        """
        self.parent = parent_widget
        self.race_manager = race_manager

    def import_from_csv(self):
        """Import athletes from CSV file"""
        from src.core.csv_importer import CSVImporter

        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Importar Atletas desde CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            logger.info(f"📂 Importando atletas desde: {file_path}")

            importer = CSVImporter(self.race_manager)
            categories, athletes = importer.import_from_csv(file_path)

            logger.info(f"✅ Importación exitosa: {len(categories)} categorías, {len(athletes)} atletas")

            QMessageBox.information(
                self.parent,
                "Importación Exitosa",
                f"✅ Importados desde CSV:\n\n"
                f"• {len(categories)} categorías\n"
                f"• {len(athletes)} atletas\n\n"
                f"Ahora puedes asignar chips RFID a cada corredor."
            )

            return True

        except Exception as e:
            error_msg = f"Error importando CSV: {str(e)}"
            logger.error(f"❌ {error_msg}")
            QMessageBox.critical(
                self.parent,
                "Error de Importación",
                f"No se pudo importar el archivo CSV:\n\n{str(e)}"
            )
            return False

    def import_assignments_from_csv(self):
        """Import chip assignments from CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Importar Asignaciones desde CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            imported_count = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    dorsal = row.get('Dorsal', '').strip()
                    chip_id = row.get('Chip RFID', '').strip()

                    if not dorsal or not chip_id:
                        continue

                    # Buscar atleta por dorsal
                    for category in self.race_manager.get_all_categories():
                        for athlete in category.participants:
                            if str(athlete.bib_number) == dorsal:
                                athlete.tag_id = chip_id
                                imported_count += 1
                                logger.info(f"✅ Chip {chip_id} asignado a {athlete.name} (#{dorsal})")
                                break

            logger.info(f"📊 Importación completa: {imported_count} asignaciones")

            QMessageBox.information(
                self.parent,
                "Importación Completada",
                f"✅ Se importaron {imported_count} asignaciones de chips."
            )

            return imported_count

        except Exception as e:
            logger.error(f"❌ Error importando asignaciones: {e}")
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Error al importar asignaciones:\n{str(e)}"
            )
            return 0

    def export_assignments(self):
        """Export chip assignments to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Guardar Asignaciones",
            "asignaciones_chips.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Dorsal', 'Nombre', 'Categoría', 'Chip RFID',
                    'Estado', 'Equipo', 'Notas'
                ])

                total = 0
                assigned = 0

                for category in self.race_manager.get_all_categories():
                    for athlete in category.participants:
                        total += 1
                        estado = '✅ Asignado' if athlete.has_chip_assigned() else '⏳ Pendiente'

                        if athlete.has_chip_assigned():
                            assigned += 1

                        writer.writerow([
                            athlete.bib_number,
                            athlete.name,
                            category.name,
                            athlete.tag_id or '',
                            estado,
                            athlete.team or '',
                            athlete.notes or ''
                        ])

            logger.info(f"💾 Asignaciones guardadas: {file_path}")
            logger.info(f"📊 Total: {total} atletas, {assigned} con chip asignado")

            QMessageBox.information(
                self.parent,
                "Guardado Exitoso",
                f"✅ Asignaciones guardadas en:\n{file_path}\n\n"
                f"Total: {total} atletas\n"
                f"Con chip: {assigned}\n"
                f"Pendientes: {total - assigned}"
            )

        except Exception as e:
            logger.error(f"❌ Error guardando: {e}")
            QMessageBox.critical(
                self.parent,
                "Error",
                f"Error al guardar:\n{str(e)}"
            )
