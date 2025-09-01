from flask import Flask, request, render_template, redirect, session, url_for, flash
import database
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from datetime import datetime

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = 'hotel-ve2-secret-key-2025'  # Clave secreta para sesiones

# Inicializamos la base de datos (crea tablas si no existen)
database.init_db()

# ========== FUNCIONES DE VALIDACIÓN Y AUTENTICACIÓN ==========

def login_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Valida formato de teléfono"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    return len(clean_phone) >= 7

def sanitize_input(text):
    """Sanitiza texto de entrada"""
    if not text:
        return ""
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

# Ruta principal: dashboard con botones de navegación
@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirige a login si no hay sesión
    return render_template("dashboard.html")

# Ruta para la lista de clientes
@app.route("/clientes", methods=['GET', 'POST'])
def lista_clientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Obtener parámetros de filtro
    termino_busqueda = request.args.get('termino', '')
    campo_filtro = request.args.get('campo', 'todos')
    
    # Construir la consulta base
    query = "SELECT * FROM clientes"
    params = []
    
    # Aplicar filtros
    if termino_busqueda:
        if campo_filtro == 'nombre':
            query += " WHERE nombre LIKE ?"
            params.append(f"%{termino_busqueda}%")
        elif campo_filtro == 'identificacion':
            query += " WHERE identificacion LIKE ?"
            params.append(f"%{termino_busqueda}%")
        elif campo_filtro == 'correo':
            query += " WHERE correo LIKE ?"
            params.append(f"%{termino_busqueda}%")
        elif campo_filtro == 'telefono':
            query += " WHERE telefono LIKE ?"
            params.append(f"%{termino_busqueda}%")
        else:  # todos los campos
            query += " WHERE nombre LIKE ? OR identificacion LIKE ? OR correo LIKE ? OR telefono LIKE ? OR direccion LIKE ?"
            params.extend([f"%{termino_busqueda}%", f"%{termino_busqueda}%", f"%{termino_busqueda}%", f"%{termino_busqueda}%", f"%{termino_busqueda}%"])
    
    query += " ORDER BY nombre ASC"
    
    cursor.execute(query, params)
    clientes = cursor.fetchall()
    conn.close()
    
    return render_template("clientes.html", 
                         clientes=clientes, 
                         termino_busqueda=termino_busqueda,
                         campo_filtro=campo_filtro)

# Ruta para gestión de usuarios
@app.route("/usuarios")
def gestion_usuarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)

# Ruta para agregar un cliente (solo autenticado)
@app.route("/agregar", methods=["POST"])
@login_required
def agregar_cliente():
    nombre = sanitize_input(request.form.get("nombre", ""))
    identificacion = sanitize_input(request.form.get("identificacion", ""))
    direccion = sanitize_input(request.form.get("direccion", ""))
    correo = sanitize_input(request.form.get("correo", ""))
    telefono = sanitize_input(request.form.get("telefono", ""))
    
    # Validaciones
    if not nombre or len(nombre) < 2:
        flash('El nombre debe tener al menos 2 caracteres.', 'danger')
        return redirect("/agregar_cliente")
    
    if not validate_email(correo):
        flash('Email inválido.', 'danger')
        return redirect("/agregar_cliente")
    
    if not validate_phone(telefono):
        flash('Teléfono inválido.', 'danger')
        return redirect("/agregar_cliente")
    
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (nombre, identificacion, direccion, correo, telefono) VALUES (?, ?, ?, ?, ?)", 
                      (nombre, identificacion, direccion, correo, telefono))
        conn.commit()
        conn.close()
        flash('Cliente agregado exitosamente.', 'success')
    except sqlite3.IntegrityError:
        flash('Ya existe un cliente con esa identificación.', 'danger')
    except Exception as e:
        flash('Error al agregar cliente.', 'danger')
    
    return redirect("/clientes")

# Ruta para la página de agregar cliente
@app.route("/agregar_cliente")
def pagina_agregar_cliente():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("agregar_cliente.html")

# Ruta para eliminar un cliente por id (solo autenticado)
@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar_cliente(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))  # Elimina el cliente
    conn.commit()
    conn.close()
    return redirect("/clientes")

# Ruta para eliminar un usuario por id (solo autenticado)
@app.route("/eliminar_usuario/<int:id>", methods=["POST"])
def eliminar_usuario(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # No permitir eliminar el usuario actual
    if id == session['user_id']:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect("/usuarios")
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect("/usuarios")

# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validaciones
        if len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Usuario registrado exitosamente. Inicia sesión.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe.', 'danger')
    return render_template('register.html')

# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Usuario y contraseña son obligatorios.', 'danger')
            return render_template('login.html')
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Sesión iniciada correctamente.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()  # Limpia la sesión
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))

# Ruta para buscar clientes por nombre
@app.route('/buscar', methods=['GET', 'POST'])
def buscar_cliente():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    resultados = []
    if request.method == 'POST':
        termino = request.form['termino']
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE nombre LIKE ?", (f"%{termino}%",))
        resultados = cursor.fetchall()
        conn.close()
    return render_template('buscar.html', resultados=resultados)

# Lista reservas
@app.route('/reservas', methods=['GET', 'POST'])
def lista_reservas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Filtros
    termino_busqueda = request.args.get('termino', '')
    estado_filtro = request.args.get('estado', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Query base
    query = """
        SELECT r.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono,
               p.estado as estado_pago, p.monto as monto_pago, p.metodo as metodo_pago
        FROM reservas r 
        JOIN clientes c ON r.cliente_id = c.id 
        LEFT JOIN pagos p ON r.id = p.reserva_id
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if termino_busqueda:
        query += " AND (c.nombre LIKE ? OR c.identificacion LIKE ? OR r.habitacion LIKE ?)"
        params.extend([f"%{termino_busqueda}%", f"%{termino_busqueda}%", f"%{termino_busqueda}%"])
    
    if estado_filtro:
        query += " AND r.estado = ?"
        params.append(estado_filtro)
    
    if fecha_desde:
        query += " AND r.fecha_entrada >= ?"
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += " AND r.fecha_entrada <= ?"
        params.append(fecha_hasta)
    
    query += " ORDER BY r.fecha_entrada ASC"
    
    cursor.execute(query, params)
    reservas = cursor.fetchall()
    conn.close()
    
    return render_template('reservas.html', 
                         reservas=reservas, 
                         termino_busqueda=termino_busqueda,
                         estado_filtro=estado_filtro,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

# Buscar reserva
@app.route('/buscar_reserva', methods=['GET', 'POST'])
def buscar_reserva():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    resultados = []
    if request.method == 'POST':
        termino = request.form['termino']
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE nombre LIKE ? OR identificacion LIKE ?", (f"%{termino}%", f"%{termino}%"))
        resultados = cursor.fetchall()
        conn.close()
    return render_template('buscar_reserva.html', resultados=resultados)

# Crear reserva
@app.route('/crear_reserva/<int:cliente_id>', methods=['GET', 'POST'])
def crear_reserva(cliente_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        habitacion = request.form['habitacion']
        fecha_entrada = request.form['fecha_entrada']
        fecha_salida = request.form['fecha_salida']
        num_personas = request.form['num_personas']
        precio_total = request.form['precio_total']
        estado = request.form['estado']
        notas = request.form['notas']
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        try:
            # Crear reserva
            cursor.execute('''
                INSERT INTO reservas (cliente_id, habitacion, fecha_entrada, fecha_salida, 
                                     num_personas, precio_total, estado, notas, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (cliente_id, habitacion, fecha_entrada, fecha_salida, num_personas, precio_total, estado, notas))
            
            # Obtener ID de reserva
            reserva_id = cursor.lastrowid
            
            # Crear pago automático
            from datetime import datetime
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO pagos (reserva_id, cliente_id, monto, fecha, metodo, estado, referencia, notas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (reserva_id, cliente_id, precio_total, fecha_actual, 'Pendiente', 'Pendiente', 
                  f'RES-{reserva_id}', f'Pago automático por reserva #{reserva_id}'))
            
            # Actualizar habitación
            cursor.execute("UPDATE habitaciones SET estado = 'Reservada' WHERE numero = ?", (habitacion,))
            
            conn.commit()
            flash('Reserva creada exitosamente con pago asociado.', 'success')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error al crear la reserva: {str(e)}', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('lista_reservas'))
    
    # Obtener datos del cliente para mostrar en el formulario
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,))
    cliente = cursor.fetchone()
    conn.close()
    
    return render_template('crear_reserva.html', cliente=cliente)

# Eliminar reserva
@app.route('/eliminar_reserva/<int:id>', methods=['POST'])
def eliminar_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener info de reserva
        cursor.execute("SELECT habitacion FROM reservas WHERE id = ?", (id,))
        reserva = cursor.fetchone()
        
        if reserva:
            # Eliminar pago
            cursor.execute("DELETE FROM pagos WHERE reserva_id = ?", (id,))
            
            # Eliminar reserva
            cursor.execute("DELETE FROM reservas WHERE id = ?", (id,))
            
            # Actualizar habitación
            cursor.execute("UPDATE habitaciones SET estado = 'Disponible' WHERE numero = ?", (reserva['habitacion'],))
            
            conn.commit()
            flash('Reserva y pago asociado eliminados exitosamente.', 'success')
        else:
            flash('Reserva no encontrada.', 'danger')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar la reserva: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('lista_reservas'))

# Cambiar estado reserva
@app.route('/cambiar_estado_reserva/<int:id>', methods=['POST'])
def cambiar_estado_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    nuevo_estado = request.form['estado']
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reservas SET estado = ? WHERE id = ?", (nuevo_estado, id))
    conn.commit()
    conn.close()
    flash(f'Estado de reserva cambiado a: {nuevo_estado}', 'success')
    return redirect(url_for('lista_reservas'))

# Check-in reserva
@app.route('/checkin_reserva/<int:id>', methods=['POST'])
def checkin_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = database.get_connection()
    cursor = conn.cursor()
    # Cambiar estado a 'Ocupada'
    cursor.execute("UPDATE reservas SET estado = 'Ocupada' WHERE id = ?", (id,))
    # Obtener habitación
    cursor.execute("SELECT habitacion FROM reservas WHERE id = ?", (id,))
    habitacion = cursor.fetchone()
    if habitacion:
        cursor.execute("UPDATE habitaciones SET estado = 'Ocupada' WHERE numero = ?", (habitacion['habitacion'],))
    conn.commit()
    conn.close()
    flash('Check-in realizado correctamente.', 'success')
    return redirect(url_for('lista_reservas'))

# Check-out reserva
@app.route('/checkout_reserva/<int:id>', methods=['POST'])
def checkout_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = database.get_connection()
    cursor = conn.cursor()
    # Cambiar estado a 'Completada'
    cursor.execute("UPDATE reservas SET estado = 'Completada' WHERE id = ?", (id,))
    # Obtener habitación
    cursor.execute("SELECT habitacion FROM reservas WHERE id = ?", (id,))
    habitacion = cursor.fetchone()
    if habitacion:
        cursor.execute("UPDATE habitaciones SET estado = 'Limpieza' WHERE numero = ?", (habitacion['habitacion'],))
    conn.commit()
    conn.close()
    flash('Check-out realizado correctamente.', 'success')
    return redirect(url_for('lista_reservas'))

# Habitaciones
@app.route('/habitaciones')
def lista_habitaciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Filtros
    estado_filtro = request.args.get('estado', '')
    tipo_filtro = request.args.get('tipo', '')
    
    # Query base
    query = "SELECT * FROM habitaciones"
    params = []
    
    # Aplicar filtros
    if estado_filtro:
        query += " WHERE estado = ?"
        params.append(estado_filtro)
        if tipo_filtro:
            query += " AND tipo = ?"
            params.append(tipo_filtro)
    elif tipo_filtro:
        query += " WHERE tipo = ?"
        params.append(tipo_filtro)
    
    query += " ORDER BY numero ASC"
    
    cursor.execute(query, params)
    habitaciones = cursor.fetchall()
    conn.close()
    
    return render_template('habitaciones.html', 
                         habitaciones=habitaciones,
                         estado_filtro=estado_filtro,
                         tipo_filtro=tipo_filtro)

# Agregar habitación
@app.route('/agregar_habitacion', methods=['GET', 'POST'])
def agregar_habitacion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        numero = request.form['numero']
        tipo = request.form['tipo']
        capacidad = request.form['capacidad']
        precio_noche = request.form['precio_noche']
        amenidades = request.form['amenidades']
        descripcion = request.form['descripcion']
        
        # Manejo de imagen
        imagen_path = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validar tipo de archivo
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in imagen.filename and \
                   imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    
                    # Crear nombre único para la imagen
                    import os
                    from werkzeug.utils import secure_filename
                    
                    # Crear directorio de uploads si no existe
                    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    # Generar nombre único
                    filename = secure_filename(f"habitacion_{numero}_{imagen.filename}")
                    imagen_path = os.path.join('uploads', filename)
                    full_path = os.path.join(upload_folder, filename)
                    
                    # Guardar imagen
                    imagen.save(full_path)
        
        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO habitaciones (numero, tipo, capacidad, precio_noche, amenidades, descripcion, imagen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (numero, tipo, capacidad, precio_noche, amenidades, descripcion, imagen_path))
            conn.commit()
            flash('Habitación agregada exitosamente.', 'success')
            return redirect(url_for('lista_habitaciones'))
        except sqlite3.IntegrityError:
            flash('El número de habitación ya existe.', 'danger')
        finally:
            conn.close()
    
    return render_template('agregar_habitacion.html')

# Cambiar estado habitación
@app.route('/cambiar_estado_habitacion/<int:id>', methods=['POST'])
def cambiar_estado_habitacion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    nuevo_estado = request.form['estado']
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE habitaciones SET estado = ? WHERE id = ?", (nuevo_estado, id))
    conn.commit()
    conn.close()
    flash(f'Estado de habitación cambiado a: {nuevo_estado}', 'success')
    return redirect(url_for('lista_habitaciones'))

# Editar habitación
@app.route('/editar_habitacion/<int:id>', methods=['GET', 'POST'])
def editar_habitacion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        numero = request.form['numero']
        tipo = request.form['tipo']
        capacidad = request.form['capacidad']
        precio_noche = request.form['precio_noche']
        estado = request.form['estado']
        amenidades = request.form['amenidades']
        descripcion = request.form['descripcion']
        
        # Manejo de imagen
        imagen_path = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validar tipo de archivo
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in imagen.filename and \
                   imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    
                    # Crear nombre único para la imagen
                    import os
                    from werkzeug.utils import secure_filename
                    
                    # Crear directorio de uploads si no existe
                    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    
                    # Generar nombre único
                    filename = secure_filename(f"habitacion_{numero}_{imagen.filename}")
                    imagen_path = os.path.join('uploads', filename)
                    full_path = os.path.join(upload_folder, filename)
                    
                    # Guardar imagen
                    imagen.save(full_path)
        
        try:
            if imagen_path:
                # Actualizar con nueva imagen
                cursor.execute("""
                    UPDATE habitaciones 
                    SET numero=?, tipo=?, capacidad=?, precio_noche=?, estado=?, amenidades=?, descripcion=?, imagen=?
                    WHERE id=?
                """, (numero, tipo, capacidad, precio_noche, estado, amenidades, descripcion, imagen_path, id))
            else:
                # Actualizar sin cambiar imagen
                cursor.execute("""
                    UPDATE habitaciones 
                    SET numero=?, tipo=?, capacidad=?, precio_noche=?, estado=?, amenidades=?, descripcion=?
                    WHERE id=?
                """, (numero, tipo, capacidad, precio_noche, estado, amenidades, descripcion, id))
            
            conn.commit()
            flash('Habitación actualizada exitosamente.', 'success')
            return redirect(url_for('lista_habitaciones'))
        except sqlite3.IntegrityError:
            flash('El número de habitación ya existe.', 'danger')
        finally:
            conn.close()
    
    # GET: Mostrar formulario de edición
    cursor.execute("SELECT * FROM habitaciones WHERE id = ?", (id,))
    habitacion = cursor.fetchone()
    conn.close()
    
    if not habitacion:
        flash('Habitación no encontrada.', 'danger')
        return redirect(url_for('lista_habitaciones'))
    
    return render_template('editar_habitacion.html', habitacion=habitacion)

# Eliminar habitación
@app.route('/eliminar_habitacion/<int:id>', methods=['POST'])
def eliminar_habitacion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Obtener información de la habitación antes de eliminar
    cursor.execute("SELECT imagen FROM habitaciones WHERE id = ?", (id,))
    habitacion = cursor.fetchone()
    
    # Eliminar la habitación
    cursor.execute("DELETE FROM habitaciones WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    # Eliminar la imagen si existe
    if habitacion and habitacion['imagen']:
        import os
        imagen_path = os.path.join(app.root_path, 'static', habitacion['imagen'])
        if os.path.exists(imagen_path):
            os.remove(imagen_path)
    
    flash('Habitación eliminada exitosamente.', 'success')
    return redirect(url_for('lista_habitaciones'))

# Pagos

# Lista pagos
@app.route('/pagos')
def lista_pagos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Obtener parámetros de filtro
        estado_filtro = request.args.get('estado', '')
        metodo_filtro = request.args.get('metodo', '')
        
        # Construir la consulta base
        query = """
            SELECT p.*, c.nombre as cliente_nombre, r.habitacion, r.fecha_entrada, r.fecha_salida
            FROM pagos p 
            JOIN clientes c ON p.cliente_id = c.id 
            JOIN reservas r ON p.reserva_id = r.id
        """
        params = []
        
        # Aplicar filtros
        if estado_filtro:
            query += " WHERE p.estado = ?"
            params.append(estado_filtro)
            if metodo_filtro:
                query += " AND p.metodo = ?"
                params.append(metodo_filtro)
        elif metodo_filtro:
            query += " WHERE p.metodo = ?"
            params.append(metodo_filtro)
        
        query += " ORDER BY p.fecha DESC"
        
        cursor.execute(query, params)
        pagos = cursor.fetchall()
        conn.close()
        
        return render_template('pagos.html', 
                             pagos=pagos,
                             estado_filtro=estado_filtro,
                             metodo_filtro=metodo_filtro)
    
    except Exception as e:
        print(f"Error en lista_pagos: {e}")
        flash('Error al cargar la lista de pagos. Verifica la base de datos.', 'danger')
        return render_template('pagos.html', 
                             pagos=[],
                             estado_filtro='',
                             metodo_filtro='')

# Registrar pago
@app.route('/registrar_pago/<int:reserva_id>', methods=['GET', 'POST'])
def registrar_pago(reserva_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Obtener datos de reserva
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono
            FROM reservas r 
            JOIN clientes c ON r.cliente_id = c.id 
            WHERE r.id = ?
        """, (reserva_id,))
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('Reserva no encontrada.', 'danger')
            return redirect(url_for('lista_reservas'))
        
        if request.method == 'POST':
            monto = request.form.get('monto', '')
            metodo = request.form.get('metodo', '')
            estado = request.form.get('estado', 'Pendiente')
            referencia = request.form.get('referencia', '')
            notas = request.form.get('notas', '')
            
            # Validaciones
            if not monto or not metodo:
                flash('Monto y método de pago son obligatorios.', 'danger')
                return render_template('registrar_pago.html', reserva=reserva)
            
            try:
                monto = float(monto)
                if monto <= 0:
                    flash('El monto debe ser mayor a 0.', 'danger')
                    return render_template('registrar_pago.html', reserva=reserva)
            except ValueError:
                flash('El monto debe ser un número válido.', 'danger')
                return render_template('registrar_pago.html', reserva=reserva)
            
            # Verificar pago existente
            cursor.execute("SELECT id, estado FROM pagos WHERE reserva_id = ?", (reserva_id,))
            pago_existente = cursor.fetchone()
            
            if pago_existente:
                # Actualizar pago
                cursor.execute("""
                    UPDATE pagos 
                    SET monto = ?, metodo = ?, estado = ?, referencia = ?, notas = ?, fecha = DATE('now')
                    WHERE reserva_id = ?
                """, (monto, metodo, estado, referencia, notas, reserva_id))
                flash('Pago actualizado exitosamente.', 'success')
            else:
                # Crear pago
                cursor.execute("""
                    INSERT INTO pagos (reserva_id, cliente_id, monto, fecha, metodo, estado, referencia, notas)
                    VALUES (?, ?, ?, DATE('now'), ?, ?, ?, ?)
                """, (reserva_id, reserva['cliente_id'], monto, metodo, estado, referencia, notas))
                flash('Pago registrado exitosamente.', 'success')
            conn.commit()
            flash('Pago registrado exitosamente.', 'success')
            conn.close()
            return redirect(url_for('lista_pagos'))
        
        conn.close()
        return render_template('registrar_pago.html', reserva=reserva)
    
    except Exception as e:
        print(f"Error en registrar_pago: {e}")
        flash('Error al procesar el pago. Inténtalo de nuevo.', 'danger')
        return redirect(url_for('lista_pagos'))

# Cambiar estado pago
@app.route('/cambiar_estado_pago/<int:id>', methods=['POST'])
def cambiar_estado_pago(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        nuevo_estado = request.form.get('estado', '')
        if not nuevo_estado:
            flash('Estado no especificado.', 'danger')
            return redirect(url_for('lista_pagos'))
        
        # Validar estado
        estados_validos = ['Pendiente', 'Completado', 'Cancelado']
        if nuevo_estado not in estados_validos:
            flash('Estado no válido.', 'danger')
            return redirect(url_for('lista_pagos'))
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Verificar pago
        cursor.execute("SELECT id FROM pagos WHERE id = ?", (id,))
        if not cursor.fetchone():
            flash('Pago no encontrado.', 'danger')
            conn.close()
            return redirect(url_for('lista_pagos'))
        
        cursor.execute("UPDATE pagos SET estado = ? WHERE id = ?", (nuevo_estado, id))
        conn.commit()
        conn.close()
        flash(f'Estado de pago cambiado a: {nuevo_estado}', 'success')
        return redirect(url_for('lista_pagos'))
    
    except Exception as e:
        print(f"Error en cambiar_estado_pago: {e}")
        flash('Error al cambiar el estado del pago.', 'danger')
        return redirect(url_for('lista_pagos'))

# Eliminar pago
@app.route('/eliminar_pago/<int:id>', methods=['POST'])
def eliminar_pago(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Verificar pago
        cursor.execute("SELECT id, estado FROM pagos WHERE id = ?", (id,))
        pago = cursor.fetchone()
        if not pago:
            flash('Pago no encontrado.', 'danger')
            conn.close()
            return redirect(url_for('lista_pagos'))
        
        # No eliminar pagos completados
        if pago['estado'] == 'Completado':
            flash('No se puede eliminar un pago completado.', 'danger')
            conn.close()
            return redirect(url_for('lista_pagos'))
        
        cursor.execute("DELETE FROM pagos WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash('Pago eliminado exitosamente.', 'success')
        return redirect(url_for('lista_pagos'))
    
    except Exception as e:
        print(f"Error en eliminar_pago: {e}")
        flash('Error al eliminar el pago.', 'danger')
        return redirect(url_for('lista_pagos'))

# Reportes
@app.route('/reportes')
@login_required
def reportes():
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Estadísticas
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservas")
        total_reservas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM habitaciones")
        total_habitaciones = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pagos WHERE estado = 'Completado'")
        pagos_completados = cursor.fetchone()[0]
        
        # Ingresos
        cursor.execute("SELECT SUM(monto) FROM pagos WHERE estado = 'Completado'")
        ingresos_totales = cursor.fetchone()[0] or 0
        
        # Reservas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM reservas 
            GROUP BY estado
        """)
        reservas_por_estado = cursor.fetchall()
        
        # Habitaciones por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM habitaciones 
            GROUP BY estado
        """)
        habitaciones_por_estado = cursor.fetchall()
        
        # Top clientes
        cursor.execute("""
            SELECT c.nombre, COUNT(r.id) as reservas 
            FROM clientes c 
            LEFT JOIN reservas r ON c.id = r.cliente_id 
            GROUP BY c.id, c.nombre 
            ORDER BY reservas DESC 
            LIMIT 5
        """)
        top_clientes = cursor.fetchall()
        
        # Ingresos por método
        cursor.execute("""
            SELECT metodo, SUM(monto) as total 
            FROM pagos 
            WHERE estado = 'Completado' 
            GROUP BY metodo
        """)
        ingresos_por_metodo = cursor.fetchall()
        
        # Reservas del mes
        cursor.execute("""
            SELECT COUNT(*) FROM reservas 
            WHERE strftime('%Y-%m', fecha_entrada) = strftime('%Y-%m', 'now')
        """)
        reservas_mes_actual = cursor.fetchone()[0]
        
        # Ingresos del mes
        cursor.execute("""
            SELECT SUM(monto) FROM pagos 
            WHERE estado = 'Completado' 
            AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
        """)
        ingresos_mes_actual = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return render_template('reportes.html',
                             total_clientes=total_clientes,
                             total_reservas=total_reservas,
                             total_habitaciones=total_habitaciones,
                             pagos_completados=pagos_completados,
                             ingresos_totales=ingresos_totales,
                             reservas_por_estado=reservas_por_estado,
                             habitaciones_por_estado=habitaciones_por_estado,
                             top_clientes=top_clientes,
                             ingresos_por_metodo=ingresos_por_metodo,
                             reservas_mes_actual=reservas_mes_actual,
                             ingresos_mes_actual=ingresos_mes_actual)
    
    except Exception as e:
        print(f"Error en reportes: {e}")
        flash('Error al cargar los reportes.', 'danger')
        return redirect(url_for('home'))

# Reporte ocupación
@app.route('/reporte_ocupacion')
@login_required
def reporte_ocupacion():
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Ocupación diaria
        cursor.execute("""
            SELECT 
                date(r.fecha_entrada) as fecha,
                COUNT(DISTINCT r.habitacion) as habitaciones_ocupadas,
                (SELECT COUNT(*) FROM habitaciones) as total_habitaciones
            FROM reservas r 
            WHERE r.fecha_entrada >= date('now', '-30 days')
            AND r.estado IN ('Confirmada', 'Ocupada')
            GROUP BY date(r.fecha_entrada)
            ORDER BY fecha DESC
        """)
        ocupacion_diaria = cursor.fetchall()
        
        # Ocupación por tipo
        cursor.execute("""
            SELECT 
                h.tipo,
                COUNT(r.id) as reservas,
                AVG(r.precio_total) as precio_promedio
            FROM habitaciones h
            LEFT JOIN reservas r ON h.numero = r.habitacion
            WHERE r.estado IN ('Confirmada', 'Ocupada')
            GROUP BY h.tipo
        """)
        ocupacion_por_tipo = cursor.fetchall()
        
        conn.close()
        
        return render_template('reporte_ocupacion.html',
                             ocupacion_diaria=ocupacion_diaria,
                             ocupacion_por_tipo=ocupacion_por_tipo)
    
    except Exception as e:
        print(f"Error en reporte_ocupacion: {e}")
        flash('Error al cargar el reporte de ocupación.', 'danger')
        return redirect(url_for('reportes'))

# Reporte financiero
@app.route('/reporte_financiero')
@login_required
def reporte_financiero():
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Ingresos mensuales
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes,
                SUM(monto) as ingresos
            FROM pagos 
            WHERE estado = 'Completado'
            AND fecha >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', fecha)
            ORDER BY mes DESC
        """)
        ingresos_mensuales = cursor.fetchall()
        
        # Métodos de pago
        cursor.execute("""
            SELECT 
                metodo,
                COUNT(*) as cantidad,
                SUM(monto) as total
            FROM pagos 
            WHERE estado = 'Completado'
            GROUP BY metodo
            ORDER BY total DESC
        """)
        metodos_pago = cursor.fetchall()
        
        # Pagos pendientes
        cursor.execute("""
            SELECT 
                p.monto,
                c.nombre as cliente,
                r.habitacion,
                p.fecha
            FROM pagos p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN reservas r ON p.reserva_id = r.id
            WHERE p.estado = 'Pendiente'
            ORDER BY p.fecha DESC
        """)
        pagos_pendientes = cursor.fetchall()
        
        conn.close()
        
        return render_template('reporte_financiero.html',
                             ingresos_mensuales=ingresos_mensuales,
                             metodos_pago=metodos_pago,
                             pagos_pendientes=pagos_pendientes)
    
    except Exception as e:
        print(f"Error en reporte_financiero: {e}")
        flash('Error al cargar el reporte financiero.', 'danger')
        return redirect(url_for('reportes'))

@app.route('/reserva_rapida', methods=['GET', 'POST'])
def reserva_rapida():
    if request.method == 'POST':
        nombre = sanitize_input(request.form.get('nombre', ''))
        correo = sanitize_input(request.form.get('correo', ''))
        telefono = sanitize_input(request.form.get('telefono', ''))
        habitacion = request.form.get('habitacion', '')
        fecha_entrada = request.form.get('fecha_entrada', '')
        fecha_salida = request.form.get('fecha_salida', '')
        num_personas = request.form.get('num_personas', '1')
        notas = sanitize_input(request.form.get('notas', ''))

        # Validación básica
        if not (nombre and correo and telefono and habitacion and fecha_entrada and fecha_salida and num_personas):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('reserva_rapida.html')

        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            # Insertar cliente visitante (identificación y dirección genéricas)
            cursor.execute('''
                INSERT INTO clientes (nombre, identificacion, direccion, correo, telefono)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre, 'VISITANTE', 'N/A', correo, telefono))
            cliente_id = cursor.lastrowid

            # Insertar reserva
            cursor.execute('''
                INSERT INTO reservas (cliente_id, habitacion, fecha_entrada, fecha_salida, num_personas, precio_total, estado, notas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (cliente_id, habitacion, fecha_entrada, fecha_salida, num_personas, 0, 'Pendiente', notas))

            # Actualizar habitación
            cursor.execute("UPDATE habitaciones SET estado = 'Reservada' WHERE numero = ?", (habitacion,))

            conn.commit()
            flash('¡Reserva rápida realizada con éxito! Pronto nos pondremos en contacto.', 'success')
            return render_template('reserva_rapida_confirmacion.html', nombre=nombre)
        except Exception as e:
            conn.rollback()
            flash(f'Error al realizar la reserva: {str(e)}', 'danger')
        finally:
            conn.close()
        return render_template('reserva_rapida.html')
    
    # GET: Obtener habitaciones disponibles para mostrar
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        # Obtener solo las primeras 3 habitaciones disponibles
        cursor.execute("""
            SELECT id, numero, tipo, capacidad, precio_noche, estado, amenidades, descripcion, imagen
            FROM habitaciones 
            WHERE estado = 'Disponible'
            ORDER BY numero
            LIMIT 3
        """)
        habitaciones = cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener habitaciones: {e}")
        habitaciones = []
    finally:
        conn.close()
    
    return render_template('reserva_rapida.html', habitaciones=habitaciones)


# Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)
