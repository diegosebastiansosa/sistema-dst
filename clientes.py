import utilidades
import sqlite3 # Asegurate de que esté importado al inicio del archivo

def editar_cliente_validado(id_cliente, nombre, telefono, email):
    #Valida los datos editados de un cliente existente y, si todo está OK, actualiza el registro en la DB.

    # 1. VALIDACIONES 
    if not nombre or not telefono or not email:
        return False, "warning", "Campos vacíos", "❌ Todos los campos son obligatorios."

    if not telefono.isdigit():
        return False, "warning", "Teléfono inválido", "⚠️ El campo de teléfono solo debe contener números, sin letras ni caracteres especiales."

    if not utilidades.es_mail_valido(email):
        return False, "warning", "Email inválido", "⚠️ El formato del correo electrónico no es válido.\nDebe usar el formato: usuario@dominio.com"

    # === Validación de Duplicados ===
    # Le pasamos id_cliente como excluir_id para que no se compare contra sí mismo (si no cambió su teléfono/email, no debe rechazarse).
    existe_tel, existe_mail = comprobar_duplicado(telefono, email, excluir_id=id_cliente)

    if existe_tel:
        return False, "warning", "Cliente Duplicado", f"⚠️ Ya existe otro cliente registrado con el número de teléfono: {telefono}.\nNo se permiten números duplicados."

    if existe_mail:
        return False, "warning", "Cliente Duplicado", f"⚠️ Ya existe otro cliente registrado con el correo electrónico: {email.lower()}.\nNo se permiten correos duplicados."

    # 2. PERSISTENCIA: reutilizamos actualizar_cliente(), que ya existía
    exito = actualizar_cliente(id_cliente, nombre, telefono, email)

    if exito:
        return True, None, None, None
    else:
        return False, "critical", "Error", "❌ No se pudieron guardar los cambios en la base de datos."

def alta_cliente_validado(nombre, telefono, email):
    # Valida los datos de un cliente nuevo y, si todo está OK, lo persiste en la DB.

    # Retorna siempre una tupla de 4 valores para que la GUI (o cualquier otra interfaz que se conecte a este backend) sepa qué mostrarle al usuario:
    #     (exito, tipo_error, titulo_error, mensaje_error)
    # - exito: True si se guardó correctamente, False si hubo cualquier problema.
    # - tipo_error: "warning" (el usuario puede corregir el dato) o "critical" (falló algo interno, como la base de datos).
    # - titulo_error y mensaje_error: texto para el QMessageBox.
    # Cuando exito es True, los otros 3 valores viajan en None porque no hay ningún error que mostrar.

    # 1. VALIDACIONES (reutilizable por cualquier interfaz, no solo por PySide6)
    if not nombre or not telefono or not email:
        return False, "warning", "Campos vacíos", "❌ Todos los campos son obligatorios. Por favor, completelos."

    # === Validación de teléfono (solo números) ===
    if not telefono.isdigit():
        return False, "warning", "Teléfono inválido", "⚠️ El campo de teléfono solo debe contener números, sin letras ni caracteres especiales."

    # Validación de formato de email usando nuestra utilidad
    if not utilidades.es_mail_valido(email):
        return False, "warning", "Email inválido", "⚠️ El formato del correo electrónico no es válido.\nDebe usar el formato: usuario@dominio.com"

    # === Validación de Duplicados ===
    # Reutilizamos la función que ya existía en este mismo archivo
    existe_tel, existe_mail = comprobar_duplicado(telefono, email)

    if existe_tel:
        return False, "warning", "Cliente Duplicado", f"⚠️ Ya existe un cliente registrado con el número de teléfono: {telefono}.\nNo se permiten números duplicados."

    if existe_mail:
        return False, "warning", "Cliente Duplicado", f"⚠️ Ya existe un cliente registrado con el correo electrónico: {email.lower()}.\nNo se permiten correos duplicados."

    # 2. PERSISTENCIA: con todo validado, intentamos guardar. Reutilizamos guardar_nuevo_cliente(), que ya existía y no la tocamos.
    exito = guardar_nuevo_cliente(nombre, telefono, email)

    if exito:
        # Los 3 valores de error van en None porque no hubo ningún error
        return True, None, None, None
    else:
        # Acá el problema no es que el usuario haya cargado mal un dato, es que falló la escritura en la base de datos (por eso "critical")
        return False, "critical", "Error", "❌ No se pudo guardar el cliente en la base de datos."

def comprobar_duplicado(telefono, email, excluir_id=None):
    # Busca si ya existe un cliente con el mismo teléfono o email.
    # Los clientes dados de baja (activo = 0) no cuentan como duplicado,
    # Retorna una tupla (existe_telefono, existe_email) con valores booleanos.

    # excluir_id: opcional. Si se pasa un ID, la búsqueda ignora al cliente con ese ID. Esto es lo que nos permite, al EDITAR un cliente, que pueda
    # conservar su propio teléfono/email sin que el sistema los marque como "duplicados de sí mismo". Al dar de ALTA un cliente nuevo no se pasa
    # este parámetro (queda en None), porque ahí sí queremos comparar contra TODOS los clientes existentes.
    existe_telefono = False
    existe_email = False

    conexion = utilidades.conectar_db()
    cursor = conexion.cursor()

    try:
        # 1. Comprobar teléfono
        if excluir_id is None:
            # Caso ALTA: comparamos contra todos los clientes
            cursor.execute("SELECT 1 FROM clientes WHERE telefono = ? AND activo = 1", (telefono,))
        else:
            # Caso EDICIÓN: comparamos contra todos MENOS el propio cliente
            cursor.execute(
                "SELECT 1 FROM clientes WHERE telefono = ? AND activo = 1 AND id != ?",
                (telefono, excluir_id)
            )
        if cursor.fetchone():
            existe_telefono = True

        # 2. Comprobar email (solo entre clientes activos)
        if excluir_id is None:
            cursor.execute(
                "SELECT 1 FROM clientes WHERE LOWER(email) = LOWER(?) AND activo = 1",
                (email,)
            )
        else:
            cursor.execute(
                "SELECT 1 FROM clientes WHERE LOWER(email) = LOWER(?) AND activo = 1 AND id != ?",
                (email, excluir_id)
            )
        if cursor.fetchone():
            existe_email = True

    except sqlite3.Error as e:
        print(f"Error al comprobar duplicados: {e}")
    finally:
        conexion.close()

    return existe_telefono, existe_email


def guardar_nuevo_cliente(nombre, telefono, email):
    # Inserta un nuevo cliente activo en la base de datos y retorna True si fue exitoso
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, email, activo) VALUES (?, ?, ?, 1)",
            (nombre, telefono, email)
        )
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        return False

def eliminar_cliente_logico(id_cliente):
    """Realiza una baja lógica (activo = 0) del cliente en SQLite y retorna True si fue exitoso"""
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        
        # 1. Desactivamos al cliente (Baja lógica)
        cursor.execute('UPDATE clientes SET activo = 0 WHERE id = ?', (id_cliente,))
        
        # 2. Desactivamos sus equipos en cascada
        cursor.execute('UPDATE equipos SET activo = 0 WHERE id_cliente = ?', (id_cliente,))
        
        # 3. Cancelamos sus órdenes en curso
        cursor.execute('''
            UPDATE ordenes 
            SET estado = 'Cancelado' 
            WHERE id_cliente = ? AND estado NOT IN ('Entregado', 'Cancelado')
        ''', (id_cliente,))
        
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        return False

def actualizar_cliente(id_cliente, nombre, telefono, email):
    """Actualiza los datos de un cliente existente y retorna True si fue exitoso"""
    try:
        conexion = utilidades.conectar_db()
        cursor = conexion.cursor()
        cursor.execute('''
            UPDATE clientes 
            SET nombre = ?, telefono = ?, email = ? 
            WHERE id = ?
        ''', (nombre, telefono, email, id_cliente))
        conexion.commit()
        conexion.close()
        return True
    except Exception as e:
        return False

