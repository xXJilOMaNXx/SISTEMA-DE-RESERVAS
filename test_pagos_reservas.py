#!/usr/bin/env python3
"""
Script para probar la vinculación de pagos con reservas
"""

import sqlite3
from datetime import datetime, timedelta

def test_pagos_reservas():
    """Prueba vinculación pagos-reservas"""
    
    print("🔍 Probando vinculación de pagos con reservas...")
    print("=" * 50)
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('hotel.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Verificar estructura de tablas
        print("1. Verificando estructura de tablas...")
        
        cursor.execute("PRAGMA table_info(reservas)")
        columnas_reservas = cursor.fetchall()
        print(f"   ✅ Tabla reservas: {len(columnas_reservas)} columnas")
        
        cursor.execute("PRAGMA table_info(pagos)")
        columnas_pagos = cursor.fetchall()
        print(f"   ✅ Tabla pagos: {len(columnas_pagos)} columnas")
        
        # 2. Verificar datos existentes
        print("\n2. Verificando datos existentes...")
        
        cursor.execute("SELECT COUNT(*) as total FROM reservas")
        total_reservas = cursor.fetchone()['total']
        print(f"   📊 Total reservas: {total_reservas}")
        
        cursor.execute("SELECT COUNT(*) as total FROM pagos")
        total_pagos = cursor.fetchone()['total']
        print(f"   💰 Total pagos: {total_pagos}")
        
        # 3. Verificar vinculación
        print("\n3. Verificando vinculación...")
        
        cursor.execute("""
            SELECT r.id as reserva_id, r.habitacion, r.precio_total,
                   p.id as pago_id, p.monto, p.estado as estado_pago,
                   c.nombre as cliente
            FROM reservas r
            LEFT JOIN pagos p ON r.id = p.reserva_id
            JOIN clientes c ON r.cliente_id = c.id
            ORDER BY r.id DESC
            LIMIT 5
        """)
        
        reservas_con_pagos = cursor.fetchall()
        
        if reservas_con_pagos:
            print("   📋 Últimas 5 reservas con sus pagos:")
            for row in reservas_con_pagos:
                estado_pago = row['estado_pago'] if row['estado_pago'] else "Sin pago"
                monto_pago = row['monto'] if row['monto'] else "N/A"
                print(f"      Reserva #{row['reserva_id']} - {row['cliente']} - Hab: {row['habitacion']}")
                print(f"         Precio: ${row['precio_total']} | Pago: ${monto_pago} ({estado_pago})")
        else:
            print("   ⚠️  No hay reservas con pagos vinculados")
        
        # 4. Verificar reservas sin pagos
        print("\n4. Verificando reservas sin pagos...")
        
        cursor.execute("""
            SELECT r.id, r.habitacion, c.nombre
            FROM reservas r
            JOIN clientes c ON r.cliente_id = c.id
            WHERE NOT EXISTS (SELECT 1 FROM pagos p WHERE p.reserva_id = r.id)
        """)
        
        reservas_sin_pagos = cursor.fetchall()
        
        if reservas_sin_pagos:
            print(f"   ⚠️  {len(reservas_sin_pagos)} reservas sin pagos:")
            for row in reservas_sin_pagos:
                print(f"      Reserva #{row['id']} - {row['nombre']} - Hab: {row['habitacion']}")
        else:
            print("   ✅ Todas las reservas tienen pagos vinculados")
        
        # 5. Verificar pagos sin reservas
        print("\n5. Verificando pagos sin reservas...")
        
        cursor.execute("""
            SELECT p.id, p.monto, p.reserva_id
            FROM pagos p
            WHERE NOT EXISTS (SELECT 1 FROM reservas r WHERE r.id = p.reserva_id)
        """)
        
        pagos_sin_reservas = cursor.fetchall()
        
        if pagos_sin_reservas:
            print(f"   ⚠️  {len(pagos_sin_reservas)} pagos sin reservas:")
            for row in pagos_sin_reservas:
                print(f"      Pago #{row['id']} - ${row['monto']} - Reserva ID: {row['reserva_id']}")
        else:
            print("   ✅ Todos los pagos están vinculados a reservas")
        
        # 6. Estadísticas de estados
        print("\n6. Estadísticas de estados...")
        
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM pagos
            GROUP BY estado
        """)
        
        estados_pagos = cursor.fetchall()
        for estado in estados_pagos:
            print(f"   📊 {estado['estado']}: {estado['cantidad']} pagos")
        
        # 7. Verificar integridad referencial
        print("\n7. Verificando integridad referencial...")
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reservas r
            JOIN pagos p ON r.id = p.reserva_id
            WHERE r.precio_total != p.monto
        """)
        
        diferencias_monto = cursor.fetchone()['total']
        if diferencias_monto > 0:
            print(f"   ⚠️  {diferencias_monto} reservas con montos diferentes en pagos")
        else:
            print("   ✅ Todos los montos coinciden entre reservas y pagos")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Prueba completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_pagos_reservas() 