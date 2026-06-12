#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportador de PDF para Resultados de Carreras
src/utils/pdf_exporter.py

Genera PDFs para:
- Clasificación general
- Clasificación por género
- Clasificación por categorías IAAF
- Formato especial para relator
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PDFExporter:
    """
    Exportador de resultados a PDF

    Genera documentos profesionales con clasificaciones y podios
    """

    def __init__(self, event_name: str = "Carrera", event_date: str = ""):
        """
        Args:
            event_name: Nombre del evento
            event_date: Fecha del evento
        """
        self.event_name = event_name
        self.event_date = event_date or datetime.now().strftime("%Y-%m-%d")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configurar estilos personalizados"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0f3460'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Sección
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#e94560'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

    def export_general_classification(
        self,
        distance_name: str,
        results: List,
        output_path: str
    ):
        """
        Exportar clasificación general (todos los participantes)

        Args:
            distance_name: Nombre de la distancia (ej: "21 Kilómetros")
            results: Lista de AthleteResult ordenados por posición
            output_path: Ruta del archivo PDF de salida
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Encabezado
        story.append(Paragraph(self.event_name, self.styles['CustomTitle']))
        story.append(Paragraph(f"Fecha: {self.event_date}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Clasificación General - {distance_name}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.5*cm))

        # Tabla de resultados
        data = [['Pos', 'Dorsal', 'Nombre', 'Género', 'Categoría', 'Tiempo']]

        for result in results:
            athlete = result.athlete
            data.append([
                str(result.position or '-'),
                str(athlete.bib_number),
                athlete.name,
                athlete.gender or '-',
                athlete.get_award_category() or '-',
                result.get_formatted_time()
            ])

        table = Table(data, colWidths=[2*cm, 2.5*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Datos
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Posición centrada
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Dorsal centrado
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        story.append(table)
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"Total de participantes: {len(results)}",
            self.styles['Normal']
        ))

        doc.build(story)
        logger.info(f"✅ PDF generado: {output_path}")

    def export_classification_by_gender(
        self,
        distance_name: str,
        results_by_gender: Dict[str, List],
        output_path: str
    ):
        """
        Exportar clasificación por género (Masculino, Femenino, Otro)

        Args:
            distance_name: Nombre de la distancia
            results_by_gender: Dict con {"M": [...], "F": [...], "Otro": [...]}
            output_path: Ruta del archivo PDF
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Encabezado
        story.append(Paragraph(self.event_name, self.styles['CustomTitle']))
        story.append(Paragraph(f"Fecha: {self.event_date}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Clasificación por Género - {distance_name}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.8*cm))

        gender_names = {
            "M": "Masculino",
            "F": "Femenino",
            "X": "No Binario",
            "O": "Otro",
            "Otro": "Otro",
        }
        gender_order = ["M", "F", "X", "O", "Otro"]
        present_genders = [g for g in gender_order if results_by_gender.get(g)]
        # Also include any unexpected keys not in the predefined order
        for g in results_by_gender:
            if g not in gender_order and results_by_gender.get(g):
                present_genders.append(g)

        for gender in present_genders:
            results = results_by_gender.get(gender, [])
            if not results:
                continue

            # Título de sección
            section_title = gender_names.get(gender, gender)
            story.append(Paragraph(section_title, self.styles['SectionHeader']))
            story.append(Spacer(1, 0.3*cm))

            # Tabla
            data = [['Pos', 'Dorsal', 'Nombre', 'Categoría', 'Tiempo']]
            for i, result in enumerate(results, 1):
                athlete = result.athlete
                data.append([
                    str(i),
                    str(athlete.bib_number),
                    athlete.name,
                    athlete.get_award_category() or '-',
                    result.get_formatted_time()
                ])

            table = Table(data, colWidths=[2*cm, 2.5*cm, 7*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffeef1')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.8*cm))

        doc.build(story)
        logger.info(f"✅ PDF por género generado: {output_path}")

    def export_classification_by_category(
        self,
        distance_name: str,
        results_by_category: Dict[str, List],
        output_path: str
    ):
        """
        Exportar clasificación por categorías IAAF

        Args:
            distance_name: Nombre de la distancia
            results_by_category: Dict con {category_id: [results]}
            output_path: Ruta del archivo PDF
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Encabezado
        story.append(Paragraph(self.event_name, self.styles['CustomTitle']))
        story.append(Paragraph(f"Fecha: {self.event_date}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Clasificación por Categorías - {distance_name}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.8*cm))

        for category_id, results in sorted(results_by_category.items()):
            if not results:
                continue

            # Título de categoría
            story.append(Paragraph(f"📊 {category_id}", self.styles['SectionHeader']))
            story.append(Spacer(1, 0.3*cm))

            # Tabla
            data = [['Pos', 'Dorsal', 'Nombre', 'Tiempo']]
            for i, result in enumerate(results, 1):
                athlete = result.athlete
                data.append([
                    str(i),
                    str(athlete.bib_number),
                    athlete.name,
                    result.get_formatted_time()
                ])

            table = Table(data, colWidths=[2*cm, 2.5*cm, 9*cm, 3.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f4f8')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.8*cm))

        doc.build(story)
        logger.info(f"✅ PDF por categorías generado: {output_path}")

    def export_announcer_format(
        self,
        distance_name: str,
        results: List,
        output_path: str
    ):
        """
        Exportar formato especial para relator (letra grande, info clara)

        Args:
            distance_name: Nombre de la distancia
            results: Lista de resultados
            output_path: Ruta del archivo PDF
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []

        # Encabezado
        story.append(Paragraph(f"🎤 {self.event_name}", self.styles['CustomTitle']))
        story.append(Paragraph(f"FORMATO PARA RELATOR - {distance_name}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 1*cm))

        for result in results[:20]:  # Top 20 para relator
            athlete = result.athlete

            # Nombre grande
            name_style = ParagraphStyle(
                name='AnnouncerName',
                fontSize=18,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#1a1a2e'),
                spaceAfter=4
            )
            story.append(Paragraph(f"🏃 {athlete.name}", name_style))

            # Info en tabla
            info_data = [
                ['Posición General:', str(result.position or '-')],
                ['Dorsal:', str(athlete.bib_number)],
                ['Género:', athlete.gender or '-'],
                ['Categoría:', athlete.get_award_category() or '-'],
                ['Tiempo:', result.get_formatted_time()],
            ]

            info_table = Table(info_data, colWidths=[5*cm, 8*cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0f3460')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))

            story.append(info_table)
            story.append(Spacer(1, 0.8*cm))

            # Línea separadora
            story.append(Paragraph("─" * 80, self.styles['Normal']))
            story.append(Spacer(1, 0.6*cm))

        doc.build(story)
        logger.info(f"✅ PDF para relator generado: {output_path}")
