# =============================================================================
# vistas/gui_ordenes.py
# =============================================================================
# Este archivo define la pantalla visual de Gestión de Órdenes de Reparación.
# Vive dentro del paquete 'vistas/', por eso sus imports al backend usan
# el nombre de módulo simple (raíz del proyecto disponible en sys.path).
#
# ESTRUCTURA DEL MÓDULO:
#   - PantallaOrdenes (QWidget): todo el contenido visual de la pantalla
#       ├── init_ui()                          → construye la tabla y la barra de búsqueda
#       ├── cargar_ordenes()                   → lee la BD y llena la tabla
#       ├── filtrar_ordenes_en_tabla()         → filtra filas en tiempo real
#       ├── abrir_formulario_orden()           → ventana flotante para dar de alta una orden
#       ├── abrir_formulario_edicion_orden()   → ventana flotante para cambiar el estado
#       └── confirmar_cancelacion_orden()      → cancela una orden de reparación
# =============================================================================

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                                QTableWidgetItem, QHeaderView, QDialog,
                                QComboBox, QLineEdit, QPushButton, QMessageBox,
                                QHBoxLayout)
from PySide6.QtCore import Qt
from qfluentwidgets import PushButton, PrimaryPushButton, SearchLineEdit, FluentIcon as FIF, setTheme, Theme
import utilidades
import ordenes  # Backend de órdenes: operaciones CRUD sobre la tabla 'ordenes' en dst.db
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, ESTILO_FORMULARIO,
    personalizar_barra_titulo, mostrar_mensaje
)

class PantallaOrdenes(QWidget):
    """
    Clase que representa la pantalla de Gestión de Órdenes.
    Hereda de QWidget para funcionar como un contenedor visual independiente.
    """
    def __init__(self, ventana_principal):
        super().__init__()
        self.ventana_principal = ventana_principal  # Guardamos referencia para cuadros de diálogo
        self.init_ui()

    def init_ui(self):
        # ---- PANTALLA 3: Órdenes ----
        lay_ordenes = QVBoxLayout(self)  # Asignamos el layout vertical al widget actual (self)
        lay_ordenes.setContentsMargins(24, 24, 24, 24)  # aire alrededor del contenido, igual que en el dashboard
        lay_ordenes.setSpacing(12)  # separación prolija entre título, tabla y buscador

        lbl_ordenes = QLabel("Gestión de Órdenes")
        lbl_ordenes.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXTO_PRINCIPAL}; border: none;")
        
        # Creamos la tabla de órdenes con 6 columnas descriptivas (agregando Acciones al final)
        self.tabla_ordenes_ui = QTableWidget()
        self.tabla_ordenes_ui.setColumnCount(6)
        self.tabla_ordenes_ui.setHorizontalHeaderLabels(["Nº Orden", "Cliente", "Equipo", "Estado", "Descripción / Problema", "Acciones"])
        self.tabla_ordenes_ui.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # ---- SOLUCIÓN DE COLOR DE TEXTO ----
        self.tabla_ordenes_ui.setAlternatingRowColors(True)
        self.tabla_ordenes_ui.setStyleSheet(f"""
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
        
        lay_ordenes.addWidget(lbl_ordenes)
        lay_ordenes.addWidget(self.tabla_ordenes_ui)
        
        # Zona de Búsqueda al Fondo para Órdenes
        # Usamos un QHBoxLayout (diseño horizontal) para colocar la etiqueta de búsqueda y el campo de texto de lado a lado
        lay_busqueda_ord = QHBoxLayout()
        # SearchLineEdit de Fluent ya viene con la lupa e íconos
        self.txt_buscar_orden = SearchLineEdit()
        self.txt_buscar_orden.setPlaceholderText("Buscar orden por dueño, marca, modelo, procesador, GPU o problema...")
        self.txt_buscar_orden.setClearButtonEnabled(True)  # Agrega la "X" para limpiar la búsqueda con un clic
        self.txt_buscar_orden.setMinimumWidth(400)         # Le damos un ancho mínimo cómodo
        
        # Lo agregamos al diseño horizontal
        lay_busqueda_ord.addWidget(self.txt_buscar_orden)
        
        # Lo agregamos al fondo del layout vertical principal de la pantalla
        lay_ordenes.addLayout(lay_busqueda_ord)

        # Conectamos la señal 'textChanged' de la barra de búsqueda a nuestro método de filtrado.
        # Esto hace que, cada vez que el usuario escriba o borre una letra, la tabla se filtre automáticamente en tiempo real.
        self.txt_buscar_orden.textChanged.connect(self.filtrar_ordenes_en_tabla)

    def cargar_ordenes(self):
        self.tabla_ordenes_ui.setRowCount(0) # Limpiamos filas anteriores
        try:
            registros = utilidades.obtener_todas_las_ordenes()

            if not registros:
                self.tabla_ordenes_ui.setRowCount(1)
                self.tabla_ordenes_ui.setItem(0, 0, QTableWidgetItem("⚠️ No hay órdenes registradas."))
            else:
                for fila_index, reg in enumerate(registros):
                    self.tabla_ordenes_ui.insertRow(fila_index)
                    
                    # Llenamos las 5 columnas básicas de la tabla de órdenes
                    self.tabla_ordenes_ui.setItem(fila_index, 0, QTableWidgetItem(str(reg['id'])))
                    self.tabla_ordenes_ui.setItem(fila_index, 1, QTableWidgetItem(reg['cliente_nombre']))
                    self.tabla_ordenes_ui.setItem(fila_index, 2, QTableWidgetItem(reg['equipo_completo']))
                    self.tabla_ordenes_ui.setItem(fila_index, 3, QTableWidgetItem(reg['estado']))
                    self.tabla_ordenes_ui.setItem(fila_index, 4, QTableWidgetItem(reg['descripcion']))
                    
                    # --- NCrear contenedor de acciones para la Columna 5 (Acciones) ---
                    # QWidget actúa como contenedor para que los dos botones compartan la misma celda de la tabla
                    widget_acciones = QWidget()
                    lay_acciones = QHBoxLayout(widget_acciones)
                    lay_acciones.setContentsMargins(2, 2, 2, 2) # Margen pequeño
                    lay_acciones.setSpacing(5) # Espacio entre botones
                    
                    # Botón Editar Estado (✏️)
                    btn_editar_ord = QPushButton("✏️")
                    btn_editar_ord.setToolTip("Editar Estado de la Orden")
                    btn_editar_ord.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(108, 99, 255, 40);
                        }
                    """)
                    
                    # Botón Cancelar Orden (❌)
                    btn_cancelar_ord = QPushButton("❌")
                    btn_cancelar_ord.setToolTip("Cancelar Orden de Reparación")
                    btn_cancelar_ord.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(239, 68, 68, 40);
                        }
                    """)
                    
                    # Si la orden ya está "Cancelado", deshabilitamos los botones para evitar que una orden cancelada pueda volver a modificarse.
                    if reg['estado'] == 'Cancelado':
                        btn_editar_ord.setEnabled(False)
                        btn_cancelar_ord.setEnabled(False)
                        btn_editar_ord.setToolTip("Orden cancelada (no modificable)")
                        btn_cancelar_ord.setToolTip("Esta orden ya ha sido cancelada")
                    
                    # Conectamos las acciones usando expresiones lambda.
                    # Pasamos el registro actual 'r=reg' y el ID 'id_o=reg['id']' para congelarlos en el scope del bucle.
                    btn_editar_ord.clicked.connect(lambda checked=False, r=reg: self.abrir_formulario_edicion_orden(r))
                    btn_cancelar_ord.clicked.connect(lambda checked=False, id_o=reg['id']: self.confirmar_cancelacion_orden(id_o))
                    
                    # Agregamos los botones al diseño horizontal
                    lay_acciones.addWidget(btn_editar_ord)
                    lay_acciones.addWidget(btn_cancelar_ord)
                    
                    # Insertamos el contenedor directamente en la columna de Acciones (columna 6, índice 5)
                    self.tabla_ordenes_ui.setCellWidget(fila_index, 5, widget_acciones)
        except Exception as e:
            self.tabla_ordenes_ui.setRowCount(1)
            self.tabla_ordenes_ui.setItem(0, 0, QTableWidgetItem(f"❌ Error al cargar órdenes: {e}"))

    def filtrar_ordenes_en_tabla(self):
        """
        Filtra las filas de la tabla de órdenes en tiempo real según el texto de búsqueda.
        Busca coincidencias parciales de texto en el cliente (dueño), en los campos del equipo
        (marca, modelo, procesador, GPU, etc.) y en la descripción del problema.
        """
        # Obtenemos el texto del buscador, lo pasamos a minúsculas y limpiamos espacios vacíos en los extremos (.strip())
        termino = self.txt_buscar_orden.text().lower().strip()
        
        # Recorremos cada fila que contiene la tabla de órdenes en la interfaz gráfica
        for fila in range(self.tabla_ordenes_ui.rowCount()):
            # Obtenemos los ítems de las celdas de las columnas relevantes para la búsqueda:
            # - Columna 1: Nombre del dueño (Cliente)
            # - Columna 2: Ficha completa del equipo (marca, modelo, procesador, GPU...)
            # - Columna 4: Descripción del problema / problema
            item_cliente = self.tabla_ordenes_ui.item(fila, 1)
            item_equipo = self.tabla_ordenes_ui.item(fila, 2)
            item_descripcion = self.tabla_ordenes_ui.item(fila, 4)
            
            # Verificamos si las celdas tienen objetos válidos antes de extraer su texto
            if item_cliente and item_equipo and item_descripcion:
                # Convertimos todo a minúsculas para realizar una comparación insensible a mayúsculas (case-insensitive)
                cliente = item_cliente.text().lower()
                equipo = item_equipo.text().lower()
                descripcion = item_descripcion.text().lower()
                
                # Comprobamos si el término ingresado por el usuario está presente en alguna de las columnas
                coincide = (
                    termino in cliente or 
                    termino in equipo or 
                    termino in descripcion
                )
                
                # Si coincide con el término de búsqueda, hacemos visible la fila; si no, la ocultamos de la interfaz
                if coincide:
                    self.tabla_ordenes_ui.setRowHidden(fila, False)
                else:
                    self.tabla_ordenes_ui.setRowHidden(fila, True)

    def abrir_formulario_orden(self):
        # Abre una ventana flotante (QDialog) con el formulario para registrar una nueva orden de reparación en el sistema.
        # 1. Obtener la lista de todos los equipos activos de la base de datos.
        # Esto es indispensable porque cada orden debe asociarse obligatoriamente a un equipo y a su dueño.
        lista_equipos = utilidades.obtener_equipos_activos()
        
        # 2. Control preliminar: si no hay ningún equipo registrado y activo, detenemos la creación y advertimos al usuario (criterio solicitado).
        if not lista_equipos:
            mostrar_mensaje(
                self.ventana_principal, QMessageBox.Warning,
                "No hay equipos cargados",
                "⚠️ No hay equipos activos registrados en el sistema.\n"
                "Para poder cargar una nueva orden de reparación, primero debe dar de alta al menos un equipo."
            )
            return

        # 3. Creación del diálogo (Ventana flotante modal)
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle("Nueva Orden de Reparación")
        dialogo.resize(400, 350)
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo
        personalizar_barra_titulo(dialogo)
        # Layout vertical para acomodar las etiquetas, combo boxes y campos de texto ordenadamente
        lay_dialogo = QVBoxLayout(dialogo)
        
        # 4. Campo de selección de Equipo (QComboBox)
        lay_dialogo.addWidget(QLabel("<b>Seleccione el Equipo:</b>"))
        combo_equipos = QComboBox()
        lay_dialogo.addWidget(combo_equipos)
        
        # Cargamos los equipos activos dentro del combo desplegable
        for eq in lista_equipos:
            # Texto descriptivo visible para el usuario final en la interfaz
            nombre_visible = f"{eq['tipo']} {eq['marca']} {eq['modelo']} (ID: {eq['id']} - Dueño: {eq['cliente_nombre']})"
            
            # Guardamos el diccionario completo del equipo de forma oculta en el combo.
            # Al guardar todo el diccionario 'eq', podemos recuperar tanto 'id' como 'id_cliente'
            # de manera muy sencilla cuando el usuario presione el botón de guardar.
            combo_equipos.addItem(nombre_visible, eq)
            
        # 5. Campo de texto para la descripción del problema (QLineEdit)
        lay_dialogo.addWidget(QLabel("<b>Descripción del Problema:</b>"))
        txt_descripcion = QLineEdit()
        txt_descripcion.setPlaceholderText("Ej: No enciende / Pantalla rota / Limpieza...")
        lay_dialogo.addWidget(txt_descripcion)
        
        # 6. Botón para guardar la orden
        btn_guardar = PushButton("Guardar Orden de Reparación")
        # Le aplicamos un estilo destacado con fondo violeta (consistente con el color de Gestión de Órdenes: #8e44ad)
        btn_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white;")
        lay_dialogo.addWidget(btn_guardar)
        
        # 7. Función interna que procesará el guardado de la nueva orden al hacer click en el botón
        def procesar_alta_orden():
            # Recuperamos el diccionario del equipo seleccionado en el combo box
            equipo_seleccionado = combo_equipos.currentData()

            # Obtenemos el texto ingresado en el campo de descripción y quitamos espacios sobrantes
            descripcion = txt_descripcion.text().strip()

            # VALIDACIÓN Y PERSISTENCIA: le delegamos todo a ordenes.py
            exito, tipo_error, titulo_error, mensaje_error = ordenes.alta_orden_validada(
                id_equipo=equipo_seleccionado['id'],
                id_cliente=equipo_seleccionado['id_cliente'],
                descripcion=descripcion
            )

            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "¡La orden de reparación se ha registrado correctamente!")
            dialogo.accept()
            self.cargar_ordenes()
                
        # Conectamos el click del botón a nuestra función procesadora
        btn_guardar.clicked.connect(procesar_alta_orden)
        
        # Iniciamos el bucle modal (bloquea la ventana de fondo hasta que se acepte o cierre el diálogo)
        dialogo.exec()

    def abrir_formulario_edicion_orden(self, orden_data):
        # Abre una ventana flotante (QDialog) que permite al usuario modificar únicamente el estado de la orden seleccionada,
        # seleccionando entre los estados fijos definidos en ordenes.py.
        # Creamos la ventana de diálogo modal
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle(f"Editar Estado - Orden Nº {orden_data['id']}")
        dialogo.resize(350, 180)
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo
        personalizar_barra_titulo(dialogo)
        lay_dialogo = QVBoxLayout(dialogo)
        
        # Etiqueta informativa con el cliente y el equipo de la orden
        lbl_info = QLabel(f"<b>Cliente:</b> {orden_data['cliente_nombre']}<br><b>Equipo:</b> {orden_data['equipo_completo']}")
        lbl_info.setWordWrap(True) # Para que el texto se ajuste al ancho
        lay_dialogo.addWidget(lbl_info)
        
        # Selector de estados (QComboBox)
        lay_dialogo.addWidget(QLabel("<b>Nuevo Estado de la Orden:</b>"))
        combo_estados = QComboBox()
        lay_dialogo.addWidget(combo_estados)
        
        # Llenamos el combo box con los estados fijos de ordenes.py
        for estado in ordenes.ESTADOS_ORDEN:
            combo_estados.addItem(estado)
            
        # Seleccionamos por defecto el estado actual en el combo box
        estado_actual = orden_data['estado']
        index_actual = combo_estados.findText(estado_actual)
        if index_actual != -1:
            combo_estados.setCurrentIndex(index_actual)
            
        # Botón para guardar cambios
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white;")
        lay_dialogo.addWidget(btn_guardar)
        
        # Función interna para procesar la edición del estado al hacer clic en el botón
        def procesar_edicion_estado():
            nuevo_estado = combo_estados.currentText()

            # no llamar a la base de datos si no cambió nada
            if nuevo_estado == estado_actual:
                dialogo.accept()
                return

            # Delegamos la persistencia y la interpretación del resultado al backend
            exito, tipo_error, titulo_error, mensaje_error = ordenes.cambiar_estado_orden_validado(
                orden_data['id'], nuevo_estado
            )

            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "¡El estado de la orden se actualizó correctamente!")
            dialogo.accept()
            self.cargar_ordenes()
                
        # Conectamos el botón de guardar con la lógica del procesador
        btn_guardar.clicked.connect(procesar_edicion_estado)
        
        dialogo.exec()

    def confirmar_cancelacion_orden(self, id_orden):
        respuesta = mostrar_mensaje(
            self.ventana_principal, QMessageBox.Question, "Confirmar cancelación",  # CORRECCIÓN: Question con mayúscula
            f"¿Está seguro de que desea cancelar la Orden de Reparación Nº {id_orden}?\n"
            "Esta acción no se puede deshacer y la orden no se podrá volver a modificar.",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            exito, tipo_error, titulo_error, mensaje_error = ordenes.cancelar_orden_validada(id_orden)

            if not exito:
                mostrar_mensaje(self.ventana_principal, QMessageBox.Critical, titulo_error, mensaje_error)  # CORRECCIÓN: Critical
                return

            mostrar_mensaje(self.ventana_principal, QMessageBox.Information, "Éxito", f"La Orden Nº {id_orden} fue cancelada correctamente.")  # CORRECCIÓN: Information
            self.cargar_ordenes()
