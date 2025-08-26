#!/usr/bin/env python3
"""
Script MEJORADO para importar todas las fases desde archivos CSV
Usa los CSV generados por extract_all_sheets_to_csv.py
"""

import sqlite3
import pandas as pd
import os
import glob
from pathlib import Path

def normalize_campo_name(filename):
    """Extrae el campo formativo del nombre del archivo CSV"""
    filename_lower = filename.lower()
    
    if 'saberes' in filename_lower and ('cientifico' in filename_lower or 'científico' in filename_lower):
        return 'Saberes y Pensamiento Científico'
    elif 'lenguajes' in filename_lower or 'lengiajes' in filename_lower:
        return 'Lenguajes'
    elif 'humano' in filename_lower and 'comunitario' in filename_lower:
        return 'De lo Humano y lo Comunitario'
    elif any(word in filename_lower for word in ['etica', 'ética', 'ëtica']) and 'naturaleza' in filename_lower:
        return 'Ética, Naturaleza y Sociedades'
    else:
        return None

def get_grados_por_fase(fase_numero):
    """Retorna los grados válidos para cada fase"""
    return {
        3: ['1°', '2°'],
        4: ['3°', '4°'],
        5: ['5°', '6°']
    }[fase_numero]

def import_contenidos_csv(csv_file, fase_numero, campo_formativo, conn):
    """Importa contenidos desde un archivo CSV de contenidos"""
    cursor = conn.cursor()
    
    # Obtener IDs
    cursor.execute("SELECT id FROM fases WHERE numero = ?", (fase_numero,))
    fase_result = cursor.fetchone()
    if not fase_result:
        print(f"❌ No se encontró la fase {fase_numero}")
        return 0
    fase_id = fase_result[0]
    
    cursor.execute("SELECT id FROM campos_formativos WHERE nombre = ?", (campo_formativo,))
    campo_result = cursor.fetchone()
    if not campo_result:
        print(f"❌ Campo formativo no encontrado: {campo_formativo}")
        return 0
    campo_formativo_id = campo_result[0]
    
    try:
        df = pd.read_csv(csv_file)
        
        # Limpiar el DataFrame
        df = df.dropna(how='all')  # Eliminar filas completamente vacías
        
        contenidos_insertados = 0
        
        # Buscar las columnas correctas basándose en los encabezados
        numero_col = None
        titulo_col = None
        
        for col in df.columns:
            col_str = str(col).lower()
            if 'contenido' in col_str and '#' in col_str:
                numero_col = col
            elif 'título' in col_str or 'titulo' in col_str:
                titulo_col = col
        
        # Si no encontramos por nombres, usar las primeras dos columnas
        if numero_col is None and len(df.columns) >= 1:
            numero_col = df.columns[0]
        if titulo_col is None and len(df.columns) >= 2:
            titulo_col = df.columns[1]
        
        if numero_col is not None and titulo_col is not None:
            for _, row in df.iterrows():
                try:
                    numero_str = str(row[numero_col]).strip()
                    titulo = str(row[titulo_col]).strip()
                    
                    if numero_str.isdigit() and titulo and titulo != 'nan':
                        numero = int(numero_str)
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO contenidos (numero, titulo, fase_id, campo_formativo_id)
                            VALUES (?, ?, ?, ?)
                        ''', (numero, titulo, fase_id, campo_formativo_id))
                        
                        contenidos_insertados += 1
                        
                except Exception as e:
                    continue  # Saltar filas problemáticas
        
        # Hacer commit después de cada archivo
        conn.commit()
        return contenidos_insertados
        
    except Exception as e:
        print(f"❌ Error procesando {csv_file}: {e}")
        return 0

def import_pdas_csv(csv_file, fase_numero, campo_formativo, grado_especifico, conn):
    """Importa PDAs desde un archivo CSV específico de grado"""
    cursor = conn.cursor()
    
    # Obtener IDs
    cursor.execute("SELECT id FROM fases WHERE numero = ?", (fase_numero,))
    fase_result = cursor.fetchone()
    if not fase_result:
        print(f"❌ No se encontró la fase {fase_numero}")
        return 0
    fase_id = fase_result[0]
    
    cursor.execute("SELECT id FROM campos_formativos WHERE nombre = ?", (campo_formativo,))
    campo_result = cursor.fetchone()
    if not campo_result:
        return 0
    campo_formativo_id = campo_result[0]
    
    cursor.execute("SELECT id FROM grados WHERE nombre = ? AND fase_id = ?", (grado_especifico, fase_id))
    grado_result = cursor.fetchone()
    if not grado_result:
        print(f"❌ No se encontró grado {grado_especifico} para fase {fase_numero} (fase_id={fase_id})")
        return 0
    grado_id = grado_result[0]
    
    try:
        df = pd.read_csv(csv_file)
        df = df.dropna(how='all')
        
        pdas_insertados = 0
        
        # Identificar columnas basándose en el formato observado
        contenido_num_col = None
        pda_num_col = None
        grado_col = None
        descripcion_col = None
        
        for col in df.columns:
            col_str = str(col).lower()
            if 'contenido' in col_str and '#' in col_str:
                contenido_num_col = col
            elif 'pda' in col_str and '#' in col_str:
                pda_num_col = col
            elif 'grado' in col_str:
                grado_col = col
            elif 'descripción' in col_str or 'descripcion' in col_str:
                descripcion_col = col
        
        # Si no encontramos por nombres, usar posiciones conocidas
        if contenido_num_col is None and len(df.columns) >= 1:
            contenido_num_col = df.columns[0]
        if pda_num_col is None and len(df.columns) >= 3:
            pda_num_col = df.columns[2]
        if grado_col is None and len(df.columns) >= 4:
            grado_col = df.columns[3]
        if descripcion_col is None and len(df.columns) >= 5:
            descripcion_col = df.columns[4]
        
        if all([contenido_num_col, descripcion_col]):
            for _, row in df.iterrows():
                try:
                    contenido_num_str = str(row[contenido_num_col]).strip()
                    descripcion = str(row[descripcion_col]).strip()
                    
                    # Verificar que es para el grado correcto
                    if grado_col:
                        grado_archivo = str(row[grado_col]).strip()
                        if grado_archivo != grado_especifico:
                            continue
                    
                    if contenido_num_str.isdigit() and descripcion and descripcion != 'nan':
                        contenido_numero = int(contenido_num_str)
                        
                        # Número de PDA (o usar contador)
                        if pda_num_col:
                            numero_pda_str = str(row[pda_num_col]).strip()
                            numero_pda = int(numero_pda_str) if numero_pda_str.isdigit() else pdas_insertados + 1
                        else:
                            numero_pda = pdas_insertados + 1
                        
                        # Buscar el contenido correspondiente
                        cursor.execute('''
                            SELECT id FROM contenidos 
                            WHERE numero = ? AND fase_id = ? AND campo_formativo_id = ?
                        ''', (contenido_numero, fase_id, campo_formativo_id))
                        
                        contenido_result = cursor.fetchone()
                        if contenido_result:
                            contenido_id = contenido_result[0]
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO pdas (numero_pda, descripcion, contenido_id, grado_id)
                                VALUES (?, ?, ?, ?)
                            ''', (numero_pda, descripcion, contenido_id, grado_id))
                            
                            pdas_insertados += 1
                            
                except Exception as e:
                    continue
        
        # Hacer commit después de cada archivo
        conn.commit()
        return pdas_insertados
        
    except Exception as e:
        print(f"❌ Error procesando PDAs en {csv_file}: {e}")
        return 0

def import_fase_from_csv(fase_numero):
    """Importa una fase completa desde archivos CSV"""
    
    print(f"\n🎯 IMPORTANDO FASE {fase_numero}")
    print("="*50)
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    csv_dir = f"CSV_Output/Fase_{fase_numero}"
    
    if not os.path.exists(csv_dir):
        print(f"❌ No se encontró directorio: {csv_dir}")
        conn.close()
        return
    
    # Obtener todos los archivos CSV de la fase
    csv_files = glob.glob(f"{csv_dir}/*.csv")
    
    # Agrupar archivos por campo formativo
    archivos_por_campo = {}
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        campo_formativo = normalize_campo_name(filename)
        
        if campo_formativo:
            if campo_formativo not in archivos_por_campo:
                archivos_por_campo[campo_formativo] = {
                    'contenidos': None,
                    'pdas': {}
                }
            
            if 'contenidos' in filename.lower():
                archivos_por_campo[campo_formativo]['contenidos'] = csv_file
            elif 'pdas' in filename.lower():
                # Identificar el grado específico
                grados_validos = get_grados_por_fase(fase_numero)
                for grado in grados_validos:
                    if grado in filename:
                        archivos_por_campo[campo_formativo]['pdas'][grado] = csv_file
                        break
                else:
                    # Archivo PDA general (sin grado específico en el nombre)
                    archivos_por_campo[campo_formativo]['pdas']['general'] = csv_file
    
    total_contenidos_fase = 0
    total_pdas_fase = 0
    
    # Procesar cada campo formativo
    for campo_formativo, archivos in archivos_por_campo.items():
        print(f"\n📚 {campo_formativo}")
        
        # 1. Importar contenidos
        if archivos['contenidos']:
            contenidos = import_contenidos_csv(
                archivos['contenidos'], 
                fase_numero, 
                campo_formativo, 
                conn
            )
            total_contenidos_fase += contenidos
            print(f"   ✅ {contenidos} contenidos")
        
        # 2. Importar PDAs por grado
        pdas_campo = 0
        grados_validos = get_grados_por_fase(fase_numero)
        
        for grado in grados_validos:
            if grado in archivos['pdas']:
                pdas = import_pdas_csv(
                    archivos['pdas'][grado], 
                    fase_numero, 
                    campo_formativo, 
                    grado, 
                    conn
                )
                pdas_campo += pdas
            elif 'general' in archivos['pdas']:
                # Usar archivo general para este grado
                pdas = import_pdas_csv(
                    archivos['pdas']['general'], 
                    fase_numero, 
                    campo_formativo, 
                    grado, 
                    conn
                )
                pdas_campo += pdas
        
        total_pdas_fase += pdas_campo
        print(f"   ✅ {pdas_campo} PDAs")
    
    print(f"\n📊 Fase {fase_numero} completada: {total_contenidos_fase} contenidos, {total_pdas_fase} PDAs")
    conn.close()

def show_database_summary():
    """Muestra un resumen completo de la base de datos"""
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    print(f"\n📊 RESUMEN FINAL DE LA BASE DE DATOS")
    print("="*60)
    
    # Por fase
    for fase_num in [3, 4, 5]:
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as contenidos, COUNT(p.id) as pdas
            FROM contenidos c
            LEFT JOIN pdas p ON c.id = p.contenido_id
            WHERE c.fase_id = (SELECT id FROM fases WHERE numero = ?)
        """, (fase_num,))
        
        result = cursor.fetchone()
        if result:
            print(f"🎓 Fase {fase_num}: {result[0]} contenidos, {result[1]} PDAs")
    
    # Por campo formativo
    print(f"\n📚 POR CAMPO FORMATIVO:")
    cursor.execute("""
        SELECT cf.nombre, COUNT(DISTINCT c.id) as contenidos, COUNT(p.id) as pdas
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id
        LEFT JOIN pdas p ON c.id = p.contenido_id
        GROUP BY cf.id, cf.nombre
        ORDER BY cf.nombre
    """)
    
    for row in cursor.fetchall():
        print(f"   📖 {row[0]}: {row[1]} contenidos, {row[2]} PDAs")
    
    # Total general
    cursor.execute("SELECT COUNT(*) FROM contenidos")
    total_contenidos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pdas")
    total_pdas = cursor.fetchone()[0]
    
    print(f"\n🎯 TOTAL GENERAL: {total_contenidos} contenidos, {total_pdas} PDAs")
    
    conn.close()

def main():
    """Función principal"""
    
    print("🚀 IMPORTACIÓN COMPLETA DESDE CSV")
    print("Programa Sintético - Nueva Escuela Mexicana")
    print("="*60)
    
    # Verificar que exista la base de datos
    if not os.path.exists('programa_sintetico_nem.db'):
        print("❌ Base de datos no encontrada.")
        print("👉 Ejecuta: python create_database.py")
        return
    
    # Verificar que existan los CSV
    if not os.path.exists('CSV_Output'):
        print("❌ Archivos CSV no encontrados.")
        print("👉 Ejecuta: python extract_all_sheets_to_csv.py")
        return
    
    # Limpiar datos anteriores
    print("🗑️ Limpiando datos anteriores...")
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pdas")
    cursor.execute("DELETE FROM contenidos")
    conn.commit()
    conn.close()
    
    # Importar cada fase
    for fase in [3, 4, 5]:
        import_fase_from_csv(fase)
    
    # Mostrar resumen final
    show_database_summary()
    
    print(f"\n✅ ¡IMPORTACIÓN COMPLETADA EXITOSAMENTE!")
    print("🔍 Ahora puedes usar:")
    print("   • python consultas.py - Para consultas interactivas")
    print("   • python ejemplos_consultas.py - Para ver ejemplos")

if __name__ == "__main__":
    main()
