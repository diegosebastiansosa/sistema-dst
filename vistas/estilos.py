# Paleta de colores centralizada del sistema

COLOR_SIDEBAR = "#1B2A4A"          # Azul marino de la barra lateral
COLOR_FONDO_CONTENIDO = "#EEF0F4"  # Gris muy claro del área de contenido
COLOR_ACENTO = "#6C63FF"           # Violeta, color de marca principal
COLOR_TEXTO_SIDEBAR = "#D5D9E8"    # Texto gris azulado para ítems inactivos del menú
COLOR_TEXTO_ACTIVO = "#FFFFFF"     # Texto blanco para el ítem activo del menú
COLOR_TEXTO_PRINCIPAL = "#1B2A4A"  # Texto oscuro (mismo tono que el sidebar, para coherencia visual)
COLOR_TEXTO_SECUNDARIO = "#6B7280" # Gris medio para subtítulos y textos de apoyo

# Estilo global reutilizable para todos los cuadros de diálogo (QDialog)
ESTILO_FORMULARIO = f"""
    QDialog {{
        background-color: {COLOR_FONDO_CONTENIDO};
    }}
    QLabel {{
        color: {COLOR_TEXTO_PRINCIPAL};
    }}
    QLineEdit, QComboBox {{
        background-color: #FFFFFF;
        color: {COLOR_TEXTO_PRINCIPAL};
        border: 1px solid #D8DAE5;
        border-radius: 6px;
        padding: 5px;
    }}
    QLineEdit:disabled {{
        background-color: #E5E7EB;
        color: {COLOR_TEXTO_SECUNDARIO};
    }}
    
    /* 1. Corrección del color de los nombres en la lista desplegable */
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        color: {COLOR_TEXTO_PRINCIPAL};
        selection-background-color: {COLOR_ACENTO};
        selection-color: #FFFFFF;
    }}

    /* 2. Solución definitiva para la flecha sin romper nada */
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border: none;
    }}
    
    /* Esta es la magia: le decimos a Qt que pinte un triángulo de texto plano */
    QComboBox::down-arrow {{
        image: none;             /* Elimina la flecha nativa rota de Windows */
        color: {COLOR_TEXTO_PRINCIPAL};
        font-family: "Arial", sans-serif;
        font-size: 10px;
        font-weight: bold;
    }}

    QCheckBox {{
        color: {COLOR_TEXTO_PRINCIPAL};
    }}
    QCheckBox::indicator {{
        border: 1px solid #D8DAE5;
        border-radius: 4px;
        background: white;
        width: 14px;
        height: 14px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLOR_ACENTO};
        border-color: {COLOR_ACENTO};
    }}
"""

import ctypes
def personalizar_barra_titulo(ventana):
    # Intenta colorear la barra de título nativa de Windows con nuestro navy de marca. Esto usa una API específica de Windows 11 (build 22000+), así
    # que la envolvemos en un try/except: si el usuario tiene Windows 10 o una versión más vieja de Windows 11, la función simplemente no hace nada y
    # la barra de título se ve con su color normal del sistema — la app sigue funcionando igual, solo sin este detalle extra.
    try:
        # DWMWA_CAPTION_COLOR = 35 (identificador fijo de esta API de Windows)
        DWMWA_CAPTION_COLOR = 35
        # Windows espera el color en formato 0x00BBGGRR (orden invertido: azul,
        # verde, rojo), al revés del formato habitual #RRGGBB que usamos en QSS.
        # COLOR_SIDEBAR = "#1B2A4A" -> R=1B, G=2A, B=4A
        color_bgr = 0x004A2A1B  # 0x00 + BB(4A) + GG(2A) + RR(1B)
        
        hwnd = int(ventana.winId())  # Identificador nativo de la ventana en Windows
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(ctypes.c_int(color_bgr)),
            ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        # Si falla (Windows 10, Windows 11 viejo, u otra causa), no hacemos nada. La app sigue funcionando normalmente, solo sin la barra coloreada.
        pass

from PySide6.QtWidgets import QMessageBox
def mostrar_mensaje(padre, tipo, titulo, texto, botones=QMessageBox.Ok):

    # Crea, colorea y muestra un QMessageBox en un solo llamado
    # tipo: QMessageBox.Question, .Information, .Warning o .Critical
    # Retorna el botón que el usuario presionó (útil para preguntas Sí/No).
    caja = QMessageBox(padre)
    caja.setWindowTitle(titulo)
    caja.setText(texto)
    caja.setIcon(tipo)
    caja.setStandardButtons(botones)
    
    # Le damos estilo explícito a los botones (Sí/No/Ok/etc.) del propio QMessageBox. Sin esto, toman el estilo nativo de Windows, que en
    # algunas configuraciones (temas oscuros del sistema, ciertas versiones de Windows) renderiza texto claro sobre fondo claro, dejándolos casi
    # invisibles. Con este estilo explícito, se ven igual en cualquier PC, sin depender del tema de Windows.
    caja.setStyleSheet(f"""
        QMessageBox {{
            background-color: {COLOR_FONDO_CONTENIDO};
        }}
        QMessageBox QLabel {{
            color: {COLOR_TEXTO_PRINCIPAL};
        }}
        QPushButton {{
            background-color: {COLOR_ACENTO};
            color: white;
            font-weight: bold;
            border-radius: 6px;
            padding: 6px 16px;
            border: none;
            min-width: 70px;
        }}
        QPushButton:hover {{
            background-color: #5A52E0;
        }}
    """)
    personalizar_barra_titulo(caja)
    return caja.exec()