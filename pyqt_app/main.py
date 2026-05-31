import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QLocale
from qfluentwidgets import setThemeColor

from app import MainAppWindow
from login_window import LoginWindow
from utils.db_model import DatabaseModel

COLOR_ACCENT = "#E31E24"


class IUTEPIApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        QLocale.setDefault(QLocale(QLocale.Spanish))
        setThemeColor(COLOR_ACCENT)

        self.modelo = DatabaseModel()
        self.modelo.inicializar_usuarios()

    def run(self):
        self.login_window = LoginWindow(self.modelo, self.on_login_success)
        self.login_window.show()
        return self.app.exec_()

    def on_login_success(self, usuario, rol):
        self.login_window.close()
        self.main_window = MainAppWindow(self.modelo, usuario, rol)
        self.main_window.show()


if __name__ == "__main__":
    aplicacion = IUTEPIApp()
    sys.exit(aplicacion.run())
