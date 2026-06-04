"""Helpers para vistas PyQt5 (QTableWidget, QMessageBox)."""
from PyQt5.QtWidgets import QMessageBox


def parsear_id_tabla(tabla, fila, columna=0):
    """Lee el id de la primera columna de una fila de QTableWidget.

    Retorna el id (int) si la celda existe y es un entero valido.
    Retorna None si la celda esta vacia, no existe, o el texto no es entero.
    Muestra un QMessageBox informativo en caso de error.
    """
    item = tabla.item(fila, columna)
    if item is None:
        QMessageBox.warning(
            tabla, "Error",
            "La celda esta vacia. Seleccione una fila valida."
        )
        return None
    texto = item.text().strip()
    if not texto:
        QMessageBox.warning(
            tabla, "Error",
            "La celda no contiene un id. Seleccione una fila valida."
        )
        return None
    try:
        return int(texto)
    except ValueError:
        QMessageBox.warning(
            tabla, "Error",
            f"El id de la fila no es un numero valido: '{texto}'."
        )
        return None


def leer_celda(tabla, fila, columna):
    """Retorna el texto de una celda o '' si esta vacia."""
    item = tabla.item(fila, columna)
    return item.text() if item is not None else ""
