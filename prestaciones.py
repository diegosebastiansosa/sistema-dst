import utilidades


def obtener_prestaciones_activas():
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT rowid AS id, empresa, fecha, equipo, cliente, ganancia
            FROM prestaciones
            WHERE activo = 1
            ORDER BY fecha DESC, rowid DESC
        """)
        return cursor.fetchall()
    finally:
        conexion.close()


def alta_prestacion_validada(empresa, fecha, equipo, cliente, ganancia):
    empresa = empresa.strip()
    equipo = equipo.strip()
    cliente = cliente.strip()
    fecha = fecha.strip() or None if fecha else None

    if not empresa or not equipo or not cliente:
        return False, "warning", "Campos obligatorios", "Complete empresa, equipo y cliente."
    if ganancia < 0:
        return False, "warning", "Valor inválido", "La ganancia no puede ser negativa."

    if guardar_nueva_prestacion(empresa, fecha, equipo, cliente, ganancia):
        return True, None, None, None
    return False, "critical", "Error", "No se pudo guardar la prestación en la base de datos."


def editar_prestacion_validada(id_prestacion, empresa, fecha, equipo, cliente, ganancia):
    empresa = empresa.strip()
    equipo = equipo.strip()
    cliente = cliente.strip()
    fecha = fecha.strip() or None if fecha else None

    if not empresa or not equipo or not cliente:
        return False, "warning", "Campos obligatorios", "Complete empresa, equipo y cliente."
    if ganancia < 0:
        return False, "warning", "Valor inválido", "La ganancia no puede ser negativa."

    if actualizar_prestacion(id_prestacion, empresa, fecha, equipo, cliente, ganancia):
        return True, None, None, None
    return False, "critical", "Error", "No se pudieron guardar los cambios de la prestación."


def guardar_nueva_prestacion(empresa, fecha, equipo, cliente, ganancia):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO prestaciones (empresa, fecha, equipo, cliente, ganancia, activo)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (empresa, fecha, equipo, cliente, ganancia))
        conexion.commit()
        return True
    except Exception as error:
        print(f"Error al guardar la prestación: {error}")
        return False
    finally:
        conexion.close()


def actualizar_prestacion(id_prestacion, empresa, fecha, equipo, cliente, ganancia):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE prestaciones
            SET empresa = ?, fecha = ?, equipo = ?, cliente = ?, ganancia = ?
            WHERE rowid = ? AND activo = 1
        """, (empresa, fecha, equipo, cliente, ganancia, id_prestacion))
        conexion.commit()
        return cursor.rowcount == 1
    except Exception as error:
        print(f"Error al actualizar la prestación: {error}")
        return False
    finally:
        conexion.close()


def eliminar_prestacion_logica(id_prestacion):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE prestaciones SET activo = 0 WHERE rowid = ? AND activo = 1",
            (id_prestacion,),
        )
        conexion.commit()
        return cursor.rowcount == 1
    except Exception as error:
        print(f"Error al dar de baja la prestación: {error}")
        return False
    finally:
        conexion.close()
