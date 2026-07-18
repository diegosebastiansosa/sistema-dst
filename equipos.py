import utilidades
def alta_equipo_validado(tipo, marca, modelo, procesador, ram, gpu_dedicada,
                          marca_gpu, modelo_gpu, vram, ssd, hdd, id_cliente):
    """
    Valida los datos de un equipo nuevo y, si están completos, lo persiste
    asociado al cliente indicado.

    Retorna (exito, tipo_error, titulo_error, mensaje_error), igual que
    en clientes.py, para que la GUI solo tenga que mostrar lo que le llega.
    """

    # 1. VALIDACIÓN: mismos campos obligatorios que exigía la GUI.
    # Nota: ssd y hdd son "obligatorios en conjunto" (al menos uno de los dos),
    # por eso la condición usa "not ssd and not hdd" en vez de "or".
    if not tipo or not marca or not modelo or not procesador or not ram or (not ssd and not hdd):
        return False, "warning", "Campos vacíos", "❌ Por favor complete los datos esenciales del equipo (Tipo, Marca, Modelo, Procesador, RAM y al menos un Almacenamiento)."

    # 2. PERSISTENCIA: reutilizamos guardar_nuevo_equipo(), que ya existía
    exito = guardar_nuevo_equipo(
        tipo, marca, modelo, procesador, ram, gpu_dedicada,
        marca_gpu, modelo_gpu, vram, ssd, hdd, id_cliente
    )

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ No se pudo registrar el equipo en la base de datos."


def editar_equipo_validado(id_equipo, tipo, marca, modelo, procesador, ram,
                            gpu_dedicada, marca_gpu, modelo_gpu, vram, ssd, hdd):
    """
    Valida los datos editados de un equipo existente y, si están completos,
    actualiza el registro.
    """

    if not tipo or not marca or not modelo or not procesador or not ram or (not ssd and not hdd):
        return False, "warning", "Campos vacíos", "❌ Faltan completar datos esenciales."

    exito = actualizar_equipo(
        id_equipo, tipo, marca, modelo, procesador, ram,
        gpu_dedicada, marca_gpu, modelo_gpu, vram, ssd, hdd
    )

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ Error al actualizar en la base de datos."


def guardar_nuevo_equipo(tipo, marca, modelo, procesador, ram, gpu_dedicada, marca_gpu, modelo_gpu, vram, almacenamiento_ssd, almacenamiento_hdd, id_cliente):
    """Inserta un nuevo equipo en la base de datos asociado a un cliente"""
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO equipos (
                tipo, marca, modelo, procesador, ram, gpu_dedicada, 
                marca_gpu, modelo_gpu, vram, almacenamiento_ssd, almacenamiento_hdd, id_cliente, activo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (tipo, marca, modelo, procesador, ram, gpu_dedicada, marca_gpu, modelo_gpu, vram, almacenamiento_ssd, almacenamiento_hdd, id_cliente))
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        return False
    
def eliminar_equipo_logico(id_equipo):
    """Realiza la baja lógica de un equipo (activo = 0) y cancela sus órdenes asociadas activas"""
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        
        # 1. Desactivamos el equipo
        cursor.execute('UPDATE equipos SET activo = 0 WHERE id = ?', (id_equipo,))
        
        # 2. Cancelamos en cascada las órdenes de este equipo que no estén terminadas
        cursor.execute('''
            UPDATE ordenes 
            SET estado = 'Cancelado' 
            WHERE id_equipo = ? AND estado NOT IN ('Entregado', 'Cancelado')
        ''', (id_equipo,))
        
        conexion.commit()
        conexion.close()
        return True
    except Exception:
        return False

def actualizar_equipo(id_equipo, tipo, marca, modelo, procesador, ram, gpu_dedicada, marca_gpu, modelo_gpu, vram, ssd, hdd):
    """Actualiza los datos técnicos de un equipo existente"""
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        cursor.execute('''
            UPDATE equipos 
            SET tipo = ?, marca = ?, modelo = ?, procesador = ?, ram = ?, gpu_dedicada = ?, 
                marca_gpu = ?, modelo_gpu = ?, vram = ?, almacenamiento_ssd = ?, almacenamiento_hdd = ?
            WHERE id = ?
        ''', (tipo, marca, modelo, procesador, ram, gpu_dedicada, marca_gpu, modelo_gpu, vram, ssd, hdd, id_equipo))
        conexion.commit()
        conexion.close()
        return True
    except Exception:
        return False

