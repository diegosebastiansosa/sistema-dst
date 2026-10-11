from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QHBoxLayout, QPushButton, QDialog, QMessageBox, QLineEdit, QSpinBox,
    QDateEdit, QCheckBox, QAbstractSpinBox,
)
from PySide6.QtCore import QDate
from qfluentwidgets import PushButton, SearchLineEdit

import prestaciones
from vistas.controles import agregar_selector_calendario
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, ESTILO_FORMULARIO,
    personalizar_barra_titulo, mostrar_mensaje,
)


class PantallaPrestaciones(QWidget):
    def __init__(self, ventana_principal, actualizar_dashboard=None):
        super().__init__()
        self.ventana_principal = ventana_principal
        self.actualizar_dashboard = actualizar_dashboard
        self.init_ui()

    def _notificar_cambio_datos(self):
        if self.actualizar_dashboard is not None:
            self.actualizar_dashboard()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        titulo = QLabel("Gestión de Prestaciones")
        titulo.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {COLOR_TEXTO_PRINCIPAL}; border: none;"
        )
        layout.addWidget(titulo)

        self.tabla_prestaciones = QTableWidget()
        self.tabla_prestaciones.setColumnCount(7)
        self.tabla_prestaciones.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Fecha", "Equipo", "Cliente", "Ganancia", "Acciones"]
        )
        self.tabla_prestaciones.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_prestaciones.setAlternatingRowColors(True)
        self.tabla_prestaciones.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                alternate-background-color: {COLOR_FONDO_CONTENIDO};
                border: 1px solid #E2E4EA;
                border-radius: 20px;
                gridline-color: #E2E4EA;
            }}
            QTableWidget::item {{
                color: {COLOR_TEXTO_PRINCIPAL};
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {COLOR_ACENTO};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {COLOR_FONDO_CONTENIDO};
                color: {COLOR_SIDEBAR};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.tabla_prestaciones)

        self.txt_buscar = SearchLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por empresa, fecha, equipo o cliente...")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setMinimumWidth(400)
        layout.addWidget(self.txt_buscar)
        self.txt_buscar.textChanged.connect(self.filtrar_prestaciones)

    def cargar_prestaciones(self):
        self.tabla_prestaciones.setRowCount(0)
        try:
            registros = prestaciones.obtener_prestaciones_activas()
            if not registros:
                self.tabla_prestaciones.setRowCount(1)
                self.tabla_prestaciones.setItem(
                    0, 0, QTableWidgetItem("No hay prestaciones activas registradas.")
                )
                return

            for fila, registro in enumerate(registros):
                self.tabla_prestaciones.insertRow(fila)
                valores = (
                    str(registro["id"]),
                    registro["empresa"],
                    registro["fecha"] or "-",
                    registro["equipo"],
                    registro["cliente"],
                    f"$ {registro['ganancia']}",
                )
                for columna, valor in enumerate(valores):
                    self.tabla_prestaciones.setItem(
                        fila, columna, QTableWidgetItem(str(valor))
                    )

                widget_acciones = QWidget()
                layout_acciones = QHBoxLayout(widget_acciones)
                layout_acciones.setContentsMargins(2, 2, 2, 2)
                layout_acciones.setSpacing(5)

                btn_editar = QPushButton("✏️")
                btn_editar.setToolTip("Editar prestación")
                btn_editar.setStyleSheet("""
                    QPushButton { border: none; border-radius: 6px; background-color: transparent; }
                    QPushButton:hover { background-color: rgba(108, 99, 255, 40); }
                """)

                btn_eliminar = QPushButton("❌")
                btn_eliminar.setToolTip("Dar de baja prestación")
                btn_eliminar.setStyleSheet("""
                    QPushButton { border: none; border-radius: 6px; background-color: transparent; }
                    QPushButton:hover { background-color: rgba(239, 68, 68, 40); }
                """)

                btn_editar.clicked.connect(
                    lambda checked=False, p=registro: self.abrir_formulario_edicion(p)
                )
                btn_eliminar.clicked.connect(
                    lambda checked=False, id_p=registro["id"], e=registro["empresa"]:
                        self.confirmar_baja(id_p, e)
                )
                layout_acciones.addWidget(btn_editar)
                layout_acciones.addWidget(btn_eliminar)
                self.tabla_prestaciones.setCellWidget(fila, 6, widget_acciones)
        except Exception as error:
            self.tabla_prestaciones.setRowCount(1)
            self.tabla_prestaciones.setItem(
                0, 0, QTableWidgetItem(f"Error al cargar prestaciones: {error}")
            )

    def filtrar_prestaciones(self):
        termino = self.txt_buscar.text().strip().lower()
        for fila in range(self.tabla_prestaciones.rowCount()):
            textos = [
                self.tabla_prestaciones.item(fila, columna).text().lower()
                for columna in range(1, 6)
                if self.tabla_prestaciones.item(fila, columna) is not None
            ]
            self.tabla_prestaciones.setRowHidden(
                fila, not any(termino in texto for texto in textos)
            )

    def confirmar_baja(self, id_prestacion, empresa):
        respuesta = mostrar_mensaje(
            self.ventana_principal,
            QMessageBox.Question,
            "Confirmar baja",
            f"¿Desea dar de baja la prestación de '{empresa}'? El registro se conservará en la base de datos.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return

        if prestaciones.eliminar_prestacion_logica(id_prestacion):
            mostrar_mensaje(
                self.ventana_principal,
                QMessageBox.Information,
                "Éxito",
                "La prestación fue dada de baja.",
            )
            self.cargar_prestaciones()
            self._notificar_cambio_datos()
        else:
            mostrar_mensaje(
                self.ventana_principal,
                QMessageBox.Critical,
                "Error",
                "No se pudo dar de baja la prestación.",
            )

    def _crear_dialogo(self, titulo, texto_boton):
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle(titulo)
        dialogo.setMinimumWidth(380)
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        personalizar_barra_titulo(dialogo)
        layout = QVBoxLayout(dialogo)

        layout.addWidget(QLabel("Empresa:"))
        campo_empresa = QLineEdit()
        layout.addWidget(campo_empresa)

        layout.addWidget(QLabel("Equipo:"))
        campo_equipo = QLineEdit()
        layout.addWidget(campo_equipo)

        layout.addWidget(QLabel("Cliente:"))
        campo_cliente = QLineEdit()
        layout.addWidget(campo_cliente)

        layout.addWidget(QLabel("Fecha:"))
        fila_fecha = QHBoxLayout()
        campo_fecha = QDateEdit()
        campo_fecha.setDisplayFormat("yyyy-MM-dd")
        campo_fecha.setDate(QDate.currentDate())
        fila_fecha.addWidget(campo_fecha)
        boton_calendario = agregar_selector_calendario(fila_fecha, campo_fecha)
        chk_sin_fecha = QCheckBox("Sin fecha")
        chk_sin_fecha.toggled.connect(campo_fecha.setDisabled)
        chk_sin_fecha.toggled.connect(boton_calendario.setDisabled)
        fila_fecha.addWidget(chk_sin_fecha)
        layout.addLayout(fila_fecha)

        layout.addWidget(QLabel("Ganancia:"))
        campo_ganancia = QSpinBox()
        campo_ganancia.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        campo_ganancia.setRange(0, 2147483647)
        campo_ganancia.setPrefix("$ ")
        layout.addWidget(campo_ganancia)

        boton_guardar = PushButton(texto_boton)
        boton_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white;")
        layout.addWidget(boton_guardar)
        return (
            dialogo, campo_empresa, campo_fecha, chk_sin_fecha,
            campo_equipo, campo_cliente, campo_ganancia, boton_guardar,
        )

    def abrir_formulario_prestacion(self):
        (dialogo, empresa, fecha, chk_sin_fecha, equipo, cliente,
         ganancia, boton) = self._crear_dialogo("Alta de Nueva Prestación", "Guardar Prestación")

        def procesar_alta():
            fecha_valor = None if chk_sin_fecha.isChecked() else fecha.date().toString("yyyy-MM-dd")
            exito, tipo_error, titulo_error, mensaje_error = prestaciones.alta_prestacion_validada(
                empresa.text(), fecha_valor, equipo.text(), cliente.text(), ganancia.value()
            )
            if not exito:
                tipo_mensaje = QMessageBox.Critical if tipo_error == "critical" else QMessageBox.Warning
                mostrar_mensaje(dialogo, tipo_mensaje, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "La prestación se guardó correctamente.")
            dialogo.accept()
            self.cargar_prestaciones()
            self._notificar_cambio_datos()

        boton.clicked.connect(procesar_alta)
        dialogo.exec()

    def abrir_formulario_edicion(self, prestacion_data):
        (dialogo, empresa, fecha, chk_sin_fecha, equipo, cliente,
         ganancia, boton) = self._crear_dialogo(
            f"Editar Prestación: {prestacion_data['empresa']}", "Guardar Cambios"
        )
        empresa.setText(prestacion_data["empresa"])
        equipo.setText(prestacion_data["equipo"])
        cliente.setText(prestacion_data["cliente"])
        fecha_actual = prestacion_data["fecha"]
        fecha_parseada = QDate.fromString(str(fecha_actual), "yyyy-MM-dd") if fecha_actual else QDate()
        fecha.setDate(fecha_parseada if fecha_parseada.isValid() else QDate.currentDate())
        chk_sin_fecha.setChecked(not fecha_parseada.isValid())
        ganancia.setValue(prestacion_data["ganancia"])

        def procesar_edicion():
            fecha_valor = None if chk_sin_fecha.isChecked() else fecha.date().toString("yyyy-MM-dd")
            exito, tipo_error, titulo_error, mensaje_error = prestaciones.editar_prestacion_validada(
                prestacion_data["id"], empresa.text(), fecha_valor,
                equipo.text(), cliente.text(), ganancia.value(),
            )
            if not exito:
                tipo_mensaje = QMessageBox.Critical if tipo_error == "critical" else QMessageBox.Warning
                mostrar_mensaje(dialogo, tipo_mensaje, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "Los datos de la prestación se actualizaron.")
            dialogo.accept()
            self.cargar_prestaciones()
            self._notificar_cambio_datos()

        boton.clicked.connect(procesar_edicion)
        dialogo.exec()
