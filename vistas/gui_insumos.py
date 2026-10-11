from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QHBoxLayout, QPushButton, QDialog, QMessageBox, QLineEdit, QSpinBox,
    QDateEdit, QCheckBox, QAbstractSpinBox,
)
from PySide6.QtCore import QDate
from qfluentwidgets import PushButton, SearchLineEdit

import insumos
from vistas.controles import agregar_selector_calendario
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, ESTILO_FORMULARIO,
    personalizar_barra_titulo, mostrar_mensaje,
)


class PantallaInsumos(QWidget):
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

        titulo = QLabel("Gestión de Insumos")
        titulo.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {COLOR_TEXTO_PRINCIPAL}; border: none;"
        )
        layout.addWidget(titulo)

        self.tabla_insumos = QTableWidget()
        self.tabla_insumos.setColumnCount(6)
        self.tabla_insumos.setHorizontalHeaderLabels(
            ["ID", "Descripción", "Fecha", "Unidades", "Costo", "Acciones"]
        )
        self.tabla_insumos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_insumos.setAlternatingRowColors(True)
        self.tabla_insumos.setStyleSheet(f"""
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
        layout.addWidget(self.tabla_insumos)

        self.txt_buscar = SearchLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar insumo por descripción o fecha...")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setMinimumWidth(400)
        layout.addWidget(self.txt_buscar)
        self.txt_buscar.textChanged.connect(self.filtrar_insumos)

    def cargar_insumos(self):
        self.tabla_insumos.setRowCount(0)
        try:
            registros = insumos.obtener_insumos_activos()
            if not registros:
                self.tabla_insumos.setRowCount(1)
                self.tabla_insumos.setItem(
                    0, 0, QTableWidgetItem("No hay insumos activos registrados.")
                )
                return

            for fila, registro in enumerate(registros):
                self.tabla_insumos.insertRow(fila)
                self.tabla_insumos.setItem(fila, 0, QTableWidgetItem(str(registro["id"])))
                self.tabla_insumos.setItem(fila, 1, QTableWidgetItem(registro["descripcion"]))
                self.tabla_insumos.setItem(fila, 2, QTableWidgetItem(registro["fecha"] or "-"))
                self.tabla_insumos.setItem(fila, 3, QTableWidgetItem(str(registro["unidades"])))
                self.tabla_insumos.setItem(fila, 4, QTableWidgetItem(f"$ {registro['costo']}"))

                widget_acciones = QWidget()
                layout_acciones = QHBoxLayout(widget_acciones)
                layout_acciones.setContentsMargins(2, 2, 2, 2)
                layout_acciones.setSpacing(5)

                btn_editar = QPushButton("✏️")
                btn_editar.setToolTip("Editar insumo")
                btn_editar.setStyleSheet("""
                    QPushButton { border: none; border-radius: 6px; background-color: transparent; }
                    QPushButton:hover { background-color: rgba(108, 99, 255, 40); }
                """)

                btn_eliminar = QPushButton("❌")
                btn_eliminar.setToolTip("Dar de baja insumo")
                btn_eliminar.setStyleSheet("""
                    QPushButton { border: none; border-radius: 6px; background-color: transparent; }
                    QPushButton:hover { background-color: rgba(239, 68, 68, 40); }
                """)

                btn_editar.clicked.connect(
                    lambda checked=False, i=registro: self.abrir_formulario_edicion(i)
                )
                btn_eliminar.clicked.connect(
                    lambda checked=False, id_i=registro["id"], d=registro["descripcion"]:
                        self.confirmar_baja(id_i, d)
                )
                layout_acciones.addWidget(btn_editar)
                layout_acciones.addWidget(btn_eliminar)
                self.tabla_insumos.setCellWidget(fila, 5, widget_acciones)
        except Exception as error:
            self.tabla_insumos.setRowCount(1)
            self.tabla_insumos.setItem(
                0, 0, QTableWidgetItem(f"Error al cargar insumos: {error}")
            )

    def filtrar_insumos(self):
        termino = self.txt_buscar.text().strip().lower()
        for fila in range(self.tabla_insumos.rowCount()):
            item_descripcion = self.tabla_insumos.item(fila, 1)
            item_fecha = self.tabla_insumos.item(fila, 2)
            if item_descripcion is not None and item_fecha is not None:
                self.tabla_insumos.setRowHidden(
                    fila,
                    termino not in item_descripcion.text().lower()
                    and termino not in item_fecha.text().lower(),
                )

    def confirmar_baja(self, id_insumo, descripcion):
        respuesta = mostrar_mensaje(
            self.ventana_principal,
            QMessageBox.Question,
            "Confirmar baja",
            f"¿Desea dar de baja el insumo '{descripcion}'? Dejará de aparecer en el listado, pero sus datos se conservarán.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return

        if insumos.eliminar_insumo_logico(id_insumo):
            mostrar_mensaje(
                self.ventana_principal,
                QMessageBox.Information,
                "Éxito",
                f"El insumo '{descripcion}' fue dado de baja.",
            )
            self.cargar_insumos()
            self._notificar_cambio_datos()
        else:
            mostrar_mensaje(
                self.ventana_principal,
                QMessageBox.Critical,
                "Error",
                "No se pudo dar de baja el insumo.",
            )

    def _crear_campos_numericos(self, layout, unidades=0, costo=0):
        layout.addWidget(QLabel("Unidades:"))
        campo_unidades = QSpinBox()
        campo_unidades.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        campo_unidades.setRange(0, 2147483647)
        campo_unidades.setValue(unidades)
        layout.addWidget(campo_unidades)

        layout.addWidget(QLabel("Costo:"))
        campo_costo = QSpinBox()
        campo_costo.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        campo_costo.setRange(0, 2147483647)
        campo_costo.setPrefix("$ ")
        campo_costo.setValue(costo)
        layout.addWidget(campo_costo)
        return campo_unidades, campo_costo

    def _crear_dialogo(self, titulo, texto_boton):
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle(titulo)
        dialogo.setMinimumWidth(340)
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        personalizar_barra_titulo(dialogo)
        layout = QVBoxLayout(dialogo)

        layout.addWidget(QLabel("Descripción:"))
        campo_descripcion = QLineEdit()
        layout.addWidget(campo_descripcion)

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

        campo_unidades, campo_costo = self._crear_campos_numericos(layout)

        boton_guardar = PushButton(texto_boton)
        boton_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white;")
        layout.addWidget(boton_guardar)
        return (
            dialogo, campo_descripcion, campo_fecha, chk_sin_fecha,
            campo_unidades, campo_costo, boton_guardar,
        )

    def abrir_formulario_insumo(self):
        (dialogo, descripcion, fecha, chk_sin_fecha,
         unidades, costo, boton) = self._crear_dialogo("Alta de Nuevo Insumo", "Guardar Insumo")

        def procesar_alta():
            fecha_valor = None if chk_sin_fecha.isChecked() else fecha.date().toString("yyyy-MM-dd")
            exito, tipo_error, titulo_error, mensaje_error = insumos.alta_insumo_validada(
                descripcion.text(), fecha_valor, unidades.value(), costo.value()
            )
            if not exito:
                tipo_mensaje = QMessageBox.Critical if tipo_error == "critical" else QMessageBox.Warning
                mostrar_mensaje(dialogo, tipo_mensaje, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "El insumo se guardó correctamente.")
            dialogo.accept()
            self.cargar_insumos()
            self._notificar_cambio_datos()

        boton.clicked.connect(procesar_alta)
        dialogo.exec()

    def abrir_formulario_edicion(self, insumo_data):
        (dialogo, descripcion, fecha, chk_sin_fecha,
         unidades, costo, boton) = self._crear_dialogo(
            f"Editar Insumo: {insumo_data['descripcion']}", "Guardar Cambios"
        )
        descripcion.setText(insumo_data["descripcion"])
        fecha_actual = insumo_data["fecha"]
        fecha_parseada = QDate.fromString(str(fecha_actual), "yyyy-MM-dd") if fecha_actual else QDate()
        fecha.setDate(fecha_parseada if fecha_parseada.isValid() else QDate.currentDate())
        chk_sin_fecha.setChecked(not fecha_parseada.isValid())
        unidades.setValue(insumo_data["unidades"])
        costo.setValue(insumo_data["costo"])

        def procesar_edicion():
            fecha_valor = None if chk_sin_fecha.isChecked() else fecha.date().toString("yyyy-MM-dd")
            exito, tipo_error, titulo_error, mensaje_error = insumos.editar_insumo_validado(
                insumo_data["id"], descripcion.text(), fecha_valor,
                unidades.value(), costo.value(),
            )
            if not exito:
                tipo_mensaje = QMessageBox.Critical if tipo_error == "critical" else QMessageBox.Warning
                mostrar_mensaje(dialogo, tipo_mensaje, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "Los datos del insumo se actualizaron.")
            dialogo.accept()
            self.cargar_insumos()
            self._notificar_cambio_datos()

        boton.clicked.connect(procesar_edicion)
        dialogo.exec()
