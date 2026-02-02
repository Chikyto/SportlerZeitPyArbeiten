from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QGroupBox, QLineEdit, QTableWidget,
                            QTableWidgetItem, QHeaderView, QTimeEdit, QSpinBox,
                            QTextEdit, QComboBox, QMessageBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal, QTime, Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, time
import logging

# Importar modelos de race tracking
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

try:
    from src.core.race_tracking.models import Athlete, RaceCategory, RaceStatus
    from src.core.race_tracking.race_manager import RaceManager
except ImportError as e:
    # Fallback si no se puede importar
    print(f"Warning: No se pudo importar race_tracking: {e}")

logger = logging.getLogger(__name__)

class EventConfigWidget(QWidget):
    """Widget para configuración de eventos con múltiples categorías"""

    # Señales
    event_updated = pyqtSignal(dict)
    category_started = pyqtSignal(str)  # category_id
    category_finished = pyqtSignal(str)  # category_id
    categories_changed = pyqtSignal()  # Se emite cuando cambian las categorías

    def __init__(self, race_manager=None):
        super().__init__()
        self.race_manager = race_manager if race_manager else RaceManager()
        self.setup_ui()
        self.load_sample_event()
        
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        
        # Información del evento
        event_info_group = QGroupBox("Información del Evento")
        event_info_layout = QGridLayout(event_info_group)
        
        event_info_layout.addWidget(QLabel("Nombre del evento:"), 0, 0)
        self.event_name_input = QLineEdit("Ultra Trail Competition 2025")
        event_info_layout.addWidget(self.event_name_input, 0, 1)
        
        event_info_layout.addWidget(QLabel("Fecha:"), 0, 2)
        self.event_date_input = QLineEdit(datetime.now().strftime('%Y-%m-%d'))
        event_info_layout.addWidget(self.event_date_input, 0, 3)
        
        layout.addWidget(event_info_group)
        
        # Gestión de categorías
        categories_group = QGroupBox("Distancias")
        categories_layout = QVBoxLayout(categories_group)
        
        # Botones de gestión
        buttons_layout = QHBoxLayout()
        
        self.add_category_btn = QPushButton("Agregar Distancia")
        self.add_category_btn.clicked.connect(self.add_new_category)
        buttons_layout.addWidget(self.add_category_btn)
        
        self.edit_category_btn = QPushButton("Editar Seleccionada")
        self.edit_category_btn.clicked.connect(self.edit_selected_category)
        buttons_layout.addWidget(self.edit_category_btn)
        
        self.delete_category_btn = QPushButton("Eliminar Seleccionada")
        self.delete_category_btn.clicked.connect(self.delete_selected_category)
        buttons_layout.addWidget(self.delete_category_btn)
        
        self.load_preset_btn = QPushButton("Cargar Preset")
        self.load_preset_btn.clicked.connect(self.load_preset_categories)
        buttons_layout.addWidget(self.load_preset_btn)
        
        buttons_layout.addStretch()
        categories_layout.addLayout(buttons_layout)
        
        # Tabla de categorías
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(8)
        self.categories_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Distancia", "Hora Largada", "Duración Max", "Estado", "Participantes", "Chips Asignados"
        ])
        
        # Configurar tabla
        header = self.categories_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.categories_table.itemSelectionChanged.connect(self.on_category_selected)
        categories_layout.addWidget(self.categories_table)
        
        layout.addWidget(categories_group)
        
        # Control de categorías activas
        control_group = QGroupBox("Control de Carreras")
        control_layout = QVBoxLayout(control_group)
        
        # Botones de control
        control_buttons_layout = QHBoxLayout()
        
        self.start_selected_btn = QPushButton("Iniciar Categoría Seleccionada")
        self.start_selected_btn.clicked.connect(self.start_selected_category)
        self.start_selected_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        control_buttons_layout.addWidget(self.start_selected_btn)
        
        self.finish_selected_btn = QPushButton("Finalizar Categoría Seleccionada")
        self.finish_selected_btn.clicked.connect(self.finish_selected_category)
        self.finish_selected_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        control_buttons_layout.addWidget(self.finish_selected_btn)
        
        control_buttons_layout.addStretch()
        control_layout.addLayout(control_buttons_layout)
        
        # Estado de categorías activas
        self.active_categories_label = QLabel("Categorías activas: Ninguna")
        self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        control_layout.addWidget(self.active_categories_label)
        
        layout.addWidget(control_group)

        # Panel de participantes de la categoría seleccionada
        participants_detail_group = QGroupBox("Participantes de la Categoría Seleccionada")
        participants_detail_layout = QVBoxLayout(participants_detail_group)

        # Tabla de participantes
        self.participants_table = QTableWidget()
        self.participants_table.setColumnCount(5)
        self.participants_table.setHorizontalHeaderLabels([
            "Dorsal", "Nombre", "Chip RFID", "Estado Chip", "Info Adicional"
        ])

        # Configurar tabla
        part_header = self.participants_table.horizontalHeader()
        part_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        part_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        part_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        part_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        part_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.participants_table.setAlternatingRowColors(True)
        self.participants_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.participants_table.setMaximumHeight(200)
        participants_detail_layout.addWidget(self.participants_table)

        # Label de estadísticas
        self.participants_stats_label = QLabel("Selecciona una categoría para ver sus participantes")
        self.participants_stats_label.setStyleSheet("font-style: italic; color: #666;")
        participants_detail_layout.addWidget(self.participants_stats_label)

        layout.addWidget(participants_detail_group)

        # Registro de participantes (simplificado)
        participants_group = QGroupBox("Registro Rápido de Participantes")
        participants_layout = QHBoxLayout(participants_group)
        
        participants_layout.addWidget(QLabel("Chip ID:"))
        self.chip_id_input = QLineEdit()
        participants_layout.addWidget(self.chip_id_input)
        
        participants_layout.addWidget(QLabel("Categoría:"))
        self.participant_category_combo = QComboBox()
        participants_layout.addWidget(self.participant_category_combo)
        
        participants_layout.addWidget(QLabel("Nombre:"))
        self.participant_name_input = QLineEdit()
        participants_layout.addWidget(self.participant_name_input)
        
        self.register_participant_btn = QPushButton("Registrar")
        self.register_participant_btn.clicked.connect(self.register_participant)
        participants_layout.addWidget(self.register_participant_btn)
        
        layout.addWidget(participants_group)
        
    def load_sample_event(self):
        """Cargar evento de ejemplo"""
        # Crear categorías de ejemplo usando el modelo de race_tracking
        categories = [
            ("100k", "Ultra 100K", 100000.0, 5, "Ultramaratón de 100 kilómetros"),
            ("50k", "Trail 50K", 50000.0, 3, "Trail running de 50 kilómetros"),
            ("30k", "Mountain 30K", 30000.0, 2, "Carrera de montaña 30K"),
            ("21k", "Half Marathon", 21000.0, 1, "Media maratón")
        ]

        for cat_id, name, distance_m, checkpoints, desc in categories:
            category = RaceCategory(
                category_id=cat_id,
                name=name,
                distance=distance_m,
                expected_checkpoints=checkpoints,
                participants=[],
                status=RaceStatus.PENDING,
                notes=desc
            )
            try:
                self.race_manager.add_category(category)
            except ValueError as e:
                logger.warning(f"No se pudo agregar categoría {cat_id}: {e}")

        self.refresh_categories_table()
        self.refresh_category_combo()
        self.categories_changed.emit()
        
    def add_new_category(self):
        """Agregar nueva categoría"""
        dialog = CategoryDialog(self)
        if dialog.exec():
            category = dialog.get_category()
            self.race_manager.add_category(category)
            self.refresh_categories_table()
            self.refresh_category_combo()
            self.categories_changed.emit()
            
    def edit_selected_category(self):
        """Editar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para editar")
            return

        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_category(category_id)

        if category:
            # TODO: Implementar diálogo de edición para el nuevo modelo
            QMessageBox.information(self, "Info", "Edición de categorías próximamente")
            # dialog = CategoryDialog(self, category)
            # if dialog.exec():
            #     updated_category = dialog.get_category()
            #     self.race_manager.add_category(updated_category)
            #     self.refresh_categories_table()
            #     self.refresh_category_combo()
                
    def delete_selected_category(self):
        """Eliminar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para eliminar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirmar", 
                                   f"¿Eliminar categoría {category_id}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.race_manager.remove_category(category_id)
            self.refresh_categories_table()
            self.refresh_category_combo()
            self.categories_changed.emit()
            
    def load_preset_categories(self):
        """Cargar categorías predefinidas"""
        # Limpiar categorías existentes
        category_ids = list(self.race_manager.categories.keys())
        for cat_id in category_ids:
            self.race_manager.remove_category(cat_id)
            
        # Cargar preset
        self.load_sample_event()
        
    def start_selected_category(self):
        """Iniciar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para iniciar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        
        if self.race_manager.start_category(category_id):
            self.refresh_categories_table()
            self.update_active_categories_label()
            self.category_started.emit(category_id)
            
    def finish_selected_category(self):
        """Finalizar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para finalizar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        
        if self.race_manager.finish_category(category_id):
            self.refresh_categories_table()
            self.update_active_categories_label()
            self.category_finished.emit(category_id)
            
    def register_participant(self):
        """Registrar participante rápidamente"""
        chip_id = self.chip_id_input.text().strip()
        category_id = self.participant_category_combo.currentText().split(" - ")[0] if self.participant_category_combo.currentText() else ""
        participant_name = self.participant_name_input.text().strip()

        if not chip_id or not category_id:
            QMessageBox.warning(self, "Error", "Completa Chip ID y Categoría")
            return

        try:
            # Obtener categoría
            category = self.race_manager.get_category(category_id)
            if not category:
                raise ValueError(f"Categoría {category_id} no existe")

            # Generar dorsal automático (siguiente disponible)
            existing_bibs = [p.bib_number for p in category.participants]
            next_bib = max(existing_bibs) + 1 if existing_bibs else 1

            # Crear atleta
            athlete = Athlete(
                tag_id=chip_id,
                bib_number=next_bib,
                name=participant_name if participant_name else f"Corredor-{chip_id}",
                category_id=category_id
            )

            # Agregar a categoría
            category.add_participant(athlete)

            self.chip_id_input.clear()
            self.participant_name_input.clear()
            self.refresh_categories_table()  # Actualizar conteo de participantes
            QMessageBox.information(self, "Éxito",
                                  f"Participante {athlete.name} (#{next_bib}) registrado en {category_id}")
            logger.info(f"✅ Atleta registrado: {athlete.name} (Chip: {chip_id}, Dorsal: {next_bib})")

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            logger.error(f"❌ Error registrando participante: {e}")
            
    def refresh_categories_table(self):
        """Actualizar tabla de categorías"""
        self.categories_table.setRowCount(0)

        for category in self.race_manager.get_all_categories():
            row = self.categories_table.rowCount()
            self.categories_table.insertRow(row)

            # Formatear distancia (de metros a km)
            distance_km = f"{category.distance/1000:.1f} km"

            # Hora de largada (si existe)
            start_time_str = category.start_time.strftime('%H:%M') if category.start_time else "-"

            # Duración estimada basada en distancia (aproximado: 1 hora cada 10km)
            est_duration = int(category.distance / 10000) + 1

            self.categories_table.setItem(row, 0, QTableWidgetItem(category.category_id))
            self.categories_table.setItem(row, 1, QTableWidgetItem(category.name))
            self.categories_table.setItem(row, 2, QTableWidgetItem(distance_km))
            self.categories_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            self.categories_table.setItem(row, 4, QTableWidgetItem(f"{est_duration}h"))

            # Colorear estado
            status_item = QTableWidgetItem(category.status.value.title())
            if category.status == RaceStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.green)
            elif category.status == RaceStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_table.setItem(row, 5, status_item)

            # Número de participantes
            participant_count = len(category.participants)
            self.categories_table.setItem(row, 6, QTableWidgetItem(str(participant_count)))

            # Chips asignados / Total
            chips_assigned = sum(1 for p in category.participants if p.tag_id)
            chip_status_text = f"{chips_assigned}/{participant_count}"
            chip_status_item = QTableWidgetItem(chip_status_text)

            # Colorear según porcentaje de asignación
            if participant_count > 0:
                percentage = (chips_assigned / participant_count) * 100
                if percentage == 100:
                    chip_status_item.setBackground(QColor("#d1fae5"))  # Verde claro
                elif percentage >= 50:
                    chip_status_item.setBackground(QColor("#fef3c7"))  # Amarillo claro
                else:
                    chip_status_item.setBackground(QColor("#fee2e2"))  # Rojo claro

            self.categories_table.setItem(row, 7, chip_status_item)
            
    def refresh_category_combo(self):
        """Actualizar combo de categorías"""
        self.participant_category_combo.clear()

        for category in self.race_manager.get_all_categories():
            self.participant_category_combo.addItem(f"{category.category_id} - {category.name}")
            
    def update_active_categories_label(self):
        """Actualizar label de categorías activas"""
        active = self.race_manager.get_active_categories()
        if active:
            names = [cat.name for cat in active]
            self.active_categories_label.setText(f"Categorías activas: {', '.join(names)}")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.active_categories_label.setText("Categorías activas: Ninguna")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: gray;")

    def on_category_selected(self):
        """Manejar selección de categoría en la tabla"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            self.participants_table.setRowCount(0)
            self.participants_stats_label.setText("Selecciona una categoría para ver sus participantes")
            return

        # Obtener ID de categoría
        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_category(category_id)

        if not category:
            return

        # Actualizar tabla de participantes
        self.refresh_participants_table(category)

    def refresh_participants_table(self, category):
        """Actualizar tabla de participantes de una categoría"""
        self.participants_table.setRowCount(0)

        if not category:
            return

        participants = category.participants
        chips_assigned = sum(1 for p in participants if p.tag_id)

        for participant in participants:
            row = self.participants_table.rowCount()
            self.participants_table.insertRow(row)

            # Dorsal
            self.participants_table.setItem(row, 0, QTableWidgetItem(str(participant.bib_number)))

            # Nombre
            self.participants_table.setItem(row, 1, QTableWidgetItem(participant.name))

            # Chip RFID
            chip_item = QTableWidgetItem(participant.tag_id or "-")
            if participant.tag_id:
                chip_item.setBackground(QColor("#d1fae5"))  # Verde claro
            else:
                chip_item.setBackground(QColor("#fee2e2"))  # Rojo claro
            self.participants_table.setItem(row, 2, chip_item)

            # Estado Chip
            status = "✅ Asignado" if participant.tag_id else "⏳ Pendiente"
            self.participants_table.setItem(row, 3, QTableWidgetItem(status))

            # Info adicional
            self.participants_table.setItem(row, 4, QTableWidgetItem(participant.notes or ""))

        # Actualizar estadísticas
        total = len(participants)
        pending = total - chips_assigned
        percentage = (chips_assigned / total * 100) if total > 0 else 0

        self.participants_stats_label.setText(
            f"📊 Total: {total} participantes | "
            f"✅ Con chip: {chips_assigned} ({percentage:.0f}%) | "
            f"⏳ Pendientes: {pending}"
        )

        if percentage == 100:
            self.participants_stats_label.setStyleSheet("font-weight: bold; color: #10b981;")
        elif percentage >= 50:
            self.participants_stats_label.setStyleSheet("font-weight: bold; color: #f59e0b;")
        else:
            self.participants_stats_label.setStyleSheet("font-weight: bold; color: #ef4444;")
            
    def get_event_manager(self):
        """Obtener el manager de eventos"""
        return self.race_manager

    def refresh_all(self):
        """Refrescar todas las tablas (llamado desde otras solapas cuando cambian datos)"""
        self.refresh_categories_table()
        self.refresh_category_combo()
        self.update_active_categories_label()

        # Refrescar tabla de participantes si hay categoría seleccionada
        current_row = self.categories_table.currentRow()
        if current_row >= 0:
            category_id = self.categories_table.item(current_row, 0).text()
            category = self.race_manager.get_category(category_id)
            if category:
                self.refresh_participants_table(category)

        logger.info("✅ EventConfigWidget refrescado desde otra solapa")

# Dialog para agregar/editar categorías
class CategoryDialog(QWidget):
    """Dialog para crear/editar categorías"""
    
    def __init__(self, parent=None, category=None):
        super().__init__()
        self.category = category
        self.result_category = None
        self.setup_ui()
        
        if category:
            self.load_category_data()
            
    def setup_ui(self):
        """Configurar interfaz del dialog"""
        self.setWindowTitle("Configurar Categoría")
        self.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout(self)
        
        # Campos de entrada
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("ID:"), 0, 0)
        self.id_input = QLineEdit()
        form_layout.addWidget(self.id_input, 0, 1)
        
        form_layout.addWidget(QLabel("Nombre:"), 1, 0)
        self.name_input = QLineEdit()
        form_layout.addWidget(self.name_input, 1, 1)
        
        form_layout.addWidget(QLabel("Distancia:"), 2, 0)
        self.distance_input = QLineEdit()
        form_layout.addWidget(self.distance_input, 2, 1)
        
        form_layout.addWidget(QLabel("Hora Largada:"), 3, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(9, 0))  # 09:00 por defecto
        form_layout.addWidget(self.start_time_input, 3, 1)
        
        form_layout.addWidget(QLabel("Duración Max (h):"), 4, 0)
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 24)
        self.duration_input.setValue(6)
        form_layout.addWidget(self.duration_input, 4, 1)
        
        form_layout.addWidget(QLabel("Descripción:"), 5, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addWidget(self.description_input, 5, 1)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self.save_category)
        self.save_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def load_category_data(self):
        """Cargar datos de categoría existente"""
        if self.category:
            self.id_input.setText(self.category.id)
            self.name_input.setText(self.category.name)
            self.distance_input.setText(self.category.distance)
            self.start_time_input.setTime(QTime(self.category.start_time.hour, self.category.start_time.minute))
            self.duration_input.setValue(self.category.max_duration_hours)
            self.description_input.setPlainText(self.category.description)
            
    def save_category(self):
        """Guardar categoría"""
        category_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        distance = self.distance_input.text().strip()
        start_time_qt = self.start_time_input.time()
        duration = self.duration_input.value()
        description = self.description_input.toPlainText().strip()
        
        if not all([category_id, name, distance]):
            QMessageBox.warning(self, "Error", "Completa todos los campos requeridos")
            return
            
        # Convertir QTime a time
        start_time_py = time(start_time_qt.hour(), start_time_qt.minute())
        
        # Crear categoría
        try:
            self.result_category = RaceCategory(
                id=category_id,
                name=name,
                distance=distance,
                start_time=start_time_py,
                max_duration_hours=duration,
                description=description
            )
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creando categoría: {e}")
            
    def get_category(self):
        """Obtener categoría creada"""
        return self.result_category
        
    def exec(self):
        """Mostrar dialog y esperar resultado"""
        self.show()
        # Simular dialog modal
        return self.result_category is not None