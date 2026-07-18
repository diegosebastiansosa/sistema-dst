# =============================================================================
# vistas/gui_equipos.py
# =============================================================================
# Este archivo define la pantalla visual de Gestión de Equipos.
# Vive dentro del paquete 'vistas/', por eso sus imports al backend usan
# el nombre de módulo simple (raíz del proyecto disponible en sys.path).
#
# ESTRUCTURA DEL MÓDULO:
#   - PantallaEquipos (QWidget): todo el contenido visual de la pantalla
#       ├── init_ui()                          → construye la tabla y la barra de búsqueda
#       ├── cargar_equipos()                   → lee la BD y llena la tabla
#       ├── filtrar_equipos_en_tabla()         → filtra filas en tiempo real
#       ├── abrir_formulario_equipo()          → ventana flotante para dar de alta un equipo
#       ├── confirmar_baja_equipo()            → elimina un equipo (baja lógica)
#       └── abrir_formulario_edicion_equipo()  → ventana flotante para editar un equipo
# =============================================================================

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                                QTableWidgetItem, QHeaderView, QHBoxLayout, 
                                QLineEdit, QPushButton, QDialog, QMessageBox,
                                QComboBox, QCheckBox)
from PySide6.QtCore import Qt

from qfluentwidgets import PushButton, PrimaryPushButton, SearchLineEdit, ComboBox, FluentIcon as FIF, setTheme, Theme

# Importamos los módulos de backend usando su nombre simple.
import utilidades
import equipos  # Backend de equipos: operaciones CRUD sobre la tabla 'equipos' en dst.db
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, ESTILO_FORMULARIO,
    personalizar_barra_titulo, mostrar_mensaje
)

class PantallaEquipos(QWidget):
    """
    Clase que representa la pantalla de Gestión de Equipos.
    Hereda de QWidget para funcionar como un contenedor visual independiente.
    """
    def __init__(self, ventana_principal):
        super().__init__()
        self.ventana_principal = ventana_principal  # Guardamos referencia para cuadros de diálogo
        self.init_ui()

    def init_ui(self):
        # PANTALLA 2: Equipos
        lay_equipos = QVBoxLayout(self)  # Asignamos el layout vertical al widget actual (self)
        lay_equipos.setContentsMargins(24, 24, 24, 24)  # aire alrededor del contenido, igual que en el dashboard
        lay_equipos.setSpacing(12)  # separación prolija entre título, tabla y buscador

        lbl_equipos = QLabel("Gestión de Equipos")
        lbl_equipos.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXTO_PRINCIPAL}; border: none;")
        lay_equipos.addWidget(lbl_equipos)
        
        # Creamos la tabla de equipos con sus columnas
        self.tabla_equipos_ui = QTableWidget()
        self.tabla_equipos_ui.setColumnCount(12) 
        self.tabla_equipos_ui.setHorizontalHeaderLabels([
            "ID", "Tipo", "Marca/Modelo", "Procesador", "RAM", 
            "GPU Tipo", "Marca GPU", "Modelo GPU", "VRAM", "Almacenamiento (SSD/HDD)", "Dueño", "Acciones"
        ])
        self.tabla_equipos_ui.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # alineamos los títulos de columna a la izquierda. Por defecto,
        # QHeaderView centra el texto del encabezado, lo que hace que en columnas angostas el título se corte por el medio (ej: "Procesador" -> "rocesado").
        # Alineado a la izquierda, al menos siempre se lee el inicio de la palabra, aunque el resto quede tapado.
        self.tabla_equipos_ui.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # Color del texto
        self.tabla_equipos_ui.setAlternatingRowColors(True)
        self.tabla_equipos_ui.setStyleSheet(f"""
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

        lay_equipos.addWidget(self.tabla_equipos_ui)

        # Zona de Búsqueda al Fondo para Equipos
        lay_busqueda_eq = QHBoxLayout()
        
        self.txt_buscar_equipo = SearchLineEdit()
        self.txt_buscar_equipo.setPlaceholderText("Ingresá tipo, marca, modelo, procesador, RAM, GPU o dueño...")
        self.txt_buscar_equipo.setClearButtonEnabled(True)  # Agrega la "X" para limpiar la búsqueda con un clic
        self.txt_buscar_equipo.setMinimumWidth(400)         # Le damos un ancho mínimo cómodo

        lay_busqueda_eq.addWidget(self.txt_buscar_equipo)
        
        # Lo agregamos al fondo del layout vertical
        lay_equipos.addLayout(lay_busqueda_eq)

        # Conectamos el buscador de equipos
        self.txt_buscar_equipo.textChanged.connect(self.filtrar_equipos_en_tabla)

    def cargar_equipos(self):
        self.tabla_equipos_ui.setRowCount(0) # Limpiamos filas anteriores
        try:
            registros = utilidades.obtener_equipos_activos()

            if not registros:
                self.tabla_equipos_ui.setRowCount(1)
                self.tabla_equipos_ui.setItem(0, 0, QTableWidgetItem("⚠️ No hay equipos activos registrados."))
            else:
                for fila_index, reg in enumerate(registros):
                    self.tabla_equipos_ui.insertRow(fila_index)
                    
                    id_equipo = reg['id']
                    equipo_data = reg
                    
                    # Formateamos datos
                    marca_modelo = f"{reg['marca']} {reg['modelo']}"
                    gpu_tipo = "Dedicada" if reg['gpu_dedicada'] == 1 else "Integrada"
                    almacenamiento = f"SSD: {reg['almacenamiento_ssd']} | HDD: {reg['almacenamiento_hdd']}"
                    
                    # Llenamos celdas estándar
                    self.tabla_equipos_ui.setItem(fila_index, 0, QTableWidgetItem(str(id_equipo)))
                    self.tabla_equipos_ui.setItem(fila_index, 1, QTableWidgetItem(reg['tipo']))
                    self.tabla_equipos_ui.setItem(fila_index, 2, QTableWidgetItem(marca_modelo))
                    self.tabla_equipos_ui.setItem(fila_index, 3, QTableWidgetItem(reg['procesador']))
                    self.tabla_equipos_ui.setItem(fila_index, 4, QTableWidgetItem(reg['ram']))
                    self.tabla_equipos_ui.setItem(fila_index, 5, QTableWidgetItem(gpu_tipo))
                    self.tabla_equipos_ui.setItem(fila_index, 6, QTableWidgetItem(reg['marca_gpu']))
                    self.tabla_equipos_ui.setItem(fila_index, 7, QTableWidgetItem(reg['modelo_gpu']))
                    self.tabla_equipos_ui.setItem(fila_index, 8, QTableWidgetItem(reg['vram']))
                    self.tabla_equipos_ui.setItem(fila_index, 9, QTableWidgetItem(almacenamiento))
                    self.tabla_equipos_ui.setItem(fila_index, 10, QTableWidgetItem(reg['cliente_nombre']))
                    
                    # Botones de Acción
                    widget_acciones = QWidget()
                    lay_acciones = QHBoxLayout(widget_acciones)
                    lay_acciones.setContentsMargins(2, 2, 2, 2)
                    lay_acciones.setSpacing(5)
                    
                    btn_editar_eq = QPushButton("✏️")
                    btn_editar_eq.setToolTip("Editar Equipo")
                    btn_editar_eq.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(108, 99, 255, 40);
                        }
                    """)
                    
                    btn_eliminar_eq = QPushButton("❌")
                    btn_eliminar_eq.setToolTip("Eliminar Equipo")
                    btn_eliminar_eq.setStyleSheet("""
                        QPushButton {
                            border: none;
                            border-radius: 6px;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: rgba(239, 68, 68, 40);
                        }
                    """)
                    
                    # Conexiones con congelamiento de Scope por ciclo
                    btn_editar_eq.clicked.connect(lambda checked=False, e=equipo_data: self.abrir_formulario_edicion_equipo(e))
                    btn_eliminar_eq.clicked.connect(lambda checked=False, id_e=id_equipo, m=marca_modelo: self.confirmar_baja_equipo(id_e, m))
                    
                    lay_acciones.addWidget(btn_editar_eq)
                    lay_acciones.addWidget(btn_eliminar_eq)
                    
                    # Colocamos el contenedor en la columna 11
                    self.tabla_equipos_ui.setCellWidget(fila_index, 11, widget_acciones)
                    
        except Exception as e:
            self.tabla_equipos_ui.setRowCount(1)
            self.tabla_equipos_ui.setItem(0, 0, QTableWidgetItem(f"❌ Error al cargar equipos: {e}"))

    def filtrar_equipos_en_tabla(self):
        termino = self.txt_buscar_equipo.text().lower().strip()
        
        for fila in range(self.tabla_equipos_ui.rowCount()):
            item_tipo = self.tabla_equipos_ui.item(fila, 1)
            item_marca_modelo = self.tabla_equipos_ui.item(fila, 2)
            item_micro = self.tabla_equipos_ui.item(fila, 3)
            item_ram = self.tabla_equipos_ui.item(fila, 4)
            item_gpu_tipo = self.tabla_equipos_ui.item(fila, 5)
            item_marca_gpu = self.tabla_equipos_ui.item(fila, 6)
            item_modelo_gpu = self.tabla_equipos_ui.item(fila, 7)
            item_vram = self.tabla_equipos_ui.item(fila, 8)
            item_dueno = self.tabla_equipos_ui.item(fila, 10)
            
            if item_tipo and item_marca_modelo and item_micro and item_dueno:
                tipo = item_tipo.text().lower()
                marca_modelo = item_marca_modelo.text().lower()
                micro = item_micro.text().lower()
                ram = item_ram.text().lower() if item_ram else ""
                gpu_tipo = item_gpu_tipo.text().lower() if item_gpu_tipo else ""
                marca_gpu = item_marca_gpu.text().lower() if item_marca_gpu else ""
                modelo_gpu = item_modelo_gpu.text().lower() if item_modelo_gpu else ""
                vram = item_vram.text().lower() if item_vram else ""
                dueno = item_dueno.text().lower()
                
                coincide = (
                    termino in tipo or 
                    termino in marca_modelo or 
                    termino in micro or 
                    termino in ram or 
                    termino in gpu_tipo or 
                    termino in marca_gpu or 
                    termino in modelo_gpu or 
                    termino in vram or 
                    termino in dueno
                )
                
                if coincide:
                    self.tabla_equipos_ui.setRowHidden(fila, False)
                else:
                    self.tabla_equipos_ui.setRowHidden(fila, True)

    def abrir_formulario_equipo(self):
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle("Alta de Nuevo Equipo")
        dialogo.resize(400, 550)
        # Aplicamos el estilo centralizado importado
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo, igual que hicimos con la ventana principal en app.py.
        personalizar_barra_titulo(dialogo)
        lay_dialogo = QVBoxLayout(dialogo)

        # --- SELECCIÓN DE DUEÑO (Combo Box dinámico) ---
        lay_dialogo.addWidget(QLabel("<b>Seleccione el Cliente (Dueño):</b>"))
        combo_clientes = QComboBox()
        lay_dialogo.addWidget(combo_clientes)
        
        # Llenamos el combo desde la BD usando el backend
        lista_clientes = utilidades.obtener_lista_clientes_combo() 
        
        for c in lista_clientes:
            # addItem(texto_visible, dato_interno) -> Guardamos el ID de forma oculta
            combo_clientes.addItem(f"{c['nombre']} (ID: {c['id']})", c['id'])

        if not lista_clientes:
            mostrar_mensaje(dialogo, QMessageBox.Warning, "Advertencia", "⚠️ No hay clientes activos para asignarle un equipo. Genere un cliente primero.")
            return

        # --- CAMPOS TÉCNICOS ---
        lay_dialogo.addWidget(QLabel("Tipo de Equipo (Notebook/Escritorio/AllInOne):"))
        txt_tipo = QLineEdit()
        lay_dialogo.addWidget(txt_tipo)

        lay_dialogo.addWidget(QLabel("Marca:"))
        txt_marca = QLineEdit()
        lay_dialogo.addWidget(txt_marca)

        lay_dialogo.addWidget(QLabel("Modelo:"))
        txt_modelo = QLineEdit()
        lay_dialogo.addWidget(txt_modelo)

        lay_dialogo.addWidget(QLabel("Procesador:"))
        txt_procesador = QLineEdit()
        lay_dialogo.addWidget(txt_procesador)

        lay_dialogo.addWidget(QLabel("Memoria RAM (ej: 16GB DDR4):"))
        txt_ram = QLineEdit()
        lay_dialogo.addWidget(txt_ram)

        # Gráficos
        chk_gpu_dedicada = QCheckBox("¿Posee Tarjeta de Video Dedicada?")
        lay_dialogo.addWidget(chk_gpu_dedicada)

        lay_dialogo.addWidget(QLabel("Marca de GPU / Modelo / VRAM:"))
        txt_marca_gpu = QLineEdit()
        txt_modelo_gpu = QLineEdit()
        txt_vram = QLineEdit()
        txt_marca_gpu.setPlaceholderText("Ej: NVIDIA")
        txt_modelo_gpu.setPlaceholderText("Ej: RTX 4060")
        txt_vram.setPlaceholderText("Ej: 8GB")
        
        lay_dialogo.addWidget(txt_marca_gpu)
        lay_dialogo.addWidget(txt_modelo_gpu)
        lay_dialogo.addWidget(txt_vram)

        # --- Deshabilitados por defecto ---
        txt_marca_gpu.setEnabled(False)
        txt_modelo_gpu.setEnabled(False)
        txt_vram.setEnabled(False)

        # --- Lógica de activación dinámica ---
        def alternar_campos_gpu(encendido):
            txt_marca_gpu.setEnabled(encendido)
            txt_modelo_gpu.setEnabled(encendido)
            txt_vram.setEnabled(encendido)
            
            # Si se desmarca, limpiamos lo que el usuario haya escrito para no mandar basura
            if not encendido:
                txt_marca_gpu.clear()
                txt_modelo_gpu.clear()
                txt_vram.clear()

        # Conectamos el evento del checkbox a la función
        chk_gpu_dedicada.toggled.connect(alternar_campos_gpu)

        # Almacenamiento
        lay_dialogo.addWidget(QLabel("Almacenamiento SSD (ej: 480GB u 'No'):"))
        txt_ssd = QLineEdit()
        lay_dialogo.addWidget(txt_ssd)

        lay_dialogo.addWidget(QLabel("Almacenamiento HDD (ej: 1TB u 'No'):"))
        txt_hdd = QLineEdit()
        lay_dialogo.addWidget(txt_hdd)

        # Botón Guardar
        btn_guardar = PushButton("Guardar Equipo")
        btn_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white;")
        lay_dialogo.addWidget(btn_guardar)

        def procesar_alta_equipo():
            # 1. Capturamos los datos de los campos del formulario
            id_cliente = combo_clientes.currentData() # Recupera el ID oculto del cliente seleccionado
            tipo = txt_tipo.text().strip()
            marca = txt_marca.text().strip()
            modelo = txt_modelo.text().strip()
            procesador = txt_procesador.text().strip()
            ram = txt_ram.text().strip()
            gpu_dedicada = 1 if chk_gpu_dedicada.isChecked() else 0
            marca_gpu = txt_marca_gpu.text().strip()
            modelo_gpu = txt_modelo_gpu.text().strip()
            vram = txt_vram.text().strip()
            ssd = txt_ssd.text().strip()
            hdd = txt_hdd.text().strip()

            # 2. VALIDACIÓN Y PERSISTENCIA: le delegamos todo a equipos.py. Desempaquetamos la tupla de 4 valores.
            exito, tipo_error, titulo_error, mensaje_error = equipos.alta_equipo_validado(
                tipo, marca, modelo, procesador, ram, gpu_dedicada,
                marca_gpu, modelo_gpu, vram, ssd, hdd, id_cliente
            )

            # 3. Si hubo error, lo mostramos y frenamos acá
            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            # 4. Si llegamos hasta acá, se guardó correctamente
            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "¡Equipo registrado correctamente!")
            dialogo.accept()
            self.cargar_equipos()  # Refresca automáticamente tu tabla de equipos

        btn_guardar.clicked.connect(procesar_alta_equipo)
        dialogo.exec()

    def confirmar_baja_equipo(self, id_equipo, marca_modelo):
        respuesta = mostrar_mensaje(
            self.ventana_principal, QMessageBox.Question, "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el equipo '{marca_modelo}'?\nSe cancelarán las órdenes de reparación asociadas a este equipo.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            exito = equipos.eliminar_equipo_logico(id_equipo)
            if exito:
                mostrar_mensaje(self.ventana_principal, QMessageBox.Information, "Éxito", "El equipo fue eliminado correctamente.")
                self.cargar_equipos() # Refresco automático
            else:
                mostrar_mensaje(self.ventana_principal, QMessageBox.Critical, "Error", "❌ No se pudo eliminar el equipo.")

    def abrir_formulario_edicion_equipo(self, equipo_data):
        dialogo = QDialog(self.ventana_principal)
        dialogo.setWindowTitle(f"Editar Equipo ID: {equipo_data['id']}")
        dialogo.resize(400, 550)
        dialogo.setStyleSheet(ESTILO_FORMULARIO)
        # coloreamos la barra de título nativa de este diálogo, igual que hicimos con la ventana principal en app.py.
        personalizar_barra_titulo(dialogo)
        lay_dialogo = QVBoxLayout(dialogo)

        # Campos técnicos precargados con los datos actuales
        lay_dialogo.addWidget(QLabel("Tipo de Equipo:"))
        txt_tipo = QLineEdit()
        txt_tipo.setText(equipo_data['tipo'])
        lay_dialogo.addWidget(txt_tipo)

        lay_dialogo.addWidget(QLabel("Marca:"))
        txt_marca = QLineEdit()
        txt_marca.setText(equipo_data['marca'])
        lay_dialogo.addWidget(txt_marca)

        lay_dialogo.addWidget(QLabel("Modelo:"))
        txt_modelo = QLineEdit()
        txt_modelo.setText(equipo_data['modelo'])
        lay_dialogo.addWidget(txt_modelo)

        lay_dialogo.addWidget(QLabel("Procesador:"))
        txt_procesador = QLineEdit()
        txt_procesador.setText(equipo_data['procesador'])
        lay_dialogo.addWidget(txt_procesador)

        lay_dialogo.addWidget(QLabel("Memoria RAM:"))
        txt_ram = QLineEdit()
        txt_ram.setText(equipo_data['ram'])
        lay_dialogo.addWidget(txt_ram)

        # Gráficos (Controlamos el estado inicial de la GPU)
        chk_gpu_dedicada = QCheckBox("¿Posee Tarjeta de Video Dedicada?")
        chk_gpu_dedicada.setChecked(equipo_data['gpu_dedicada'] == 1)
        lay_dialogo.addWidget(chk_gpu_dedicada)

        lay_dialogo.addWidget(QLabel("Marca de GPU / Modelo / VRAM:"))
        txt_marca_gpu = QLineEdit()
        txt_modelo_gpu = QLineEdit()
        txt_vram = QLineEdit()
        
        txt_marca_gpu.setText(equipo_data['marca_gpu'])
        txt_modelo_gpu.setText(equipo_data['modelo_gpu'])
        txt_vram.setText(equipo_data['vram'])
        
        lay_dialogo.addWidget(txt_marca_gpu)
        lay_dialogo.addWidget(txt_modelo_gpu)
        lay_dialogo.addWidget(txt_vram)

        # Activación/Desactivación dinámica según el estado del checkbox
        def alternar_campos_gpu(encendido):
            txt_marca_gpu.setEnabled(encendido)
            txt_modelo_gpu.setEnabled(encendido)
            txt_vram.setEnabled(encendido)
            if not encendido:
                txt_marca_gpu.clear()
                txt_modelo_gpu.clear()
                txt_vram.clear()

        chk_gpu_dedicada.toggled.connect(alternar_campos_gpu)
        # Disparamos la función una vez al inicio para que herede el estado correcto de la DB
        alternar_campos_gpu(chk_gpu_dedicada.isChecked())

        # Almacenamiento
        lay_dialogo.addWidget(QLabel("Almacenamiento SSD:"))
        txt_ssd = QLineEdit()
        txt_ssd.setText(equipo_data['almacenamiento_ssd'])
        lay_dialogo.addWidget(txt_ssd)

        lay_dialogo.addWidget(QLabel("Almacenamiento HDD:"))
        txt_hdd = QLineEdit()
        txt_hdd.setText(equipo_data['almacenamiento_hdd'])
        lay_dialogo.addWidget(txt_hdd)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setStyleSheet(f"background-color: {COLOR_ACENTO}; color: white; padding: 6px;")
        lay_dialogo.addWidget(btn_guardar)

        def procesar_edicion_equipo():
            tipo = txt_tipo.text().strip()
            marca = txt_marca.text().strip()
            modelo = txt_modelo.text().strip()
            procesador = txt_procesador.text().strip()
            ram = txt_ram.text().strip()
            gpu_dedicada = 1 if chk_gpu_dedicada.isChecked() else 0
            marca_gpu = txt_marca_gpu.text().strip()
            modelo_gpu = txt_modelo_gpu.text().strip()
            vram = txt_vram.text().strip()
            ssd = txt_ssd.text().strip()
            hdd = txt_hdd.text().strip()

            exito, tipo_error, titulo_error, mensaje_error = equipos.editar_equipo_validado(
                equipo_data['id'], tipo, marca, modelo, procesador, ram,
                gpu_dedicada, marca_gpu, modelo_gpu, vram, ssd, hdd
            )

            if not exito:
                if tipo_error == "critical":
                    mostrar_mensaje(dialogo, QMessageBox.Critical, titulo_error, mensaje_error)
                else:
                    mostrar_mensaje(dialogo, QMessageBox.Warning, titulo_error, mensaje_error)
                return

            mostrar_mensaje(dialogo, QMessageBox.Information, "Éxito", "Los especificaciones del equipo se actualizaron.")
            dialogo.accept()
            self.cargar_equipos()

        btn_guardar.clicked.connect(procesar_edicion_equipo)
        dialogo.exec()
