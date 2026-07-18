import utilidades

# Estados fijos
ESTADOS_ORDEN = ['Recibido', 'En diagnóstico', 'Esperando repuesto', 'Reparado', 'Entregado']

def cancelar_orden_validada(id_orden):
    # Cancela una orden. Sin validación de inputs, mismo contrato de 4 valores
    exito = cancelar_orden(id_orden)

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ No se pudo cancelar la orden de reparación en la base de datos."

def cambiar_estado_orden_validado(id_orden, nuevo_estado):
    # Actualiza el estado de una orden de reparación.
    # No hay validación de datos porque el estado siempre viene de una lista cerrada (ESTADOS_ORDEN) elegida en un combo box, no de texto libre.
    # Aun así, devolvemos el mismo contrato de 4 valores que el resto de las funciones _validado, para que la GUI trate todos los backends igual.
    exito = actualizar_estado_orden(id_orden, nuevo_estado)

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ No se pudo actualizar el estado de la orden en la base de datos."

def alta_orden_validada(id_equipo, id_cliente, descripcion):
    # Valida los datos de una nueva orden de reparación y, si están completos, la persiste con estado inicial 'Recibido'.
    # Retorna (exito, tipo_error, titulo_error, mensaje_error), mismo contrato que usamos en clientes.py y equipos.py.

    # 1. VALIDACIÓN: la única obligatoria acá es la descripción del problema
    if not descripcion:
        return False, "warning", "Campos vacíos", "❌ Por favor, ingrese la descripción del problema de la orden de reparación."

    # 2. PERSISTENCIA: reutilizamos guardar_nueva_orden(), que ya existía
    exito = guardar_nueva_orden(id_equipo, id_cliente, descripcion)

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ Ocurrió un error al intentar registrar la orden de reparación en la base de datos."
    

def guardar_nueva_orden(id_equipo, id_cliente, descripcion):
    # Inserta una nueva orden de reparación en la base de datos. Retorna True si la inserción fue exitosa, o False si ocurrió algún error.
    try:
        # Establecemos la conexión centralizada con la base de datos
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        
        # Insertamos la orden con estado inicial 'Recibido'
        cursor.execute('''
            INSERT INTO ordenes (id_equipo, id_cliente, descripcion, estado)
            VALUES (?, ?, ?, 'Recibido')
        ''', (id_equipo, id_cliente, descripcion))
        
        # Confirmamos los cambios en la base de datos
        conexion.commit()
        # Cerramos la conexión para liberar recursos
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al guardar la orden: {e}")
        return False


def actualizar_estado_orden(id_orden, nuevo_estado):
    # Actualiza el estado de una orden de reparación en la base de datos. Retorna True si fue exitoso, o False si ocurrió un error.
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        
        # Ejecutamos la actualización del estado de la orden por su ID
        cursor.execute('UPDATE ordenes SET estado = ? WHERE id = ?', (nuevo_estado, id_orden))
        
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al actualizar el estado de la orden: {e}")
        return False


def cancelar_orden(id_orden):
    # Establece el estado de una orden de reparación como 'Cancelado'. Retorna True si fue exitoso, o False si ocurrió un error.
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        
        # Marcamos la orden con el estado 'Cancelado'
        cursor.execute("UPDATE ordenes SET estado = 'Cancelado' WHERE id = ?", (id_orden,))
        
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        print(f"Error al cancelar la orden: {e}")
        return False

