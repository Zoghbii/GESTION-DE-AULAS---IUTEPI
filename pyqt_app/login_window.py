from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import os
import logging

logger = logging.getLogger("iutepi.login")

COLOR_ROJO = "#E31E24"


class LoginWindow(QWidget):
    def __init__(self, modelo, callback_login):
        super().__init__()
        self.modelo = modelo
        self.callback_login = callback_login
        self.intentos = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("IUTEPI - Gestión de Laboratorios")
        self.setFixedSize(400, 500)
        self.center_window()
        self.setStyleSheet("background-color: #F5F7F9;")

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(30, 30, 30, 30)

        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "LOG40CM-3-scaled-e1643832660979-removebg-preview.png"
        )
        if os.path.exists(logo_path):
            lbl_logo = QLabel()
            pixmap = QPixmap(logo_path).scaled(
                140, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(lbl_logo)

        lbl_titulo = QLabel("IUTEPI")
        lbl_titulo.setFont(QFont("Segoe UI", 32, QFont.Bold))
        lbl_titulo.setStyleSheet(f"color: {COLOR_ROJO};")
        lbl_titulo.setAlignment(Qt.AlignCenter)

        lbl_subtitulo = QLabel("Gestión de Laboratorios")
        lbl_subtitulo.setFont(QFont("Segoe UI", 12))
        lbl_subtitulo.setStyleSheet("color: #6B7280;")
        lbl_subtitulo.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(lbl_titulo)
        card_layout.addWidget(lbl_subtitulo)
        card_layout.addSpacing(30)

        self.ent_user = QLineEdit()
        self.ent_user.setPlaceholderText("Usuario")
        self.ent_user.setFixedHeight(45)
        self.ent_user.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: #F9F9F9;
            }
            QLineEdit:focus {
                border: 2px solid #E31E24;
            }
        """)

        self.ent_pass = QLineEdit()
        self.ent_pass.setPlaceholderText("Contraseña")
        self.ent_pass.setFixedHeight(45)
        self.ent_pass.setEchoMode(QLineEdit.Password)
        self.ent_pass.returnPressed.connect(self.intentar_login)
        self.ent_pass.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: #F9F9F9;
            }
            QLineEdit:focus {
                border: 2px solid #E31E24;
            }
        """)

        self.btn_entrar = QPushButton("ENTRAR")
        self.btn_entrar.setFixedHeight(45)
        self.btn_entrar.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_entrar.setCursor(Qt.PointingHandCursor)
        self.btn_entrar.clicked.connect(self.intentar_login)
        self.btn_entrar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ROJO};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C41920;
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)

        card_layout.addWidget(self.ent_user)
        card_layout.addWidget(self.ent_pass)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.btn_entrar)

        card.setLayout(card_layout)
        layout.addWidget(card)
        self.setLayout(layout)

    def center_window(self):
        from PyQt5.QtWidgets import QDesktopWidget
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def intentar_login(self):
        if self.intentos >= 5:
            QMessageBox.critical(
                self, "Bloqueado",
                "Demasiados intentos fallidos. Reinicia la aplicación."
            )
            self.btn_entrar.setEnabled(False)
            return

        usuario = self.ent_user.text().strip()
        contrasena = self.ent_pass.text()

        if not usuario or not contrasena:
            QMessageBox.warning(self, "Error", "Por favor complete todos los campos.")
            return

        self.btn_entrar.setEnabled(False)
        self.btn_entrar.setText("Verificando...")

        try:
            rol = self.modelo.validar_usuario(usuario, contrasena)
            if rol:
                self.intentos = 0
                self.callback_login(usuario, rol)
            else:
                self.intentos += 1
                restantes = 5 - self.intentos
                msg = "Usuario o contraseña incorrectos."
                if restantes > 0:
                    msg += f" Intentos restantes: {restantes}"
                QMessageBox.critical(self, "Error", msg)
                self.ent_pass.clear()
                self.ent_pass.setFocus()
        except Exception:
            logger.exception("Error de transporte al validar usuario")
            QMessageBox.critical(
                self, "Error de conexion",
                "No se pudo contactar al servidor. Intente nuevamente."
            )
        finally:
            self.btn_entrar.setEnabled(True)
            self.btn_entrar.setText("ENTRAR")
