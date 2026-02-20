#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget para Gestión de Categorías de Premiación
src/gui/widgets/award_categories_widget.py

Permite configurar categorías de premiación por género y edad:
- Visualizar categorías IAAF estándar
- Crear categorías personalizadas
- Editar/eliminar categorías personalizadas
- Resetear a IAAF por defecto

Versión: 1.0.0
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QLineEdit,
    QSpinBox, QComboBox, QGridLayout, QCheckBox, QListWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
import logging

# Importar modelos
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from src.core.race_tracking.models import AwardCategory
from src.core.race_tracking.race_manager import RaceManager

logger = logging.getLogger(__name__)


class AwardCategoriesWidget(QWidget):
    """Widget para gestión de categorías de premiación"""

    # Señales
    award_categories_changed = pyqtSignal()  # Se emite cuando cambian las categorías

    def __init__(self, race_manager: RaceManager = None):
        super().__init__()
        self.race_manager = race_manager
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)

        # Título y descripción
        title_label = QLabel("⭐ Categorías de Premiación")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            "Configura categorías de premiación por género y edad. "
            "Las categorías IAAF son estándar y no pueden modificarse. "
            "Puedes agregar categorías personalizadas para tu evento."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # ====== PRESETS DE CATEGORÍAS ======
        presets_group = QGroupBox("⚡ Presets de Categorías")
        presets_layout = QHBoxLayout(presets_group)

        preset_label = QLabel("Seleccionar preset:")
        presets_layout.addWidget(preset_label)

        self.presets_combo = QComboBox()
        self.presets_combo.addItems([
            "Seleccionar...",
            "IAAF (Estándar internacional)",
            "Por 5 años (20-24, 25-29, 30-34...)",
            "Por 10 años (20-29, 30-39, 40-49...)"
        ])
        self.presets_combo.setMinimumWidth(300)
        presets_layout.addWidget(self.presets_combo)

        apply_preset_btn = QPushButton("✨ Aplicar Preset")
        apply_preset_btn.clicked.connect(self.apply_preset)
        apply_preset_btn.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; padding: 8px;")
        presets_layout.addWidget(apply_preset_btn)

        presets_layout.addStretch()
        layout.addWidget(presets_group)

        # Botones de gestión
        buttons_layout = QHBoxLayout()

        self.add_category_btn = QPushButton("➕ Agregar Categoría Personalizada")
        self.add_category_btn.clicked.connect(self.add_custom_category)
        self.add_category_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.add_category_btn)

        self.edit_category_btn = QPushButton("✏️ Editar Seleccionada")
        self.edit_category_btn.clicked.connect(self.edit_selected_category)
        buttons_layout.addWidget(self.edit_category_btn)

        self.delete_category_btn = QPushButton("🗑️ Eliminar Seleccionada")
        self.delete_category_btn.clicked.connect(self.delete_selected_category)
        self.delete_category_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(self.delete_category_btn)

        self.reset_btn = QPushButton("🔄 Resetear a IAAF")
        self.reset_btn.clicked.connect(self.reset_to_iaaf)
        buttons_layout.addWidget(self.reset_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabla de categorías
        categories_group = QGroupBox("Categorías Configuradas")
        categories_layout = QVBoxLayout(categories_group)

        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(7)
        self.categories_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Género", "Edad Mín", "Edad Máx", "Distancias", "Tipo"
        ])

        # Configurar tabla
        header = self.categories_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.categories_table.itemSelectionChanged.connect(self.on_category_selected)

        categories_layout.addWidget(self.categories_table)

        # Estadísticas
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("font-weight: bold; padding: 5px;")
        categories_layout.addWidget(self.stats_label)

        layout.addWidget(categories_group)

    def refresh_table(self):
        """Actualizar tabla de categorías"""
        if not self.race_manager:
            return

        self.categories_table.setRowCount(0)

        all_categories = self.race_manager.get_all_award_categories()

        # Ordenar: primero IAAF por género y edad, luego personalizadas
        all_categories.sort(key=lambda c: (
            0 if c.is_iaaf else 1,  # IAAF primero
            c.gender or "Z",  # Por género
            c.min_age  # Por edad mínima
        ))

        iaaf_count = 0
        custom_count = 0

        for category in all_categories:
            row = self.categories_table.rowCount()
            self.categories_table.insertRow(row)

            # ID
            id_item = QTableWidgetItem(category.award_category_id)
            if category.is_iaaf:
                id_item.setForeground(QColor("#6b7280"))  # Gris para IAAF
            self.categories_table.setItem(row, 0, id_item)

            # Nombre
            name_item = QTableWidgetItem(category.name)
            if category.is_iaaf:
                name_item.setForeground(QColor("#6b7280"))
            self.categories_table.setItem(row, 1, name_item)

            # Género
            gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro", None: "Mixto"}
            gender_item = QTableWidgetItem(gender_map.get(category.gender, "Mixto"))
            self.categories_table.setItem(row, 2, gender_item)

            # Edad mínima
            self.categories_table.setItem(row, 3, QTableWidgetItem(str(category.min_age)))

            # Edad máxima
            max_age_str = str(category.max_age) if category.max_age is not None else "∞"
            self.categories_table.setItem(row, 4, QTableWidgetItem(max_age_str))

            # Distancias
            if category.distance_ids is None:
                distances_str = "Todas"
            else:
                distances_str = ", ".join(category.distance_ids)
            self.categories_table.setItem(row, 5, QTableWidgetItem(distances_str))

            # Tipo
            type_item = QTableWidgetItem("IAAF" if category.is_iaaf else "Personalizada")
            if category.is_iaaf:
                type_item.setBackground(QColor("#e0f2fe"))  # Azul claro
                iaaf_count += 1
            else:
                type_item.setBackground(QColor("#fef3c7"))  # Amarillo claro
                custom_count += 1
            self.categories_table.setItem(row, 6, type_item)

        # Actualizar estadísticas
        total = iaaf_count + custom_count
        self.stats_label.setText(
            f"📊 Total: {total} categorías | "
            f"🏛️ IAAF: {iaaf_count} | "
            f"⚙️ Personalizadas: {custom_count}"
        )

    def on_category_selected(self):
        """Manejar selección de categoría"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            self.edit_category_btn.setEnabled(False)
            self.delete_category_btn.setEnabled(False)
            return

        # Obtener ID de categoría
        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_award_category(category_id)

        if category:
            # Solo permitir editar/eliminar si no es IAAF
            is_iaaf = category.is_iaaf
            self.edit_category_btn.setEnabled(not is_iaaf)
            self.delete_category_btn.setEnabled(not is_iaaf)

    def add_custom_category(self):
        """Agregar categoría personalizada"""
        dialog = AwardCategoryDialog(self, self.race_manager)
        if dialog.exec():
            category = dialog.get_category()
            try:
                self.race_manager.add_award_category(category)
                self.refresh_table()
                self.award_categories_changed.emit()
                QMessageBox.information(self, "Éxito", f"Categoría '{category.name}' agregada correctamente")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def edit_selected_category(self):
        """Editar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para editar")
            return

        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_award_category(category_id)

        if not category:
            return

        if category.is_iaaf:
            QMessageBox.warning(self, "Error", "No se pueden editar categorías IAAF estándar")
            return

        dialog = AwardCategoryDialog(self, self.race_manager, category)
        if dialog.exec():
            updated_category = dialog.get_category()
            try:
                self.race_manager.add_award_category(updated_category)
                self.refresh_table()
                self.award_categories_changed.emit()
                QMessageBox.information(self, "Éxito", f"Categoría '{updated_category.name}' actualizada")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def delete_selected_category(self):
        """Eliminar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una categoría para eliminar")
            return

        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_award_category(category_id)

        if not category:
            return

        if category.is_iaaf:
            QMessageBox.warning(self, "Error", "No se pueden eliminar categorías IAAF estándar")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar categoría '{category.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.race_manager.remove_award_category(category_id)
                self.refresh_table()
                self.award_categories_changed.emit()
                QMessageBox.information(self, "Éxito", f"Categoría '{category.name}' eliminada")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def apply_preset(self):
        """Aplicar preset de categorías seleccionado"""
        preset = self.presets_combo.currentText()

        if preset == "Seleccionar...":
            QMessageBox.warning(self, "Atención", "Por favor selecciona un preset")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Aplicar preset '{preset}'?\n\n"
            "Esto reemplazará todas las categorías actuales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Limpiar categorías actuales
        self.race_manager.award_categories.clear()

        if "IAAF" in preset:
            self.race_manager.reset_award_categories_to_iaaf()

        elif "5 años" in preset:
            # Preset por 5 años: Sub-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49, 50-54, 55-59, 60+
            categories_5y = [
                ("M_Sub19", "Masculino Sub-19", "M", 0, 18),
                ("M_20-24", "Masculino 20-24", "M", 20, 24),
                ("M_25-29", "Masculino 25-29", "M", 25, 29),
                ("M_30-34", "Masculino 30-34", "M", 30, 34),
                ("M_35-39", "Masculino 35-39", "M", 35, 39),
                ("M_40-44", "Masculino 40-44", "M", 40, 44),
                ("M_45-49", "Masculino 45-49", "M", 45, 49),
                ("M_50-54", "Masculino 50-54", "M", 50, 54),
                ("M_55-59", "Masculino 55-59", "M", 55, 59),
                ("M_60+", "Masculino 60+", "M", 60, None),
                ("F_Sub19", "Femenino Sub-19", "F", 0, 18),
                ("F_20-24", "Femenino 20-24", "F", 20, 24),
                ("F_25-29", "Femenino 25-29", "F", 25, 29),
                ("F_30-34", "Femenino 30-34", "F", 30, 34),
                ("F_35-39", "Femenino 35-39", "F", 35, 39),
                ("F_40-44", "Femenino 40-44", "F", 40, 44),
                ("F_45-49", "Femenino 45-49", "F", 45, 49),
                ("F_50-54", "Femenino 50-54", "F", 50, 54),
                ("F_55-59", "Femenino 55-59", "F", 55, 59),
                ("F_60+", "Femenino 60+", "F", 60, None),
            ]
            for cat_id, name, gender, min_age, max_age in categories_5y:
                cat = AwardCategory(
                    award_category_id=cat_id,
                    name=name,
                    gender=gender,
                    min_age=min_age,
                    max_age=max_age,
                    distance_ids=None  # Aplica a todas
                )
                self.race_manager.add_award_category(cat)

        elif "10 años" in preset:
            # Preset por 10 años: Sub-19, 20-29, 30-39, 40-49, 50-59, 60+
            categories_10y = [
                ("M_Sub19", "Masculino Sub-19", "M", 0, 18),
                ("M_20-29", "Masculino 20-29", "M", 20, 29),
                ("M_30-39", "Masculino 30-39", "M", 30, 39),
                ("M_40-49", "Masculino 40-49", "M", 40, 49),
                ("M_50-59", "Masculino 50-59", "M", 50, 59),
                ("M_60+", "Masculino 60+", "M", 60, None),
                ("F_Sub19", "Femenino Sub-19", "F", 0, 18),
                ("F_20-29", "Femenino 20-29", "F", 20, 29),
                ("F_30-39", "Femenino 30-39", "F", 30, 39),
                ("F_40-49", "Femenino 40-49", "F", 40, 49),
                ("F_50-59", "Femenino 50-59", "F", 50, 59),
                ("F_60+", "Femenino 60+", "F", 60, None),
            ]
            for cat_id, name, gender, min_age, max_age in categories_10y:
                cat = AwardCategory(
                    award_category_id=cat_id,
                    name=name,
                    gender=gender,
                    min_age=min_age,
                    max_age=max_age,
                    distance_ids=None  # Aplica a todas
                )
                self.race_manager.add_award_category(cat)

        self.refresh_table()
        self.award_categories_changed.emit()
        QMessageBox.information(self, "Éxito", f"Preset '{preset}' aplicado correctamente")

    def reset_to_iaaf(self):
        """Resetear categorías a IAAF por defecto"""
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Resetear todas las categorías a IAAF estándar?\n\n"
            "Esto eliminará todas las categorías personalizadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.race_manager.reset_award_categories_to_iaaf()
            self.refresh_table()
            self.award_categories_changed.emit()
            QMessageBox.information(self, "Éxito", "Categorías reseteadas a IAAF estándar")


class AwardCategoryDialog(QDialog):
    """Diálogo para crear/editar categoría de premiación"""

    def __init__(self, parent=None, race_manager: RaceManager = None, category: AwardCategory = None):
        super().__init__(parent)
        self.race_manager = race_manager
        self.category = category  # Si no es None, estamos editando
        self.result_category = None
        self.setup_ui()

        if category:
            self.load_category_data()

    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Configurar Categoría de Premiación")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Formulario
        form_layout = QGridLayout()

        # ID
        form_layout.addWidget(QLabel("ID de Categoría:"), 0, 0)
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ej: M40-49-21K")
        form_layout.addWidget(self.id_input, 0, 1)

        # Nombre
        form_layout.addWidget(QLabel("Nombre:"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ej: Masculino Master 40-49 (21K)")
        form_layout.addWidget(self.name_input, 1, 1)

        # Género
        form_layout.addWidget(QLabel("Género:"), 2, 0)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Masculino", "Femenino", "Otro", "Mixto"])
        form_layout.addWidget(self.gender_combo, 2, 1)

        # Edad mínima
        form_layout.addWidget(QLabel("Edad Mínima:"), 3, 0)
        self.min_age_spin = QSpinBox()
        self.min_age_spin.setRange(0, 120)
        self.min_age_spin.setValue(0)
        form_layout.addWidget(self.min_age_spin, 3, 1)

        # Edad máxima
        form_layout.addWidget(QLabel("Edad Máxima:"), 4, 0)
        age_max_layout = QHBoxLayout()
        self.max_age_spin = QSpinBox()
        self.max_age_spin.setRange(0, 120)
        self.max_age_spin.setValue(99)
        age_max_layout.addWidget(self.max_age_spin)
        self.no_max_age_check = QCheckBox("Sin límite")
        self.no_max_age_check.stateChanged.connect(self.toggle_max_age)
        age_max_layout.addWidget(self.no_max_age_check)
        form_layout.addLayout(age_max_layout, 4, 1)

        # Distancias
        form_layout.addWidget(QLabel("Distancias:"), 5, 0)
        distances_layout = QVBoxLayout()

        self.all_distances_check = QCheckBox("Aplicar a todas las distancias")
        self.all_distances_check.setChecked(True)
        self.all_distances_check.stateChanged.connect(self.toggle_distances_selection)
        distances_layout.addWidget(self.all_distances_check)

        self.distances_list = QListWidget()
        self.distances_list.setMaximumHeight(100)
        self.distances_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.distances_list.setEnabled(False)

        # Poblar con categorías de carrera disponibles
        if self.race_manager:
            for cat in self.race_manager.get_all_categories():
                self.distances_list.addItem(f"{cat.distance_id} - {cat.name}")

        distances_layout.addWidget(self.distances_list)
        form_layout.addLayout(distances_layout, 5, 1)

        # Descripción
        form_layout.addWidget(QLabel("Descripción:"), 6, 0)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Opcional")
        form_layout.addWidget(self.description_input, 6, 1)

        layout.addLayout(form_layout)

        # Botones
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Guardar")
        save_btn.clicked.connect(self.save_category)
        save_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def toggle_max_age(self, state):
        """Toggle edad máxima"""
        self.max_age_spin.setEnabled(state == Qt.CheckState.Unchecked.value)

    def toggle_distances_selection(self, state):
        """Toggle selección de distancias"""
        self.distances_list.setEnabled(state == Qt.CheckState.Unchecked.value)

    def load_category_data(self):
        """Cargar datos de categoría existente"""
        if not self.category:
            return

        self.id_input.setText(self.category.award_category_id)
        self.name_input.setText(self.category.name)

        # Género
        gender_map = {"M": 0, "F": 1, "O": 2, None: 3}
        self.gender_combo.setCurrentIndex(gender_map.get(self.category.gender, 3))

        # Edades
        self.min_age_spin.setValue(self.category.min_age)
        if self.category.max_age is None:
            self.no_max_age_check.setChecked(True)
            self.max_age_spin.setEnabled(False)
        else:
            self.max_age_spin.setValue(self.category.max_age)

        # Distancias
        if self.category.distance_ids is None:
            self.all_distances_check.setChecked(True)
        else:
            self.all_distances_check.setChecked(False)
            self.distances_list.setEnabled(True)
            # Seleccionar distancias correspondientes
            for i in range(self.distances_list.count()):
                item = self.distances_list.item(i)
                cat_id = item.text().split(" - ")[0]
                if cat_id in self.category.distance_ids:
                    item.setSelected(True)

        # Descripción
        if self.category.description:
            self.description_input.setText(self.category.description)

    def save_category(self):
        """Guardar categoría"""
        # Validar campos
        category_id = self.id_input.text().strip()
        name = self.name_input.text().strip()

        if not category_id or not name:
            QMessageBox.warning(self, "Error", "Completa ID y Nombre")
            return

        # Género
        gender_map = {0: "M", 1: "F", 2: "O", 3: None}
        gender = gender_map[self.gender_combo.currentIndex()]

        # Edades
        min_age = self.min_age_spin.value()
        max_age = None if self.no_max_age_check.isChecked() else self.max_age_spin.value()

        # Distancias
        if self.all_distances_check.isChecked():
            distance_ids = None
        else:
            selected_items = self.distances_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Error", "Selecciona al menos una distancia o marca 'Aplicar a todas'")
                return
            distance_ids = [item.text().split(" - ")[0] for item in selected_items]

        # Descripción
        description = self.description_input.text().strip() or None

        # Crear categoría
        try:
            self.result_category = AwardCategory(
                award_category_id=category_id,
                name=name,
                gender=gender,
                min_age=min_age,
                max_age=max_age,
                distance_ids=distance_ids,
                is_iaaf=False,  # Las personalizadas nunca son IAAF
                description=description
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creando categoría: {e}")

    def get_category(self) -> AwardCategory:
        """Obtener categoría creada/editada"""
        return self.result_category
