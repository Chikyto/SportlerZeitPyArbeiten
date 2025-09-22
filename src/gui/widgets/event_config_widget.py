from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QGroupBox, QLineEdit, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QTimeEdit, QSpinBox,
                            QTextEdit, QComboBox, QMessageBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal, QTime, Qt
from PyQt6.QtGui import QFont
from datetime import datetime, time

# Importar el sistema de eventos que acabamos de crear
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

try:
    from src.core.event_manager import EventManager, RaceCategory, RaceStatus
except ImportError:
    # Fallback si no se puede importar
    print("Warning: No se pudo importar event_manager")

class EventConfigWidget(QWidget):
    """Widget para configuración de eventos con múltiples categorías"""
    
    # Señales
    event_updated = pyqtSignal(dict)
    category_started = pyqtSignal(str)  # category_id
    category_finished = pyqtSignal(str)  # category_id
    
    def __init__(self):
        super().__init__()
        self.event_manager = EventManager()
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
        categories_group = QGroupBox("Categorías de Carrera")
        categories_layout = QVBoxLayout(categories_group)
        
        # Botones de gestión
        buttons_layout = QHBoxLayout()
        
        self.add_category_btn = QPushButton("Agregar Categoría")
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
        self.categories_table.setColumnCount(7)
        self.categories_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Distancia", "Hora Largada", "Duración Max", "Estado", "Participantes"
        ])
        
        # Configurar tabla
        header = self.categories_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
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
        # Crear categorías de ejemplo
        categories = [
            ("100k", "Ultra 100K", "100 km", QTime(2, 0), 16, "Ultramaratón de 100 kilómetros"),
            ("50k", "Trail 50K", "50 km", QTime(4, 0), 8, "Trail running de 50 kilómetros"), 
            ("30k", "Mountain 30K", "30 km", QTime(6, 0), 6, "Carrera de montaña 30K"),
            ("21k", "Half Marathon", "21 km", QTime(9, 0), 4, "Media maratón")
        ]
        
        for cat_id, name, distance, start_time, duration, desc in categories:
            # Convertir QTime a time
            start_time_py = time(start_time.hour(), start_time.minute())
            category = RaceCategory(cat_id, name, distance, start_time_py, duration, desc)
            self.event_manager.add_category(category)
        
        self.refresh_categories_table()
        self.refresh_category_combo()
        
    def add_new_category(self):
        """Agregar nueva categoría"""
        dialog = CategoryDialog(self)
        if dialog.exec():
            category = dialog.get_category()
            self.event_manager.add_category(category)
            self.refresh_categories_table()
            self.refresh_category_combo()
            
    def edit_selected_category(self):
        """Editar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para editar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        category = self.event_manager.categories.get(category_id)
        
        if category:
            dialog = CategoryDialog(self, category)
            if dialog.exec():
                updated_category = dialog.get_category()
                self.event_manager.add_category(updated_category)  # Sobrescribe
                self.refresh_categories_table()
                self.refresh_category_combo()
                
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
            self.event_manager.remove_category(category_id)
            self.refresh_categories_table()
            self.refresh_category_combo()
            
    def load_preset_categories(self):
        """Cargar categorías predefinidas"""
        # Limpiar categorías existentes
        category_ids = list(self.event_manager.categories.keys())
        for cat_id in category_ids:
            self.event_manager.remove_category(cat_id)
            
        # Cargar preset
        self.load_sample_event()
        
    def start_selected_category(self):
        """Iniciar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para iniciar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        
        if self.event_manager.start_category(category_id):
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
        
        if self.event_manager.finish_category(category_id):
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
            self.event_manager.register_participant(chip_id, category_id, participant_name)
            self.chip_id_input.clear()
            self.participant_name_input.clear()
            self.refresh_categories_table()  # Actualizar conteo de participantes
            QMessageBox.information(self, "Éxito", f"Participante {chip_id} registrado en {category_id}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            
    def refresh_categories_table(self):
        """Actualizar tabla de categorías"""
        self.categories_table.setRowCount(0)
        
        for cat_id in self.event_manager.get_categories_by_time():
            info = self.event_manager.get_category_info(cat_id)
            category = info['category']
            status = info['status']
            participant_count = info['participant_count']
            
            row = self.categories_table.rowCount()
            self.categories_table.insertRow(row)
            
            self.categories_table.setItem(row, 0, QTableWidgetItem(cat_id))
            self.categories_table.setItem(row, 1, QTableWidgetItem(category.name))
            self.categories_table.setItem(row, 2, QTableWidgetItem(category.distance))
            self.categories_table.setItem(row, 3, QTableWidgetItem(category.start_time.strftime('%H:%M')))
            self.categories_table.setItem(row, 4, QTableWidgetItem(f"{category.max_duration_hours}h"))
            
            # Colorear estado
            status_item = QTableWidgetItem(status.value.title())
            if status == RaceStatus.ACTIVE:
                status_item.setBackground(Qt.GlobalColor.green)
            elif status == RaceStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_table.setItem(row, 5, status_item)
            
            self.categories_table.setItem(row, 6, QTableWidgetItem(str(participant_count)))
            
    def refresh_category_combo(self):
        """Actualizar combo de categorías"""
        self.participant_category_combo.clear()
        
        for cat_id in self.event_manager.get_categories_by_time():
            category = self.event_manager.categories[cat_id]
            self.participant_category_combo.addItem(f"{cat_id} - {category.name}")
            
    def update_active_categories_label(self):
        """Actualizar label de categorías activas"""
        active = self.event_manager.get_active_categories()
        if active:
            names = [self.event_manager.categories[cat_id].name for cat_id in active]
            self.active_categories_label.setText(f"Categorías activas: {', '.join(names)}")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.active_categories_label.setText("Categorías activas: Ninguna")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: gray;")
            
    def get_event_manager(self):
        """Obtener el manager de eventos"""
        return self.event_manager

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