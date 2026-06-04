from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidgetItem
from qfluentwidgets import (
    ScrollArea, CardWidget, TitleLabel, BodyLabel,
    CaptionLabel, setFont, TableWidget, CalendarPicker
)


class HomeView(ScrollArea):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.setObjectName("HomeView")
        self.setStyleSheet("HomeView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Panel de Control")
        layout.addWidget(title)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.card_labs, self.lbl_labs_val = self._crear_stat_card("Laboratorios", "0", "#E31E24")
        self.card_hoy, self.lbl_hoy_val = self._crear_stat_card("Reservas Hoy", "0", "#16A34A")
        self.card_capacidad, self.lbl_cap_val = self._crear_stat_card("Capacidad Total", "0", "#2563EB")
        stats_layout.addWidget(self.card_labs)
        stats_layout.addWidget(self.card_hoy)
        stats_layout.addWidget(self.card_capacidad)
        layout.addLayout(stats_layout)

        card_calendario = CardWidget()
        cal_layout = QVBoxLayout(card_calendario)
        cal_layout.setContentsMargins(16, 16, 16, 16)
        lbl_cal = BodyLabel("Calendario de Reservas")
        setFont(lbl_cal, 13, QFont.Weight.DemiBold)
        cal_layout.addWidget(lbl_cal)

        self.calendario = CalendarPicker()
        self.calendario.setDate(QDate.currentDate())
        self.calendario.dateChanged.connect(self._on_fecha_cambiada)
        cal_layout.addWidget(self.calendario)

        self.lbl_count = CaptionLabel("Selecciona una fecha para ver reservas")
        cal_layout.addWidget(self.lbl_count)
        layout.addWidget(card_calendario)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)
        lbl_tabla = BodyLabel("Reservas del Día")
        setFont(lbl_tabla, 13, QFont.Weight.DemiBold)
        tabla_layout.addWidget(lbl_tabla)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Hora", "Docente", "Materia", "Carrera",
            "Estudiantes", "Laboratorio", "Día"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        tabla_layout.addWidget(self.tabla)
        layout.addWidget(card_tabla)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def _crear_stat_card(self, titulo, valor, color):
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color};")
        lbl_titulo = CaptionLabel(titulo)
        lbl_titulo.setStyleSheet("color: #6B7280;")
        layout.addWidget(lbl_valor)
        layout.addWidget(lbl_titulo)
        return card, lbl_valor

    def _on_fecha_cambiada(self, date):
        fecha_sql = date.toString("yyyy-MM-dd")
        reservas = self.modelo.obtener_reservas_por_fecha(fecha_sql)
        self.lbl_count.setText(f"{len(reservas)} reserva(s) en esta fecha")
        self.tabla.setRowCount(0)
        for row_idx, r in enumerate(reservas):
            self.tabla.insertRow(row_idx)
            for col_idx in range(len(r)):
                valor = str(r[col_idx]) if r[col_idx] is not None else ""
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(valor))

    def cargar_datos(self):
        stats = self.modelo.obtener_estadisticas_generales()
        if stats:
            self.lbl_labs_val.setText(str(stats[0]))
            self.lbl_cap_val.setText(str(int(stats[1])))
        hoy = QDate.currentDate()
        self.calendario.setDate(hoy)
        self._on_fecha_cambiada(hoy)
