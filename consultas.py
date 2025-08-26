#!/usr/bin/env python3
"""
Script de consultas para la base de datos del Programa Sintético NEM
Permite realizar consultas comunes y explorar los datos
"""

import sqlite3
import os

def conectar_db():
    """Conecta a la base de datos"""
    return sqlite3.connect('programa_sintetico_nem.db')

def mostrar_menu():
    """Muestra el menú de opciones"""
    print("\n" + "="*60)
    print("🎓 CONSULTAS - PROGRAMA SINTÉTICO NEM")
    print("="*60)
    print("1. 📊 Resumen general")
    print("2. 📚 Ver contenidos por campo formativo")
    print("3. 📝 Ver PDAs por contenido y grado")
    print("4. 🔍 Buscar contenido por palabra clave")
    print("5. 📈 Comparar PDAs entre 1° y 2° grado")
    print("6. 🗃️ Exportar datos a CSV")
    print("7. ⚙️ Consulta SQL personalizada")
    print("0. 🚪 Salir")
    print("="*60)

def resumen_general():
    """Muestra un resumen general de la base de datos"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    print("\n📊 RESUMEN GENERAL:")
    
    # Estadísticas por campo formativo
    cursor.execute("""
        SELECT 
            cf.nombre,
            COUNT(DISTINCT c.id) as num_contenidos,
            COUNT(p.id) as num_pdas
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id AND c.fase_id = 1
        LEFT JOIN pdas p ON c.id = p.contenido_id
        GROUP BY cf.id, cf.nombre
        ORDER BY cf.id
    """)
    
    for row in cursor.fetchall():
        print(f"📚 {row[0]}:")
        print(f"   📋 Contenidos: {row[1]}")
        print(f"   📝 PDAs: {row[2]}")
        print()
    
    conn.close()

def ver_contenidos_por_campo():
    """Muestra contenidos por campo formativo"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Mostrar campos disponibles
    cursor.execute("SELECT id, nombre FROM campos_formativos ORDER BY id")
    campos = cursor.fetchall()
    
    print("\n📚 CAMPOS FORMATIVOS DISPONIBLES:")
    for campo in campos:
        print(f"{campo[0]}. {campo[1]}")
    
    try:
        opcion = int(input("\nSelecciona un campo formativo (1-4): "))
        if 1 <= opcion <= 4:
            cursor.execute("""
                SELECT c.numero, c.titulo
                FROM contenidos c
                WHERE c.campo_formativo_id = ? AND c.fase_id = 1
                ORDER BY c.numero
            """, (opcion,))
            
            print(f"\n📋 CONTENIDOS - {campos[opcion-1][1]}:")
            for row in cursor.fetchall():
                print(f"{row[0]:2d}. {row[1]}")
        else:
            print("❌ Opción inválida")
    except ValueError:
        print("❌ Por favor ingresa un número válido")
    
    conn.close()

def ver_pdas_por_contenido():
    """Muestra PDAs de un contenido específico"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Mostrar campos disponibles
    cursor.execute("SELECT id, nombre FROM campos_formativos ORDER BY id")
    campos = cursor.fetchall()
    
    print("\n📚 CAMPOS FORMATIVOS:")
    for campo in campos:
        print(f"{campo[0]}. {campo[1]}")
    
    try:
        campo_id = int(input("\nSelecciona un campo formativo (1-4): "))
        
        if 1 <= campo_id <= 4:
            # Mostrar contenidos del campo seleccionado
            cursor.execute("""
                SELECT c.id, c.numero, c.titulo
                FROM contenidos c
                WHERE c.campo_formativo_id = ? AND c.fase_id = 1
                ORDER BY c.numero
            """, (campo_id,))
            
            contenidos = cursor.fetchall()
            print(f"\n📋 CONTENIDOS:")
            for contenido in contenidos:
                print(f"{contenido[1]:2d}. {contenido[2][:60]}...")
            
            contenido_num = int(input("\nSelecciona número de contenido: "))
            
            # Buscar el contenido seleccionado
            contenido_seleccionado = None
            for contenido in contenidos:
                if contenido[1] == contenido_num:
                    contenido_seleccionado = contenido
                    break
            
            if contenido_seleccionado:
                # Mostrar PDAs del contenido seleccionado
                cursor.execute("""
                    SELECT g.nombre, p.numero_pda, p.descripcion
                    FROM pdas p
                    JOIN grados g ON p.grado_id = g.id
                    WHERE p.contenido_id = ?
                    ORDER BY g.numero, p.numero_pda
                """, (contenido_seleccionado[0],))
                
                print(f"\n📝 PDAs para: {contenido_seleccionado[2]}")
                print("-" * 80)
                
                for row in cursor.fetchall():
                    print(f"\n🎓 {row[0]} GRADO - PDA #{row[1]}:")
                    print(f"   {row[2]}")
            else:
                print("❌ Contenido no encontrado")
        else:
            print("❌ Opción inválida")
            
    except ValueError:
        print("❌ Por favor ingresa números válidos")
    
    conn.close()

def buscar_por_palabra_clave():
    """Busca contenidos y PDAs por palabra clave"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    palabra = input("\n🔍 Ingresa palabra clave para buscar: ").strip()
    
    if palabra:
        print(f"\n🔍 RESULTADOS PARA: '{palabra}'")
        
        # Buscar en contenidos
        cursor.execute("""
            SELECT cf.nombre, c.numero, c.titulo
            FROM contenidos c
            JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
            WHERE c.titulo LIKE ? AND c.fase_id = 1
            ORDER BY cf.nombre, c.numero
        """, (f"%{palabra}%",))
        
        contenidos_encontrados = cursor.fetchall()
        if contenidos_encontrados:
            print(f"\n📋 CONTENIDOS ENCONTRADOS ({len(contenidos_encontrados)}):")
            for row in contenidos_encontrados:
                print(f"📚 {row[0]} - {row[1]:2d}. {row[2]}")
        
        # Buscar en PDAs
        cursor.execute("""
            SELECT cf.nombre, c.titulo, g.nombre, p.descripcion
            FROM pdas p
            JOIN contenidos c ON p.contenido_id = c.id
            JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
            JOIN grados g ON p.grado_id = g.id
            WHERE p.descripcion LIKE ? AND c.fase_id = 1
            ORDER BY cf.nombre, c.numero, g.numero
        """, (f"%{palabra}%",))
        
        pdas_encontrados = cursor.fetchall()
        if pdas_encontrados:
            print(f"\n📝 PDAs ENCONTRADOS ({len(pdas_encontrados)}):")
            for row in pdas_encontrados:
                print(f"📚 {row[0]} | {row[2]} | {row[1][:40]}...")
                print(f"   📝 {row[3][:100]}...")
                print()
    
    conn.close()

def comparar_grados():
    """Compara PDAs entre 1° y 2° grado para el mismo contenido"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Buscar contenidos que tengan PDAs en ambos grados
    cursor.execute("""
        SELECT DISTINCT c.id, cf.nombre, c.numero, c.titulo
        FROM contenidos c
        JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
        JOIN pdas p1 ON c.id = p1.contenido_id
        JOIN grados g1 ON p1.grado_id = g1.id AND g1.nombre = '1°'
        JOIN pdas p2 ON c.id = p2.contenido_id  
        JOIN grados g2 ON p2.grado_id = g2.id AND g2.nombre = '2°'
        WHERE c.fase_id = 1
        ORDER BY cf.nombre, c.numero
        LIMIT 5
    """)
    
    contenidos = cursor.fetchall()
    
    print(f"\n📈 COMPARACIÓN ENTRE GRADOS (Primeros 5 ejemplos):")
    
    for contenido in contenidos:
        contenido_id, campo_nombre, numero, titulo = contenido
        
        print(f"\n📚 {campo_nombre} - {numero}. {titulo[:50]}...")
        print("-" * 80)
        
        # PDAs de 1° grado
        cursor.execute("""
            SELECT p.descripcion
            FROM pdas p
            JOIN grados g ON p.grado_id = g.id
            WHERE p.contenido_id = ? AND g.nombre = '1°'
            ORDER BY p.numero_pda
        """, (contenido_id,))
        
        pdas_1 = cursor.fetchall()
        
        # PDAs de 2° grado  
        cursor.execute("""
            SELECT p.descripcion
            FROM pdas p
            JOIN grados g ON p.grado_id = g.id
            WHERE p.contenido_id = ? AND g.nombre = '2°'
            ORDER BY p.numero_pda
        """, (contenido_id,))
        
        pdas_2 = cursor.fetchall()
        
        print(f"🎓 1° GRADO ({len(pdas_1)} PDAs):")
        for pda in pdas_1[:2]:  # Solo primeros 2
            print(f"   • {pda[0][:100]}...")
        
        print(f"🎓 2° GRADO ({len(pdas_2)} PDAs):")
        for pda in pdas_2[:2]:  # Solo primeros 2
            print(f"   • {pda[0][:100]}...")
    
    conn.close()

def consulta_personalizada():
    """Permite ejecutar consultas SQL personalizadas"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    print("\n⚙️ CONSULTA SQL PERSONALIZADA")
    print("Tablas disponibles: fases, campos_formativos, contenidos, grados, pdas")
    print("Ejemplo: SELECT COUNT(*) FROM contenidos WHERE fase_id = 1")
    
    consulta = input("\nIngresa tu consulta SQL: ").strip()
    
    if consulta:
        try:
            cursor.execute(consulta)
            
            if consulta.upper().startswith('SELECT'):
                resultados = cursor.fetchall()
                if resultados:
                    # Obtener nombres de columnas
                    columnas = [description[0] for description in cursor.description]
                    
                    print(f"\n📊 RESULTADOS ({len(resultados)} filas):")
                    print(" | ".join(columnas))
                    print("-" * 80)
                    
                    for row in resultados[:10]:  # Limitar a 10 filas
                        print(" | ".join(str(cell)[:20] for cell in row))
                    
                    if len(resultados) > 10:
                        print(f"... y {len(resultados) - 10} filas más")
                else:
                    print("📭 No se encontraron resultados")
            else:
                print(f"✅ Consulta ejecutada. Filas afectadas: {cursor.rowcount}")
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"❌ Error en la consulta: {e}")
    
    conn.close()

def main():
    """Función principal del menú de consultas"""
    
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción (0-7): ").strip()
            
            if opcion == '0':
                print("👋 ¡Hasta luego!")
                break
            elif opcion == '1':
                resumen_general()
            elif opcion == '2':
                ver_contenidos_por_campo()
            elif opcion == '3':
                ver_pdas_por_contenido()
            elif opcion == '4':
                buscar_por_palabra_clave()
            elif opcion == '5':
                comparar_grados()
            elif opcion == '6':
                print("🚧 Función de exportación en desarrollo...")
            elif opcion == '7':
                consulta_personalizada()
            else:
                print("❌ Opción inválida. Por favor selecciona 0-7.")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\n⏸️ Presiona Enter para continuar...")

if __name__ == "__main__":
    # Verificar que existe la base de datos
    if not os.path.exists('programa_sintetico_nem.db'):
        print("❌ No se encontró la base de datos. Ejecuta primero create_database.py e import_data.py")
    else:
        main()
