# =============================================================================
# vistas/dashboard.py
# =============================================================================
# Este archivo define la pantalla de Bienvenida (Dashboard) del sistema.
# Es una clase, no un widget inline
#
# ESTRUCTURA DEL MÓDULO:
#   - PantallaDashboard (QWidget): contenedor de la pantalla de inicio
#       ├── init_ui()             → construye tarjetas y gráficos
#       └── actualizar_metricas() → refresca los números y gráficos con datos de la BD
# =============================================================================

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QToolButton,
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtCharts import (
    QChart, QChartView, QPieSeries, QBarSet, QBarSeries,
    QBarCategoryAxis, QValueAxis,
)
from PySide6.QtGui import QPainter, QColor
import utilidades # Importamos las utilidades para consultar la BD directamente

# Importamos las joyas de la corona de qfluentwidgets
from qfluentwidgets import (
    SimpleCardWidget, 
    TitleLabel, 
    SubtitleLabel, 
    CaptionLabel, 
    LargeTitleLabel,
    IconWidget,
    FluentIcon as FIF,
)

# Importamos la paleta centralizada. Se define una sola vez en vistas/estilos.py.
from vistas.estilos import (
    COLOR_SIDEBAR, COLOR_ACENTO,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO,
)


class PantallaDashboard(QWidget):
    # Clase que representa la pantalla de Bienvenida / Panel de Control.
    # Hereda de QWidget para funcionar como un contenedor visual independiente, igual que el resto de pantallas del sistema.

    def __init__(self):
        # Llamamos al constructor de la clase padre (QWidget) para inicializar
        # correctamente el widget antes de agregarle nuestros propios componentes.
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Construye la pantalla de bienvenida con estadísticas y reportes mensuales.

        # ---- Layout principal del Dashboard ----
        # Usamos QVBoxLayout para organizar los widgets de arriba hacia abajo.
        # Al pasarle 'self' en el constructor, el layout queda automáticamente asignado a este widget sin necesidad de llamar a self.setLayout().
        lay_dashboard = QVBoxLayout(self)
        lay_dashboard.setContentsMargins(24, 24, 24, 24)  # NUEVO: aire alrededor de todo el contenido
        lay_dashboard.setSpacing(12)  # NUEVO: separación prolija entre secciones

        # ---- Mensaje de bienvenida ----
        lbl_bienvenida = LargeTitleLabel(
            "Dashboard"
        )

        # Forzamos el color explícitamente en vez de dejar que TitleLabel use el color automático del tema de qfluentwidgets.
        # Como en app.py fijamos Theme.LIGHT (nuestra paleta es propia y fija, no depende del modo claro/oscuro de Windows), conviene ser explícitos
        # acá también para asegurar buen contraste siempre.
        lbl_bienvenida.setStyleSheet(f"color: {COLOR_TEXTO_PRINCIPAL}; border: none; background: transparent;")

        lay_dashboard.addWidget(lbl_bienvenida)

        lbl_subtitulo = CaptionLabel("Estado general del taller de reparaciones:")
        # --- NUEVO: mismo criterio que arriba, color explícito y consistente
        lbl_subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; border: none; background: transparent;")
        lay_dashboard.addWidget(lbl_subtitulo)

        # Grilla para distribuir las 5 tarjetas de forma armónica (Fila 0: 3 tarjetas | Fila 1: 2 tarjetas)
        grid_tarjetas = QGridLayout()
        grid_tarjetas.setSpacing(20)

        # =====================================================================
        # Lista de datos + un bucle, que arma las 5 tarjetas, menos código duplicado para mantener.
        # Elegimos 5 colores que armonizan entre sí y con la paleta general (navy + violeta)
        # =====================================================================
        datos_tarjetas = [
            {"icono": FIF.PEOPLE,            "titulo": "Clientes Activos",   "color": COLOR_ACENTO},  # Violeta de marca
            {"icono": FIF.DEVELOPER_TOOLS,   "titulo": "Equipos Activos",    "color": "#0776F5"},      # Azul complementario
            {"icono": FIF.FOLDER,            "titulo": "Órdenes Abiertas",   "color": "#F59E0B"},      # Ámbar (pendiente)
            {"icono": FIF.SYNC,              "titulo": "Órdenes Reparadas",  "color": "#14B8A6"},      # Teal (en curso avanzado)
            {"icono": FIF.COMPLETED,         "titulo": "Órdenes Entregadas", "color": "#22C55E"},      # Verde (completado)
        ]

        # Guardamos referencia a cada QLabel de número, para poder actualizarlo después desde actualizar_metricas() sin tener que reconstruir las tarjetas.
        self.labels_valores = {}

        # Posiciones (fila, columna) en la grilla para cada una de las 5 tarjetas, en el mismo orden que datos_tarjetas.
        posiciones = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]

        for datos, (fila, columna) in zip(datos_tarjetas, posiciones):
            # SimpleCardWidget reemplaza al viejo QFrame manual. Tiene sombras y efecto hover automáticos, sin necesidad de programarlos.
            card = SimpleCardWidget()
            lay_card = QVBoxLayout(card)
            lay_card.setContentsMargins(20, 18, 20, 18)
            lay_card.setSpacing(8)

            # Encabezado con ícono y texto
            lay_header = QHBoxLayout()
            icono = IconWidget(datos["icono"], card)
            icono.setFixedSize(24, 24)
            lay_header.addWidget(icono)
            # Separamos el CaptionLabel en una variable para aplicarle estilo
            lbl_tarjeta_titulo = CaptionLabel(datos["titulo"])
            lbl_tarjeta_titulo.setStyleSheet(
                f"background: transparent; border: none; color: {COLOR_TEXTO_SECUNDARIO};"
            )
            lay_header.addWidget(lbl_tarjeta_titulo)
            # -------------------------
            lay_header.addStretch()
            lay_card.addLayout(lay_header)

            # El número grande de la tarjeta, con el color distintivo de cada métrica
            lbl_valor = LargeTitleLabel("0")
            lbl_valor.setStyleSheet(
                f"font-size: 28px; font-weight: bold; color: {datos['color']}; "
                f"border: none; background: transparent;"
            )
            lay_card.addWidget(lbl_valor)

            # La tarjeta de "Órdenes Entregadas" ocupa 2 columnas, igual que en el original
            if datos["titulo"] == "Órdenes Entregadas":
                grid_tarjetas.addWidget(card, fila, columna, 1, 2)
            else:
                grid_tarjetas.addWidget(card, fila, columna)

            # Guardamos la referencia al QLabel usando el título como clave, para poder ubicarlo fácilmente en actualizar_metricas()
            self.labels_valores[datos["titulo"]] = lbl_valor

        lay_dashboard.addLayout(grid_tarjetas)

        # --- SECCIÓN: Distribución de estados y ganancias mensuales ---
        lay_graficos = QHBoxLayout()
        lay_graficos.setSpacing(15)

        # ==========================================
        # CONFIGURACIÓN: Gráfico de Torta
        # ==========================================
        self.chart_torta = QChart()
        self.chart_torta.setTitle("Distribución Porcentual")
        self.chart_torta.legend().setAlignment(Qt.AlignBottom)

        self.view_torta = QChartView(self.chart_torta)
        self.view_torta.setRenderHint(QPainter.Antialiasing)
        self.view_torta.setMinimumHeight(300)
        self.view_torta.setMaximumHeight(380)

        self.mes_actual_ganancias = self._primer_dia_mes(QDate.currentDate())
        self.mes_seleccionado_ganancias = self.mes_actual_ganancias
        self.chart_ganancias = QChart()
        self.chart_ganancias.legend().setAlignment(Qt.AlignBottom)
        self.chart_ganancias.legend().setLabelColor(QColor(COLOR_TEXTO_SECUNDARIO))
        self.view_ganancias = QChartView(self.chart_ganancias)
        self.view_ganancias.setRenderHint(QPainter.Antialiasing)
        self.view_ganancias.setMinimumHeight(210)
        self.view_ganancias.setMaximumHeight(260)

        card_ganancias = SimpleCardWidget()
        lay_card_ganancias = QVBoxLayout(card_ganancias)
        lay_card_ganancias.setContentsMargins(16, 14, 16, 12)
        lay_card_ganancias.setSpacing(4)

        fila_mes = QHBoxLayout()
        self.btn_mes_anterior = QToolButton()
        self.btn_mes_anterior.setIcon(FIF.LEFT_ARROW.icon(color=QColor(COLOR_SIDEBAR)))
        self.btn_mes_anterior.setIconSize(QSize(16, 16))
        self.btn_mes_anterior.setFixedSize(32, 32)
        self.btn_mes_anterior.setToolTip("Mes anterior")
        self.btn_mes_anterior.clicked.connect(lambda checked=False: self.cambiar_mes_ganancias(-1))
        fila_mes.addWidget(self.btn_mes_anterior)

        self.lbl_mes_ganancias = CaptionLabel()
        self.lbl_mes_ganancias.setAlignment(Qt.AlignCenter)
        self.lbl_mes_ganancias.setStyleSheet(
            f"color: {COLOR_TEXTO_PRINCIPAL}; font-weight: bold;"
        )
        fila_mes.addWidget(self.lbl_mes_ganancias, 1)

        self.btn_mes_siguiente = QToolButton()
        self.btn_mes_siguiente.setIcon(FIF.RIGHT_ARROW.icon(color=QColor(COLOR_SIDEBAR)))
        self.btn_mes_siguiente.setIconSize(QSize(16, 16))
        self.btn_mes_siguiente.setFixedSize(32, 32)
        self.btn_mes_siguiente.setToolTip("Mes siguiente")
        self.btn_mes_siguiente.clicked.connect(lambda checked=False: self.cambiar_mes_ganancias(1))
        fila_mes.addWidget(self.btn_mes_siguiente)
        lay_card_ganancias.addLayout(fila_mes)

        self.lbl_ganancia_neta = LargeTitleLabel("$ 0")
        self.lbl_ganancia_neta.setAlignment(Qt.AlignCenter)
        self.lbl_ganancia_neta.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #16A34A; "
            "border: none; background: transparent;"
        )
        lay_card_ganancias.addWidget(self.lbl_ganancia_neta)
        lay_card_ganancias.addWidget(self.view_ganancias, 1)

        # Nota: los colores de fondo y bordes de estos gráficos se terminan
        # de aplicar en actualizar_metricas(), que se llama al final de este
        # método y cada vez que hay que refrescar los datos.

        # =====================================================================
        # Envolvemos cada gráfico dentro de una SimpleCardWidget para
        # integrarlos visualmente con el resto del dashboard.
        # =====================================================================

        card_torta = SimpleCardWidget()
        lay_card_torta = QVBoxLayout(card_torta)
        lay_card_torta.setContentsMargins(16, 16, 16, 16)
        lay_card_torta.addWidget(self.view_torta)

        # El gráfico de volumen se reemplaza por el reporte mensual integrado.
        lay_graficos.addWidget(card_torta, 1)
        lay_graficos.addWidget(card_ganancias, 1)

        lay_dashboard.addLayout(lay_graficos)

        # Carga inicial de datos
        self.actualizar_metricas()

    def actualizar_metricas(self):
        """Llama al backend y refresca todos los números y gráficos en pantalla"""
        # 1. Carga de los indicadores de las tarjetas superiores
        datos = utilidades.obtener_metricas_dashboard()
        self.labels_valores["Clientes Activos"].setText(str(datos["clientes_activos"]))
        self.labels_valores["Equipos Activos"].setText(str(datos["equipos_activos"]))
        self.labels_valores["Órdenes Abiertas"].setText(str(datos["ordenes_abiertas"]))
        self.labels_valores["Órdenes Reparadas"].setText(str(datos["ordenes_reparadas"]))
        self.labels_valores["Órdenes Entregadas"].setText(str(datos["ordenes_entregadas"]))
        self.actualizar_grafico_ganancias()

        # 2. Obtención de datos detallados por estado desde la BD
        estados_data = utilidades.obtener_estados_ordenes()
        total_ordenes = sum(estados_data.values())

        # Colores definidos
        color_fondo_grafico = QColor("#FFFFFF")
        color_texto_titulo = QColor(COLOR_TEXTO_PRINCIPAL)
        color_texto_leyendas = QColor(COLOR_TEXTO_SECUNDARIO)
        borde_style = "border: none; background-color: white;"

        # Aplicar estilos al gráfico de distribución
        self.view_torta.setStyleSheet(borde_style)

        # Configurar Gráfico de Torta
        self.chart_torta.setBackgroundBrush(color_fondo_grafico)
        self.chart_torta.setTitleBrush(color_texto_titulo)
        self.chart_torta.titleFont().setBold(True)
        #self.chart_torta.legend().setAlignment(Qt.AlignRight)
        self.chart_torta.legend().setLabelColor(color_texto_leyendas)

        # Colores de las rebanadas de la torta, alineados con la paleta general.
        colores_estados = {
            "Recibido": "#4C6EF5",           # Azul
            "En diagnóstico": "#F59E0B",     # Ámbar
            "Esperando repuesto": "#EF4444", # Rojo
            "Reparado": "#14B8A6",           # Teal
            "Entregado": "#22C55E"           # Verde
        }

        # --- RECONSTRUIR GRÁFICO DE TORTA (%) ---
        self.chart_torta.removeAllSeries()
        series_torta = QPieSeries()
        
        for estado, cantidad in estados_data.items():
            if total_ordenes > 0 and cantidad > 0:
                porcentaje = (cantidad / total_ordenes) * 100
                # slice_pie representa cada tajada del gráfico
                slice_pie = series_torta.append(f"{estado} ({porcentaje:.1f}%)", cantidad)
                
                # Aplicamos el color flat personalizado si existe en nuestro mapeo
                if estado in colores_estados:
                    slice_pie.setBrush(QColor(colores_estados[estado]))
                    
                slice_pie.setLabelVisible(False) # Dejamos el detalle en la leyenda lateral
        
        self.chart_torta.addSeries(series_torta)

        self.actualizar_grafico_ganancias()

    @staticmethod
    def _primer_dia_mes(fecha):
        return fecha.addDays(1 - fecha.day())

    def cambiar_mes_ganancias(self, cantidad):
        nuevo_mes = self.mes_seleccionado_ganancias.addMonths(cantidad)
        if nuevo_mes <= self.mes_actual_ganancias:
            self.mes_seleccionado_ganancias = nuevo_mes
            self.actualizar_grafico_ganancias()

    def actualizar_grafico_ganancias(self):
        nombres_meses = (
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        )
        mes = self.mes_seleccionado_ganancias
        self.lbl_mes_ganancias.setText(
            f"{nombres_meses[mes.month() - 1].capitalize()} {mes.year()}"
        )
        self.btn_mes_siguiente.setEnabled(mes < self.mes_actual_ganancias)

        try:
            ganancias = utilidades.obtener_ganancias_mensuales(mes.year(), mes.month())
        except Exception as error:
            print(f"Error al obtener ganancias mensuales: {error}")
            ganancias = {
                "ordenes_entregadas": 0,
                "prestaciones": 0,
                "costo_insumos": 0,
                "ganancia_neta": 0,
            }

        neto = ganancias["ganancia_neta"]
        self.lbl_ganancia_neta.setText(
            "$ " + f"{neto:,.0f}".replace(",", ".")
        )
        color_neto = "#16A34A" if neto >= 0 else "#B91C1C"
        self.lbl_ganancia_neta.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {color_neto}; "
            "border: none; background: transparent;"
        )

        self.view_ganancias.setStyleSheet("border: none; background-color: white;")
        self.chart_ganancias.removeAllSeries()
        for eje in self.chart_ganancias.axes():
            self.chart_ganancias.removeAxis(eje)
        self.chart_ganancias.setBackgroundBrush(QColor("#FFFFFF"))
        self.chart_ganancias.setTitleBrush(QColor(COLOR_TEXTO_PRINCIPAL))

        componentes = (
            ("Órdenes", ganancias["ordenes_entregadas"], "#4C6EF5"),
            ("Prestaciones", ganancias["prestaciones"], "#14B8A6"),
            ("Insumos", ganancias["costo_insumos"], "#EF4444"),
            ("Neto", neto, "#22C55E" if neto >= 0 else "#B91C1C"),
        )
        serie = QBarSeries()
        serie.setLabelsVisible(True)
        serie.setLabelsFormat("$ @value")
        for nombre, valor, color in componentes:
            barra = QBarSet(nombre)
            barra.setColor(QColor(color))
            barra.append(valor)
            serie.append(barra)
        self.chart_ganancias.addSeries(serie)

        eje_x = QBarCategoryAxis()
        eje_x.append(["Mes seleccionado"])
        eje_x.setLabelsColor(QColor(COLOR_TEXTO_SECUNDARIO))
        self.chart_ganancias.addAxis(eje_x, Qt.AlignBottom)
        serie.attachAxis(eje_x)

        valores = [valor for _, valor, _ in componentes]
        minimo = min(0, min(valores))
        maximo = max(0, max(valores))
        margen = max((maximo - minimo) * 0.15, 1)
        eje_y = QValueAxis()
        eje_y.setRange(minimo - margen if minimo < 0 else 0, maximo + margen)
        eje_y.setLabelFormat("$ %d")
        eje_y.setLabelsColor(QColor(COLOR_TEXTO_SECUNDARIO))
        self.chart_ganancias.addAxis(eje_y, Qt.AlignLeft)
        serie.attachAxis(eje_y)