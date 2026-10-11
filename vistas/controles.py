from PySide6.QtWidgets import (
    QAbstractSpinBox, QBoxLayout, QCalendarWidget, QDateEdit, QDialog,
    QToolButton, QVBoxLayout,
)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from qfluentwidgets import FluentIcon as FIF

from vistas.estilos import COLOR_ACENTO, COLOR_TEXTO_PRINCIPAL


def agregar_selector_calendario(layout: QBoxLayout, campo_fecha: QDateEdit) -> QToolButton:
    campo_fecha.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    campo_fecha.setCalendarPopup(False)

    boton_calendario = QToolButton()
    boton_calendario.setIcon(FIF.CALENDAR.icon(color=QColor(COLOR_TEXTO_PRINCIPAL)))
    boton_calendario.setToolTip("Elegir fecha")
    boton_calendario.setFixedSize(32, 32)
    boton_calendario.setStyleSheet(f"""
        QToolButton {{
            background-color: white;
            border: 1px solid #D8DAE5;
            border-radius: 6px;
        }}
        QToolButton:hover {{
            background-color: #E5E7EB;
            border-color: {COLOR_ACENTO};
        }}
    """)

    def mostrar_calendario():
        dialogo = QDialog(boton_calendario.window(), Qt.Popup)
        dialogo.setStyleSheet(f"""
            QDialog {{
                background-color: white;
                border: 1px solid #D8DAE5;
                border-radius: 8px;
            }}
            QCalendarWidget QToolButton {{
                color: {COLOR_TEXTO_PRINCIPAL};
                background-color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: #E5E7EB;
            }}
            QCalendarWidget QTableView {{
                selection-background-color: {COLOR_ACENTO};
                selection-color: white;
            }}
        """)
        layout_calendario = QVBoxLayout(dialogo)
        layout_calendario.setContentsMargins(8, 8, 8, 8)
        calendario = QCalendarWidget()
        calendario.setSelectedDate(campo_fecha.date())
        calendario.clicked.connect(lambda fecha: (campo_fecha.setDate(fecha), dialogo.accept()))
        layout_calendario.addWidget(calendario)
        dialogo.adjustSize()
        dialogo.move(boton_calendario.mapToGlobal(QPoint(0, boton_calendario.height())))
        dialogo.exec()

    boton_calendario.clicked.connect(mostrar_calendario)
    layout.addWidget(boton_calendario)
    return boton_calendario
