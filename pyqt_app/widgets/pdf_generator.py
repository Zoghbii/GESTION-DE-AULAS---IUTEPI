import os
from datetime import datetime, time
from collections import defaultdict

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)

ANCHO_PAGINA, ALTO_PAGINA = landscape(A4)
MARGEN = 10 * mm

DIAS_SEMANA = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SÁBADO"]
DIAS_SEMANA_SIN_TILDE = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"]
DIAS_LUN_VIE = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
HORAS = [f"{h:02d}" for h in range(7, 22)]
ROJO = HexColor("#E31E24")
GRIS_CLARO = HexColor("#F5F5F5")
GRIS_MEDIO = HexColor("#9CA3AF")
GRIS_OSCURO = HexColor("#4B5563")

PAGE_W = ANCHO_PAGINA - 2 * MARGEN

DIAS_MAP = {
    "Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIERCOLES",
    "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO",
    "Lunes": "LUNES", "Martes": "MARTES", "Miercoles": "MIERCOLES",
    "Jueves": "JUEVES", "Viernes": "VIERNES", "Sabado": "SÁBADO",
    "LUNES": "LUNES", "MARTES": "MARTES", "MIERCOLES": "MIERCOLES",
    "JUEVES": "JUEVES", "VIERNES": "VIERNES",
    "SABADO": "SÁBADO", "SÁBADO": "SÁBADO",
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


def _format_ampm(h, m):
    """Convierte hora 24h a formato 12h con AM/PM."""
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12:02d}:{m:02d} {ampm}"


def _wrap_texto(texto, max_chars=22, max_lineas=3):
    """Divide texto en lineas y trunca con ... si excede max_lineas."""
    if not texto:
        return ""
    palabras = str(texto).split()
    lineas = []
    actual = ""
    for p in palabras:
        if not actual:
            actual = p
        elif len(actual) + 1 + len(p) <= max_chars:
            actual += " " + p
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        ultima = lineas[-1]
        if len(ultima) > max_chars - 3:
            ultima = ultima[:max_chars - 3]
        lineas[-1] = ultima + "..."
    return " ".join(lineas)


def _color_hex_a_rgb(hex_color):
    return HexColor(hex_color)


def _logo_ruta():
    ruta = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "LOG40CM-3-scaled-e1643832660979-removebg-preview.png"
    )
    return ruta if os.path.exists(ruta) else None


def _estilo_celda(size=6, color=black):
    return ParagraphStyle(
        "celda", fontSize=size, leading=size * 1.2,
        alignment=TA_CENTER, textColor=color, fontName="Helvetica"
    )


def _estilo_celda_invertido(size=9, color=white):
    return ParagraphStyle(
        "celda_inv", fontSize=size, leading=size * 1.1,
        alignment=TA_CENTER, textColor=color, fontName="Helvetica-Bold"
    )


def _calcular_span(h_inicio_h, h_inicio_m, h_fin_h, h_fin_m):
    """Numero de bloques de hora que ocupa la clase (hora final inclusiva)."""
    if h_fin_h < h_inicio_h:
        return 1
    return max(1, h_fin_h - h_inicio_h + 1)


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
            hora_ampm = f"{_format_ampm(h_inicio_h, h_inicio_m)}-{_format_ampm(h_fin_h, h_fin_m)}"
            horario[dia_semana][hora_key].append({
                "profesor": profesor, "materia": materia,
                "hora": hora_ampm, "span": span
            })
        periodo_lab = str(reservas[0][5]) if reservas and len(reservas[0]) >= 6 else periodo
        encabezado = f"Laboratorio: {lab_nombre}"
        info_line = f"Periodo: {periodo_lab}  |  {datetime.now().strftime('%d/%m/%Y')}"
        PDFGenerator._render_pdf(archivo, "LABORATORIO", horario, color, encabezado, info_line,
                                 periodo, carrera)

    @staticmethod
    def generar_semestral(id_semestre, horarios, archivo, config, color_celda="#E31E24",
                          dias=None, color_texto="#FFFFFF"):
        color = _color_hex_a_rgb(color_celda)
        if dias is None:
            dias = DIAS_LUN_VIE
        horario = defaultdict(lambda: defaultdict(list))
        for h in horarios:
            materia = str(h[1]) if len(h) > 1 and h[1] else ""
            profesor = str(h[2]) if len(h) > 2 and h[2] else ""
            dia_raw = str(h[3]).upper() if len(h) > 3 and h[3] else "LUNES"
            dia = DIAS_MAP.get(dia_raw, "LUNES")
            h_inicio_str, h_inicio_h, h_inicio_m = _timedelta_a_str(h[4] if len(h) > 4 else None)
            h_fin_str, h_fin_h, h_fin_m = _timedelta_a_str(h[5] if len(h) > 5 else None)
            span = _calcular_span(h_inicio_h, h_inicio_m, h_fin_h, h_fin_m)
            hora_key = f"{h_inicio_h:02d}"
            hora_ampm = f"{_format_ampm(h_inicio_h, h_inicio_m)}-{_format_ampm(h_fin_h, h_fin_m)}"
            horario[dia][hora_key].append({
                "materia": materia, "profesor": profesor,
                "hora": hora_ampm, "span": span
            })
        seccion = config.get("seccion", "")
        seccion_str = f"  |  Sección: {seccion}" if seccion else ""
        encabezado = (f"Semestre: {config.get('semestre', '')}  |  "
                      f"Periodo: {config.get('periodo', '')}  |  "
                      f"Carrera: {config.get('carrera', '')}{seccion_str}")
        info_line = (f"Aula: {config.get('aula', '')}  |  "
                     f"Vigencia: {config.get('fecha_inicio', '')} - {config.get('fecha_fin', '')}")
        PDFGenerator._render_pdf(archivo, "SEMESTRAL", horario, color, encabezado, info_line,
                                 config.get("periodo", ""), config.get("carrera", ""),
                                 dias=dias, color_texto=color_texto)

    @staticmethod
    def _render_pdf(archivo, tipo, horario, color_celda, encabezado, info_line, periodo, carrera,
                    dias=None, color_texto=None):
        if dias is None:
            dias = DIAS_SEMANA if tipo == "LABORATORIO" else DIAS_LUN_VIE
        if color_texto is None:
            color_texto = white

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
        COL_DIA_MAX = 90 * mm
        col_dia = min((PAGE_W - col_hora) / len(dias), COL_DIA_MAX)

        data = []

        header = [Paragraph("HORA", _estilo_celda_invertido(9, color_texto))]
        for d in dias:
            header.append(Paragraph(d, _estilo_celda_invertido(9, color_texto)))
        data.append(header)

        spans_por_celda = {}
        merged_cells = set()

        for j, dia in enumerate(dias):
            col_idx = j + 1
            clases_dia = []
            for hora, items in horario.get(dia, {}).items():
                for it in items:
                    clases_dia.append((int(hora), it.get("span", 1), it))
            clases_dia.sort(key=lambda x: x[0])

            for idx, (h_ini, sp, _it) in enumerate(clases_dia):
                h_fin_ideal = h_ini + sp - 1
                if idx + 1 < len(clases_dia):
                    h_ini_next = clases_dia[idx + 1][0]
                    h_fin = min(h_fin_ideal, h_ini_next - 1)
                else:
                    h_fin = h_fin_ideal
                sp_final = max(1, h_fin - h_ini + 1)
                fila_ini = h_ini - 7 + 1
                fila_fin = fila_ini + sp_final - 1
                if sp_final > 1:
                    spans_por_celda[(col_idx, fila_ini)] = (fila_ini, fila_fin)
                    for r in range(fila_ini + 1, fila_fin + 1):
                        merged_cells.add((col_idx, r))

        for i, hora in enumerate(HORAS):
            fila_idx = i + 1
            fila = [Paragraph(f"{hora}:00", _estilo_celda(8, GRIS_OSCURO))]
            for j, dia in enumerate(dias):
                col_idx = j + 1
                if (col_idx, fila_idx) in merged_cells:
                    fila.append(Paragraph("", _estilo_celda(6)))
                    continue
                reservas = horario.get(dia, {}).get(hora, [])
                if reservas:
                    partes = []
                    for res in reservas:
                        profesor_w = _wrap_texto(res.get("profesor", ""), 22, 2)
                        materia_w = _wrap_texto(res.get("materia", ""), 24, 3)
                        partes.append(
                            f'<b>{profesor_w}</b><br/>{materia_w}<br/>{res["hora"]}'
                        )
                    texto = "<br/><br/>".join(partes)
                    fila.append(Paragraph(texto, _estilo_celda_invertido(9, color_texto)))
                else:
                    fila.append(Paragraph("", _estilo_celda(6)))
            data.append(fila)

        col_widths = [col_hora] + [col_dia] * len(dias)
        tabla = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')

        estilo_tabla = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#333333")),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, HexColor("#D1D5DB")),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]

        for (col, fila_ini), (fila_ini_real, fila_fin) in spans_por_celda.items():
            estilo_tabla.append(('SPAN', (col, fila_ini_real), (col, fila_fin)))

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
                    if (col_idx, fila_idx) in spans_por_celda:
                        max_span = spans_por_celda[(col_idx, fila_idx)][1] - fila_idx + 1
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
