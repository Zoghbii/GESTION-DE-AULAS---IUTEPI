from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMessageBox, QDialog, QFormLayout, QTableWidgetItem
from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton, TitleLabel,
    CaptionLabel, ComboBox, LineEdit, InfoBar, InfoBarPosition, TableWidget
)
from utils.qt_helpers import parsear_id_tabla

DIAS_LUN_VIE = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]


def _parsear_hora_12h(texto, ampm):
    texto = (texto or "").strip()
    if not texto:
        return None
    partes = texto.split(":")
    if len(partes) != 2:
        return None
    try:
        h = int(partes[0])
        m = int(partes[1])
    except ValueError:
        return None
    if h < 1 or h > 12 or m < 0 or m > 59:
        return None
    ampm = (ampm or "AM").upper()
    if ampm == "PM" and h != 12:
        h += 12
    elif ampm == "AM" and h == 12:
        h = 0
    return f"{h:02d}:{m:02d}:00"


class SemestralView(ScrollArea):
    DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
    HORARIO_SA_INICIO = (7, 20)
    HORARIO_SA_FIN = (17, 0)

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
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Materia", "Profesor", "Día", "Hora Inicio", "Hora Fin", "Sección"]
        )
        self.tabla.setColumnWidth(0, 40)
        tabla_layout.addWidget(self.tabla)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btn_agregar = PrimaryPushButton("+ Agregar Clase")
        btn_agregar.clicked.connect(self.abrir_agregar)
        btn_horario_sa = PrimaryPushButton("+ Horario Sábado")
        btn_horario_sa.clicked.connect(lambda: self.abrir_agregar_horario_completo("SA"))
        btn_eliminar = PushButton("Eliminar")
        btn_eliminar.clicked.connect(self.eliminar_seleccionado)
        btn_pdf = PrimaryPushButton("Generar PDF")
        btn_pdf.clicked.connect(self.generar_pdf)
        btns.addWidget(btn_agregar)
        btns.addWidget(btn_horario_sa)
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
            seccion = h[6] if len(h) > 6 and h[6] else ""
            vals = [
                str(h[0]),
                str(h[1] or ""),
                str(h[2] or ""),
                str(h[3] or ""),
                str(h[4])[:5] if h[4] else "",
                str(h[5])[:5] if h[5] else "",
                seccion,
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
        dialog.setFixedSize(380, 360)
        dialog.setStyleSheet("background-color: #FFFFFF;")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        ent_materia = LineEdit()
        ent_materia.setPlaceholderText("Nombre de la materia")
        ent_profesor = LineEdit()
        ent_profesor.setPlaceholderText("Nombre del profesor")
        ent_seccion = LineEdit()
        ent_seccion.setPlaceholderText("Ej: SAI-101 (opcional)")
        comb_dia = ComboBox()
        comb_dia.addItems(self.DIAS)

        ent_hora_ini = LineEdit()
        ent_hora_ini.setText("08:00")
        ent_hora_ini.setPlaceholderText("hh:mm")
        ent_hora_ini.setFixedHeight(36)
        ent_hora_ini.setMaximumWidth(90)
        ent_hora_ini.setStyleSheet(self._time_style())
        comb_ampm_ini = ComboBox()
        comb_ampm_ini.addItems(["AM", "PM"])
        comb_ampm_ini.setFixedHeight(36)
        comb_ampm_ini.setMaximumWidth(70)
        hbox_ini = QHBoxLayout()
        hbox_ini.setSpacing(4)
        hbox_ini.addWidget(ent_hora_ini)
        hbox_ini.addWidget(comb_ampm_ini)
        hbox_ini.addStretch()
        wrap_ini = QFrame()
        wrap_ini.setLayout(hbox_ini)

        ent_hora_fin = LineEdit()
        ent_hora_fin.setText("09:00")
        ent_hora_fin.setPlaceholderText("hh:mm")
        ent_hora_fin.setFixedHeight(36)
        ent_hora_fin.setMaximumWidth(90)
        ent_hora_fin.setStyleSheet(self._time_style())
        comb_ampm_fin = ComboBox()
        comb_ampm_fin.addItems(["AM", "PM"])
        comb_ampm_fin.setFixedHeight(36)
        comb_ampm_fin.setMaximumWidth(70)
        hbox_fin = QHBoxLayout()
        hbox_fin.setSpacing(4)
        hbox_fin.addWidget(ent_hora_fin)
        hbox_fin.addWidget(comb_ampm_fin)
        hbox_fin.addStretch()
        wrap_fin = QFrame()
        wrap_fin.setLayout(hbox_fin)

        layout.addRow("Materia:", ent_materia)
        layout.addRow("Profesor:", ent_profesor)
        layout.addRow("Día:", comb_dia)
        layout.addRow("Sección:", ent_seccion)
        layout.addRow("Hora Inicio:", wrap_ini)
        layout.addRow("Hora Fin:", wrap_fin)

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
            seccion = ent_seccion.text().strip()
            dia = comb_dia.currentText()
            h_inicio = _parsear_hora_12h(ent_hora_ini.text(), comb_ampm_ini.currentText())
            h_fin = _parsear_hora_12h(ent_hora_fin.text(), comb_ampm_fin.currentText())
            if not materia or not profesor:
                QMessageBox.warning(self, "Error", "Complete todos los campos")
                return
            if not h_inicio or not h_fin:
                QMessageBox.warning(
                    self, "Error",
                    "Horas inválidas. Use formato hh:mm (1-12) con AM/PM."
                )
                return
            if h_inicio >= h_fin:
                QMessageBox.warning(self, "Error", "La hora de fin debe ser posterior a la de inicio.")
                return
            if self.modelo.agregar_horario_semestral(
                self.semestre_actual, materia, profesor, dia, h_inicio, h_fin, seccion
            ):
                QMessageBox.information(self, "Éxito", "Clase agregada correctamente")
                dialog.close()
                self.cargar_horarios()
            else:
                QMessageBox.critical(self, "Error", "No se pudo agregar la clase")

        btn_guardar.clicked.connect(guardar)
        btn_cancelar.clicked.connect(dialog.close)
        dialog.setLayout(layout)
        dialog.exec_()

    def abrir_agregar_horario_completo(self, tipo):
        if not self.semestre_actual:
            QMessageBox.warning(self, "Error", "Seleccione un semestre primero.")
            return

        if tipo == "LV":
            titulo = "Horario Lunes a Viernes"
            dias = DIAS_LUN_VIE
            h_inicio_12h = "07:40"
            ampm_ini = "AM"
            h_fin_12h = "03:00"
            ampm_fin = "PM"
        else:
            titulo = "Horario Sábado"
            dias = ["SÁBADO"]
            h_inicio_12h = f"{self.HORARIO_SA_INICIO[0]:02d}:{self.HORARIO_SA_INICIO[1]:02d}"
            h_fin_12h = f"{self.HORARIO_SA_FIN[0] % 12 or 12:02d}:{self.HORARIO_SA_FIN[1]:02d}"
            ampm_ini = "AM" if self.HORARIO_SA_INICIO[0] < 12 else "PM"
            ampm_fin = "AM" if self.HORARIO_SA_FIN[0] < 12 else "PM"

        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setFixedSize(380, 360)
        dialog.setStyleSheet("background-color: #FFFFFF;")
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        ent_materia = LineEdit()
        ent_materia.setPlaceholderText("Nombre de la materia")
        ent_profesor = LineEdit()
        ent_profesor.setPlaceholderText("Nombre del profesor")
        ent_seccion = LineEdit()
        ent_seccion.setPlaceholderText("Ej: SAI-101 (opcional)")

        ent_hora_ini = LineEdit()
        ent_hora_ini.setText(h_inicio_12h)
        ent_hora_ini.setPlaceholderText("hh:mm")
        ent_hora_ini.setFixedHeight(36)
        ent_hora_ini.setMaximumWidth(90)
        ent_hora_ini.setStyleSheet(self._time_style())
        comb_ampm_ini = ComboBox()
        comb_ampm_ini.addItems(["AM", "PM"])
        comb_ampm_ini.setFixedHeight(36)
        comb_ampm_ini.setMaximumWidth(70)
        comb_ampm_ini.setCurrentText(ampm_ini)
        hbox_ini = QHBoxLayout()
        hbox_ini.setSpacing(4)
        hbox_ini.addWidget(ent_hora_ini)
        hbox_ini.addWidget(comb_ampm_ini)
        hbox_ini.addStretch()
        wrap_ini = QFrame()
        wrap_ini.setLayout(hbox_ini)

        ent_hora_fin = LineEdit()
        ent_hora_fin.setText(h_fin_12h)
        ent_hora_fin.setPlaceholderText("hh:mm")
        ent_hora_fin.setFixedHeight(36)
        ent_hora_fin.setMaximumWidth(90)
        ent_hora_fin.setStyleSheet(self._time_style())
        comb_ampm_fin = ComboBox()
        comb_ampm_fin.addItems(["AM", "PM"])
        comb_ampm_fin.setFixedHeight(36)
        comb_ampm_fin.setMaximumWidth(70)
        comb_ampm_fin.setCurrentText(ampm_fin)
        hbox_fin = QHBoxLayout()
        hbox_fin.setSpacing(4)
        hbox_fin.addWidget(ent_hora_fin)
        hbox_fin.addWidget(comb_ampm_fin)
        hbox_fin.addStretch()
        wrap_fin = QFrame()
        wrap_fin.setLayout(hbox_fin)

        lbl_info = QLabel(f"Se crearán {len(dias)} clases: {', '.join(dias)}")
        lbl_info.setStyleSheet("color: #4B5563; font-size: 12px;")
        lbl_info.setWordWrap(True)

        layout.addRow("Materia:", ent_materia)
        layout.addRow("Profesor:", ent_profesor)
        layout.addRow("Sección:", ent_seccion)
        layout.addRow("Hora Inicio:", wrap_ini)
        layout.addRow("Hora Fin:", wrap_fin)
        layout.addRow("", lbl_info)

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
            seccion = ent_seccion.text().strip()
            h_inicio = _parsear_hora_12h(ent_hora_ini.text(), comb_ampm_ini.currentText())
            h_fin = _parsear_hora_12h(ent_hora_fin.text(), comb_ampm_fin.currentText())
            if not materia or not profesor:
                QMessageBox.warning(self, "Error", "Complete todos los campos")
                return
            if not h_inicio or not h_fin:
                QMessageBox.warning(
                    self, "Error",
                    "Horas inválidas. Use formato hh:mm (1-12) con AM/PM."
                )
                return
            if h_inicio >= h_fin:
                QMessageBox.warning(self, "Error", "La hora de fin debe ser posterior a la de inicio.")
                return

            ok_count = 0
            for dia in dias:
                if self.modelo.agregar_horario_semestral(
                    self.semestre_actual, materia, profesor, dia, h_inicio, h_fin, seccion
                ):
                    ok_count += 1

            if ok_count == len(dias):
                QMessageBox.information(
                    self, "Éxito",
                    f"{ok_count} clase(s) agregada(s) correctamente"
                )
                dialog.close()
                self.cargar_horarios()
            else:
                QMessageBox.warning(
                    self, "Parcial",
                    f"Solo {ok_count} de {len(dias)} clases se pudieron agregar"
                )
                self.cargar_horarios()

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
            id_horario = parsear_id_tabla(self.tabla, fila)
            if id_horario is None:
                return
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
            color_texto = dialog.color_texto
            from PyQt5.QtWidgets import QFileDialog
            archivo, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "horario_semestral.pdf", "PDF Files (*.pdf)")
            if archivo:
                dias = config.get("dias") or DIAS_LUN_VIE
                horarios = self.modelo.obtener_horarios_por_dias(config["id_semestre"], dias)
                from widgets.pdf_generator import PDFGenerator
                PDFGenerator.generar_semestral(
                    config["id_semestre"], horarios, archivo, config, color,
                    dias=dias, color_texto=color_texto
                )
                QMessageBox.information(self, "Éxito", f"PDF guardado en:\n{archivo}")

    @staticmethod
    def _time_style():
        return "border: 1px solid rgba(0,0,0,0.12); border-radius: 4px; padding: 6px;"
