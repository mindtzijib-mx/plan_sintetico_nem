#!/usr/bin/env python3
"""
Script para crear la base de datos del Programa Sintético de la Nueva Escuela Mexicana
Estructura: Fases -> Campos Formativos -> Contenidos -> PDAs por grado
"""

import sqlite3
import os

def create_database():
    """Crea la base de datos y todas las tablas necesarias"""
    
    # Conectar a la base de datos (se crea si no existe)
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    # Crear tablas
    
    # 1. Fases (Fase 3, 4, 5 para primaria)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER UNIQUE NOT NULL,
            nombre VARCHAR(50) NOT NULL,
            descripcion TEXT,
            grados_incluidos VARCHAR(20)
        )
    ''')
    
    # 2. Campos Formativos (constantes para todas las fases)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campos_formativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) UNIQUE NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # 3. Grados (vinculados a fases)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            nombre VARCHAR(10) NOT NULL,
            fase_id INTEGER NOT NULL,
            FOREIGN KEY (fase_id) REFERENCES fases(id),
            UNIQUE(numero, fase_id)
        )
    ''')
    
    # 4. Contenidos (varían por fase y campo formativo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contenidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            fase_id INTEGER NOT NULL,
            campo_formativo_id INTEGER NOT NULL,
            FOREIGN KEY (fase_id) REFERENCES fases(id),
            FOREIGN KEY (campo_formativo_id) REFERENCES campos_formativos(id),
            UNIQUE(numero, fase_id, campo_formativo_id)
        )
    ''')
    
    # 5. PDAs (Procesos de Desarrollo de Aprendizaje)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_pda INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            contenido_id INTEGER NOT NULL,
            grado_id INTEGER NOT NULL,
            FOREIGN KEY (contenido_id) REFERENCES contenidos(id),
            FOREIGN KEY (grado_id) REFERENCES grados(id)
        )
    ''')
    
    # Insertar datos maestros
    
    # Insertar fases
    fases_data = [
        (3, 'Fase 3', 'Educación Primaria - Primeros grados', '1° y 2°'),
        (4, 'Fase 4', 'Educación Primaria - Grados intermedios', '3° y 4°'), 
        (5, 'Fase 5', 'Educación Primaria - Últimos grados', '5° y 6°')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO fases (numero, nombre, descripcion, grados_incluidos)
        VALUES (?, ?, ?, ?)
    ''', fases_data)
    
    # Insertar campos formativos (constantes)
    campos_data = [
        ('Saberes y Pensamiento Científico',),
        ('Lenguajes',),
        ('De lo Humano y lo Comunitario',),
        ('Ética, Naturaleza y Sociedades',)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO campos_formativos (nombre)
        VALUES (?)
    ''', campos_data)
    
    # Insertar grados para cada fase
    grados_data = [
        # Fase 3
        (1, '1°', 3),
        (2, '2°', 3),
        # Fase 4 (para el futuro)
        (3, '3°', 4),
        (4, '4°', 4),
        # Fase 5 (para el futuro)  
        (5, '5°', 5),
        (6, '6°', 5)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO grados (numero, nombre, fase_id)
        VALUES (?, ?, ?)
    ''', grados_data)
    
    # Crear índices para mejorar el rendimiento
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contenidos_fase_campo ON contenidos(fase_id, campo_formativo_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pdas_contenido ON pdas(contenido_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pdas_grado ON pdas(grado_id)')
    
    # Confirmar cambios
    conn.commit()
    
    print("✅ Base de datos creada exitosamente!")
    print("📊 Estructura:")
    print("   - Fases: 3 registros")
    print("   - Campos Formativos: 4 registros") 
    print("   - Grados: 6 registros")
    print("   - Contenidos: (pendiente importación)")
    print("   - PDAs: (pendiente importación)")
    
    return conn

def show_database_info(conn):
    """Muestra información de la base de datos creada"""
    cursor = conn.cursor()
    
    print("\n📋 Información de la base de datos:")
    
    # Mostrar fases
    cursor.execute("SELECT numero, nombre, grados_incluidos FROM fases ORDER BY numero")
    print("\n🔢 FASES:")
    for row in cursor.fetchall():
        print(f"   Fase {row[0]}: {row[1]} ({row[2]})")
    
    # Mostrar campos formativos
    cursor.execute("SELECT id, nombre FROM campos_formativos ORDER BY id")
    print("\n📚 CAMPOS FORMATIVOS:")
    for row in cursor.fetchall():
        print(f"   {row[0]}. {row[1]}")
    
    # Mostrar grados
    cursor.execute("""
        SELECT g.numero, g.nombre, f.numero as fase_num, f.nombre as fase_nombre 
        FROM grados g 
        JOIN fases f ON g.fase_id = f.id 
        ORDER BY g.numero
    """)
    print("\n🎓 GRADOS:")
    for row in cursor.fetchall():
        print(f"   {row[1]} grado - Fase {row[2]} ({row[3]})")

if __name__ == "__main__":
    # Crear la base de datos
    conn = create_database()
    
    # Mostrar información
    show_database_info(conn)
    
    # Cerrar conexión
    conn.close()
    
    print(f"\n💾 Archivo de base de datos creado: programa_sintetico_nem.db")
    print("📁 Ubicación:", os.path.abspath("programa_sintetico_nem.db"))
