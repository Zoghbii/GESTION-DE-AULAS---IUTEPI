from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QTableWidgetItem
from qfluentwidgets import (
    ScrollArea, CardWidget, PushButton, TitleLabel,
    InfoBar, InfoBarPosition, TableWidget
)

class EspaciosView(ScrollArea):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.setObjectName("EspaciosView")
        self.setStyleSheet("EspaciosView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Laboratorios y Espacios")
        layout.addWidget(title)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Tipo", "Capacidad", "Estatus"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        tabla_layout.addWidget(self.tabla)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        self.btn_estado = PushButton("Cambiar Estado")
        self.btn_estado.clicked.connect(self.cambiar_estado)
        btns.addWidget(self.btn_estado)
        btns.addStretch()
        tabla_layout.addLayout(btns)
        layout.addWidget(card_tabla)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def cargar_datos(self):
        espacios = self.modelo.obtener_espacios()
        self.tabla.setRowCount(0)
        for row_idx, e in enumerate(espacios):
            self.tabla.insertRow(row_idx)
            for col_idx in range(len(e)):
                valor = str(e[col_idx]) if e[col_idx] is not None else ""
                self.tabla.setItem(row_idx, col_idx, QTableWidgetItem(valor))

    def cambiar_estado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione un laboratorio")
            return
        id_item = self.tabla.item(fila, 0)
        estatus_item = self.tabla.item(fila, 4)
        if id_item is None or estatus_item is None:
            QMessageBox.warning(self, "Error", "Datos de la fila no válidos")
            return
        try:
            id_lab = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "ID de laboratorio inválido")
            return
        estatus_actual = estatus_item.text()
        nuevo = "Disponible" if estatus_actual == "Ocupado" else "Ocupado"
        if self.modelo.actualizar_estatus_laboratorio(id_lab, nuevo):
            self.cargar_datos()
            InfoBar.success(
                title="Estado actualizado",
                content=f"Laboratorio cambiado a {nuevo}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el estado")
