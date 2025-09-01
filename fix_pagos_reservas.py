#!/usr/bin/env python3
"""
Script para corregir la vinculación de pagos con reservas
"""

import sqlite3
from datetime import datetime

def fix_pagos_reservas():
    """Corrige vinculación pagos-reservas"""
    
    print("🔧 Corrigiendo vinculación de pagos con reservas...")
    print("=" * 50)
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('hotel.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Limpiar pagos sin reservas
        print("1. Limpiando pagos sin reservas...")
        
        cursor.execute("""
            DELETE FROM pagos 
            WHERE reserva_id IS NULL OR reserva_id NOT IN (SELECT id FROM reservas)
        """)
        
        pagos_eliminados = cursor.rowcount
        print(f"   🗑️  Eliminados {pagos_eliminados} pagos sin reservas válidas")
        
        # 2. Crear pagos para reservas sin pagos
        print("\n2. Creando pagos para reservas sin pagos...")
        
        cursor.execute("""
            SELECT r.id, r.cliente_id, r.precio_total, r.habitacion
            FROM reservas r
            WHERE NOT EXISTS (SELECT 1 FROM pagos p WHERE p.reserva_id = r.id)
        """)
        
        reservas_sin_pagos = cursor.fetchall()
        
        for reserva in reservas_sin_pagos:
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO pagos (reserva_id, cliente_id, monto, fecha, metodo, estado, referencia, notas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (reserva['id'], reserva['cliente_id'], reserva['precio_total'], fecha_actual, 
                  'Pendiente', 'Pendiente', f'RES-{reserva["id"]}', 
                  f'Pago automático por reserva #{reserva["id"]}'))
        
        print(f"   ✅ Creados {len(reservas_sin_pagos)} pagos para reservas")
        
        # 3. Corregir montos de pagos que no coinciden
        print("\n3. Corrigiendo montos de pagos...")
        
        cursor.execute("""
            SELECT r.id, r.precio_total, p.monto, p.id as pago_id
            FROM reservas r
            JOIN pagos p ON r.id = p.reserva_id
            WHERE r.precio_total != p.monto
        """)
        
        pagos_incorrectos = cursor.fetchall()
        
        for pago in pagos_incorrectos:
            cursor.execute("""
                UPDATE pagos 
                SET monto = ? 
                WHERE id = ?
            """, (pago['precio_total'], pago['pago_id']))
        
        print(f"   ✅ Corregidos {len(pagos_incorrectos)} montos de pagos")
        
        # 4. Actualizar estados de habitaciones
        print("\n4. Actualizando estados de habitaciones...")
        
        cursor.execute("""
            UPDATE habitaciones 
            SET estado = 'Reservada' 
            WHERE numero IN (
                SELECT DISTINCT habitacion 
                FROM reservas 
                WHERE estado IN ('Confirmada', 'Reservada')
            )
        """)
        
        habitaciones_actualizadas = cursor.rowcount
        print(f"   ✅ Actualizadas {habitaciones_actualizadas} habitaciones a 'Reservada'")
        
        # 5. Verificar resultados
        print("\n5. Verificando resultados...")
        
        cursor.execute("SELECT COUNT(*) as total FROM reservas")
        total_reservas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM pagos")
        total_pagos = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reservas r
            JOIN pagos p ON r.id = p.reserva_id
        """)
        reservas_con_pagos = cursor.fetchone()['total']
        
        print(f"   📊 Total reservas: {total_reservas}")
        print(f"   💰 Total pagos: {total_pagos}")
        print(f"   🔗 Reservas con pagos: {reservas_con_pagos}")
        
        if total_reservas == total_pagos and total_reservas == reservas_con_pagos:
            print("   ✅ ¡Perfecto! Todas las reservas tienen pagos vinculados")
        else:
            print("   ⚠️  Aún hay inconsistencias")
        
        # 6. Mostrar resumen final
        print("\n6. Resumen final:")
        
        cursor.execute("""
            SELECT p.estado, COUNT(*) as cantidad
            FROM pagos p
            GROUP BY p.estado
        """)
        
        estados = cursor.fetchall()
        for estado in estados:
            print(f"   📊 {estado['estado']}: {estado['cantidad']} pagos")
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Corrección completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_pagos_reservas() 