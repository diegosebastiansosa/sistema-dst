# =============================================================================
# vistas/gui_clientes.py
# =============================================================================
# Este archivo define la pantalla visual de Gestión de Clientes.
# Vive dentro del paquete 'vistas/', por eso sus imports al backend deben
# subir un nivel con un punto '.' relativo, o bien importar directamente
# por nombre (ya que app.py agrega la raíz del proyecto al sys.path).
#
# ESTRUCTURA DEL MÓDULO:
#   - PantallaClientes (QWidget): todo el contenido visual de la pantalla
#       ├── init_ui()                    → construye la tabla y la barra de búsqueda
#       ├── cargar_clientes()            → lee la BD y llena la tabla
#       ├── filtrar_clientes_en_tabla()  → filtra filas en tiempo real
#       ├── confirmar_baja_logica()      → elimina un cliente (baja lógica)
#       ├── abrir_formulario_edicion()   → ventana flotante para editar un cliente
#       └── abrir_formulario_cliente()   → ventana flotante para dar de alta un cliente
# =============================================================================

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                                QTableWidgetItem, QHeaderView, QHBoxLayout, 
                                QLineEdit, QPushButton, QDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression

from qfluentwidgets import PushButton, PrimaryPushButton, SearchLineEdit, FluentIcon as FIF, setTheme, Theme

# Importamos los módulos de backend usando su nombre simple.
# Esto funciona porque app.py (que está en la raíz) ya fue ejecutado,
# lo que hace que Python conozca la ruta raíz del proyecto.
import utilidades
import clientes  # Backend de clientes: operaciones CRUD sobre la tabla 'clientes' en dst.db

# Importamos la paleta de colores centralizada, la misma que usan app.py y dashboard.py
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, ESTILO_FORMULARIO,
    personalizar_barra_titulo, mostrar_mensaje
)

class PantallaClientes(QWidget):
    # Clase que representa la pantalla de Gestión de Clientes.
    # Hereda de QWidget para funcionar como un contenedor visual independiente.
    def __init__(self, ventana_principal):
        super().__init__()
        self.ventana_principal = ventana_principal  # Guardamos referencia para cuadros de diálogo
        self.init_ui()

    def init_ui(self):
        # PANTALLA 1: Clientes
        lay_clientes = QVBoxLayout(self)  # Asignamos el layout vertical al widget actual (self)
        lay_clientes.setContentsMargins(24, 24, 24, 24)  # aire alrededor del contenido, igual que en el dashboard
        lay_clientes.setSpacing(12)  # separación prolija entre título, tabla y buscador

        lbl_clientes = QLabel("Gestión de Clientes")
        lbl_clientes.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXTO_PRINCIPAL}; border: none;")
        
        # Creamos la tabla
        self.tabla_clientes_ui = QTableWidget()
        
        # Le ponemos 5 columnas (ID, Nombre, Teléfono, Email y la nueva de Acciones)
        self.tabla_clientes_ui.setColumnCount(5)
        self.tabla_clientes_ui.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Email", "Acciones"])
        
        # Hacer que las columnas se estiren para ocupar todo el ancho disponible
        self.tabla_clientes_ui.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Estilo general de la tabla, integrado a la paleta.
        # - El encabezado toma el navy del sidebar con texto blanco, para reforzar la identidad visual de la marca en toda la pantalla.
        # - Las filas alternan entre blanco y un gris apenas perceptible, lo que ayuda a leer filas largas sin perder la línea (efecto "cebra", muy común en tablas de datos modernas).
        # - Quitamos el borde grueso por defecto de QTableWidget y lo reemplazamos por uno sutil y redondeado.
        self.tabla_clientes_ui.setAlternatingRowColors(True)
        self.tabla_clientes_ui.setStyleSheet(f"""
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

        lay_clientes.addWidget(lbl_clientes)
        lay_clientes.addWidget(self.tabla_clientes_ui)  # Agregamos la tabla al layout

        # --- NUEVO: Zona de Búsqueda al Fondo ---
        lay_busqueda = QHBoxLayout()
        
        self.txt_buscar_cliente = SearchLineEdit()
        self.txt_buscar_cliente.setPlaceholderText("Ingresá nombre, teléfono o email para filtrar...")
        self.txt_buscar_cliente.setClearButtonEnabled(True)  # Agrega la "X" para limpiar la búsqueda con un clic
        self.txt_buscar_cliente.setMinimumWidth(400)         # Le damos un ancho mínimo cómodo
        lay_busqueda.addWidget(self.txt_buscar_cliente)
        
        # Agregamos el diseño de búsqueda abajo de la tabla
        lay_clientes.addLayout(lay_busqueda)

        # Conectamos el filtro de búsqueda en tiempo real
        self.txt_buscar_cliente.textChanged.connect(self.filtrar_clientes_en_tabla)

    def cargar_clientes(self):
        # Limpiamos las filas anteriores para no duplicar datos al reingresar
        self.tabla_clientes_ui.setRowCount(0) 
        
        try:
            # Le pedimos los datos al backend (Sigue viniendo de utilidades de forma limpia)
            registros = utilidades.obtener_clientes_activos()

            if not registros:
                # Si no hay clientes, creamos una fila temporal para mostrar el mensaje de advertencia
                self.tabla_clientes_ui.setRowCount(1)
                item_vacio = QTableWidgetItem("⚠️ No hay clientes activos registrados.")
                # Unimos las 4 celdas visualmente para el mensaje (opcional)
                self.tabla_clientes_ui.setItem(0, 0, item_vacio)
            else:
                # Iteramos sobre los registros e insertamos fila por fila
                for fila_index, reg in enumerate(registros):
                    self.tabla_clientes_ui.insertRow(fila_index)
                    
                    # Guardamos el ID del cliente de forma segura en una variable local por cada ciclo
                    id_cliente = reg['id']
                    cliente_data = reg # Copia de los datos actuales por si la necesitamos
                    
                    # Llenamos las columnas normales
                    self.tabla_clientes_ui.setItem(fila_index, 0, QTableWidgetItem(str(id_cliente)))
                    self.tabla_clientes_ui.setItem(fila_index, 1, QTableWidgetItem(reg['nombre']))
                    self.tabla_clientes_ui.setItem(fila_index, 2, QTableWidgetItem(reg['telefono']))
                    self.tabla_clientes_ui.setItem(fila_index, 3, QTableWidgetItem(reg['email']))
                    
                    # --- NUEVO: Crear contenedor de acciones para la Columna 4 ---
                    widget_acciones = QWidget()
                    lay_acciones = QHBoxLayout(widget_acciones)
                    lay_acciones.setContentsMargins(2, 2, 2, 2) # Margen pequeño para que entre bien
                    lay_acciones.setSpacing(5)
                    
                    btn_editar = QPushButton("✏️")
                    btn_editar.setToolTip("Editar Cliente")
                    # Le damos un hover violeta sutil, para que el botón se sienta "clickeable" y a la vez integrado a la paleta.
                    btn_editar.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(108, 99, 255, 40);
                        }
                    """)
                    
                    btn_eliminar = QPushButton("❌")
                    btn_eliminar.setToolTip("Eliminar Cliente")
                    # Mismo criterio que btn_editar, pero con un hover rojizo sutil para reforzar que es una acción destructiva.
                    btn_eliminar.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(239, 68, 68, 40);
                        }
                    """)
                    
                    # Conectamos temporalmente con lambdas pasando el diccionario del cliente y el ID
                    # Usamos 'id_c=id_cliente' para congelar el valor en el scope actual del bucle
                    btn_editar.clicked.connect(lambda checked=False, c=cliente_data: self.abrir_formulario_edicion(c))
                    btn_eliminar.clicked.connect(lambda checked=False, id_c=id_cliente, n=reg['nombre']: self.confirmar_baja_logica(id_c, n))
                    
                    lay_acciones.addWidget(btn_editar)
                    lay_acciones.addWidget(btn_eliminar)
                    
                    # Insertamos el contenedor directamente en la celda de la columna 4 (la quinta columna)
                    self.tabla_clientes_ui.setCellWidget(fila_index, 4, widget_acciones)
                    
        except Exception as e:
            # En caso de error, mostramos el mensaje directamente en la primera celda
            self.tabla_clientes_ui.setRowCount(1)
            self.tabla_clientes_ui.setItem(0, 0, QTableWidgetItem(f"❌ Error al cargar clientes: {e}"))

    def filtrar_clientes_en_tabla(self):
        # Capturamos el texto en minúsculas para que no importen las mayúsculas
        termino = self.txt_buscar_cliente.text().lower().strip()
        
        # Recorremos fila por fila de la tabla
        for fila in range(self.tabla_clientes_ui.rowCount()):
            # Traemos los textos de las celdas de Nombre(1), Teléfono(2) y Email(3)
            item_nombre = self.tabla_clientes_ui.item(fila, 1)
            item_tel = self.tabla_clientes_ui.item(fila, 2)
            item_email = self.tabla_clientes_ui.item(fila, 3)
            
            # Si la fila tiene datos válidos
            if item_nombre and item_tel and item_email:
                nombre = item_nombre.text().lower()
                telefono = item_tel.text().lower()
                email = item_email.text().lower()
                
                # Si el término está en alguno de estos campos, mostramos la fila, sino la ocultamos
                if termino in nombre or termino in telefono or termino in email:
                    self.tabla_clientes_ui.setRowHidden(fila, False)
                else:
                    self.tabla_clientes_ui.setRowHidden(fila, True)

    def confirmar_baja_logica(self, id_cliente, nombre_cliente):
        # 1. Cuadro de diálogo para confirmar la acción (Seguridad de UI)
        respuesta = mostrar_mensaje(
            self.ventana_principal, QMessageBox.Question, "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar al cliente '{nombre_cliente}'?\nSe cancelarán sus órdenes y equipos asociados.",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            exito = clientes.eliminar_cliente_logico(id_cliente)

            if exito:
                mostrar_mensaje(self.ventana_principal, QMessageBox.Information, "Éxito", f"El cliente '{nombre_cliente}' fue eliminado correctamente.")
                self.cargar_clientes()
            else:
                mostrar_mensaje(self.ventana_principal, QMessageBox.Critical, "Error", "❌ No se pudo eliminar al cliente en la base de datos.")

    # Estilo compartido para los campos de texto (QLineEdit) de los formularios de alta y edición
    # Lo armamos como un pequeño método reusable para no repetirlo 3 veces por formulario.
    def _estilo_campo_texto(self):
        return """
            QLineEdit {
                border: 1px solid #D8DAE5;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #6C63FF;
            }
        """

    def abrir_formulario_edicion(self, cliente_data):
        # Creamos la ventana de diálogo independiente
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle(f"Editar Cliente: {cliente_data['nombre']}")
        dialogo.resize(300, 200)
        # fondo del diálogo consistente con el resto de la app
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo, igual que hicimos con la ventana principal en app.py.
        personalizar_barra_titulo(dialogo)
        lay_dialogo = QVBoxLayout(dialogo)

        # Campos de texto con sus etiquetas precargados
        lay_dialogo.addWidget(QLabel("Nombre:"))
        txt_nombre = QLineEdit()
        txt_nombre.setText(cliente_data['nombre']) # Precarga
        txt_nombre.setStyleSheet(self._estilo_campo_texto())  # NUEVO
        lay_dialogo.addWidget(txt_nombre)

        lay_dialogo.addWidget(QLabel("Teléfono:"))
        txt_telefono = QLineEdit()
        txt_telefono.setText(cliente_data['telefono']) # Precarga
        # Restringir a que SOLO permita números (y opcionalmente el signo + si manejás prefijos)
        # Esta expresión regular permite únicamente dígitos del 0 al 9
        reg_ex = QRegularExpression("^[0-9]*$") 
        validador_numerico = QRegularExpressionValidator(reg_ex, txt_telefono)
        txt_telefono.setValidator(validador_numerico)
        txt_telefono.setStyleSheet(self._estilo_campo_texto())
        lay_dialogo.addWidget(txt_telefono)

        lay_dialogo.addWidget(QLabel("Email:"))
        txt_email = QLineEdit()
        txt_email.setText(cliente_data['email']) # Precarga
        txt_email.setStyleSheet(self._estilo_campo_texto())
        lay_dialogo.addWidget(txt_email)

        # Botón para guardar cambios
        btn_guardar = QPushButton("Guardar Cambios")
        # le damos el violeta de acento, igual que el botón "Nuevo" del sidebar
        btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #5A52E0;
            }}
        """)
        lay_dialogo.addWidget(btn_guardar)

        def procesar_edicion():
            nombre = txt_nombre.text().strip()
            telefono = txt_telefono.text().strip()
            email = txt_email.text().strip()

            # Mismo patrón que en el alta: le pasamos los datos crudos al backend
            # (junto con el ID del cliente que estamos editando) y esperamos su veredicto.
            exito, tipo_error, titulo_error, mensaje_error = clientes.editar_cliente_validado(
                cliente_data['id'], nombre, telefono, email
            )

            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            # Si exito es True, actualizamos la vista
            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "Los datos del cliente se actualizaron correctamente.")
            dialogo.accept()  # Cierra la ventana
            self.cargar_clientes()  # Refresca la tabla automáticamente sin reiniciar la app

        # Conectamos el botón a su lógica interna
        btn_guardar.clicked.connect(procesar_edicion)
        
        # Mostramos de forma modal
        dialogo.exec()

    def abrir_formulario_cliente(self):
        #Creamos la ventana flotante independiente
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle("Alta de Nuevo Cliente")
        dialogo.resize(300, 200)
        # --- NUEVO: fondo del diálogo consistente con el resto de la app
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo, igual que hicimos con la ventana principal en app.py.
        personalizar_barra_titulo(dialogo)
        lay_dialogo = QVBoxLayout(dialogo)

        #Creamos los campos de texto con sus etiquetas
        lay_dialogo.addWidget(QLabel("Nombre:"))
        txt_nombre = QLineEdit()
        txt_nombre.setStyleSheet(self._estilo_campo_texto())  # NUEVO
        lay_dialogo.addWidget(txt_nombre)

        lay_dialogo.addWidget(QLabel("Teléfono:"))
        # Buscá donde creás el campo de teléfono:
        txt_telefono = QLineEdit()
        
        # Restringir a que SOLO permita números (y opcionalmente el signo + si manejás prefijos) ---
        # Esta expresión regular permite únicamente dígitos del 0 al 9
        reg_ex = QRegularExpression("^[0-9]*$") 
        validador_numerico = QRegularExpressionValidator(reg_ex, txt_telefono)
        txt_telefono.setValidator(validador_numerico)
        txt_telefono.setStyleSheet(self._estilo_campo_texto())  # NUEVO
        lay_dialogo.addWidget(txt_telefono)

        lay_dialogo.addWidget(QLabel("Email:"))
        txt_email = QLineEdit()
        txt_email.setStyleSheet(self._estilo_campo_texto())  # NUEVO
        lay_dialogo.addWidget(txt_email)

        #Botón para guardar
        btn_guardar = PushButton("Guardar Cliente")
        btn_guardar.setStyleSheet(f"""
            PushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                border-radius: 6px;
            }}
            PushButton:hover {{
                background-color: #5A52E0;
            }}
        """)
        lay_dialogo.addWidget(btn_guardar)

        def procesar_alta():
            #1. Capturamos los datos limpiando espacios
            nombre = txt_nombre.text().strip()
            telefono = txt_telefono.text().strip()
            email = txt_email.text().strip()

            # VALIDACIÓN Y PERSISTENCIA: le delegamos todo el trabajo al backend.
            # La GUI ysolo le pasa los datos crudos a clientes.py y espera la respuesta.

            # clientes.alta_cliente_validado() nos devuelve una TUPLA de 4 valores.
            #   exito         -> True o False
            #   tipo_error    -> "warning" o "critical" (para saber qué ícono/mensaje usar)
            #   titulo_error  -> texto del título del QMessageBox
            #   mensaje_error -> texto del cuerpo del QMessageBox
            # Si exito es True, los otros tres valores van a venir en None, porque no hay error que mostrar.
            exito, tipo_error, titulo_error, mensaje_error = clientes.alta_cliente_validado(
                nombre, telefono, email
            )

            # Si el backend nos dice que hubo un error, lo mostramos y frenamos acá.
            # Usamos tipo_error para elegir entre .warning (validación) y .critical (fallo de guardado)
            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            # 4. Si llegamos hasta acá, significa que exito fue True: el cliente se guardó bien.
            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "El cliente se guardó correctamente.")
            dialogo.accept()  # Cierra la ventana del formulario
            self.cargar_clientes()  # Refresca la tabla automáticamente sin reiniciar la app

        #Conectamos el botón de la ventana flotante a su lógica
        btn_guardar.clicked.connect(procesar_alta)
        
        #Mostramos la ventana de forma modal (bloquea la de atrás hasta que se cierre)
        dialogo.exec()