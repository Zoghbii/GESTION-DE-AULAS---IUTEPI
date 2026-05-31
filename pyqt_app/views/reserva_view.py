from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QMessageBox, QTableWidgetItem
from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton, TitleLabel, BodyLabel,
    CaptionLabel, LineEdit, ComboBox, DatePicker, TimePicker, setFont,
    InfoBar, InfoBarPosition, TableWidget
)


class ReservaView(ScrollArea):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.setObjectName("ReservaView")
        self.setStyleSheet("ReservaView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Crear Reserva")
        layout.addWidget(title)

        content = QHBoxLayout()
        content.setSpacing(16)

        card_form = CardWidget()
        form_layout = QVBoxLayout(card_form)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        lbl_form = BodyLabel("Datos de la Reserva")
        setFont(lbl_form, 14, QFont.Weight.DemiBold)
        form_layout.addWidget(lbl_form)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.ent_docente = LineEdit()
        self._add_field(grid, 0, 0, "Docente", self.ent_docente, "Nombre del docente")
        self.ent_materia = LineEdit()
        self._add_field(grid, 0, 1, "Materia", self.ent_materia, "Nombre de la materia")

        self.comb_carrera = ComboBox()
        self.comb_carrera.addItems([
            "Administración Industrial", "Análisis de Sistemas", "Electrónica"
        ])
        self._add_field(grid, 1, 0, "Carrera", self.comb_carrera, "Seleccionar carrera")

        self.ent_estudiantes = LineEdit()
        self._add_field(grid, 1, 1, "N° Estudiantes", self.ent_estudiantes, "Cantidad")

        self.ent_periodo = LineEdit()
        self._add_field(grid, 2, 0, "Período", self.ent_periodo, "Ej: PR25-4")

        form_layout.addLayout(grid)

        btn_crear = PrimaryPushButton("Guardar Reserva")
        btn_crear.clicked.connect(self.guardar)
        form_layout.addWidget(btn_crear)

        content.addWidget(card_form, 1)

        card_cal = CardWidget()
        cal_layout = QVBoxLayout(card_cal)
        cal_layout.setContentsMargins(16, 16, 16, 16)
        lbl_cal = BodyLabel("Fecha y Hora")
        setFont(lbl_cal, 13, QFont.Weight.DemiBold)
        cal_layout.addWidget(lbl_cal)

        lbl_fecha = CaptionLabel("Fecha:")
        cal_layout.addWidget(lbl_fecha)
        self.date_picker = DatePicker()
        self.date_picker.setDate(QDate.currentDate())
        cal_layout.addWidget(self.date_picker)

        lbl_ini = CaptionLabel("Hora inicio:")
        cal_layout.addWidget(lbl_ini)
        self.time_inicio = TimePicker()
        self.time_inicio.setTime(QTime(8, 0))
        cal_layout.addWidget(self.time_inicio)

        lbl_fin = CaptionLabel("Hora fin:")
        cal_layout.addWidget(lbl_fin)
        self.time_fin = TimePicker()
        self.time_fin.setTime(QTime(9, 0))
        cal_layout.addWidget(self.time_fin)

        lbl_lab = CaptionLabel("Laboratorio:")
        cal_layout.addWidget(lbl_lab)
        self.comb_lab = ComboBox()
        cal_layout.addWidget(self.comb_lab)

        content.addWidget(card_cal, 1)
        layout.addLayout(content)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)
        lbl_tab = BodyLabel("Reservas Recientes")
        setFont(lbl_tab, 13, QFont.Weight.DemiBold)
        tabla_layout.addWidget(lbl_tab)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Docente", "Materia", "Carrera",
            "Estudiantes", "Lab", "Fecha", "Inicio", "Fin"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        tabla_layout.addWidget(self.tabla)

        btn_eliminar = PushButton("Eliminar Reserva")
        btn_eliminar.clicked.connect(self.eliminar)
        tabla_layout.addWidget(btn_eliminar)

        layout.addWidget(card_tabla)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def _add_field(self, grid, row, col, label, widget, placeholder):
        lbl = CaptionLabel(label)
        grid.addWidget(lbl, row * 2, col)
        grid.addWidget(widget, row * 2 + 1, col)
        if isinstance(widget, LineEdit):
            widget.setPlaceholderText(placeholder)

    def guardar(self):
        docente = self.ent_docente.text().strip()
        materia = self.ent_materia.text().strip()
        carrera = self.comb_carrera.currentText()
        estudiantes_text = self.ent_estudiantes.text().strip()
        periodo = self.ent_periodo.text().strip()

        if not all([docente, materia, estudiantes_text, periodo]):
            QMessageBox.warning(self, "Error", "Complete todos los campos obligatorios.")
            return

        try:
            estudiantes = int(estudiantes_text)
            if estudiantes <= 0 or estudiantes > 100:
                QMessageBox.warning(self, "Error", "N° de estudiantes inválido (1-100).")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "N° de estudiantes debe ser un número.")
            return

        fecha = self.date_picker.date.toString("yyyy-MM-dd")
        h_inicio = self.time_inicio.time.toString("HH:mm:ss")
        h_fin = self.time_fin.time.toString("HH:mm:ss")

        if h_inicio >= h_fin:
            QMessageBox.warning(self, "Error", "La hora de fin debe ser posterior a la de inicio.")
            return

        id_lab = self.comb_lab.currentData()
        if not id_lab:
            QMessageBox.warning(self, "Error", "Seleccione un laboratorio.")
            return

        disponible, msg = self.modelo.verificar_disponibilidad(id_lab, fecha, h_inicio, h_fin)
        if not disponible:
            QMessageBox.warning(self, "Sin disponibilidad", msg)
            return

        datos = {
            'profesor': docente,
            'materia': materia,
            'carrera': carrera,
            'estudiantes': estudiantes,
            'periodo': periodo,
            'tipo': 'Evento Único',
            'dia': '',
            'fecha': fecha,
            'h_inicio': h_inicio,
            'h_fin': h_fin,
            'id_lab': id_lab,
        }

        if self.modelo.guardar_reserva(datos):
            InfoBar.success(
                title="Reserva creada",
                content="Reserva guardada correctamente",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.ent_docente.clear()
            self.ent_materia.clear()
            self.ent_estudiantes.clear()
            self.ent_periodo.clear()
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar la reserva. Intente de nuevo.")

    def eliminar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una reserva de la tabla.")
            return

        id_reserva = int(self.tabla.item(fila, 0).text())
        docente = self.tabla.item(fila, 1).text()
        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar reserva de {docente}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.modelo.eliminar_reserva(id_reserva):
                InfoBar.success(
                    title="Reserva eliminada",
                    content="La reserva fue eliminada correctamente",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self.cargar_datos()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la reserva.")

    def cargar_datos(self):
        espacios = self.modelo.obtener_espacios()
        self.comb_lab.clear()
        for e in espacios:
            self.comb_lab.addItem(f"{e[1]}", userData=e[0])

        reservas = self.modelo.obtener_todas_reservas(50)
        self.tabla.setRowCount(0)
        for row_idx, r in enumerate(reservas):
            self.tabla.insertRow(row_idx)
            for col_idx in range(len(r)):
                valor = str(r[col_idx]) if r[col_idx] is not None else ""
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(valor))
