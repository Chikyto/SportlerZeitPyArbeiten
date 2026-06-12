#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportador de PDF para Resultados de Carreras
src/utils/pdf_exporter.py
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ── Paleta de colores (igual que el frontend) ────────────────────────────────
C_NAVY       = colors.HexColor('#1e2a4a')   # encabezado de tablas
C_BLUE       = colors.HexColor('#2b6cb0')   # "Clasificación General …"
C_ORANGE     = colors.HexColor('#c05621')   # "Damas — F 20-29", subcats
C_ROW_ALT    = colors.HexColor('#f7fafc')   # fila alternada
C_RULE       = colors.HexColor('#e2e8f0')   # línea separadora
C_META       = colors.HexColor('#718096')   # texto pequeño de meta
C_WHITE      = colors.white
C_BLACK      = colors.HexColor('#1a202c')


def _pace_str(total_seconds: float, distance_meters: float) -> str:
    """Calcula ritmo en min:seg /km"""
    if not total_seconds or not distance_meters:
        return "-"
    pace_sec_km = total_seconds / (distance_meters / 1000)
    mins = int(pace_sec_km // 60)
    secs = int(pace_sec_km % 60)
    return f"{mins}:{secs:02d} /km"


def _table_style(header_color=None, no_category: bool = False) -> TableStyle:
    """Estilo de tabla estándar reutilizable"""
    hc = header_color or C_NAVY
    if no_category:
        # 5 columns: #, Atleta, Dorsal, Tiempo, Ritmo
        return TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), hc),
            ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 9),
            ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING',    (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
            ('ALIGN',         (0, 1), (0, -1), 'CENTER'),   # #
            ('ALIGN',         (2, 1), (2, -1), 'CENTER'),   # Dorsal
            ('ALIGN',         (3, 1), (3, -1), 'RIGHT'),    # Tiempo
            ('ALIGN',         (4, 1), (4, -1), 'RIGHT'),    # Ritmo
            ('TOPPADDING',    (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.25, C_RULE),
        ])
    return TableStyle([
        # Encabezado
        ('BACKGROUND',    (0, 0), (-1, 0), hc),
        ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        # Filas de datos
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
        ('ALIGN',         (0, 1), (0, -1), 'CENTER'),   # #
        ('ALIGN',         (2, 1), (2, -1), 'CENTER'),   # Dorsal
        ('ALIGN',         (3, 1), (3, -1), 'CENTER'),   # Categoría
        ('ALIGN',         (4, 1), (4, -1), 'RIGHT'),    # Tiempo
        ('ALIGN',         (5, 1), (5, -1), 'RIGHT'),    # Ritmo
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.25, C_RULE),
    ])


class PDFExporter:
    """Exportador de resultados a PDF con el estilo del frontend web"""

    # 6 cols: #, Atleta, Dorsal, Cat, Tiempo, Ritmo
    _COL_WIDTHS = [1*cm, 6.5*cm, 1.5*cm, 2.8*cm, 3*cm, 2.5*cm]
    # 5 cols: #, Atleta, Dorsal, Tiempo, Ritmo  (sin columna Categoría)
    _COL_WIDTHS_5 = [1*cm, 8.3*cm, 1.5*cm, 3.3*cm, 3.2*cm]

    def __init__(self, event_name: str = "Carrera", event_date: str = ""):
        self.event_name = event_name
        self.event_date = event_date or datetime.now().strftime("%d/%m/%Y")
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='EventTitle',
            fontSize=20, fontName='Helvetica-Bold',
            textColor=C_BLACK, spaceAfter=6, spaceBefore=0, alignment=TA_LEFT,
            leading=24,
        ))
        self.styles.add(ParagraphStyle(
            name='DistanceName',
            fontSize=13, fontName='Helvetica-Bold',
            textColor=C_NAVY, spaceAfter=4, spaceBefore=0, alignment=TA_LEFT,
            leading=16,
        ))
        self.styles.add(ParagraphStyle(
            name='MetaLine',
            fontSize=8, fontName='Helvetica',
            textColor=C_META, spaceAfter=8, alignment=TA_LEFT,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            name='SectionBlue',
            fontSize=11, fontName='Helvetica-Bold',
            textColor=C_BLUE, spaceBefore=10, spaceAfter=4, alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name='SectionOrange',
            fontSize=10, fontName='Helvetica-Bold',
            textColor=C_ORANGE, spaceBefore=8, spaceAfter=3, alignment=TA_LEFT,
        ))
        # Para el relator
        self.styles.add(ParagraphStyle(
            name='AnnouncerName',
            fontSize=18, fontName='Helvetica-Bold',
            textColor=C_BLACK, spaceAfter=4, alignment=TA_LEFT,
        ))
        # Compat con código anterior
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=11, fontName='Helvetica-Bold',
            textColor=C_BLUE, spaceBefore=10, spaceAfter=4, alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            fontSize=20, fontName='Helvetica-Bold',
            textColor=C_BLACK, spaceAfter=6, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            fontSize=13, fontName='Helvetica-Bold',
            textColor=C_NAVY, spaceAfter=4, alignment=TA_CENTER,
        ))

    # ── Encabezado de página ──────────────────────────────────────────────────

    def _header(self, story: list, distance_name: str, extra_meta: str = ""):
        story.append(Paragraph(self.event_name, self.styles['EventTitle']))
        story.append(Paragraph(distance_name, self.styles['DistanceName']))
        meta = f"Finalizado: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}"
        if extra_meta:
            meta += f"  |  {extra_meta}"
        story.append(Paragraph(meta, self.styles['MetaLine']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_RULE, spaceAfter=6))

    # ── Tabla de resultados ───────────────────────────────────────────────────

    @staticmethod
    def _strip_gender_prefix(cat_name: str) -> str:
        """'Masculino 45-49' → '45-49', 'Femenino Sub-19' → 'Sub-19'"""
        for prefix in ('No binario ', 'Masculino ', 'Femenino ',
                       'Male ', 'Female ', 'Masc ', 'Fem '):
            if cat_name.startswith(prefix):
                return cat_name[len(prefix):]
        return cat_name

    def _results_table(self, results: list, distance_meters: float = 0,
                       header_color=None,
                       athlete_cat_map: dict = None,
                       cat_mode: str = 'full') -> Table:
        """
        cat_mode:
          'full'   — nombre completo de categoría (6 cols)
          'short'  — letra género + rango edad: 'M 45-49' (6 cols, general)
          'age'    — solo rango edad: '45-49'  (6 cols, por género)
          'none'   — sin columna Categoría     (5 cols, subcats/relator)
        athlete_cat_map: {athlete_id: category_name}
        """
        if cat_mode == 'none':
            header = ['#', 'Atleta', 'Dorsal', 'Tiempo neto', 'Ritmo']
            rows = [header]
            for i, result in enumerate(results, 1):
                a = result.athlete
                t_sec = None
                if result.total_time is not None:
                    try:
                        t_sec = result.total_time.total_seconds()
                    except AttributeError:
                        t_sec = float(result.total_time)
                rows.append([str(i), a.name, str(a.bib_number),
                             result.get_formatted_time(),
                             _pace_str(t_sec, distance_meters) if distance_meters else '-'])
            t = Table(rows, colWidths=self._COL_WIDTHS_5, repeatRows=1)
            t.setStyle(_table_style(header_color, no_category=True))
            return t

        header = ['#', 'Atleta', 'Dorsal', 'Categoría', 'Tiempo neto', 'Ritmo']
        rows = [header]
        for i, result in enumerate(results, 1):
            a = result.athlete
            g = (getattr(a, 'gender', '') or '').upper()
            letter = g[0] if g else '?'
            cat_name = (athlete_cat_map or {}).get(getattr(a, 'athlete_id', ''), '') if athlete_cat_map else ''
            if cat_mode == 'short':
                age_part = self._strip_gender_prefix(cat_name) if cat_name else ''
                cat = f"{letter} {age_part}".strip() if age_part else letter
            elif cat_mode == 'age':
                cat = self._strip_gender_prefix(cat_name) if cat_name else '-'
            else:  # 'full'
                cat = cat_name or (getattr(a, 'get_award_category', lambda: None)() or
                                   f"{letter} {getattr(a, 'age_category', '') or ''}").strip()
            t_sec = None
            if result.total_time is not None:
                try:
                    t_sec = result.total_time.total_seconds()
                except AttributeError:
                    t_sec = float(result.total_time)
            rows.append([
                str(i), a.name, str(a.bib_number),
                str(cat).strip() or '-',
                result.get_formatted_time(),
                _pace_str(t_sec, distance_meters) if distance_meters else '-',
            ])
        t = Table(rows, colWidths=self._COL_WIDTHS, repeatRows=1)
        t.setStyle(_table_style(header_color))
        return t

    @staticmethod
    def _build_cat_map(results_by_award: dict, award_categories: dict) -> dict:
        """Builds {athlete_id: category_name} from results_by_award_category data."""
        m = {}
        for award_id, results in results_by_award.items():
            ac = award_categories.get(award_id)
            name = ac.name if ac else award_id
            for r in results:
                aid = getattr(r.athlete, 'athlete_id', None)
                if aid:
                    m[aid] = name
        return m

    # ── Documento completo por distancia (igual que el frontend) ─────────────

    def export_full_results(
        self,
        distance_name: str,
        distance_meters: float,
        all_results: list,
        results_by_gender: Dict[str, list],
        podiums_by_award_cat: Dict[str, list],
        award_categories: Dict,
        output_path: str,
        results_by_award_cat: Dict = None,
    ):
        """
        Genera un PDF completo con:
          - Clasificación General (todos)
          - Clasificación General Damas + subcategorías
          - Clasificación General Varones + subcategorías
          - Clasificación General No binario + subcategorías

        Idéntico en estructura al PDF exportado por el frontend web.
        """
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []
        self._header(story, distance_name)

        cat_map = self._build_cat_map(results_by_award_cat or {}, award_categories)

        # 1. Clasificación General — muestra letra de género (M/F/X)
        if all_results:
            story.append(Paragraph("Clasificación General", self.styles['SectionBlue']))
            story.append(self._results_table(all_results, distance_meters, athlete_cat_map=cat_map, cat_mode='short'))
            story.append(Spacer(1, 0.6*cm))

        # 2. Por género — sin columna Categoría (el header ya lo indica)
        gender_cfg = [
            ("M", "Clasificación General Varones", "Varones"),
            ("F", "Clasificación General Damas",   "Damas"),
            ("X", "Clasificación General No binario", "No binario"),
            ("O", "Clasificación General No binario", "No binario"),
        ]
        seen_genders = set()
        for gender_key, section_title, group_label in gender_cfg:
            results = results_by_gender.get(gender_key, [])
            if not results or gender_key in seen_genders:
                continue
            seen_genders.add(gender_key)

            story.append(Paragraph(section_title, self.styles['SectionBlue']))
            story.append(self._results_table(results, distance_meters, athlete_cat_map=cat_map, cat_mode='age'))
            story.append(Spacer(1, 0.4*cm))

            # Subcategorías — sin columna Categoría (el header naranja ya lo indica)
            for award_id, podium in sorted(podiums_by_award_cat.items()):
                if not podium:
                    continue
                gender_podium = [(pos, r) for pos, r in podium
                                 if getattr(r.athlete, 'gender', '') == gender_key]
                if not gender_podium:
                    continue
                award_cat = award_categories.get(award_id)
                cat_name = award_cat.name if award_cat else award_id
                story.append(Paragraph(
                    f"{group_label} — {cat_name}", self.styles['SectionOrange']
                ))
                rows = [['#', 'Atleta', 'Dorsal', 'Tiempo neto', 'Ritmo']]
                for pos, result in gender_podium:
                    a = result.athlete
                    t_sec = None
                    if result.total_time is not None:
                        try:
                            t_sec = result.total_time.total_seconds()
                        except AttributeError:
                            t_sec = float(result.total_time)
                    rows.append([
                        str(pos), a.name, str(a.bib_number),
                        result.get_formatted_time(),
                        _pace_str(t_sec, distance_meters) if distance_meters else '-',
                    ])
                t = Table(rows, colWidths=self._COL_WIDTHS_5, repeatRows=1)
                t.setStyle(_table_style(C_NAVY, no_category=True))
                story.append(KeepTogether([t]))
                story.append(Spacer(1, 0.3*cm))

            story.append(Spacer(1, 0.4*cm))

        doc.build(story)
        logger.info(f"✅ PDF completo generado: {output_path}")

    # ── Métodos individuales (signaturas originales, estilo mejorado) ─────────

    def export_general_classification(
        self,
        distance_name: str,
        results: list,
        output_path: str,
        distance_meters: float = 0,
    ):
        """Clasificación general (todos los participantes)"""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []
        self._header(story, distance_name)
        story.append(Paragraph("Clasificación General", self.styles['SectionBlue']))
        story.append(self._results_table(results, distance_meters))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"Total participantes: {len(results)}",
            self.styles['MetaLine']
        ))
        doc.build(story)
        logger.info(f"✅ PDF clasificación general: {output_path}")

    def export_classification_by_gender(
        self,
        distance_name: str,
        results_by_gender: Dict[str, list],
        output_path: str,
        distance_meters: float = 0,
    ):
        """Clasificación separada por género"""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []
        self._header(story, distance_name)

        gender_labels = {
            "M": ("Clasificación General Varones", C_NAVY),
            "F": ("Clasificación General Damas",   C_NAVY),
            "X": ("Clasificación General No binario", C_NAVY),
            "O": ("Clasificación General No binario", C_NAVY),
        }
        seen = set()
        for key in ["M", "F", "X", "O"]:
            results = results_by_gender.get(key, [])
            if not results or key in seen:
                continue
            seen.add(key)
            label, hc = gender_labels.get(key, (key, C_NAVY))
            story.append(Paragraph(label, self.styles['SectionBlue']))
            story.append(self._results_table(results, distance_meters, hc))
            story.append(Spacer(1, 0.6*cm))

        doc.build(story)
        logger.info(f"✅ PDF por género: {output_path}")

    def export_classification_by_category(
        self,
        distance_name: str,
        results_by_category: Dict[str, list],
        output_path: str,
        distance_meters: float = 0,
    ):
        """Clasificación por categorías de premiación"""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []
        self._header(story, distance_name)

        for category_id, results in sorted(results_by_category.items()):
            if not results:
                continue
            story.append(Paragraph(category_id, self.styles['SectionOrange']))
            story.append(self._results_table(results, distance_meters))
            story.append(Spacer(1, 0.5*cm))

        doc.build(story)
        logger.info(f"✅ PDF por categorías: {output_path}")

    def export_announcer_format(
        self,
        distance_name: str,
        results: list,
        output_path: str,
        distance_meters: float = 0,
    ):
        """Formato especial para relator — letra grande"""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []
        self._header(story, distance_name, extra_meta="FORMATO RELATOR")

        col_w = [1.2*cm, 7*cm, 1.8*cm, 3*cm, 3.5*cm]
        header = ['#', 'Atleta', 'Dorsal', 'Tiempo neto', 'Ritmo']

        rows = [header]
        for i, result in enumerate(results[:30], 1):
            a = result.athlete
            t_sec = None
            if result.total_time is not None:
                try:
                    t_sec = result.total_time.total_seconds()
                except AttributeError:
                    t_sec = float(result.total_time)
            rows.append([
                str(i), a.name, str(a.bib_number),
                result.get_formatted_time(),
                _pace_str(t_sec, distance_meters) if distance_meters else '-',
            ])

        style = TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), C_NAVY),
            ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 11),
            ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
            ('TOPPADDING',    (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 12),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
            ('ALIGN',         (0, 1), (0, -1), 'CENTER'),
            ('ALIGN',         (2, 1), (2, -1), 'CENTER'),
            ('ALIGN',         (3, 1), (3, -1), 'RIGHT'),
            ('ALIGN',         (4, 1), (4, -1), 'RIGHT'),
            ('TOPPADDING',    (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.25, C_RULE),
        ])
        t = Table(rows, colWidths=col_w, repeatRows=1)
        t.setStyle(style)
        story.append(t)

        doc.build(story)
        logger.info(f"✅ PDF relator: {output_path}")

    # ── Multi-distancia (todas en un solo PDF) ────────────────────────────────

    def export_multi_distance(
        self,
        distances_data: list,
        kind: str,
        output_path: str,
    ):
        """
        Genera un PDF con todas las distancias, separadas por salto de página.

        Args:
            distances_data: lista de dicts con claves:
                - distance: objeto RaceDistance
                - all_results: lista de AthleteResult (general)
                - results_by_gender: dict {gender: [results]}
                - podiums_by_award_cat: dict {award_id: [(pos, result)]}
                - award_categories: dict {award_id: AwardCategory}
            kind: 'full' | 'gender' | 'categories' | 'announcer'
            output_path: ruta del PDF de salida
        """
        from reportlab.platypus import PageBreak

        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )
        story = []

        for i, data in enumerate(distances_data):
            distance = data['distance']
            dm = getattr(distance, 'distance_meters', 0)

            if i > 0:
                story.append(PageBreak())

            self._header(story, distance.name)

            if kind == 'full':
                all_r = data.get('all_results', [])
                by_gender = data.get('results_by_gender', {})
                podiums = data.get('podiums_by_award_cat', {})
                award_cats = data.get('award_categories', {})
                by_award = data.get('results_by_category', {})

                cat_map = self._build_cat_map(by_award, award_cats)

                if all_r:
                    story.append(Paragraph("Clasificación General", self.styles['SectionBlue']))
                    story.append(self._results_table(all_r, dm, athlete_cat_map=cat_map, cat_mode='short'))
                    story.append(Spacer(1, 0.6*cm))

                seen = set()
                for gk, sec_title, grp_label in [
                    ("M", "Clasificación General Varones", "Varones"),
                    ("F", "Clasificación General Damas",   "Damas"),
                    ("X", "Clasificación General No binario", "No binario"),
                    ("O", "Clasificación General No binario", "No binario"),
                ]:
                    results = by_gender.get(gk, [])
                    if not results or gk in seen:
                        continue
                    seen.add(gk)
                    story.append(Paragraph(sec_title, self.styles['SectionBlue']))
                    story.append(self._results_table(results, dm, athlete_cat_map=cat_map, cat_mode='age'))
                    story.append(Spacer(1, 0.4*cm))
                    for award_id, podium in sorted(podiums.items()):
                        gender_podium = [(p, r) for p, r in podium
                                        if getattr(r.athlete, 'gender', '') == gk]
                        if not gender_podium:
                            continue
                        ac = award_cats.get(award_id)
                        story.append(Paragraph(
                            f"{grp_label} — {ac.name if ac else award_id}",
                            self.styles['SectionOrange']
                        ))
                        rows = [['#', 'Atleta', 'Dorsal', 'Tiempo neto', 'Ritmo']]
                        for pos, result in gender_podium:
                            a = result.athlete
                            t_sec = None
                            if result.total_time is not None:
                                try:
                                    t_sec = result.total_time.total_seconds()
                                except AttributeError:
                                    t_sec = float(result.total_time)
                            rows.append([str(pos), a.name, str(a.bib_number),
                                         result.get_formatted_time(),
                                         _pace_str(t_sec, dm) if dm else '-'])
                        t = Table(rows, colWidths=self._COL_WIDTHS_5, repeatRows=1)
                        t.setStyle(_table_style(C_NAVY, no_category=True))
                        story.append(KeepTogether([t]))
                        story.append(Spacer(1, 0.3*cm))
                    story.append(Spacer(1, 0.4*cm))

            elif kind == 'gender':
                seen = set()
                for gk in ["M", "F", "X", "O"]:
                    results = data.get('results_by_gender', {}).get(gk, [])
                    if not results or gk in seen:
                        continue
                    seen.add(gk)
                    labels = {"M": "Clasificación General Varones",
                              "F": "Clasificación General Damas",
                              "X": "Clasificación General No binario",
                              "O": "Clasificación General No binario"}
                    story.append(Paragraph(labels[gk], self.styles['SectionBlue']))
                    story.append(self._results_table(results, dm, cat_mode='age'))
                    story.append(Spacer(1, 0.6*cm))

            elif kind == 'categories':
                award_cats = data.get('award_categories', {})
                for cat_id, results in sorted(data.get('results_by_category', {}).items()):
                    if not results:
                        continue
                    ac = award_cats.get(cat_id)
                    story.append(Paragraph(ac.name if ac else cat_id, self.styles['SectionOrange']))
                    story.append(self._results_table(results, dm, cat_mode='none'))
                    story.append(Spacer(1, 0.5*cm))

            elif kind == 'announcer':
                story.append(Paragraph("Clasificación General", self.styles['SectionBlue']))
                story.append(self._results_table(data.get('all_results', [])[:30], dm, cat_mode='none'))

        doc.build(story)
        logger.info(f"✅ PDF multi-distancia ({kind}): {output_path}")
