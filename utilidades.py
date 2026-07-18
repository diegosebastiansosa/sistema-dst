import re
import sqlite3
import os  # Para verificar si el archivo de la base de datos ya existe en el disco
import sys

# Determinamos la ruta de la base de datos según si estamos en modo desarrollo o en modo ejecutable (PyInstaller)
if getattr(sys, 'frozen', False):
    CARPETA_BASE = os.path.dirname(sys.executable)
else:
    CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))

RUTA_DB = os.path.join(CARPETA_BASE, 'dst.db')

def obtener_estados_ordenes():
    # Trae el conteo de órdenes agrupadas por su estado actual
    estados = {
        "Recibido": 0,
        "En Diagnóstico": 0,
        "Esperando repuesto": 0,
        "Reparado": 0,
        "Entregado": 0
    }
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        
        # Agrupamos y contamos por la columna estado
        cursor.execute("SELECT estado, COUNT(*) FROM ordenes GROUP BY estado")
        filas = cursor.fetchall()
        
        for estado, conteo in filas:
            if estado in estados:
                estados[estado] = conteo
                
        conexion.close()
    except Exception as e:
        print(f"Error al obtener estados de órdenes: {e}")
    return estados

def obtener_metricas_dashboard():
    # Trae las métricas reales desde SQLite para poblar el Dashboard
    metricas = {
        "clientes_activos": 0,
        "equipos_activos": 0,
        "ordenes_abiertas": 0,
        "ordenes_reparadas": 0,
        "ordenes_entregadas": 0
    }
    try:
        conexion = conectar_db() # Usá tu función de conexión habitual
        cursor = conexion.cursor()
        
        # 1. Clientes activos
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1")
        metricas["clientes_activos"] = cursor.fetchone()[0]
        
        # 2. Equipos activos
        cursor.execute("SELECT COUNT(*) FROM equipos WHERE activo = 1")
        metricas["equipos_activos"] = cursor.fetchone()[0]
        
        # 3. Órdenes abiertas (no entregadas ni canceladas ni reparadas aún)
        cursor.execute("SELECT COUNT(*) FROM ordenes WHERE estado NOT IN ('Reparado', 'Entregado', 'Cancelado')")
        metricas["ordenes_abiertas"] = cursor.fetchone()[0]
        
        # 4. Órdenes reparadas (listas para retirar)
        cursor.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'Reparado'")
        metricas["ordenes_reparadas"] = cursor.fetchone()[0]
        
        # 5. Órdenes entregadas (histórico de éxito)
        cursor.execute("SELECT COUNT(*) FROM ordenes WHERE estado = 'Entregado'")
        metricas["ordenes_entregadas"] = cursor.fetchone()[0]
        
        conexion.close()
    except Exception as e:
        print(f"Error al obtener métricas de base de datos: {e}")
        
    return metricas

# --- CONEXIÓN CENTRALIZADA ---
def conectar_db():
    """Función única para conectarse a la base de datos dst.db"""
    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    return conexion

def inicializar_db():
    """
    Crea las tablas de la base de datos SOLO si el archivo dst.db no existe.
    Debe llamarse UNA SOLA VEZ al arrancar la aplicación, desde app.py.
    """
    # os.path.exists() retorna True si el archivo ya existe, False si no existe.
    # Si ya existe, no hacemos nada: las tablas ya están creadas de antes.
    if os.path.exists(RUTA_DB):
        return

    # Si el archivo NO existe, nos conectamos (esto crea el archivo vacío) y creamos las tablas.
    conexion = conectar_db()
    cursor = conexion.cursor()

    # CREATE TABLE IF NOT EXISTS es una precaución extra: si la tabla ya existiera, no falla.
    # INTEGER PRIMARY KEY AUTOINCREMENT: SQLite asigna automáticamente un ID único a cada fila.

    # Tabla de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT    NOT NULL,
            telefono  TEXT    NOT NULL,
            email     TEXT    NOT NULL,
            activo    INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Tabla de Equipos
    # id_cliente es una FOREIGN KEY: vincula cada equipo con su dueño en la tabla clientes.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipos (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo                TEXT    NOT NULL,
            marca               TEXT    NOT NULL,
            modelo              TEXT    NOT NULL,
            procesador          TEXT    NOT NULL,
            ram                 TEXT    NOT NULL,
            gpu_dedicada        INTEGER NOT NULL DEFAULT 0,
            marca_gpu           TEXT    NOT NULL DEFAULT 'n/a',
            modelo_gpu          TEXT    NOT NULL DEFAULT 'n/a',
            vram                TEXT    NOT NULL DEFAULT 'n/a',
            almacenamiento_ssd  TEXT    NOT NULL,
            almacenamiento_hdd  TEXT    NOT NULL,
            id_cliente          INTEGER NOT NULL,
            activo              INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id)
        )
    ''')

    # Tabla de Órdenes de Reparación
    # id_equipo e id_cliente son FOREIGN KEY: vinculan la orden con su equipo y cliente.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            id_equipo   INTEGER NOT NULL,
            id_cliente  INTEGER NOT NULL,
            descripcion TEXT    NOT NULL,
            estado      TEXT    NOT NULL DEFAULT 'Recibido',
            FOREIGN KEY (id_equipo)  REFERENCES equipos(id),
            FOREIGN KEY (id_cliente) REFERENCES clientes(id)
        )
    ''')

    # Guardamos los cambios y cerramos la conexión
    conexion.commit()
    conexion.close()
    print('Base de datos inicializada correctamente.')

# --- VALIDACIONES DE DATOS ---

def es_mail_valido(correo): # VALIDAR MAIL EN LA GUI
    # Verifica si un correo cumple con la estructura estándar (retorna True o False)
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    # Evaluamos con re.match y devolvemos un booleano directo
    return bool(re.match(patron, correo))


# --- SELECCIONES CENTRALIZADAS DE ENTIDADES ---

def obtener_clientes_activos():
    """Retorna la lista de clientes activos para la UI"""
    conexion = conectar_db()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, telefono, email FROM clientes WHERE activo = 1")
    clientes = cursor.fetchall()
    conexion.close()
    return clientes

def obtener_equipos_activos():
    """Retorna la lista de equipos con sus datos de hardware y dueño para la UI"""
    conexion = conectar_db()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT e.id, e.tipo, e.marca, e.modelo, e.procesador, e.ram, e.gpu_dedicada,
               e.marca_gpu, e.modelo_gpu, e.vram, e.almacenamiento_ssd, e.almacenamiento_hdd,
               c.nombre AS cliente_nombre, e.id_cliente
        FROM equipos e
        INNER JOIN clientes c ON e.id_cliente = c.id
        WHERE e.activo = 1
    ''')
    equipos = cursor.fetchall()
    conexion.close()
    return equipos

def obtener_todas_las_ordenes():
    """Retorna el listado completo de órdenes para la UI"""
    conexion = conectar_db()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT o.id, c.nombre AS cliente_nombre,
               (e.tipo || ' ' || e.marca || ' ' || e.modelo || ' (' || e.procesador || ' | ' || e.ram || ' | Video: ' || 
                CASE WHEN e.gpu_dedicada = 1 THEN e.marca_gpu || ' ' || e.modelo_gpu || ' ' || e.vram ELSE 'Intel/AMD o/b' END || 
                ' | SSD: ' || e.almacenamiento_ssd || ')') AS equipo_completo, 
               o.descripcion, o.estado
        FROM ordenes o
        INNER JOIN equipos e ON o.id_equipo = e.id
        INNER JOIN clientes c ON o.id_cliente = c.id
    ''')
    ordenes = cursor.fetchall()
    conexion.close()
    return ordenes

def obtener_lista_clientes_combo():
    """Trae solo ID y Nombre de clientes activos para llenar el desplegable de la UI"""
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre FROM clientes WHERE activo = 1")
        clientes = cursor.fetchall()
        conexion.close()
        return clientes # Retorna lista de diccionarios/rows con 'id' y 'nombre'
    except Exception:
        return []