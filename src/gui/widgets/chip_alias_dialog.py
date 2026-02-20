"""
Diálogo para registrar chips con IDs alternativos (aliases)

Cuando un chip físico es detectado por TCP/IP con un ID diferente al que
USB reporta, este diálogo permite al usuario asociarlo al atleta correcto.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ChipAliasDialog(QDialog):
    """
    Diálogo que aparece cuando se detecta un chip desconocido.

    Permite al usuario indicar a qué atleta pertenece ese chip,
    registrando el ID alternativo como alias del chip principal.
    """

    # Señal emitida cuando el usuario confirma: (alias_tag_id, athlete_id)
    alias_registered = pyqtSignal(str, str)

    def __init__(self, unknown_tag_id: str, athletes_with_chips: list, parent=None):
        """
        Args:
            unknown_tag_id: ID del chip desconocido (ej: "E3806894")
            athletes_with_chips: Lista de tuplas (Athlete, distance_name) con chip asignado
            parent: Widget padre
        """
        super().__init__(parent)
        self.unknown_tag_id = unknown_tag_id
        self.athletes_with_chips = athletes_with_chips
        self.selected_athlete_id = None

        self.setWindowTitle("Chip Desconocido Detectado")
        self.setMinimumWidth(600)
        self.setMinimumHeight(420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Banner de alerta ---
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        banner_layout = QVBoxLayout(banner)

        title = QLabel("⚠️  Chip RFID Desconocido Detectado")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        title.setStyleSheet("color: #856404;")
        banner_layout.addWidget(title)

        info = QLabel(
            f"El chip con ID  <b>{self.unknown_tag_id}</b>  fue detectado por la antena de carrera "
            f"pero no está registrado en la base de datos.\n\n"
            f"Esto ocurre cuando el mismo chip físico reporta IDs diferentes según el escáner "
            f"(ej: USB → '0818', TCP/IP → 'E3806894').\n\n"
            f"Seleccioná el atleta al que pertenece este chip para registrar el ID alternativo."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #533f03;")
        banner_layout.addWidget(info)

        layout.addWidget(banner)

        # --- Buscador ---
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar atleta:")
        search_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre, dorsal o chip actual...")
        self.search_input.textChanged.connect(self.filter_athletes)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # --- Tabla de atletas con chip ---
        table_label = QLabel("Atletas con chip asignado:")
        table_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(table_label)

        self.athletes_table = QTableWidget()
        self.athletes_table.setColumnCount(4)
        self.athletes_table.setHorizontalHeaderLabels([
            "Dorsal", "Nombre", "Chip actual (USB)", "Distancia"
        ])
        self.athletes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.athletes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.athletes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.athletes_table.setAlternatingRowColors(True)
        self.athletes_table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.athletes_table)

        self.populate_athletes_table(self.athletes_with_chips)

        # --- Confirmación ---
        self.confirm_label = QLabel("")
        self.confirm_label.setStyleSheet("color: #0f3460; font-style: italic; padding: 4px;")
        layout.addWidget(self.confirm_label)

        # --- Botones ---
        buttons_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Ignorar (no es de estos atletas)")
        self.cancel_btn.setStyleSheet("color: #666;")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        buttons_layout.addStretch()

        self.register_btn = QPushButton("✅ Registrar Alias")
        self.register_btn.setEnabled(False)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
            QPushButton:hover:enabled {
                background-color: #059669;
            }
        """)
        self.register_btn.clicked.connect(self.confirm_alias)
        buttons_layout.addWidget(self.register_btn)

        layout.addLayout(buttons_layout)

    def populate_athletes_table(self, athletes_with_chips: list):
        """Llenar la tabla con atletas que tienen chip asignado"""
        self.athletes_table.setRowCount(0)
        for athlete, distance_name in athletes_with_chips:
            row = self.athletes_table.rowCount()
            self.athletes_table.insertRow(row)

            bib_item = QTableWidgetItem(str(athlete.bib_number))
            bib_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.athletes_table.setItem(row, 0, bib_item)

            self.athletes_table.setItem(row, 1, QTableWidgetItem(athlete.name))

            chip_item = QTableWidgetItem(athlete.tag_id)
            chip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.athletes_table.setItem(row, 2, chip_item)

            self.athletes_table.setItem(row, 3, QTableWidgetItem(distance_name))

            # Guardar athlete_id como dato oculto en la columna del nombre
            self.athletes_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, athlete.athlete_id)

    def filter_athletes(self, text: str):
        """Filtrar la tabla por nombre, dorsal o chip"""
        text = text.lower().strip()
        for row in range(self.athletes_table.rowCount()):
            name = self.athletes_table.item(row, 1).text().lower()
            bib = self.athletes_table.item(row, 0).text().lower()
            chip = self.athletes_table.item(row, 2).text().lower()
            visible = not text or text in name or text in bib or text in chip
            self.athletes_table.setRowHidden(row, not visible)

    def on_selection_changed(self):
        """Actualizar estado del botón según selección"""
        selected_rows = self.athletes_table.selectedItems()
        if selected_rows:
            row = self.athletes_table.currentRow()
            athlete_name = self.athletes_table.item(row, 1).text()
            athlete_chip = self.athletes_table.item(row, 2).text()
            self.selected_athlete_id = self.athletes_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            self.confirm_label.setText(
                f"✓ Registrar '{self.unknown_tag_id}' como alias del chip '{athlete_chip}' "
                f"de {athlete_name}"
            )
            self.register_btn.setEnabled(True)
        else:
            self.selected_athlete_id = None
            self.confirm_label.setText("")
            self.register_btn.setEnabled(False)

    def confirm_alias(self):
        """Confirmar y emitir señal de registro"""
        if self.selected_athlete_id:
            self.alias_registered.emit(self.unknown_tag_id, self.selected_athlete_id)
            self.accept()
