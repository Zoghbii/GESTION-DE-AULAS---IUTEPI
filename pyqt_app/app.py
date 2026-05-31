import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    setTheme, Theme, setThemeColor, NavigationAvatarWidget, InfoBar, InfoBarPosition
)

from utils.db_model import DatabaseModel
from views.home_view import HomeView
from views.reserva_view import ReservaView
from views.reportes_view import ReportesView
from views.semestral_view import SemestralView
from views.espacios_view import EspaciosView
from views.usuarios_view import UsuariosView

COLOR_ACCENT = "#E31E24"

class MainAppWindow(FluentWindow):
    def __init__(self, modelo, usuario, rol):
        super().__init__()
        self.modelo = modelo
        self.usuario = usuario
        self.rol = rol

        setThemeColor(COLOR_ACCENT)
        self.setWindowTitle("IUTEPI - Gestión de Laboratorios")
        self.resize(1200, 780)
        self.navigationInterface.setExpandWidth(200)
        self.navigationInterface.setCollapsible(False)

        self._init_views()
        self._init_footer()

    def _init_views(self):
        self.home_view = HomeView(self.modelo)
        self.reserva_view = ReservaView(self.modelo)
        self.reportes_view = ReportesView(self.modelo)
        self.semestral_view = SemestralView(self.modelo)
        self.espacios_view = EspaciosView(self.modelo)

        self.addSubInterface(self.home_view, FluentIcon.HOME, "Inicio")
        self.home_view.cargar_datos()
        self.addSubInterface(self.reserva_view, FluentIcon.CALENDAR, "Reservas")
        self.addSubInterface(self.reportes_view, FluentIcon.CHAT, "Reportes")
        self.addSubInterface(self.semestral_view, FluentIcon.LIBRARY, "Semestral")
        self.addSubInterface(self.espacios_view, FluentIcon.BUS, "Espacios")

        if self.rol == "Admin":
            self.usuarios_view = UsuariosView(self.modelo)
            self.addSubInterface(self.usuarios_view, FluentIcon.PEOPLE, "Usuarios")

    def _init_footer(self):
        nav_avatar = NavigationAvatarWidget(self.usuario, self.usuario)
        self.navigationInterface.addWidget(
            "avatar", nav_avatar, self._on_avatar_clicked,
            NavigationItemPosition.BOTTOM
        )
        self.navigationInterface.addItem(
            "theme-toggle", FluentIcon.BRIGHTNESS, "Tema",
            onClick=self._toggle_theme,
            position=NavigationItemPosition.BOTTOM
        )

    def _toggle_theme(self):
        from qfluentwidgets import qconfig
        if qconfig.themeMode.value == Theme.LIGHT:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)

    def _onCurrentInterfaceChanged(self, index: int):
        widget = self.stackedWidget.widget(index)
        if widget is not None and hasattr(widget, 'cargar_datos'):
            widget.cargar_datos()

    def _on_avatar_clicked(self):
        InfoBar.info(
            title=f"Conectado como {self.usuario}",
            content=f"Rol: {self.rol}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
