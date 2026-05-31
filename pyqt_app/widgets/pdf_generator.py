import os
from datetime import datetime, time
from collections import defaultdict

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ANCHO_PAGINA, ALTO_PAGINA = landscape(A4)
MARGEN = 10 * mm

DIAS_SEMANA = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"]
HORAS = [f"{h:02d}" for h in range(7, 22)]
ROJO = HexColor("#E31E24")
GRIS_CLARO = HexColor("#F5F5F5")
GRIS_MEDIO = HexColor("#9CA3AF")
GRIS_OSCURO = HexColor("#4B5563")

PAGE_W = ANCHO_PAGINA - 2 * MARGEN

DIAS_MAP = {
    "Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIERCOLES",
    "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SABADO",
    "Lunes": "LUNES", "Martes": "MARTES", "Miercoles": "MIERCOLES",
    "Jueves": "JUEVES", "Viernes": "VIERNES", "Sabado": "SABADO",
    "LUNES": "LUNES", "MARTES": "MARTES", "MIERCOLES": "MIERCOLES",
    "JUEVES": "JUEVES", "VIERNES": "VIERNES", "SABADO": "SABADO",
}


def _timedelta_a_str(td):
    if td is None:
        return "08:00", 8, 0
    if isinstance(td, time):
        return td.strftime("%H:%M"), td.hour, td.minute
    total_seg = int(td.total_seconds())
    h = total_seg // 3600
    m = (total_seg % 3600) // 60
    return f"{h:02d}:{m:02d}", h, m


def _color_hex_a_rgb(hex_color):
    return HexColor(hex_color)


def _logo_ruta():
    ruta = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "LOG40CM-3-scaled-e1643832660979-removebg-preview.png"
    )
    return ruta if os.path.exists(ruta) else None


def _estilo_celda(size=8, color=black):
    return ParagraphStyle(
        "celda", fontSize=size, leading=size * 1.3,
        alignment=TA_CENTER, textColor=color, fontName="Helvetica"
    )


def _estilo_celda_invertido(size=8, color=white):
    return ParagraphStyle(
        "celda_inv", fontSize=size, leading=size * 1.3,
        alignment=TA_CENTER, textColor=color, fontName="Helvetica-Bold"
    )


def _calcular_span(h_inicio_h, h_inicio_m, h_fin_h, h_fin_m):
    ultima_hora = h_fin_h if h_fin_m > 0 else h_fin_h - 1
    return max(1, ultima_hora - h_inicio_h + 1)


class PDFGenerator:
    @staticmethod
    def generar_laboratorio(lab_nombre, reservas, archivo, periodo="", carrera="", color_celda="#E31E24"):
        color = _color_hex_a_rgb(color_celda)
        horario = defaultdict(lambda: defaultdict(list))
        for r in reservas:
            if len(r) < 9:
                continue
            profesor = str(r[1]) if r[1] else ""
            materia = str(r[2]) if r[2] else ""
            h_inicio_str, h_inicio_h, h_inicio_m = _timedelta_a_str(r[7])
            h_fin_str, h_fin_h, h_fin_m = _timedelta_a_str(r[8])
            dia_semana = DIAS_MAP.get(str(r[9]).upper() if len(r) > 9 and r[9] else "LUNES", "LUNES")
            span = _calcular_span(h_inicio_h, h_inicio_m, h_fin_h, h_fin_m)
            hora_key = f"{h_inicio_h:02d}"
            horario[dia_semana][hora_key].append({
                "profesor": profesor[:20], "materia": materia[:25],
                "hora": f"{h_inicio_str}-{h_fin_str}", "span": span
            })
        periodo_lab = str(reservas[0][5]) if reservas and len(reservas[0]) >= 6 else periodo
        encabezado = f"Laboratorio: {lab_nombre}"
        info_line = f"Periodo: {periodo_lab}  |  {datetime.now().strftime('%d/%m/%Y')}"
        PDFGenerator._render_pdf(archivo, "LABORATORIO", horario, color, encabezado, info_line,
                                 periodo, carrera)

    @staticmethod
    def generar_semestral(id_semestre, horarios, archivo, config, color_celda="#E31E24"):
        color = _color_hex_a_rgb(color_celda)
        horario = defaultdict(lambda: defaultdict(list))
        for h in horarios:
            materia = str(h[0]) if h[0] else ""
            profesor = str(h[1]) if h[1] else ""
            dia = DIAS_MAP.get(str(h[2]).upper() if h[2] else "LUNES", "LUNES")
            h_inicio_str, h_inicio_h, h_inicio_m = _timedelta_a_str(h[3])
            h_fin_str, h_fin_h, h_fin_m = _timedelta_a_str(h[4])
            span = _calcular_span(h_inicio_h, h_inicio_m, h_fin_h, h_fin_m)
            hora_key = f"{h_inicio_h:02d}"
            horario[dia][hora_key].append({
                "materia": materia[:25], "profesor": profesor[:20],
                "hora": f"{h_inicio_str}-{h_fin_str}", "span": span
            })
        encabezado = (f"Semestre: {config.get('semestre', '')}  |  "
                      f"Periodo: {config.get('periodo', '')}  |  "
                      f"Carrera: {config.get('carrera', '')}")
        info_line = (f"Aula: {config.get('aula', '')}  |  "
                     f"Vigencia: {config.get('fecha_inicio', '')} - {config.get('fecha_fin', '')}")
        PDFGenerator._render_pdf(archivo, "SEMESTRAL", horario, color, encabezado, info_line,
                                 config.get("periodo", ""), config.get("carrera", ""))

    @staticmethod
    def _render_pdf(archivo, tipo, horario, color_celda, encabezado, info_line, periodo, carrera):
        dias = DIAS_SEMANA if tipo == "LABORATORIO" else ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]

        doc = SimpleDocTemplate(
            archivo, pagesize=landscape(A4),
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=12 * mm, bottomMargin=12 * mm
        )

        story = []

        logo = _logo_ruta()
        if logo:
            img = Image(logo, width=30 * mm, height=10 * mm)
            story.append(img)

        story.append(Spacer(1, 2 * mm))

        style_titulo = ParagraphStyle("titulo", fontSize=16, leading=20,
                                      textColor=black, spaceAfter=2 * mm,
                                      fontName="Helvetica-Bold")
        story.append(Paragraph(f"IUTEPI - Horario {tipo}", style_titulo))

        style_sub = ParagraphStyle("sub", fontSize=10, leading=13,
                                   textColor=GRIS_OSCURO, spaceAfter=1 * mm,
                                   fontName="Helvetica")
        story.append(Paragraph(encabezado, style_sub))
        style_info = ParagraphStyle("info", fontSize=10, leading=13,
                                    textColor=GRIS_OSCURO, fontName="Helvetica")
        story.append(Paragraph(info_line, style_info))
        story.append(Spacer(1, 2 * mm))

        col_hora = 22 * mm
        col_dia = (PAGE_W - col_hora) / len(dias)

        data = []

        header = [Paragraph("HORA", _estilo_celda_invertido(9, white))]
        for d in dias:
            header.append(Paragraph(d, _estilo_celda_invertido(9, white)))
        data.append(header)

        merge_ranges = []
        merged_cells = set()

        for i, hora in enumerate(HORAS):
            fila_idx = i + 1
            fila = [Paragraph(f"{hora}:00", _estilo_celda(10, GRIS_OSCURO))]
            for j, dia in enumerate(dias):
                col_idx = j + 1
                reservas = horario.get(dia, {}).get(hora, [])
                if reservas:
                    max_span = max(r.get("span", 1) for r in reservas)
                    if max_span > 1:
                        end_row = fila_idx + max_span - 1
                        merge_ranges.append((col_idx, fila_idx, end_row))
                        for r in range(fila_idx + 1, end_row + 1):
                            merged_cells.add((col_idx, r))
                    partes = []
                    for res in reservas:
                        partes.append(
                            f'<b>{res["profesor"]}</b><br/>{res["materia"]}<br/>{res["hora"]}'
                        )
                    texto = "<br/><br/>".join(partes)
                    fila.append(Paragraph(texto, _estilo_celda_invertido(8, white)))
                else:
                    fila.append(Paragraph("", _estilo_celda(8)))
            data.append(fila)

        col_widths = [col_hora] + [col_dia] * len(dias)
        tabla = Table(data, colWidths=col_widths, repeatRows=1)

        estilo_tabla = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#333333")),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, HexColor("#D1D5DB")),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]

        for col, start_row, end_row in merge_ranges:
            estilo_tabla.append(('SPAN', (col, start_row), (col, end_row)))

        for i, hora in enumerate(HORAS):
            fila_idx = i + 1
            bg_color = HexColor("#F5F5F5") if i % 2 == 0 else white
            estilo_tabla.append(('BACKGROUND', (0, fila_idx), (0, fila_idx), bg_color))
            for j, dia in enumerate(dias):
                col_idx = j + 1
                if (col_idx, fila_idx) in merged_cells:
                    continue
                reservas = horario.get(dia, {}).get(hora, [])
                if not reservas:
                    estilo_tabla.append(('BACKGROUND', (col_idx, fila_idx), (col_idx, fila_idx), bg_color))
                else:
                    max_span = max(r.get("span", 1) for r in reservas)
                    end_row = fila_idx + max_span - 1
                    estilo_tabla.append(('BACKGROUND', (col_idx, fila_idx), (col_idx, end_row), color_celda))

        tabla.setStyle(TableStyle(estilo_tabla))
        story.append(tabla)

        story.append(Spacer(1, 4 * mm))

        style_footer = ParagraphStyle("footer", fontSize=7, leading=9,
                                      textColor=GRIS_MEDIO, alignment=TA_CENTER,
                                      fontName="Helvetica-Oblique")
        story.append(Paragraph(f"IUTEPI - Sistema de Gestión de Laboratorios  |  {info_line}", style_footer))

        doc.build(story)
