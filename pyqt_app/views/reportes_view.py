from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QFileDialog,
    QMessageBox, QTableWidgetItem
)
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton, TitleLabel, BodyLabel,
    CaptionLabel, ComboBox, setFont, InfoBar, InfoBarPosition, TableWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

matplotlib.use('Qt5Agg')


class ReportesView(ScrollArea):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.setObjectName("ReportesView")
        self.setStyleSheet("ReportesView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Reportes y Estadísticas")
        layout.addWidget(title)

        charts = QHBoxLayout()
        charts.setSpacing(12)

        card_ocu = CardWidget()
        ocu_layout = QVBoxLayout(card_ocu)
        ocu_layout.setContentsMargins(16, 16, 16, 16)
        lbl_ocu = BodyLabel("Ocupación por Laboratorio")
        setFont(lbl_ocu, 13, QFont.Weight.DemiBold)
        ocu_layout.addWidget(lbl_ocu)

        self.lbl_ocu_empty = CaptionLabel("")
        self.lbl_ocu_empty.setStyleSheet("color: #9CA3AF;")
        ocu_layout.addWidget(self.lbl_ocu_empty)
        self.fig_ocu = Figure(figsize=(4, 3), dpi=100)
        self.canvas_ocu = FigureCanvas(self.fig_ocu)
        ocu_layout.addWidget(self.canvas_ocu)
        charts.addWidget(card_ocu)

        card_car = CardWidget()
        car_layout = QVBoxLayout(card_car)
        car_layout.setContentsMargins(16, 16, 16, 16)
        lbl_car = BodyLabel("Reservas por Carrera")
        setFont(lbl_car, 13, QFont.Weight.DemiBold)
        car_layout.addWidget(lbl_car)

        self.lbl_car_empty = CaptionLabel("")
        self.lbl_car_empty.setStyleSheet("color: #9CA3AF;")
        car_layout.addWidget(self.lbl_car_empty)
        self.fig_car = Figure(figsize=(4, 3), dpi=100)
        self.canvas_car = FigureCanvas(self.fig_car)
        car_layout.addWidget(self.canvas_car)
        charts.addWidget(card_car)

        layout.addLayout(charts)

        card_pdf = CardWidget()
        pdf_layout = QVBoxLayout(card_pdf)
        pdf_layout.setContentsMargins(16, 16, 16, 16)
        lbl_pdf = BodyLabel("Generar PDF de Laboratorio")
        setFont(lbl_pdf, 13, QFont.Weight.DemiBold)
        pdf_layout.addWidget(lbl_pdf)

        form_pdf = QHBoxLayout()
        form_pdf.setSpacing(8)
        lbl_lab = CaptionLabel("Laboratorio:")
        form_pdf.addWidget(lbl_lab)
        self.comb_lab = ComboBox()
        form_pdf.addWidget(self.comb_lab)
        btn_pdf = PrimaryPushButton("Generar PDF")
        btn_pdf.clicked.connect(self.generar_pdf)
        form_pdf.addWidget(btn_pdf)
        form_pdf.addStretch()
        pdf_layout.addLayout(form_pdf)
        layout.addWidget(card_pdf)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)
        lbl_tab = BodyLabel("Estadísticas Detalladas")
        setFont(lbl_tab, 13, QFont.Weight.DemiBold)
        tabla_layout.addWidget(lbl_tab)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Laboratorio", "Tipo", "Clases Semestrales", "Eventos Únicos"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        tabla_layout.addWidget(self.tabla)
        layout.addWidget(card_tabla)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def cargar_datos(self):
        self._cargar_ocupacion()
        self._cargar_carreras()
        self._cargar_estadisticas()
        self._cargar_labs()

    def _cargar_labs(self):
        espacios = self.modelo.obtener_espacios()
        self.comb_lab.clear()
        for e in espacios:
            self.comb_lab.addItem(f"{e[1]} ({e[2]})", userData=e[0])

    def _cargar_ocupacion(self):
        datos = self.modelo.obtener_datos_analiticas_ocupacion()
        self.fig_ocu.clear()
        self.lbl_ocu_empty.setText("")

        if not datos or all(d[1] == 0 for d in datos):
            self.lbl_ocu_empty.setText("No hay datos de ocupación")
            self.canvas_ocu.draw()
            return

        ax = self.fig_ocu.add_subplot(111)
        labs = [d[0] for d in datos]
        totales = [int(d[1]) for d in datos]
        ax.bar(labs, totales, color="#E31E24")
        ax.set_xticks(range(len(labs)))
        ax.set_xticklabels(labs, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel("Reservas")
        self.fig_ocu.tight_layout()
        self.canvas_ocu.draw()

    def _cargar_carreras(self):
        datos = self.modelo.obtener_datos_analiticas_carreras()
        self.fig_car.clear()
        self.lbl_car_empty.setText("")

        if not datos:
            self.lbl_car_empty.setText("No hay datos de carreras")
            self.canvas_car.draw()
            return

        ax = self.fig_car.add_subplot(111)
        carreras = [d[0] for d in datos]
        totales = [int(d[1]) for d in datos]
        colores = ["#E31E24", "#16A34A", "#2563EB", "#D97706", "#8B5CF6"]
        ax.pie(
            totales, labels=carreras, autopct='%1.1f%%',
            colors=colores[:len(carreras)]
        )
        self.fig_car.tight_layout()
        self.canvas_car.draw()

    def _cargar_estadisticas(self):
        stats = self.modelo.obtener_estadisticas_detalladas()
        self.tabla.setRowCount(0)
        for row_idx, s in enumerate(stats):
            self.tabla.insertRow(row_idx)
            for col_idx in range(len(s)):
                valor = str(s[col_idx]) if s[col_idx] is not None else "0"
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(valor))

    def generar_pdf(self):
        id_lab = self.comb_lab.currentData()
        if not id_lab:
            QMessageBox.warning(self, "Error", "Seleccione un laboratorio")
            return
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "horario_lab.pdf", "PDF Files (*.pdf)"
        )
        if archivo:
            reservas = self.modelo.obtener_reservas_por_lab(id_lab)
            lab_nombre = self.comb_lab.currentText()
            from widgets.pdf_generator import PDFGenerator
            PDFGenerator.generar_laboratorio(lab_nombre, reservas, archivo)
            QMessageBox.information(self, "Éxito", f"PDF guardado en:\n{archivo}")
