import sys
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                                QPushButton, QLabel, QHBoxLayout, QVBoxLayout, 
                                QStackedWidget, QMenu, QFrame, QButtonGroup, QSizePolicy)
from PySide6.QtCore import Qt, QPoint, QSize
import utilidades  # Para poder llamar a inicializar_db() antes de arrancar la interfaz
# Modificá la importación para agregar setTheme y Theme:
from qfluentwidgets import PushButton, PrimaryPushButton, FluentIcon as FIF, setTheme, Theme

# --- Importamos la paleta de colores centralizada ---
# los definimos una sola vez en vistas/estilos.py y los importamos acá.
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_SIDEBAR, COLOR_TEXTO_ACTIVO
)
from PySide6.QtGui import QColor  # Necesario para pedirle a FluentIcon una versión pintada de un color específico

# Para que Python encuentre Los archivos dentro de 'vistas/' (gui_clientes.py, etc.) que importan módulos de backend como 'import clientes' o 'import utilidades'
raiz_proyecto = os.path.dirname(os.path.abspath(__file__))
if raiz_proyecto not in sys.path:
    sys.path.insert(0, raiz_proyecto)

# Importamos las pantallas desde el paquete 'vistas/'

from vistas.gui_clientes import PantallaClientes
from vistas.gui_equipos import PantallaEquipos
from vistas.gui_ordenes import PantallaOrdenes
from vistas.dashboard import PantallaDashboard  # Nueva pantalla de bienvenida encapsulada
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_FONDO_CONTENIDO, COLOR_ACENTO,
    COLOR_TEXTO_SIDEBAR, COLOR_TEXTO_ACTIVO,
    personalizar_barra_titulo
)

import ctypes
myappid = 'mi_emprendimiento.sistema_dst.gestion.1.0' # Un identificador único cualquiera
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def crear_boton_navegacion(icono_fluent, texto):
    """
    Crea un QPushButton de navegación cuyo ícono cambia de color según su estado:
      - Inactivo: gris azulado claro (COLOR_TEXTO_SIDEBAR), igual que el texto inactivo.
      - Activo (checked): navy (COLOR_SIDEBAR), igual que el texto activo.

    ¿Por qué necesitamos esta función y no alcanza con el QSS?
    Porque un ícono de FluentIcon (FIF) no es texto: es una imagen ya "pintada"
    en el momento en que la generamos con .icon(). El QSS puede cambiar el
    color de un TEXTO dinámicamente según el estado (:checked), pero no puede
    "repintar" una imagen ya generada. Por eso generamos DOS versiones del
    mismo ícono acá (una clara, una navy) y las intercambiamos a mano cada vez
    que el botón cambia de estado.
    """
    boton = QPushButton(f" {texto}")

    icono_inactivo = icono_fluent.icon(color=QColor(COLOR_TEXTO_SIDEBAR))
    icono_activo = icono_fluent.icon(color=QColor(COLOR_SIDEBAR))

    boton.setIcon(icono_inactivo)  # Arranca en su estado inactivo
    boton.setIconSize(QSize(16, 16))

    # 'toggled' se dispara cada vez que el estado checked/unchecked del botón
    # cambia (tanto al activarse como al desactivarse). Conectamos una función
    # que decide cuál de los dos íconos mostrar según ese nuevo estado.
    def actualizar_icono(esta_activo):
        boton.setIcon(icono_activo if esta_activo else icono_inactivo)

    boton.toggled.connect(actualizar_icono)
    return boton

def iniciar_interfaz():
    app = QApplication(sys.argv)

    # -Fijamos Theme.LIGHT porque armamos una paleta de colores propia y fija (sidebar navy, contenido gris claro)
    setTheme(Theme.LIGHT)

    ventana_principal = QMainWindow()
    ventana_principal.setWindowTitle("Sistema DST - Gestión de Reparaciones")
    ventana_principal.resize(1000, 650)
    ruta_logo = os.path.join(os.path.dirname(__file__),"logo.png")
    ventana_principal.setWindowIcon(QIcon(ruta_logo))

    # Le damos color de fondo a la ventana completa
    ventana_principal.setStyleSheet(f"QMainWindow {{ background-color: {COLOR_FONDO_CONTENIDO}; }}")

    # 1. Creamos el Widget Central (el lienzo en blanco obligatorio de la ventana)
    widget_central = QWidget()
    ventana_principal.setCentralWidget(widget_central)

    layout_ventana = QHBoxLayout(widget_central)
    layout_ventana.setContentsMargins(0, 0, 0, 0)

    # =========================================================================
    # --- PANEL PRINCIPAL ---
    # =========================================================================
    panel_principal = QFrame()
    panel_principal.setObjectName("panelPrincipal")
    panel_principal.setStyleSheet(f"""
        #panelPrincipal {{
            background-color: {COLOR_FONDO_CONTENIDO};
        }}
    """)
    layout_ventana.addWidget(panel_principal)

    # 2. Layout Principal: HORIZONTAL (Izquierda: Menú | Derecha: Contenido)
    # Ahora este layout se asigna al panel_principal en vez de directo al
    # widget_central, porque el panel_principal es quien tiene el redondeo.
    layout_principal = QHBoxLayout(panel_principal)
    layout_principal.setContentsMargins(0, 0, 0, 0)  # Sin margen interno: sidebar y contenido se tocan entre sí
    layout_principal.setSpacing(0)  # Sin espacio entre ambos, para que se vean unidos visualmente


    # ========================================================
    # MENÚ LATERAL IZQUIERDO (Navegación)
    # ========================================================
    widget_menu = QWidget()
    widget_menu.setObjectName("MenuLateral") # Le damos un ID único
    # --- Aplicamos el color navy de la barra lateral, redondeando
    # SOLO las esquinas izquierdas (las que dan hacia afuera del panel).
    # Las esquinas derechas quedan rectas porque ahí se junta con el contenido.
    widget_menu.setMaximumWidth(160)
    widget_menu.setStyleSheet(f"""
        #MenuLateral {{
            background-color: {COLOR_SIDEBAR};
        }}
    """)
    layout_menu = QVBoxLayout()
    # Sin margen izquierdo/derecho: los botones de navegación ocupan el ancho
    # completo del sidebar, para que el botón activo pueda tocar el borde
    # derecho y fundirse con el contenido de al lado.
    layout_menu.setContentsMargins(20, 20, 0, 20)
    layout_menu.setSpacing(4)
    widget_menu.setLayout(layout_menu)

    # --- Botón "Nuevo" ---
    # --- Cambiamos PrimaryPushButton (qfluentwidgets) por QPushButton
    # (estándar de Qt), por el mismo motivo que con los botones de navegación:
    # PrimaryPushButton dibuja el ícono "+" con su propio motor interno, que no
    # respeta el padding que le mandamos por QSS, y termina superpuesto con el
    # texto. QPushButton usa el motor nativo de Qt, que sí calcula correctamente
    # el espacio entre ícono y texto según nuestro estilo.
    icono_nuevo = FIF.ADD.icon(color=QColor("#FFFFFF"))
    btn_nuevo = QPushButton(icono_nuevo, " Nuevo")
    btn_nuevo.setIconSize(QSize(16, 16))  # Mismo tamaño de ícono que usamos en los botones de navegación

    # --- Forzamos que el botón se estire para ocupar todo el
    # ancho disponible dentro de su contenedor (ver contenedor_nuevo más abajo).
    # Sin esto, el botón toma solo el ancho de su contenido ("Nuevo" + ícono)
    # y Qt lo alinea a la izquierda dentro del layout, dejando todo el margen
    # sobrante del lado derecho en vez de repartirlo simétricamente.
    btn_nuevo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    btn_nuevo.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_ACENTO};
            color: white;
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #5A52E0;
        }}
    """)

    menu_desplegable = QMenu()
    # Estilo consistente con la paleta del sistema. Por defecto,
    # QMenu toma el aspecto nativo de Windows (fondo oscuro en tu caso), que
    # no tenía relación con nuestros colores. Acá lo alineamos: fondo gris
    # claro (igual al del contenido) y texto navy (igual al resto de la app).
    menu_desplegable.setStyleSheet(f"""
        QMenu {{
            background-color: {COLOR_FONDO_CONTENIDO};
            color: {COLOR_SIDEBAR};
            border: 1px solid #D8DAE5;
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background-color: {COLOR_ACENTO};
            color: white;
        }}
    """)
    accion_cliente = menu_desplegable.addAction("Cliente")
    accion_equipo = menu_desplegable.addAction("Equipo")
    accion_orden = menu_desplegable.addAction("Orden de reparación")
    
    # 2. AGREGAMOS: Función para forzar el despliegue hacia arriba
    def mostrar_menu_arriba():
        # Obtenemos la posición del botón global en la pantalla
        posicion_boton = btn_nuevo.mapToGlobal(btn_nuevo.rect().topLeft())
        # Calculamos la altura que va a tener el menú para restársela a la posición 'Y'
        altura_menu = menu_desplegable.sizeHint().height()
        
        # Posicionamos el menú justo arriba del botón (restando la altura)
        punto_despliegue = posicion_boton - QPoint(0, altura_menu)
        
        # Ejecutamos el menú de forma flotante en esa posición exacta
        menu_desplegable.exec(punto_despliegue)

    # Conectamos el click del botón para que ejecute la magia
    btn_nuevo.clicked.connect(mostrar_menu_arriba)

    # =========================================================================
    # --- CORRECCIÓN DE ÍCONOS: Botones de navegación estándar de Qt ---
    #
    # Usamos QPushButton (el estándar de Qt, ya importado arriba)
    # y cargamos el ícono con .setIcon(). FluentIconBase (la clase de FIF)
    # tiene un método .icon() que devuelve un QIcon común. Con QPushButton
    # estándar, Qt calcula automáticamente el espacio entre ícono y texto
    # usando su motor nativo, que SÍ respeta el padding de nuestro QSS.
    # =========================================================================
    # En vez de crear estos botones "a mano" como antes, usamos
    # la función crear_boton_navegacion() para que cada uno tenga la lógica de
    # ícono claro/navy automáticamente resuelta.
    btn_dashboard = crear_boton_navegacion(FIF.TILES, "Dashboard")
    btn_clientes = crear_boton_navegacion(FIF.PEOPLE, "Clientes")
    btn_equipos = crear_boton_navegacion(FIF.DEVELOPER_TOOLS, "Equipos")
    btn_ordenes = crear_boton_navegacion(FIF.SETTING, "Órdenes")

    # =========================================================================
    # ESTILO Y COMPORTAMIENTO "PESTAÑA ACTIVA"
    # Le damos a estos 4 botones (incluyendo Dashboard) la capacidad de quedar
    # "marcados" como activos, y un estilo que hace que el botón activo tome
    # el MISMO color de fondo que el contenido de al lado (COLOR_FONDO_CONTENIDO).
    # Eso es lo que genera la ilusión de que la pestaña "se funde" con la pantalla.
    #
    # QSS (los estilos de Qt) acepta selectores de estado con dos puntos, como CSS:
    #   :checked   -> cuando el botón está en su estado "presionado/activo"
    #   :hover     -> cuando el mouse está encima
    #   :!checked  -> "NO está checked" (para no pisar el estilo del activo con el hover)
    # =========================================================================
    estilo_botones_nav = f"""
        QPushButton {{
            text-align: left;
            padding: 10px 16px;
            border: none;
            border-top-left-radius: 15px;
            border-bottom-left-radius: 15px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            color: {COLOR_TEXTO_SIDEBAR};
            font-size: 13px;
        }}
        QPushButton:checked {{
            background-color: {COLOR_FONDO_CONTENIDO};
            color: {COLOR_SIDEBAR};
            font-weight: bold;
        }}
        QPushButton:hover:!checked {{
            background-color: rgba(255, 255, 255, 25);
            color: white;
        }}
    """
    # Con QPushButton estándar, el padding ya no necesita un número gigante
    # como 40px: Qt reserva el espacio del ícono automáticamente y agrega el
    # texto después, así que un padding normal alcanza.
    for boton in (btn_clientes, btn_equipos, btn_ordenes, btn_dashboard):
        boton.setCheckable(True)  # Habilita el estado "presionado persistente"
        boton.setStyleSheet(estilo_botones_nav)

    # --- QButtonGroup agrupa varios botones checkeables para que se
    # comporten como un menú de radio: al marcar uno, los demás se desmarcan solos automáticamente
    grupo_navegacion = QButtonGroup(widget_menu)
    grupo_navegacion.setExclusive(True)
    grupo_navegacion.addButton(btn_dashboard)
    grupo_navegacion.addButton(btn_clientes)
    grupo_navegacion.addButton(btn_equipos)
    grupo_navegacion.addButton(btn_ordenes)

    # Los agregamos al organizador vertical del menú.
    layout_menu.addWidget(btn_dashboard)
    layout_menu.addWidget(btn_clientes)
    layout_menu.addWidget(btn_equipos)
    layout_menu.addWidget(btn_ordenes)
    
    # Este truco ("addStretch") empuja los botones hacia arriba para que no se estiren feo
    layout_menu.addStretch()

    # =========================================================================
    # El botón "Nuevo" NO debe tocar los bordes del sidebar (es una acción tipo
    # "píldora", no una pestaña de navegación). Como el layout_menu general ya
    # no tiene márgenes laterales, envolvemos a btn_nuevo en un contenedor
    # propio que sí le agrega margen izquierdo y derecho, sin afectar a los
    # botones de navegación de arriba. Junto con el setSizePolicy de arriba,
    # esto garantiza un margen SIMÉTRICO en ambos lados.
    # =========================================================================
    contenedor_nuevo = QWidget()
    lay_contenedor_nuevo = QHBoxLayout(contenedor_nuevo)
    lay_contenedor_nuevo.setContentsMargins(0, 0, 20, 0)
    lay_contenedor_nuevo.addWidget(btn_nuevo)

    layout_menu.addWidget(contenedor_nuevo)

    # ========================================================
    # 2. EL CONTENEDOR DINÁMICO (QStackedWidget)
    # ========================================================
    # Zona derecha de la pantalla que cambia dinámicamente
    pantallas_reemplazables = QStackedWidget()
    # mismo color gris que el resto del contenido, para que no haya ningún salto de color entre el sidebar activo y esta zona.
    pantallas_reemplazables.setStyleSheet(f"background-color: {COLOR_FONDO_CONTENIDO}; border: none;")


    # ---- PANTALLA 0: Bienvenida ----
    # Lo importamos desde vistas/dashboard.py
    pag_bienvenida = PantallaDashboard()

    # Instanciamos nuestras nuevas pantallas modulares pasándoles la ventana principal
    pag_clientes = PantallaClientes(ventana_principal)
    pag_equipos = PantallaEquipos(ventana_principal)
    pag_ordenes = PantallaOrdenes(ventana_principal)

    # ========================================================
    #  APILAR LAS PANTALLAS EN EL MAZO
    # ========================================================
    # Al agregarlas, PySide6 les asigna un número de índice automático (0, 1, 2, 3...)
    pantallas_reemplazables.addWidget(pag_bienvenida) # Índice 0
    pantallas_reemplazables.addWidget(pag_clientes)   # Índice 1
    pantallas_reemplazables.addWidget(pag_equipos)    # Índice 2
    pantallas_reemplazables.addWidget(pag_ordenes)    # Índice 3

    # ========================================================
    # 3. FUNCIONES PARA LEER LA BASE DE DATOS EN TIEMPO REAL
    # ========================================================
    
    def cargar_clientes():
        pag_clientes.cargar_clientes()
        # Mantenemos la navegación intacta abriendo el mazo en el índice 1
        pantallas_reemplazables.setCurrentIndex(1)
        btn_clientes.setChecked(True)  # Marcamos visualmente este botón como el activo

    def cargar_equipos():
        pag_equipos.cargar_equipos()
        # Mantenemos la navegación intacta abriendo el mazo en el índice 2
        pantallas_reemplazables.setCurrentIndex(2)
        btn_equipos.setChecked(True)

    def cargar_ordenes():
        pag_ordenes.cargar_ordenes()
        # Mantenemos la navegación intacta abriendo el mazo en el índice 3
        pantallas_reemplazables.setCurrentIndex(3)
        btn_ordenes.setChecked(True)

    # ========================================================
    # 4. CONECTAR LOS BOTONES A LAS NUEVAS FUNCIONES
    # ========================================================
    # Función para actualizar métricas y viajar al índice 0 (Dashboard)
    def mostrar_dashboard():
        pag_bienvenida.actualizar_metricas() # Fuerza el refresh con la base de datos
        pantallas_reemplazables.setCurrentIndex(0) # Vuelve al inicio
        btn_dashboard.setChecked(True)  # Marcamos visualmente este botón como el activo

    # Conectamos el nuevo botón de Dashboard
    btn_dashboard.clicked.connect(mostrar_dashboard)
    
    # Primero llamamos a la función que lee la BD y esa función se encarga de cambiar de pantalla.
    btn_clientes.clicked.connect(cargar_clientes)
    btn_equipos.clicked.connect(cargar_equipos)
    btn_ordenes.clicked.connect(cargar_ordenes)
    
    accion_cliente.triggered.connect(pag_clientes.abrir_formulario_cliente)
    accion_equipo.triggered.connect(pag_equipos.abrir_formulario_equipo)
    accion_orden.triggered.connect(pag_ordenes.abrir_formulario_orden)

    # ========================================================
    # 5. UNIÓN FINAL EN LA VENTANA
    # ========================================================
    layout_principal.addWidget(widget_menu, 1)
    layout_principal.addWidget(pantallas_reemplazables, 4) # En lugar de un widget fijo, metemos el mazo de pantallas


    # === ACTUALIZACIÓN INICIAL DEL DASHBOARD ===
    pag_bienvenida.actualizar_metricas()
    btn_dashboard.setChecked(True)  # Al arrancar la app, el Dashboard debe verse como la pestaña activa

    ventana_principal.show()
    personalizar_barra_titulo(ventana_principal)  # intenta pintar la barra de título de navy
    sys.exit(app.exec())


if __name__ == "__main__":
    # Verificamos si la base de datos existe y creamos las tablas si es necesario
    # ANTES de lanzar la interfaz gráfica, para que todo esté listo desde el primer uso.
    utilidades.inicializar_db()
    iniciar_interfaz()