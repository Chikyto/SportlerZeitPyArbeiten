#!/usr/bin/env python3
"""
Clasificaciones SportlerZeit — Concarán 2026.
Fuente: Excel corregido por el usuario. Estética original SportlerZeit.
"""
import csv, sqlite3, openpyxl
from datetime import datetime, date
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, PageBreak, KeepTogether, Image, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

XLS      = '/root/.claude/uploads/328ec440-d350-5747-b245-4c32d39897d0/751a1021-clasificaciones_concaran2026.xlsx'
CSV_PATH = '/root/.claude/uploads/328ec440-d350-5747-b245-4c32d39897d0/4f6efa3e-conca.csv'
DB_PATH  = '/root/.claude/uploads/328ec440-d350-5747-b245-4c32d39897d0/d630824d-race_event.db'
LOGO     = '/tmp/claude-0/-home-user-SportlerZeitPyArbeiten/328ec440-d350-5747-b245-4c32d39897d0/images/5.jpg'
OUT_PDF  = '/tmp/claude-0/-home-user-SportlerZeitPyArbeiten/328ec440-d350-5747-b245-4c32d39897d0/scratchpad/clasificaciones_final.pdf'

RACE_DATE = date(2026, 9, 26)

# ── Colores ────────────────────────────────────────────────────────────────────
BLUE   = colors.HexColor('#1565C0')
LBLUE  = colors.HexColor('#E3F2FD')
GREEN  = colors.HexColor('#1B5E20')
LGREEN = colors.HexColor('#E8F5E9')
PINK   = colors.HexColor('#880E4F')
LPINK  = colors.HexColor('#FCE4EC')
DGRAY  = colors.HexColor('#212121')
MGRAY  = colors.HexColor('#757575')
LGRAY  = colors.HexColor('#F5F5F5')
BORDER = colors.HexColor('#CFD8DC')
WHITE  = colors.white

# ── Utilidades ─────────────────────────────────────────────────────────────────
def fmt_time(sec):
    if sec is None: return '—'
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'

def parse_time_str(s):
    if not s: return None
    p = str(s).strip().split(':')
    try:
        if len(p) == 2: return int(p[0]) * 60 + int(p[1])
        if len(p) == 3: return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
    except: return None

def age_on_race(dob):
    if not dob: return None
    return RACE_DATE.year - dob.year - ((RACE_DATE.month, RACE_DATE.day) < (dob.month, dob.day))

def assign_cat(gender, age, award_cats):
    if not age or not gender: return None, None
    for cid, name, g, mina, maxa in award_cats:
        if g != gender: continue
        if maxa is None:
            if age >= mina: return cid, name
        elif mina <= age <= maxa: return cid, name
    return None, None

# ── Cargar datos de referencia ─────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
award_cats = conn.execute(
    'SELECT award_category_id,name,gender,min_age,max_age FROM award_categories ORDER BY gender,min_age'
).fetchall()
conn.close()

dob_by_dorsal = {}
with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        dorsal = str(r.get('N° Pecho', '')).strip()
        fn = str(r.get('Fecha Nacimiento', '')).strip()
        if not dorsal or not fn: continue
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                dob_by_dorsal[dorsal] = datetime.strptime(fn, fmt).date()
                break
            except: pass

# ── Leer generales del Excel corregido ────────────────────────────────────────
wb = openpyxl.load_workbook(XLS, data_only=True)

def read_general_sheet(ws, default_gender):
    rows = list(ws.iter_rows(values_only=True))
    hdr_idx = next((i for i, r in enumerate(rows) if r and
                    any(str(c or '').upper() in ('PUESTO', 'APELLIDO Y NOMBRE') for c in r)), None)
    if hdr_idx is None: return []
    hdr = [str(c or '').strip().upper() for c in rows[hdr_idx]]
    athletes = []
    for pos, row in enumerate(rows[hdr_idx + 1:], 1):
        if not row or not row[0]: continue
        d = {hdr[i]: (row[i] if i < len(row) else None) for i in range(len(hdr))}
        name = str(d.get('APELLIDO Y NOMBRE', '') or '').strip()
        if not name: continue
        dorsal   = str(d.get('DORSAL', '') or '').strip()
        time_str = str(d.get('TIEMPO', '') or '').strip()
        nota     = str(d.get('NOTA', '') or '').strip()
        net = parse_time_str(time_str)
        if net is None: continue
        dob = dob_by_dorsal.get(dorsal)
        age = age_on_race(dob)
        cid, cname = assign_cat(default_gender, age, award_cats)
        athletes.append({
            'pos': pos, 'nombre': name, 'dorsal': dorsal,
            'genero': default_gender, 'net': net,
            'cat_id': cid, 'cat_name': cname,
            'nota': nota,
        })
    return athletes

gen_m5  = read_general_sheet(wb['Varones 5 km'],  'M')
gen_f5  = read_general_sheet(wb['Damas 5 km'],    'F')
gen_m10 = read_general_sheet(wb['Varones 10 km'], 'M')
gen_f10 = read_general_sheet(wb['Damas 10 km'],   'F')

# Orden de llegada: merge + sort por net
def make_orden(athletes):
    s = sorted(athletes, key=lambda x: x['net'])
    for i, a in enumerate(s, 1):
        a['llegada_pos'] = i
    return s

orden_5k  = make_orden(gen_m5  + gen_f5)
orden_10k = make_orden(gen_m10 + gen_f10)

# ── Estilos de párrafo ─────────────────────────────────────────────────────────
def P(text, **kw):
    defaults = dict(fontName='Helvetica', fontSize=9, textColor=DGRAY, spaceAfter=0)
    defaults.update(kw)
    return Paragraph(str(text), ParagraphStyle('p', **defaults))

def section_title(text, color=BLUE):
    return Paragraph(f'<b>{text}</b>',
                     ParagraphStyle('st', fontName='Helvetica-Bold', fontSize=14,
                                    textColor=color, spaceBefore=6, spaceAfter=3))

def sub_title(text, color=MGRAY):
    return Paragraph(text, ParagraphStyle('sub', fontName='Helvetica', fontSize=8,
                                          textColor=color, spaceAfter=4))

# ── Tabla de resultados ────────────────────────────────────────────────────────
def result_table(athletes, cols, cws, hdr_bg=DGRAY, row_alt=LBLUE):
    rows = [cols]
    for i, a in enumerate(athletes, 1):
        bold = i <= 3
        rank = Paragraph(f'<b><font color="#1565C0">{i}°</font></b>',
                         ParagraphStyle('r', fontName='Helvetica-Bold', fontSize=8,
                                        alignment=TA_CENTER))
        nota_str = f' <i><font color="#757575">*{a["nota"]}</font></i>' if a.get('nota') else ''
        nombre = Paragraph(
            (f'<b>{a["nombre"]}</b>' if bold else a['nombre']) + nota_str,
            ParagraphStyle('n', fontName='Helvetica-Bold' if bold else 'Helvetica', fontSize=8))
        row = [rank, a['dorsal'], nombre]
        col_names_lower = [c.lower() if isinstance(c, str) else '' for c in cols]
        if 'g.' in col_names_lower:
            g_label = 'V' if a['genero'] == 'M' else 'D'
            row.append(g_label)
        if 'cat.' in col_names_lower:
            row.append(a.get('cat_name') or '—')
        row.append(fmt_time(a['net']))
        rows.append(row)

    ts = TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  hdr_bg),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0),  7.5),
        ('ALIGN',         (0,0), (-1,0),  'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('FONTSIZE',      (0,1), (-1,-1), 8),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, row_alt]),
        ('GRID',          (0,1), (-1,-1), 0.3, BORDER),
        ('LINEBELOW',     (0,0), (-1,0),  0.5, WHITE),
        ('ALIGN',         (0,1), (1,-1),  'CENTER'),
        ('ALIGN',         (-1,1),(-1,-1), 'RIGHT'),
    ])
    t = Table(rows, colWidths=cws, repeatRows=1)
    t.setStyle(ts)
    return t

def gen_table(athletes, hdr_bg, row_alt):
    return result_table(athletes,
        cols=['PUESTO', 'DORSAL', 'APELLIDO Y NOMBRE', 'CAT.', 'TIEMPO'],
        cws=[1.2*cm, 1.4*cm, 8.2*cm, 2.5*cm, 1.8*cm],
        hdr_bg=hdr_bg, row_alt=row_alt)

def arrival_table(athletes):
    return result_table(athletes,
        cols=['PUESTO', 'DORSAL', 'APELLIDO Y NOMBRE', 'G.', 'CAT.', 'TIEMPO'],
        cws=[1.2*cm, 1.4*cm, 7*cm, 0.9*cm, 2.5*cm, 2.1*cm],
        hdr_bg=DGRAY, row_alt=LBLUE)

def cat_table(athletes, hdr_bg, row_alt):
    return result_table(athletes,
        cols=['PUESTO', 'DORSAL', 'APELLIDO Y NOMBRE', 'TIEMPO'],
        cws=[1.2*cm, 1.4*cm, 10*cm, 2.5*cm],
        hdr_bg=hdr_bg, row_alt=row_alt)

# ── Logo + encabezado de página ────────────────────────────────────────────────
def page_header(dist_label):
    logo = Image(LOGO, width=3.5*cm, height=2.33*cm)
    info = Table([
        [P('CRONOMETRAJE QUE CONECTA EXPERIENCIAS',
           fontName='Helvetica-Bold', fontSize=8, textColor=BLUE)],
        [P('Carrera SportlerZeit 2026', fontName='Helvetica-Bold', fontSize=10, textColor=DGRAY)],
        [P(f'26 de septiembre de 2026  ·  {dist_label}  ·  Concarán, San Luis',
           fontSize=8, textColor=MGRAY)],
    ], colWidths=[11.7*cm])
    info.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    hdr = Table([[logo, info]], colWidths=[3.8*cm, 11.7*cm])
    hdr.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,0), (-1,-1), 0),
        ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW',     (0,0), (-1,0),  1.5, BLUE),
    ]))
    return hdr

def footer_line():
    return Table([[
        P('SPORTLER ZEIT', fontName='Helvetica-Bold', fontSize=7, textColor=DGRAY),
        P('www.sportlerzeit.com.ar  ·  contacto@sportlerzeit.com.ar  ·  +54 9 2657 510021',
          fontSize=7, textColor=MGRAY, alignment=TA_CENTER),
        P('', fontSize=7),
    ]], colWidths=[3.5*cm, 9.5*cm, 2.5*cm])

# ── Armar el PDF ───────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(OUT_PDF, pagesize=A4,
                        leftMargin=1.5*cm, rightMargin=1.5*cm,
                        topMargin=1.5*cm, bottomMargin=1.5*cm)
story = []

# ── Generales 5K ──────────────────────────────────────────────────────────────
story.append(page_header('5 km'))
story.append(Spacer(1, 5*mm))
story.append(section_title(f'Clasificación General 5 km — Varones', GREEN))
story.append(sub_title(f'{len(gen_m5)} atletas clasificados'))
story.append(gen_table(gen_m5, GREEN, LGREEN))
story.append(Spacer(1, 6*mm))
story.append(section_title(f'Clasificación General 5 km — Damas', PINK))
story.append(sub_title(f'{len(gen_f5)} atletas clasificadas'))
story.append(gen_table(gen_f5, PINK, LPINK))
story.append(PageBreak())

# ── Generales 10K ─────────────────────────────────────────────────────────────
story.append(page_header('10 km'))
story.append(Spacer(1, 5*mm))
story.append(section_title(f'Clasificación General 10 km — Varones', GREEN))
story.append(sub_title(f'{len(gen_m10)} atletas clasificados'))
story.append(gen_table(gen_m10, GREEN, LGREEN))
story.append(Spacer(1, 6*mm))
story.append(section_title(f'Clasificación General 10 km — Damas', PINK))
story.append(sub_title(f'{len(gen_f10)} atletas clasificadas'))
story.append(gen_table(gen_f10, PINK, LPINK))
story.append(PageBreak())

# ── Categorías 10K ────────────────────────────────────────────────────────────
all_10k = gen_m10 + gen_f10
story.append(page_header('10 km'))
story.append(Spacer(1, 5*mm))
story.append(section_title('Categorías de Premiación — 10 km', BLUE))
story.append(Spacer(1, 2*mm))

for cid, cname, cg, mina, maxa in award_cats:
    sub = sorted([r for r in all_10k if r['cat_id'] == cid], key=lambda x: x['net'])
    if not sub: continue
    hdr_bg  = GREEN if cg == 'M' else PINK
    row_alt = LGREEN if cg == 'M' else LPINK
    block = [
        section_title(cname, hdr_bg),
        sub_title(f'{len(sub)} clasificados'),
        cat_table(sub, hdr_bg, row_alt),
        Spacer(1, 4*mm),
    ]
    story.append(KeepTogether(block))

story.append(PageBreak())

# ── Orden de llegada — al final ────────────────────────────────────────────────
for orden, dlabel in [(orden_5k, '5 km'), (orden_10k, '10 km')]:
    story.append(page_header(dlabel))
    story.append(Spacer(1, 5*mm))
    story.append(section_title(f'Orden de Llegada — {dlabel}', BLUE))
    story.append(sub_title(f'{len(orden)} atletas · Disparo: 15:01:05'))
    story.append(arrival_table(orden))
    story.append(PageBreak())

# quitar último PageBreak y agregar pie
if story and isinstance(story[-1], PageBreak):
    story.pop()
story.append(Spacer(1, 5*mm))
story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
story.append(Spacer(1, 2*mm))
story.append(footer_line())

doc.build(story)

import os
print(f'PDF: {OUT_PDF}  ({os.path.getsize(OUT_PDF):,} bytes)')
