from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QColorDialog, QFormLayout
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor

DIAS_LUN_VIE = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
DIAS_SABADO = ["SÁBADO"]
TIPO_HORARIO_LV = "LUN_VIE"
TIPO_HORARIO_SA = "SABADO"


class PDFConfigDialog(QDialog):
    def __init__(self, modelo, parent=None):
        super().__init__(parent)
        self.modelo = modelo
        self.color_celda = "#E31E24"
        self.color_texto = "#FFFFFF"
        self.setWindowTitle("Configurar PDF Semestral")
        self.setFixedSize(420, 520)
        self.setStyleSheet("background-color: #FFFFFF;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_title = QLabel("Configuración del Horario Semestral")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #111827;")
        layout.addWidget(lbl_title)

        form = QFormLayout()
        form.setSpacing(10)

        self.comb_tipo_horario = QComboBox()
        self.comb_tipo_horario.setFixedHeight(36)
        self.comb_tipo_horario.setStyleSheet(self._combo_style())
        self.comb_tipo_horario.addItem("Lunes a Viernes (7:40 - 15:00)", TIPO_HORARIO_LV)
        self.comb_tipo_horario.addItem("Sábado (7:20 - 17:00)", TIPO_HORARIO_SA)
        form.addRow("Tipo de Horario:", self.comb_tipo_horario)

        self.ent_periodo = QLineEdit()
        self.ent_periodo.setPlaceholderText("Ej: PR25-4")
        self.ent_periodo.setFixedHeight(36)
        self.ent_periodo.setStyleSheet(self._input_style())
        form.addRow("Período:", self.ent_periodo)

        self.comb_semestre = QComboBox()
        self.comb_semestre.setFixedHeight(36)
        self.comb_semestre.setStyleSheet(self._combo_style())
        form.addRow("Semestre:", self.comb_semestre)

        self.ent_carrera = QComboBox()
        self.ent_carrera.setFixedHeight(36)
        self.ent_carrera.setStyleSheet(self._combo_style())
        self.ent_carrera.setEditable(True)
        self.ent_carrera.addItems(["Análisis de Sistemas", "Electrónica", "Administración"])
        form.addRow("Carrera:", self.ent_carrera)

        self.ent_seccion = QLineEdit()
        self.ent_seccion.setPlaceholderText("Ej: SAI-101")
        self.ent_seccion.setFixedHeight(36)
        self.ent_seccion.setStyleSheet(self._input_style())
        form.addRow("Sección:", self.ent_seccion)

        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate())
        self.date_inicio.setDisplayFormat("dd/MM/yyyy")
        self.date_inicio.setFixedHeight(36)
        self.date_inicio.setStyleSheet(self._input_style())
        form.addRow("Fecha inicio:", self.date_inicio)

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate().addMonths(4))
        self.date_fin.setDisplayFormat("dd/MM/yyyy")
        self.date_fin.setFixedHeight(36)
        self.date_fin.setStyleSheet(self._input_style())
        form.addRow("Fecha fin:", self.date_fin)

        self.ent_aula = QLineEdit()
        self.ent_aula.setPlaceholderText("Ej: LAB-01")
        self.ent_aula.setFixedHeight(36)
        self.ent_aula.setStyleSheet(self._input_style())
        form.addRow("Aula:", self.ent_aula)

        color_layout = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(36, 36)
        self.btn_color.setStyleSheet(f"background-color: {self.color_celda}; border: 1px solid #D1D5DB; border-radius: 4px;")
        self.btn_color.clicked.connect(self.seleccionar_color)
        lbl_color = QLabel("Color de celdas:")
        lbl_color.setStyleSheet("color: #4B5563; font-size: 13px;")
        color_layout.addWidget(lbl_color)
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()
        form.addRow("", color_layout)

        color_texto_layout = QHBoxLayout()
        self.btn_color_texto = QPushButton()
        self.btn_color_texto.setFixedSize(36, 36)
        self.btn_color_texto.setStyleSheet(f"background-color: {self.color_texto}; border: 1px solid #D1D5DB; border-radius: 4px;")
        self.btn_color_texto.clicked.connect(self.seleccionar_color_texto)
        lbl_color_texto = QLabel("Color de texto:")
        lbl_color_texto.setStyleSheet("color: #4B5563; font-size: 13px;")
        color_texto_layout.addWidget(lbl_color_texto)
        color_texto_layout.addWidget(self.btn_color_texto)
        color_texto_layout.addStretch()
        form.addRow("", color_texto_layout)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_generar = QPushButton("Generar PDF")
        btn_generar.setFixedHeight(36)
        btn_generar.setStyleSheet(self._primary_style())
        btn_generar.clicked.connect(self.accept)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(36)
        btn_cancelar.setStyleSheet(self._secondary_style())
        btn_cancelar.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_generar)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.cargar_semestres()

    def cargar_semestres(self):
        semestres = self.modelo.obtener_semestres()
        for s in semestres:
            self.comb_semestre.addItem(f"{s[1]} - {s[2] if s[2] else 'Sin período'}", s[0])

    def seleccionar_color(self):
        color = QColorDialog.getColor(QColor(self.color_celda), self, "Color de celdas")
        if color.isValid():
            self.color_celda = color.name()
            self.btn_color.setStyleSheet(f"background-color: {self.color_celda}; border: 1px solid #D1D5DB; border-radius: 4px;")

    def seleccionar_color_texto(self):
        color = QColorDialog.getColor(QColor(self.color_texto), self, "Color de texto")
        if color.isValid():
            self.color_texto = color.name()
            self.btn_color_texto.setStyleSheet(f"background-color: {self.color_texto}; border: 1px solid #D1D5DB; border-radius: 4px;")

    def obtener_config(self):
        tipo = self.comb_tipo_horario.currentData() or TIPO_HORARIO_LV
        dias = DIAS_SABADO if tipo == TIPO_HORARIO_SA else DIAS_LUN_VIE
        return {
            "periodo": self.ent_periodo.text().strip(),
            "semestre": self.comb_semestre.currentText().split(" - ")[0] if self.comb_semestre.currentData() else "",
            "id_semestre": self.comb_semestre.currentData(),
            "carrera": self.ent_carrera.currentText().strip(),
            "seccion": self.ent_seccion.text().strip(),
            "fecha_inicio": self.date_inicio.date().toString("dd/MM/yyyy"),
            "fecha_fin": self.date_fin.date().toString("dd/MM/yyyy"),
            "aula": self.ent_aula.text().strip(),
            "tipo_horario": tipo,
            "dias": dias,
            "color_texto": self.color_texto,
        }

    def _input_style(self):
        return """
            QLineEdit, QDateEdit {
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                background-color: #FFFFFF;
                color: #111827;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 1px solid #E31E24;
            }
        """

    def _combo_style(self):
        return """
            QComboBox {
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                background-color: #FFFFFF;
                color: #111827;
            }
            QComboBox:focus { border: 1px solid #E31E24; }
        """

    def _primary_style(self):
        return """
            QPushButton {
                background-color: #E31E24;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #C41920; }
        """

    def _secondary_style(self):
        return """
            QPushButton {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 4px;
                padding: 7px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F5F5F5; }
        """
