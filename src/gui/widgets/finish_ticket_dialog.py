#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo de Ticket de Llegada
src/gui/widgets/finish_ticket_dialog.py

Muestra un ticket imprimible cuando un atleta cruza la meta
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FinishTicketDialog(QDialog):
    """
    Diálogo que muestra el ticket de llegada de un atleta

    Se puede imprimir o guardar como PDF
    """

    def __init__(
        self,
        athlete_name: str,
        distance_name: str,
        bib_number: int,
        finish_time: str,
        position_overall: int,
        position_gender: int,
        position_category: int,
        gender: str,
        category: str,
        event_name: str = "Carrera",
        parent=None
    ):
        super().__init__(parent)
        self.athlete_name = athlete_name
        self.distance_name = distance_name
        self.bib_number = bib_number
        self.finish_time = finish_time
        self.position_overall = position_overall
        self.position_gender = position_gender
        self.position_category = position_category
        self.gender = gender
        self.category = category
        self.event_name = event_name

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz"""
        self.setWindowTitle("🏁 Ticket de Llegada")
        self.setMinimumWidth(450)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Frame del ticket
        ticket_frame = QFrame()
        ticket_frame.setFrameShape(QFrame.Shape.Box)
        ticket_frame.setLineWidth(3)
        ticket_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 3px solid #1a1a2e;
                border-radius: 8px;
                margin: 10px;
                padding: 20px;
            }
        """)
        ticket_layout = QVBoxLayout(ticket_frame)
        ticket_layout.setSpacing(12)

        # Encabezado del evento
        header_label = QLabel(f"🏁 {self.event_name}")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #1a1a2e; padding: 10px 0;")
        ticket_layout.addWidget(header_label)

        # Distancia
        distance_label = QLabel(f"📍 {self.distance_name}")
        distance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        distance_label.setFont(QFont("Helvetica", 14))
        distance_label.setStyleSheet("color: #0f3460; padding: 5px 0;")
        ticket_layout.addWidget(distance_label)

        # Línea separadora
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: #e94560; min-height: 2px;")
        ticket_layout.addWidget(separator1)

        # Información del atleta
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Dorsal
        dorsal_label = QLabel(f"Dorsal: #{self.bib_number}")
        dorsal_label.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        dorsal_label.setStyleSheet("color: #1a1a2e;")
        info_layout.addWidget(dorsal_label)

        # Nombre (grande y destacado)
        name_label = QLabel(self.athlete_name)
        name_label.setFont(QFont("Helvetica", 22, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #e94560; padding: 8px 0;")
        info_layout.addWidget(name_label)

        # Tiempo
        time_label = QLabel(f"⏱️  Tiempo: {self.finish_time}")
        time_label.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        time_label.setStyleSheet("color: #0f3460;")
        info_layout.addWidget(time_label)

        ticket_layout.addLayout(info_layout)

        # Línea separadora
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #e94560; min-height: 2px;")
        ticket_layout.addWidget(separator2)

        # Posiciones
        positions_layout = QVBoxLayout()
        positions_layout.setSpacing(6)

        # Posición general
        pos_general = QLabel(f"🥇 Posición General: {self.position_overall}°")
        pos_general.setFont(QFont("Helvetica", 14, QFont.Weight.Bold))
        pos_general.setStyleSheet("color: #1a1a2e;")
        positions_layout.addWidget(pos_general)

        # Posición por género
        gender_icon = "♂️" if self.gender == "M" else "♀️" if self.gender == "F" else "👤"
        gender_name = "Masculino" if self.gender == "M" else "Femenino" if self.gender == "F" else "Otro"
        pos_gender = QLabel(f"{gender_icon} Posición {gender_name}: {self.position_gender}°")
        pos_gender.setFont(QFont("Helvetica", 14))
        pos_gender.setStyleSheet("color: #0f3460;")
        positions_layout.addWidget(pos_gender)

        # Posición por categoría
        pos_category = QLabel(f"📊 Categoría {self.category}: {self.position_category}°")
        pos_category.setFont(QFont("Helvetica", 14))
        pos_category.setStyleSheet("color: #0f3460;")
        positions_layout.addWidget(pos_category)

        ticket_layout.addLayout(positions_layout)

        # Fecha y hora actual
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        footer_label = QLabel(f"Generado: {now}")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setFont(QFont("Helvetica", 9))
        footer_label.setStyleSheet("color: gray; padding-top: 10px;")
        ticket_layout.addWidget(footer_label)

        layout.addWidget(ticket_frame)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(20, 10, 20, 20)

        # Botón Imprimir
        print_btn = QPushButton("🖨️  Imprimir")
        print_btn.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1a4d7a;
            }
        """)
        print_btn.clicked.connect(self.print_ticket)
        buttons_layout.addWidget(print_btn)

        # Botón Guardar PDF
        pdf_btn = QPushButton("💾 Guardar PDF")
        pdf_btn.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d63651;
            }
        """)
        pdf_btn.clicked.connect(self.save_as_pdf)
        buttons_layout.addWidget(pdf_btn)

        # Botón Cerrar
        close_btn = QPushButton("❌ Cerrar")
        close_btn.setFont(QFont("Helvetica", 12))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def print_ticket(self):
        """Imprimir el ticket"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            print_dialog = QPrintDialog(printer, self)

            if print_dialog.exec() == QDialog.DialogCode.Accepted:
                # Renderizar el ticket
                self.render(printer)
                logger.info(f"✅ Ticket impreso: {self.athlete_name}")
                QMessageBox.information(
                    self,
                    "Impresión Exitosa",
                    f"Ticket de {self.athlete_name} enviado a impresora."
                )
        except Exception as e:
            logger.error(f"❌ Error imprimiendo ticket: {e}")
            QMessageBox.critical(
                self,
                "Error de Impresión",
                f"No se pudo imprimir el ticket:\n{str(e)}"
            )

    def save_as_pdf(self):
        """Guardar ticket como PDF"""
        try:
            # Generar nombre de archivo sugerido
            safe_name = self.athlete_name.replace(" ", "_")
            suggested_filename = f"ticket_{safe_name}_{self.bib_number}.pdf"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Ticket como PDF",
                suggested_filename,
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Crear printer para PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)

            # Renderizar
            self.render(printer)

            logger.info(f"✅ Ticket guardado como PDF: {file_path}")
            QMessageBox.information(
                self,
                "PDF Guardado",
                f"Ticket guardado exitosamente:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"❌ Error guardando PDF: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el PDF:\n{str(e)}"
            )
