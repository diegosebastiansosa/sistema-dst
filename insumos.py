import utilidades


def obtener_insumos_activos():
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id, descripcion, fecha, unidades, costo FROM insumos WHERE activo = 1 ORDER BY descripcion"
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def alta_insumo_validada(descripcion, fecha, unidades, costo):
    descripcion = descripcion.strip()
    fecha = fecha.strip() or None if fecha else None
    if not descripcion:
        return False, "warning", "Campo obligatorio", "Ingrese la descripción del insumo."
    if unidades < 0 or costo < 0:
        return False, "warning", "Valor inválido", "Las unidades y el costo no pueden ser negativos."

    if guardar_nuevo_insumo(descripcion, fecha, unidades, costo):
        return True, None, None, None
    return False, "critical", "Error", "No se pudo guardar el insumo en la base de datos."


def editar_insumo_validado(id_insumo, descripcion, fecha, unidades, costo):
    descripcion = descripcion.strip()
    fecha = fecha.strip() or None if fecha else None
    if not descripcion:
        return False, "warning", "Campo obligatorio", "Ingrese la descripción del insumo."
    if unidades < 0 or costo < 0:
        return False, "warning", "Valor inválido", "Las unidades y el costo no pueden ser negativos."

    if actualizar_insumo(id_insumo, descripcion, fecha, unidades, costo):
        return True, None, None, None
    return False, "critical", "Error", "No se pudieron guardar los cambios del insumo."


def guardar_nuevo_insumo(descripcion, fecha, unidades, costo):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO insumos (descripcion, fecha, unidades, costo, activo) VALUES (?, ?, ?, ?, 1)",
            (descripcion, fecha, unidades, costo),
        )
        conexion.commit()
        return True
    except Exception as error:
        print(f"Error al guardar el insumo: {error}")
        return False
    finally:
        conexion.close()


def actualizar_insumo(id_insumo, descripcion, fecha, unidades, costo):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE insumos SET descripcion = ?, fecha = ?, unidades = ?, costo = ? WHERE id = ? AND activo = 1",
            (descripcion, fecha, unidades, costo, id_insumo),
        )
        conexion.commit()
        return cursor.rowcount == 1
    except Exception as error:
        print(f"Error al actualizar el insumo: {error}")
        return False
    finally:
        conexion.close()


def eliminar_insumo_logico(id_insumo):
    conexion = utilidades.conectar_db()
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE insumos SET activo = 0 WHERE id = ? AND activo = 1", (id_insumo,))
        conexion.commit()
        return cursor.rowcount == 1
    except Exception as error:
        print(f"Error al eliminar el insumo: {error}")
        return False
    finally:
        conexion.close()
