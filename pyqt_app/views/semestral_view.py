from PyQt5.QtCore import Qt, QTime
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QHeaderView, QMessageBox, QDialog, QFormLayout, QTableWidgetItem, QTimeEdit
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton, TitleLabel, BodyLabel,
    CaptionLabel, ComboBox, LineEdit, setFont, InfoBar, InfoBarPosition, TableWidget
)

class SemestralView(ScrollArea):
    DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SÁBADO"]

    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.semestre_actual = None
        self.setObjectName("SemestralView")
        self.setStyleSheet("SemestralView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = TitleLabel("Horarios Semestrales")
        layout.addWidget(title)

        selector = QHBoxLayout()
        selector.setSpacing(12)
        lbl_sem = CaptionLabel("Semestre:")
        selector.addWidget(lbl_sem)
        self.comb_semestre = ComboBox()
        self.comb_semestre.currentIndexChanged.connect(self.on_semestre_changed)
        selector.addWidget(self.comb_semestre)
        lbl_per = CaptionLabel("Período:")
        selector.addWidget(lbl_per)
        self.ent_periodo = LineEdit()
        self.ent_periodo.setPlaceholderText("ej: PR25-4")
        self.ent_periodo.editingFinished.connect(self.guardar_periodo)
        selector.addWidget(self.ent_periodo)
        layout.addLayout(selector)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Materia", "Profesor", "Día", "Hora Inicio", "Hora Fin"])
        self.tabla.setColumnWidth(0, 40)
        tabla_layout.addWidget(self.tabla)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_agregar = PrimaryPushButton("+ Agregar Clase")
        btn_agregar.clicked.connect(self.abrir_agregar)
        btn_eliminar = PushButton("Eliminar")
        btn_eliminar.clicked.connect(self.eliminar_seleccionado)
        btn_pdf = PrimaryPushButton("Generar PDF")
        btn_pdf.clicked.connect(self.generar_pdf)
        btns.addWidget(btn_agregar)
        btns.addWidget(btn_eliminar)
        btns.addStretch()
        btns.addWidget(btn_pdf)
        tabla_layout.addLayout(btns)
        layout.addWidget(card_tabla)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def cargar_datos(self):
        semestres = self.modelo.obtener_semestres()
        self.comb_semestre.clear()
        for s in semestres:
            self.comb_semestre.addItem(f"{s[1]}", userData=s[0])
        if semestres:
            self.comb_semestre.setCurrentIndex(0)

    def on_semestre_changed(self):
        id_semestre = self.comb_semestre.currentData()
        if id_semestre:
            self.semestre_actual = id_semestre
            self.cargar_horarios()

    def cargar_horarios(self):
        if not self.semestre_actual:
            return
        horarios = self.modelo.obtener_horarios_semestrales(self.semestre_actual)
        self.tabla.setRowCount(0)
        for row_idx, h in enumerate(horarios):
            self.tabla.insertRow(row_idx)
            vals = [
                str(h[0]),
                str(h[1] or ""),
                str(h[2] or ""),
                str(h[3] or ""),
                str(h[4])[:5] if h[4] else "",
                str(h[5])[:5] if h[5] else "",
            ]
            for col_idx, val in enumerate(vals):
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def guardar_periodo(self):
        if not self.semestre_actual:
            return
        periodo = self.ent_periodo.text().strip()
        if periodo:
            self.modelo.actualizar_periodo_semestre(self.semestre_actual, periodo)
            InfoBar.success(
                title="Período guardado",
                content="",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def abrir_agregar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Agregar Clase")
        dialog.setFixedSize(380, 300)
        dialog.setStyleSheet("background-color: #FFFFFF;")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        ent_materia = LineEdit()
        ent_materia.setPlaceholderText("Nombre de la materia")
        ent_profesor = LineEdit()
        ent_profesor.setPlaceholderText("Nombre del profesor")
        comb_dia = ComboBox()
        comb_dia.addItems(self.DIAS)

        time_inicio = QTimeEdit()
        time_inicio.setDisplayFormat("HH:mm")
        time_inicio.setTime(QTime(8, 0))
        time_inicio.setFixedHeight(36)
        time_inicio.setStyleSheet("border: 1px solid rgba(0,0,0,0.12); border-radius: 4px; padding: 6px;")
        time_fin = QTimeEdit()
        time_fin.setDisplayFormat("HH:mm")
        time_fin.setTime(QTime(9, 0))
        time_fin.setFixedHeight(36)
        time_fin.setStyleSheet("border: 1px solid rgba(0,0,0,0.12); border-radius: 4px; padding: 6px;")

        layout.addRow("Materia:", ent_materia)
        layout.addRow("Profesor:", ent_profesor)
        layout.addRow("Día:", comb_dia)
        layout.addRow("Hora Inicio:", time_inicio)
        layout.addRow("Hora Fin:", time_fin)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_guardar = PrimaryPushButton("Guardar")
        btn_cancelar = PushButton("Cancelar")
        btn_layout.addWidget(btn_guardar)
        btn_layout.addWidget(btn_cancelar)
        layout.addRow("", btn_layout)

        def guardar():
            materia = ent_materia.text().strip()
            profesor = ent_profesor.text().strip()
            dia = comb_dia.currentText()
            h_inicio = time_inicio.time().toString("HH:mm:ss")
            h_fin = time_fin.time().toString("HH:mm:ss")
            if not materia or not profesor:
                QMessageBox.warning(self, "Error", "Complete todos los campos")
                return
            if self.modelo.agregar_horario_semestral(self.semestre_actual, materia, profesor, dia, h_inicio, h_fin):
                QMessageBox.information(self, "Éxito", "Clase agregada correctamente")
                dialog.close()
                self.cargar_horarios()
            else:
                QMessageBox.critical(self, "Error", "No se pudo agregar la clase")

        btn_guardar.clicked.connect(guardar)
        btn_cancelar.clicked.connect(dialog.close)
        dialog.setLayout(layout)
        dialog.exec_()

    def eliminar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una clase de la tabla")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta clase?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            id_horario = int(self.tabla.item(fila, 0).text())
            if self.modelo.eliminar_horario_semestral(id_horario):
                QMessageBox.information(self, "Éxito", "Clase eliminada")
                self.cargar_horarios()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar")

    def generar_pdf(self):
        if not self.semestre_actual:
            QMessageBox.warning(self, "Error", "Seleccione un semestre")
            return
        from utils.pdf_config_dialog import PDFConfigDialog
        dialog = PDFConfigDialog(self.modelo, self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.obtener_config()
            color = dialog.color_celda
            from PyQt5.QtWidgets import QFileDialog
            archivo, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", f"horario_semestral.pdf", "PDF Files (*.pdf)")
            if archivo:
                horarios = self.modelo.obtener_horarios_semestrales(config["id_semestre"])
                from widgets.pdf_generator import PDFGenerator
                PDFGenerator.generar_semestral(config["id_semestre"], horarios, archivo, config, color)
                QMessageBox.information(self, "Éxito", f"PDF guardado en:\n{archivo}")
