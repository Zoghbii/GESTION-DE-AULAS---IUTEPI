from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    ScrollArea, CardWidget, PrimaryPushButton, PushButton, TitleLabel, BodyLabel,
    CaptionLabel, LineEdit, ComboBox, setFont, TableWidget
)
from utils.qt_helpers import parsear_id_tabla, leer_celda


class UsuariosView(ScrollArea):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.setObjectName("UsuariosView")
        self.setStyleSheet("UsuariosView { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        scroll_widget = QFrame()
        scroll_widget.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = TitleLabel("Usuarios")
        layout.addWidget(title)

        content = QHBoxLayout()
        content.setSpacing(16)

        card_form = CardWidget()
        form_layout = QVBoxLayout(card_form)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        lbl_form = BodyLabel("Crear Usuario")
        setFont(lbl_form, 14, QFont.Weight.DemiBold)
        form_layout.addWidget(lbl_form)

        lbl_user = CaptionLabel("Usuario:")
        form_layout.addWidget(lbl_user)
        self.ent_usuario = LineEdit()
        self.ent_usuario.setPlaceholderText("3-50 caracteres alfanuméricos")
        form_layout.addWidget(self.ent_usuario)

        lbl_pass = CaptionLabel("Contraseña:")
        form_layout.addWidget(lbl_pass)
        self.ent_pass = LineEdit()
        self.ent_pass.setPlaceholderText("Mínimo 6 caracteres")
        self.ent_pass.setEchoMode(LineEdit.Password)
        form_layout.addWidget(self.ent_pass)

        lbl_rol = CaptionLabel("Rol:")
        form_layout.addWidget(lbl_rol)
        self.comb_rol = ComboBox()
        self.comb_rol.addItems(["Admin", "Profesor"])
        form_layout.addWidget(self.comb_rol)

        form_layout.addSpacing(8)
        btn_crear = PrimaryPushButton("Crear Usuario")
        btn_crear.clicked.connect(self.crear_usuario)
        form_layout.addWidget(btn_crear)
        form_layout.addStretch()
        content.addWidget(card_form, 1)

        card_tabla = CardWidget()
        tabla_layout = QVBoxLayout(card_tabla)
        tabla_layout.setContentsMargins(16, 16, 16, 16)

        lbl_tab = BodyLabel("Usuarios Existentes")
        setFont(lbl_tab, 13, QFont.Weight.DemiBold)
        tabla_layout.addWidget(lbl_tab)

        self.tabla = TableWidget()
        self.tabla.setBorderVisible(True)
        self.tabla.setBorderRadius(4)
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Usuario", "Rol"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        tabla_layout.addWidget(self.tabla)

        btn_eliminar = PushButton("Eliminar Usuario")
        btn_eliminar.clicked.connect(self.eliminar_usuario)
        tabla_layout.addWidget(btn_eliminar)

        content.addWidget(card_tabla, 2)
        layout.addLayout(content)

        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

    def cargar_datos(self):
        usuarios = self.modelo.obtener_usuarios()
        self.tabla.setRowCount(0)
        for row_idx, usuario in enumerate(usuarios):
            self.tabla.insertRow(row_idx)
            for col_idx, valor in enumerate(usuario):
                self.tabla.setItem(
                    row_idx, col_idx,
                    QTableWidgetItem(str(valor) if valor is not None else "")
                )

    def crear_usuario(self):
        nombre = self.ent_usuario.text().strip()
        contrasena = self.ent_pass.text()
        rol = self.comb_rol.currentText()

        if not nombre or not contrasena:
            QMessageBox.warning(self, "Error", "Complete todos los campos.")
            return

        if not self.modelo.validar_nombre_usuario(nombre):
            QMessageBox.warning(
                self, "Error",
                "Usuario debe tener 3-50 caracteres alfanuméricos (solo letras, números y _)."
            )
            return

        if not self.modelo.validar_contrasena(contrasena):
            QMessageBox.warning(
                self, "Error",
                "Contraseña debe tener al menos 6 caracteres."
            )
            return

        ok, msg = self.modelo.crear_usuario(nombre, contrasena, rol)
        if ok:
            QMessageBox.information(self, "Éxito", f"Usuario '{nombre}' creado correctamente.")
            self.ent_usuario.clear()
            self.ent_pass.clear()
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario.\n{msg}")

    def eliminar_usuario(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione un usuario para eliminar.")
            return
        id_usuario = parsear_id_tabla(self.tabla, fila)
        if id_usuario is None:
            return
        nombre_usuario = leer_celda(self.tabla, fila, 1)
        if nombre_usuario == 'admin':
            QMessageBox.warning(self, "Error", "No se puede eliminar el usuario admin principal.")
            return
        confirm = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar usuario '{nombre_usuario}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.modelo.eliminar_usuario(id_usuario):
                QMessageBox.information(self, "Éxito", "Usuario eliminado.")
                self.cargar_datos()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el usuario.")
