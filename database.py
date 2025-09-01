import sqlite3

DATABASE_NAME = "hotel.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection () as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            identificacion TEXT NOT NULL,
            direccion TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT NOT NULL
        )
        """)
        # Agregar columnas si no existen
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN direccion TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN correo TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN telefono TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        # Tabla pagos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reserva_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            metodo TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            referencia TEXT,
            notas TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(reserva_id) REFERENCES reservas(id),
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
        """)
        
        # Agregar columnas si no existen
        try:
            cursor.execute("ALTER TABLE pagos ADD COLUMN reserva_id INTEGER")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE pagos ADD COLUMN estado TEXT DEFAULT 'Pendiente'")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE pagos ADD COLUMN referencia TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE pagos ADD COLUMN notas TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE pagos ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """)
        
        # Tabla reservas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            habitacion TEXT NOT NULL,
            fecha_entrada TEXT NOT NULL,
            fecha_salida TEXT NOT NULL,
            num_personas INTEGER NOT NULL,
            precio_total REAL NOT NULL,
            estado TEXT DEFAULT 'Confirmada',
            notas TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
        """)
        
        # Tabla habitaciones
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habitaciones(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            capacidad INTEGER NOT NULL,
            precio_noche REAL NOT NULL,
            estado TEXT DEFAULT 'Disponible',
            amenidades TEXT,
            descripcion TEXT,
            imagen TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Agregar columna imagen si no existe
        try:
            cursor.execute("ALTER TABLE habitaciones ADD COLUMN imagen TEXT")
        except Exception:
            pass
        

        
        # Habitaciones de ejemplo
        cursor.execute("SELECT COUNT(*) FROM habitaciones")
        if cursor.fetchone()[0] == 0:
            habitaciones_ejemplo = [
                ('101', 'Individual', 1, 120000.00, 'Disponible', 'WiFi, TV, A/C', 'Habitación individual con vista al jardín'),
                ('102', 'Individual', 1, 120000.00, 'Disponible', 'WiFi, TV, A/C', 'Habitación individual con vista al jardín'),
                ('201', 'Doble', 2, 250000.00, 'Disponible', 'WiFi, TV, A/C, Balcón', 'Habitación doble con balcón'),
                ('202', 'Doble', 2, 250000.00, 'Disponible', 'WiFi, TV, A/C, Balcón', 'Habitación doble con balcón'),
                ('301', 'Suite', 4, 380000.00, 'Disponible', 'WiFi, TV, A/C, Jacuzzi, Balcón', 'Suite de lujo con jacuzzi'),
                ('302', 'Suite', 4, 380000.00, 'Disponible', 'WiFi, TV, A/C, Jacuzzi, Balcón', 'Suite de lujo con jacuzzi')
            ]
            cursor.executemany("""
                INSERT INTO habitaciones (numero, tipo, capacidad, precio_noche, estado, amenidades, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, habitaciones_ejemplo)
        
        conn.commit()