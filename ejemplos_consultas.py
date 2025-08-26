#!/usr/bin/env python3
"""
Script de ejemplo con consultas útiles para el Programa Sintético NEM
"""

import sqlite3

def consultas_ejemplo():
    """Ejecuta varias consultas de ejemplo útiles"""
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    print("🎯 CONSULTAS DE EJEMPLO - PROGRAMA SINTÉTICO NEM")
    print("="*70)
    
    # 1. Contenidos de Matemáticas/Ciencias
    print("\n🔢 CONTENIDOS RELACIONADOS CON MATEMÁTICAS Y CIENCIAS:")
    cursor.execute("""
        SELECT cf.nombre, c.numero, c.titulo
        FROM contenidos c
        JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
        WHERE c.titulo LIKE '%número%' OR c.titulo LIKE '%matemática%' 
           OR c.titulo LIKE '%medición%' OR c.titulo LIKE '%geométr%'
           OR c.titulo LIKE '%cienc%' OR c.titulo LIKE '%natural%'
        AND c.fase_id = 1
        ORDER BY cf.nombre, c.numero
    """)
    
    for row in cursor.fetchall():
        print(f"📚 {row[0]} - {row[1]:2d}. {row[2]}")
    
    # 2. Progresión de aprendizajes en el cuerpo humano
    print("\n🧠 PROGRESIÓN: CUERPO HUMANO (1° vs 2° grado):")
    cursor.execute("""
        SELECT g.nombre, p.descripcion
        FROM pdas p
        JOIN contenidos c ON p.contenido_id = c.id
        JOIN grados g ON p.grado_id = g.id
        WHERE c.titulo LIKE '%cuerpo humano%' AND c.fase_id = 1
        ORDER BY g.numero, p.numero_pda
    """)
    
    grado_actual = None
    for row in cursor.fetchall():
        if row[0] != grado_actual:
            print(f"\n🎓 {row[0]} GRADO:")
            grado_actual = row[0]
        print(f"   • {row[1]}")
    
    # 3. Contenidos relacionados con tecnología
    print("\n💻 CONTENIDOS RELACIONADOS CON TECNOLOGÍA:")
    cursor.execute("""
        SELECT cf.nombre, c.numero, c.titulo
        FROM contenidos c
        JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
        WHERE c.titulo LIKE '%tecnolog%' OR c.titulo LIKE '%digital%' 
           OR c.titulo LIKE '%internet%' OR c.titulo LIKE '%comunicación%'
        AND c.fase_id = 1
        ORDER BY cf.nombre, c.numero
    """)
    
    for row in cursor.fetchall():
        print(f"📚 {row[0]} - {row[1]:2d}. {row[2]}")
    
    # 4. Estadísticas por campo formativo
    print("\n📊 DISTRIBUCIÓN DE PDAs POR CAMPO Y GRADO:")
    cursor.execute("""
        SELECT 
            cf.nombre,
            g.nombre as grado,
            COUNT(p.id) as num_pdas
        FROM campos_formativos cf
        JOIN contenidos c ON cf.id = c.campo_formativo_id AND c.fase_id = 1
        JOIN pdas p ON c.id = p.contenido_id
        JOIN grados g ON p.grado_id = g.id
        GROUP BY cf.id, g.id
        ORDER BY cf.id, g.numero
    """)
    
    campo_actual = None
    for row in cursor.fetchall():
        if row[0] != campo_actual:
            print(f"\n📚 {row[0]}:")
            campo_actual = row[0]
        print(f"   🎓 {row[1]}: {row[2]} PDAs")
    
    # 5. Contenidos más complejos (por longitud de título)
    print("\n📏 CONTENIDOS MÁS ESPECÍFICOS (por longitud de título):")
    cursor.execute("""
        SELECT cf.nombre, c.numero, c.titulo, LENGTH(c.titulo) as longitud
        FROM contenidos c
        JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
        WHERE c.fase_id = 1
        ORDER BY LENGTH(c.titulo) DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"📚 {row[0]} - {row[1]:2d}. {row[2]} ({row[3]} caracteres)")
    
    conn.close()

if __name__ == "__main__":
    consultas_ejemplo()
