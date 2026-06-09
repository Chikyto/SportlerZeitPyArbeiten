from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QGroupBox, QLineEdit, QTableWidget,
                            QTableWidgetItem, QHeaderView, QTimeEdit, QSpinBox,
                            QTextEdit, QComboBox, QMessageBox, QGridLayout, QDialog)
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
    from src.core.race_tracking.models import Athlete, RaceDistance, RaceStatus
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

    def __init__(self, race_manager=None, signals=None):
        super().__init__()
        self.race_manager = race_manager if race_manager else RaceManager()
        self.signals = signals  # 🔥 Agregar soporte para señales globales

        # DEBUG: Verificar race_manager recibido
        if race_manager:
            distances = race_manager.get_all_distances()
            logger.info(f"🔍 EventConfigWidget.__init__() - RaceManager recibido con {len(distances)} distancias")
            for dist in distances:
                logger.info(f"   • {dist.distance_id}: {dist.name} ({len(dist.participants)} participantes)")
        else:
            logger.warning("⚠️  EventConfigWidget creado sin race_manager (nuevo vacío)")

        self.setup_ui()
        # Refrescar tabla para mostrar distancias existentes (cargadas desde CSV o JSON)
        self.refresh_categories_table()
        self.refresh_category_combo()
        
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

        self.load_from_chips_btn = QPushButton("Cargar desde Asignación de Chips")
        self.load_from_chips_btn.clicked.connect(self.load_distances_from_chip_assignments)
        self.load_from_chips_btn.setStyleSheet("background-color: #3b82f6; color: white;")
        buttons_layout.addWidget(self.load_from_chips_btn)

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
        
        self.start_selected_btn = QPushButton("Iniciar Distancia Seleccionada")
        self.start_selected_btn.clicked.connect(self.start_selected_category)
        self.start_selected_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        control_buttons_layout.addWidget(self.start_selected_btn)
        
        self.finish_selected_btn = QPushButton("Finalizar Distancia Seleccionada")
        self.finish_selected_btn.clicked.connect(self.finish_selected_category)
        self.finish_selected_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        control_buttons_layout.addWidget(self.finish_selected_btn)

        self.start_all_btn = QPushButton("Iniciar Todas las Distancias")
        self.start_all_btn.clicked.connect(self.start_all_categories)
        self.start_all_btn.setStyleSheet("background-color: #1e40af; color: white; font-weight: bold;")
        control_buttons_layout.addWidget(self.start_all_btn)

        control_buttons_layout.addStretch()
        control_layout.addLayout(control_buttons_layout)
        
        # Estado de categorías activas
        self.active_categories_label = QLabel("Distancias activas: Ninguna")
        self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        control_layout.addWidget(self.active_categories_label)
        
        layout.addWidget(control_group)

        # Panel de participantes de la categoría seleccionada
        participants_detail_group = QGroupBox("Participantes de la Distancia Seleccionada")
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
        self.participants_stats_label = QLabel("Selecciona una distancia para ver sus participantes")
        self.participants_stats_label.setStyleSheet("font-style: italic; color: #666;")
        participants_detail_layout.addWidget(self.participants_stats_label)

        layout.addWidget(participants_detail_group)

        # Registro de participantes (simplificado)
        participants_group = QGroupBox("Registro Rápido de Participantes")
        participants_layout = QHBoxLayout(participants_group)
        
        participants_layout.addWidget(QLabel("Chip ID:"))
        self.chip_id_input = QLineEdit()
        participants_layout.addWidget(self.chip_id_input)
        
        participants_layout.addWidget(QLabel("Distancia:"))
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
        # Crear distancias de ejemplo usando el modelo de race_tracking
        distances_data = [
            ("100k", "Ultra 100K", 100000.0, 5, "Ultramaratón de 100 kilómetros"),
            ("50k", "Trail 50K", 50000.0, 3, "Trail running de 50 kilómetros"),
            ("30k", "Mountain 30K", 30000.0, 2, "Carrera de montaña 30K"),
            ("21k", "Half Marathon", 21000.0, 1, "Media maratón")
        ]

        for dist_id, name, distance_m, checkpoints, desc in distances_data:
            distance = RaceDistance(
                distance_id=dist_id,
                name=name,
                distance_meters=distance_m,
                expected_checkpoints=checkpoints,
                participants=[],
                status=RaceStatus.PENDING,
                notes=desc
            )
            try:
                self.race_manager.add_distance(distance)
            except ValueError as e:
                logger.warning(f"No se pudo agregar distancia {dist_id}: {e}")

        self.refresh_categories_table()
        self.refresh_category_combo()
        self.categories_changed.emit()
        
    def add_new_category(self):
        """Agregar nueva distancia"""
        dialog = CategoryDialog(self)
        if dialog.exec():
            distance = dialog.get_distance()  # El dialog ahora retorna RaceDistance
            self.race_manager.add_distance(distance)
            self.refresh_categories_table()
            self.refresh_category_combo()
            self.categories_changed.emit()
            
    def edit_selected_category(self):
        """Editar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una distancia para editar")
            return

        category_id = self.categories_table.item(current_row, 0).text()
        category = self.race_manager.get_category(category_id)

        if category:
            # TODO: Implementar diálogo de edición para el nuevo modelo
            QMessageBox.information(self, "Info", "Edición de distancias próximamente")
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
            QMessageBox.warning(self, "Error", "Selecciona una distancia para eliminar")
            return
            
        category_id = self.categories_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirmar",
                                   f"¿Eliminar distancia {category_id}?",
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

    def load_distances_from_chip_assignments(self):
        """Cargar distancias automáticamente desde asignaciones de chips existentes"""
        # Obtener todas las distancias actuales
        existing_distances = self.race_manager.get_all_distances()

        # Agrupar atletas por distance_id
        distance_athletes = {}
        for distance in existing_distances:
            for athlete in distance.participants:
                if athlete.distance_id not in distance_athletes:
                    distance_athletes[athlete.distance_id] = []
                distance_athletes[athlete.distance_id].append(athlete)

        if not distance_athletes:
            QMessageBox.information(
                self,
                "Sin asignaciones",
                "No hay atletas con asignaciones de chips. Importa atletas primero desde la pestaña 'Asignación de Chips'."
            )
            return

        # Crear distancias que no existen
        created_count = 0
        updated_count = 0

        for distance_id, athletes in distance_athletes.items():
            # Verificar si la distancia ya existe
            existing = self.race_manager.get_distance(distance_id)

            if not existing:
                # Inferir nombre y distancia desde el ID
                name = self._infer_distance_name(distance_id)
                distance_meters = self._infer_distance_meters(distance_id)

                # Crear distancia con 0 checkpoints por defecto
                # El usuario puede editarlos después con "Editar Seleccionada"
                new_distance = RaceDistance(
                    distance_id=distance_id,
                    name=name,
                    distance_meters=distance_meters,
                    expected_checkpoints=0,
                    participants=athletes,
                    status=RaceStatus.PENDING,
                    notes=f"Generada automáticamente desde asignaciones de chips ({len(athletes)} participantes)"
                )

                try:
                    self.race_manager.add_distance(new_distance)
                    created_count += 1
                    logger.info(f"✅ Distancia creada: {distance_id} ({name}) con {len(athletes)} participantes")
                except ValueError as e:
                    logger.error(f"❌ Error creando distancia {distance_id}: {e}")
            else:
                # La distancia ya existe, solo actualizar conteo
                updated_count += 1

        # Refrescar UI
        self.refresh_categories_table()
        self.refresh_category_combo()
        self.categories_changed.emit()

        # Mostrar resultado
        msg_parts = []
        if created_count > 0:
            msg_parts.append(f"✅ Se crearon {created_count} distancia(s) con 0 checkpoints")
            msg_parts.append("   → Edita cada distancia para configurar sus checkpoints")
        if updated_count > 0:
            msg_parts.append(f"📊 {updated_count} distancia(s) ya existían (sin cambios)")

        if msg_parts:
            QMessageBox.information(
                self,
                "Carga desde Chips",
                "\n".join(msg_parts) + f"\n\nTotal detectadas: {len(distance_athletes)} distancia(s)"
            )
        else:
            QMessageBox.information(
                self,
                "Sin cambios",
                f"Todas las distancias ({len(distance_athletes)}) ya estaban cargadas."
            )

    def _infer_distance_name(self, distance_id: str) -> str:
        """Inferir nombre descriptivo desde el ID de distancia"""
        # Mapeo común de IDs a nombres
        name_map = {
            "100k": "Ultra 100K",
            "50k": "Trail 50K",
            "30k": "Mountain 30K",
            "21k": "Half Marathon",
            "10k": "10 Kilometers",
            "5k": "5 Kilometers",
            "42k": "Marathon",
            "ultra": "Ultra Trail"
        }

        # Buscar coincidencia exacta
        if distance_id.lower() in name_map:
            return name_map[distance_id.lower()]

        # Si no hay coincidencia, usar el ID con formato título
        return distance_id.replace("_", " ").replace("-", " ").title()

    def _infer_distance_meters(self, distance_id: str) -> float:
        """Inferir distancia en metros desde el ID"""
        # Intentar extraer número del ID
        import re
        match = re.search(r'(\d+)\s*k', distance_id.lower())
        if match:
            km = float(match.group(1))
            return km * 1000.0

        # Si no se puede inferir, usar valor por defecto
        logger.warning(f"⚠️  No se pudo inferir distancia para '{distance_id}', usando 10000m por defecto")
        return 10000.0  # 10km por defecto

    def _infer_expected_checkpoints(self, distance_id: str) -> int:
        """
        Inferir número de checkpoints esperados según la distancia

        Reglas estándar:
        - 5K, 7K: 0 checkpoints
        - 10K, 14K: 1 checkpoint
        - 21K, 24K, 30K: 2 checkpoints
        - 42K, 50K: 3 checkpoints
        - 100K: 5 checkpoints

        Args:
            distance_id: ID de la distancia (ej: "5k", "10k", "21k")

        Returns:
            int: Número de checkpoints esperados
        """
        # Mapeo directo de IDs conocidos
        checkpoint_map = {
            "5k": 0,
            "7k": 0,
            "10k": 1,
            "14k": 1,
            "21k": 2,
            "24k": 2,
            "30k": 2,
            "42k": 3,
            "50k": 3,
            "100k": 5
        }

        # Buscar coincidencia exacta
        dist_id_lower = distance_id.lower()
        if dist_id_lower in checkpoint_map:
            return checkpoint_map[dist_id_lower]

        # Si no hay coincidencia exacta, inferir según distancia en km
        import re
        match = re.search(r'(\d+)\s*k', dist_id_lower)
        if match:
            km = int(match.group(1))
            if km < 10:
                return 0
            elif km < 21:
                return 1
            elif km < 42:
                return 2
            elif km < 100:
                return 3
            else:
                return 5

        # Si no se puede inferir, retornar 0
        logger.warning(f"⚠️  No se pudo inferir checkpoints para '{distance_id}', usando 0 por defecto")
        return 0

    def start_selected_category(self):
        """Iniciar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una distancia para iniciar")
            return

        category_id = self.categories_table.item(current_row, 0).text()

        if self.race_manager.start_category(category_id):
            self.refresh_categories_table()
            self.update_active_categories_label()
            self.category_started.emit(category_id)
            self._reset_live_reads(category_id)

            # 🔥 AUTO-INICIAR ESCANEO: Emitir señal para que DetectionTab inicie automáticamente
            if self.signals:
                logger.info("🚀 Emitiendo señal auto_start_scanning para iniciar detección automáticamente")
                self.signals.auto_start_scanning.emit()
            
    def finish_selected_category(self):
        """Finalizar categoría seleccionada"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una distancia para finalizar")
            return

        category_id = self.categories_table.item(current_row, 0).text()

        if self.race_manager.finish_category(category_id):
            self.refresh_categories_table()
            self.update_active_categories_label()
            self.category_finished.emit(category_id)

    def start_all_categories(self):
        """Iniciar todas las distancias que no estén corriendo o finalizadas"""
        distances = self.race_manager.get_all_distances()

        if not distances:
            QMessageBox.information(self, "Sin distancias", "No hay distancias configuradas para iniciar")
            return

        # Filtrar distancias que pueden ser iniciadas (no RUNNING ni FINISHED)
        startable_distances = [
            dist for dist in distances
            if dist.status not in [RaceStatus.RUNNING, RaceStatus.FINISHED]
        ]

        if not startable_distances:
            QMessageBox.information(
                self,
                "Ninguna distancia disponible",
                "Todas las distancias ya están corriendo o finalizadas"
            )
            return

        # Confirmar acción
        reply = QMessageBox.question(
            self,
            "Confirmar inicio masivo",
            f"¿Iniciar {len(startable_distances)} distancia(s)?\n\n" +
            "\n".join([f"• {d.name} ({d.distance_id})" for d in startable_distances]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Iniciar todas las distancias
        started_count = 0
        failed_count = 0

        for distance in startable_distances:
            if self.race_manager.start_category(distance.distance_id):
                started_count += 1
                self.category_started.emit(distance.distance_id)
                logger.info(f"✅ Distancia iniciada: {distance.name} ({distance.distance_id})")
            else:
                failed_count += 1
                logger.error(f"❌ Error iniciando distancia: {distance.name} ({distance.distance_id})")

        # Actualizar UI
        self.refresh_categories_table()
        self.update_active_categories_label()

        # 🔥 AUTO-INICIAR ESCANEO: Emitir señal para que DetectionTab inicie automáticamente
        if started_count > 0 and self.signals:
            logger.info("🚀 Emitiendo señal auto_start_scanning para iniciar detección automáticamente")
            self.signals.auto_start_scanning.emit()

        # Mostrar resultado
        result_msg = f"✅ Se iniciaron {started_count} distancia(s) exitosamente"
        if failed_count > 0:
            result_msg += f"\n❌ {failed_count} distancia(s) fallaron al iniciar"

        QMessageBox.information(self, "Inicio masivo completado", result_msg)

    def register_participant(self):
        """Registrar participante rápidamente"""
        chip_id = self.chip_id_input.text().strip()
        distance_id = self.participant_category_combo.currentText().split(" - ")[0] if self.participant_category_combo.currentText() else ""
        participant_name = self.participant_name_input.text().strip()

        if not chip_id or not distance_id:
            QMessageBox.warning(self, "Error", "Completa Chip ID y Distancia")
            return

        try:
            # Obtener distancia
            distance = self.race_manager.get_distance(distance_id)
            if not distance:
                raise ValueError(f"Distancia {distance_id} no existe")

            # Generar dorsal automático (siguiente disponible)
            existing_bibs = [p.bib_number for p in distance.participants]
            next_bib = max(existing_bibs) + 1 if existing_bibs else 1

            # Crear atleta
            athlete = Athlete(
                tag_id=chip_id,
                bib_number=next_bib,
                name=participant_name if participant_name else f"Corredor-{chip_id}",
                distance_id=distance_id
            )

            # Agregar a distancia
            distance.add_participant(athlete)

            self.chip_id_input.clear()
            self.participant_name_input.clear()
            self.refresh_categories_table()  # Actualizar conteo de participantes
            QMessageBox.information(self, "Éxito",
                                  f"Participante {athlete.name} (#{next_bib}) registrado en {distance_id}")
            logger.info(f"✅ Atleta registrado: {athlete.name} (Chip: {chip_id}, Dorsal: {next_bib})")

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            logger.error(f"❌ Error registrando participante: {e}")
            
    def refresh_categories_table(self):
        """Actualizar tabla de distancias"""
        self.categories_table.setRowCount(0)

        # DEBUG: Verificar race_manager y distancias
        if not self.race_manager:
            logger.error("❌ race_manager es None en refresh_categories_table()")
            return

        distances = self.race_manager.get_all_distances()
        logger.info(f"🔍 EventConfigWidget.refresh_categories_table() - Distancias obtenidas: {len(distances)}")

        if not distances:
            logger.warning("⚠️  No hay distancias para mostrar en EventConfigWidget")
            return

        for distance in distances:
            row = self.categories_table.rowCount()
            self.categories_table.insertRow(row)

            # Formatear distancia (de metros a km)
            distance_km = f"{distance.distance_meters/1000:.1f} km"

            # Hora de largada (si existe)
            start_time_str = distance.start_time.strftime('%H:%M') if distance.start_time else "-"

            # Duración estimada basada en distancia (aproximado: 1 hora cada 10km)
            est_duration = int(distance.distance_meters / 10000) + 1

            self.categories_table.setItem(row, 0, QTableWidgetItem(distance.distance_id))
            self.categories_table.setItem(row, 1, QTableWidgetItem(distance.name))
            self.categories_table.setItem(row, 2, QTableWidgetItem(distance_km))
            self.categories_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            self.categories_table.setItem(row, 4, QTableWidgetItem(f"{est_duration}h"))

            # Colorear estado
            status_item = QTableWidgetItem(distance.status.value.title())
            if distance.status == RaceStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.green)
            elif distance.status == RaceStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_table.setItem(row, 5, status_item)

            # Número de participantes
            participant_count = len(distance.participants)
            self.categories_table.setItem(row, 6, QTableWidgetItem(str(participant_count)))

            # Chips asignados / Total
            chips_assigned = sum(1 for p in distance.participants if p.tag_id)
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
        """Actualizar combo de distancias"""
        self.participant_category_combo.clear()

        if not self.race_manager:
            logger.error("❌ race_manager es None en refresh_category_combo()")
            return

        distances = self.race_manager.get_all_distances()
        logger.info(f"🔍 EventConfigWidget.refresh_category_combo() - Distancias: {len(distances)}")

        for distance in distances:
            self.participant_category_combo.addItem(f"{distance.distance_id} - {distance.name}")

    def update_active_categories_label(self):
        """Actualizar label de distancias activas"""
        active = self.race_manager.get_active_distances()
        if active:
            names = [dist.name for dist in active]
            self.active_categories_label.setText(f"Distancias activas: {', '.join(names)}")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.active_categories_label.setText("Distancias activas: Ninguna")
            self.active_categories_label.setStyleSheet("font-weight: bold; font-size: 14px; color: gray;")

    def on_category_selected(self):
        """Manejar selección de distancia en la tabla"""
        current_row = self.categories_table.currentRow()
        if current_row < 0:
            self.participants_table.setRowCount(0)
            self.participants_stats_label.setText("Selecciona una distancia para ver sus participantes")
            return

        # Obtener ID de distancia
        distance_id = self.categories_table.item(current_row, 0).text()
        distance = self.race_manager.get_distance(distance_id)

        if not distance:
            return

        # Actualizar tabla de participantes
        self.refresh_participants_table(distance)

    def refresh_participants_table(self, distance):
        """Actualizar tabla de participantes de una distancia"""
        self.participants_table.setRowCount(0)

        if not distance:
            return

        participants = distance.participants
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
        logger.info("🔄 EventConfigWidget.refresh_all() llamado")

        if not self.race_manager:
            logger.error("❌ race_manager es None en refresh_all()")
            return

        distances = self.race_manager.get_all_distances()
        logger.info(f"🔍 EventConfigWidget.refresh_all() - RaceManager tiene {len(distances)} distancias")

        self.refresh_categories_table()
        self.refresh_category_combo()
        self.update_active_categories_label()

        # Refrescar tabla de participantes si hay distancia seleccionada
        current_row = self.categories_table.currentRow()
        if current_row >= 0:
            distance_id = self.categories_table.item(current_row, 0).text()
            distance = self.race_manager.get_distance(distance_id)
            if distance:
                self.refresh_participants_table(distance)

        logger.info("✅ EventConfigWidget refrescado desde otra solapa")

    def _reset_live_reads(self, distance_id: str):
        """Llamar al backend para limpiar las lecturas del live al iniciar una distancia."""
        import json, os, threading, requests
        try:
            path = 'config/api_config.json'
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cloud = data.get('cloud', data)
            api_url = cloud.get('api_url', '').rstrip('/')
            api_key = cloud.get('api_key', '')
            event_id = cloud.get('event_id', '')
            if not api_url or not api_key or not event_id:
                return

            base = api_url.removesuffix('/api/v1')

            def _post():
                try:
                    url = f"{base}/api/v1/timing/events/{event_id}/reads/reset"
                    headers = {'Authorization': f"Bearer {api_key}"}
                    r = requests.post(url, json={'distance_id': distance_id}, headers=headers, timeout=5)
                    if r.status_code in (200, 201, 204):
                        logger.info(f"☁️ Live reset OK para distancia {distance_id}")
                    else:
                        logger.warning(f"⚠️ Live reset respondió {r.status_code}: {r.text[:100]}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo resetear live: {e}")

            threading.Thread(target=_post, daemon=True).start()

        except Exception as e:
            logger.warning(f"⚠️ _reset_live_reads error: {e}")

# Dialog para agregar/editar distancias
class CategoryDialog(QDialog):
    """Dialog para crear/editar distancias"""

    def __init__(self, parent=None, distance=None):
        super().__init__(parent)
        self.distance = distance
        self.result_distance = None
        self.setup_ui()

        if distance:
            self.load_distance_data()
            
    def setup_ui(self):
        """Configurar interfaz del dialog"""
        self.setWindowTitle("Configurar Distancia")
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
        
        form_layout.addWidget(QLabel("Distancia (m):"), 2, 0)
        self.distance_input = QLineEdit()
        form_layout.addWidget(self.distance_input, 2, 1)

        form_layout.addWidget(QLabel("Modo de Carrera:"), 3, 0)
        self.race_mode_combo = QComboBox()
        self.race_mode_combo.addItems(["Lineal (Normal)", "Por Vueltas", "Por Tiempo"])
        self.race_mode_combo.setToolTip(
            "Lineal: Largada → Checkpoints → Meta\n"
            "Por Vueltas: Múltiples pasadas por misma antena\n"
            "Por Tiempo: Máximo de vueltas en X horas (ej: 7km/hora)"
        )
        self.race_mode_combo.currentIndexChanged.connect(self.on_race_mode_changed)
        form_layout.addWidget(self.race_mode_combo, 3, 1)

        form_layout.addWidget(QLabel("Checkpoints:"), 4, 0)
        checkpoints_row = QHBoxLayout()
        self.checkpoints_input = QSpinBox()
        self.checkpoints_input.setRange(0, 20)
        self.checkpoints_input.setValue(0)
        self.checkpoints_input.setToolTip("Ingresa manualmente el número de checkpoints (sin contar largada ni meta)")
        checkpoints_row.addWidget(self.checkpoints_input)

        self.checkpoint_preset_combo = QComboBox()
        self.checkpoint_preset_combo.setToolTip("Presets rápidos")
        self.checkpoint_preset_combo.addItems([
            "Preset...",
            "Sin checkpoints (0)",
            "1 checkpoint",
            "2 checkpoints",
            "3 checkpoints",
            "5 checkpoints",
        ])
        self.checkpoint_preset_combo.currentIndexChanged.connect(self._apply_checkpoint_preset)
        checkpoints_row.addWidget(self.checkpoint_preset_combo)

        checkpoints_container = QWidget()
        checkpoints_container.setLayout(checkpoints_row)
        form_layout.addWidget(checkpoints_container, 4, 1)

        form_layout.addWidget(QLabel("Duración (horas):"), 5, 0)
        self.duration_hours_input = QSpinBox()
        self.duration_hours_input.setRange(1, 48)
        self.duration_hours_input.setValue(6)
        self.duration_hours_input.setToolTip("Duración del evento (solo para modo 'Por Tiempo')")
        self.duration_hours_input.setEnabled(False)  # Inicialmente deshabilitado
        form_layout.addWidget(self.duration_hours_input, 5, 1)

        form_layout.addWidget(QLabel("Hora Largada:"), 6, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(9, 0))  # 09:00 por defecto
        form_layout.addWidget(self.start_time_input, 6, 1)

        form_layout.addWidget(QLabel("Descripción:"), 7, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addWidget(self.description_input, 7, 1)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Guardar")
        self.save_btn.clicked.connect(self.save_category)
        self.save_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)

        # Conectar señal para auto-inferir checkpoints cuando cambia el ID
        self.id_input.textChanged.connect(self.on_distance_id_changed)

    def on_race_mode_changed(self, index):
        """Manejar cambio de modo de carrera"""
        # index: 0 = Lineal, 1 = Por Vueltas, 2 = Por Tiempo

        if index == 2:  # Por Tiempo
            # Habilitar campo de duración
            self.duration_hours_input.setEnabled(True)
            self.duration_hours_input.setStyleSheet("background-color: #fef3c7;")
            # Deshabilitar checkpoints (no aplican en modo por tiempo)
            self.checkpoints_input.setEnabled(False)
            self.checkpoints_input.setValue(0)
        else:
            # Deshabilitar campo de duración
            self.duration_hours_input.setEnabled(False)
            self.duration_hours_input.setStyleSheet("")
            # Habilitar checkpoints
            self.checkpoints_input.setEnabled(True)

    def on_distance_id_changed(self, distance_id):
        """Callback cuando cambia el ID de distancia - no modifica checkpoints automáticamente"""
        pass  # Los checkpoints los define el usuario manualmente o con el combo de presets

    def _apply_checkpoint_preset(self, index):
        """Aplicar preset de checkpoints seleccionado"""
        preset_values = [None, 0, 1, 2, 3, 5]
        if index > 0 and index < len(preset_values):
            self.checkpoints_input.setValue(preset_values[index])
        self.checkpoint_preset_combo.setCurrentIndex(0)  # Resetear el combo al placeholder

    def load_distance_data(self):
        """Cargar datos de distancia existente"""
        from src.core.race_tracking.models import RaceMode

        if self.distance:
            self.id_input.setText(self.distance.distance_id)
            self.name_input.setText(self.distance.name)
            self.distance_input.setText(str(self.distance.distance_meters))
            self.checkpoints_input.setValue(self.distance.expected_checkpoints)

            # Cargar modo de carrera
            if hasattr(self.distance, 'race_mode'):
                if self.distance.race_mode == RaceMode.LINEAR:
                    self.race_mode_combo.setCurrentIndex(0)
                elif self.distance.race_mode == RaceMode.LAPS:
                    self.race_mode_combo.setCurrentIndex(1)
                elif self.distance.race_mode == RaceMode.TIME_BASED:
                    self.race_mode_combo.setCurrentIndex(2)

            # Cargar duración si existe
            if hasattr(self.distance, 'duration_hours') and self.distance.duration_hours:
                self.duration_hours_input.setValue(int(self.distance.duration_hours))

            if self.distance.start_time:
                self.start_time_input.setTime(QTime(self.distance.start_time.hour, self.distance.start_time.minute))
            self.description_input.setPlainText(self.distance.notes or "")

    def save_category(self):
        """Guardar distancia"""
        from src.core.race_tracking.models import RaceMode

        distance_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        distance_str = self.distance_input.text().strip()
        start_time_qt = self.start_time_input.time()
        description = self.description_input.toPlainText().strip()

        if not all([distance_id, name, distance_str]):
            QMessageBox.warning(self, "Error", "Completa todos los campos requeridos")
            return

        # Convertir distancia a metros
        try:
            distance_meters = float(distance_str)
        except ValueError:
            QMessageBox.warning(self, "Error", "Distancia debe ser un número")
            return

        # Convertir QTime a datetime
        start_time_py = datetime.now().replace(hour=start_time_qt.hour(), minute=start_time_qt.minute())

        # Determinar modo de carrera
        race_mode_index = self.race_mode_combo.currentIndex()
        if race_mode_index == 0:
            race_mode = RaceMode.LINEAR
        elif race_mode_index == 1:
            race_mode = RaceMode.LAPS
        else:  # 2
            race_mode = RaceMode.TIME_BASED

        # Obtener número de checkpoints y duración
        expected_checkpoints = self.checkpoints_input.value()
        duration_hours = self.duration_hours_input.value() if race_mode == RaceMode.TIME_BASED else None

        # Crear distancia
        try:
            self.result_distance = RaceDistance(
                distance_id=distance_id,
                name=name,
                distance_meters=distance_meters,
                expected_checkpoints=expected_checkpoints,
                participants=[],
                status=RaceStatus.PENDING,
                start_time=start_time_py,
                notes=description,
                race_mode=race_mode,
                duration_hours=duration_hours
            )
            self.accept()  # Cerrar con éxito
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creando distancia: {e}")

    def get_distance(self):
        """Obtener distancia creada"""
        return self.result_distance