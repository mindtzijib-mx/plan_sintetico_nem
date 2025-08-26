#!/usr/bin/env python3
"""
Script para importar TODAS las fases del Programa Sintético NEM
Procesa Fase 3, 4 y 5 de manera automática
"""

import sqlite3
import xml.etree.ElementTree as ET
import os
import re

def get_shared_strings(shared_strings_path):
    """Extrae las cadenas compartidas del archivo sharedStrings.xml"""
    strings = []
    try:
        tree = ET.parse(shared_strings_path)
        root = tree.getroot()
        
        # Namespace para Excel
        ns = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        for si in root.findall('.//ss:si', ns):
            t_elem = si.find('.//ss:t', ns)
            if t_elem is not None:
                strings.append(t_elem.text or "")
            else:
                strings.append("")
        
        return strings
    except Exception as e:
        print(f"❌ Error leyendo shared strings: {e}")
        return []

def process_worksheet(worksheet_path, shared_strings):
    """Procesa una hoja de cálculo y extrae su contenido"""
    try:
        tree = ET.parse(worksheet_path)
        root = tree.getroot()
        
        ns = {'ws': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        data = []
        for row in root.findall('.//ws:row', ns):
            row_data = []
            for cell in row.findall('.//ws:c', ns):
                cell_type = cell.get('t')
                value_elem = cell.find('.//ws:v', ns)
                
                if value_elem is not None:
                    value = value_elem.text
                    if cell_type == 's' and value.isdigit():  # Es una referencia a shared strings
                        idx = int(value)
                        if idx < len(shared_strings):
                            row_data.append(shared_strings[idx])
                        else:
                            row_data.append(value)
                    else:
                        row_data.append(value)
                else:
                    row_data.append("")
            
            if row_data:  # Solo agregar filas no vacías
                data.append(row_data)
        
        return data
    except Exception as e:
        print(f"❌ Error procesando worksheet: {e}")
        return []

def detectar_campo_formativo(nombre_archivo):
    """Detecta el campo formativo basado en el nombre del archivo"""
    nombre_lower = nombre_archivo.lower()
    
    if 'saberes' in nombre_lower or 'cienti' in nombre_lower:
        return "Saberes y Pensamiento Científico"
    elif 'lenguaj' in nombre_lower:
        return "Lenguajes"
    elif 'humano' in nombre_lower or 'comunitario' in nombre_lower:
        return "De lo Humano y lo Comunitario"
    elif 'ética' in nombre_lower or 'etica' in nombre_lower or 'naturaleza' in nombre_lower:
        return "Ética, Naturaleza y Sociedades"
    else:
        return None

def detectar_fase(nombre_directorio):
    """Detecta el número de fase basado en el nombre del directorio"""
    if 'fase3' in nombre_directorio.lower():
        return 3
    elif 'fase4' in nombre_directorio.lower():
        return 4
    elif 'fase5' in nombre_directorio.lower():
        return 5
    else:
        return None

def detectar_grados_por_fase(fase_numero):
    """Devuelve los grados correspondientes a cada fase"""
    grados_por_fase = {
        3: ['1°', '2°'],
        4: ['3°', '4°'],
        5: ['5°', '6°']
    }
    return grados_por_fase.get(fase_numero, [])

def import_archivo_excel_fase(base_dir, dir_name, fase_numero, campo_formativo_nombre, conn):
    """Importa un archivo Excel de cualquier fase a la base de datos"""
    
    cursor = conn.cursor()
    
    # Obtener IDs necesarios
    cursor.execute("SELECT id FROM fases WHERE numero = ?", (fase_numero,))
    fase_result = cursor.fetchone()
    if not fase_result:
        print(f"❌ No se encontró la fase {fase_numero}")
        return
    fase_id = fase_result[0]
    
    cursor.execute("SELECT id FROM campos_formativos WHERE nombre = ?", (campo_formativo_nombre,))
    campo_result = cursor.fetchone()
    if not campo_result:
        print(f"❌ No se encontró el campo formativo: {campo_formativo_nombre}")
        return
    campo_formativo_id = campo_result[0]
    
    print(f"📁 Procesando Fase {fase_numero}: {campo_formativo_nombre}")
    
    # Rutas importantes
    shared_strings_path = f"{base_dir}/{dir_name}/xl/sharedStrings.xml"
    worksheets_dir = f"{base_dir}/{dir_name}/xl/worksheets"
    
    if not os.path.exists(shared_strings_path):
        print(f"❌ No se encontró {shared_strings_path}")
        return
    
    # Obtener strings compartidas
    shared_strings = get_shared_strings(shared_strings_path)
    
    # 1. Procesar hoja de Contenidos (sheet1.xml)
    contenidos_data = process_worksheet(f"{worksheets_dir}/sheet1.xml", shared_strings)
    
    print(f"   📋 Importando contenidos...")
    contenidos_insertados = 0
    
    for row in contenidos_data[1:]:  # Saltar encabezado
        if len(row) >= 2 and str(row[0]).isdigit():
            numero = int(row[0])
            titulo = row[1]
            
            cursor.execute('''
                INSERT OR IGNORE INTO contenidos (numero, titulo, fase_id, campo_formativo_id)
                VALUES (?, ?, ?, ?)
            ''', (numero, titulo, fase_id, campo_formativo_id))
            
            if cursor.rowcount > 0:
                contenidos_insertados += 1
    
    print(f"   ✅ {contenidos_insertados} contenidos insertados")
    
    # 2. Procesar hoja de PDAs (sheet2.xml) - Todos los PDAs
    pdas_data = process_worksheet(f"{worksheets_dir}/sheet2.xml", shared_strings)
    
    print(f"   📝 Importando PDAs...")
    pdas_insertados = 0
    
    grados_fase = detectar_grados_por_fase(fase_numero)
    
    for row in pdas_data[1:]:  # Saltar encabezado
        if len(row) >= 5 and str(row[0]).isdigit():
            contenido_numero = int(row[0])
            numero_pda = int(row[2]) if str(row[2]).isdigit() else 1
            grado_nombre = row[3]
            descripcion = row[4]
            
            # Verificar que el grado pertenece a esta fase
            if grado_nombre not in grados_fase:
                continue
            
            # Obtener IDs
            cursor.execute('''
                SELECT id FROM contenidos 
                WHERE numero = ? AND fase_id = ? AND campo_formativo_id = ?
            ''', (contenido_numero, fase_id, campo_formativo_id))
            
            contenido_result = cursor.fetchone()
            if not contenido_result:
                continue
            contenido_id = contenido_result[0]
            
            cursor.execute('''
                SELECT id FROM grados WHERE nombre = ? AND fase_id = ?
            ''', (grado_nombre, fase_id))
            
            grado_result = cursor.fetchone()
            if not grado_result:
                continue
            grado_id = grado_result[0]
            
            cursor.execute('''
                INSERT OR IGNORE INTO pdas (numero_pda, descripcion, contenido_id, grado_id)
                VALUES (?, ?, ?, ?)
            ''', (numero_pda, descripcion, contenido_id, grado_id))
            
            if cursor.rowcount > 0:
                pdas_insertados += 1
    
    print(f"   ✅ {pdas_insertados} PDAs insertados")
    
    conn.commit()

def main():
    """Función principal para importar todas las fases"""
    
    # Limpiar base de datos anterior
    print("🗑️ Limpiando datos anteriores...")
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM pdas")
    cursor.execute("DELETE FROM contenidos") 
    conn.commit()
    
    print("🚀 Iniciando importación de TODAS las fases...")
    
    base_dir = "/home/otilio/Documents/Projects/plan_sintetico_nem/extracted"
    
    # Obtener todos los directorios extraídos
    directorios = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    # Agrupar por fase y procesar
    for directorio in sorted(directorios):
        fase_numero = detectar_fase(directorio)
        
        if fase_numero:
            campo_formativo = detectar_campo_formativo(directorio)
            
            if campo_formativo:
                import_archivo_excel_fase(base_dir, directorio, fase_numero, campo_formativo, conn)
            else:
                print(f"⚠️ No se pudo detectar campo formativo para: {directorio}")
        else:
            print(f"⚠️ No se pudo detectar fase para: {directorio}")
    
    # Mostrar estadísticas finales
    print("\n📊 RESUMEN FINAL DE IMPORTACIÓN:")
    
    for fase_num in [3, 4, 5]:
        cursor.execute("""
            SELECT COUNT(DISTINCT c.id) as contenidos, COUNT(p.id) as pdas
            FROM contenidos c
            LEFT JOIN pdas p ON c.id = p.contenido_id
            WHERE c.fase_id = (SELECT id FROM fases WHERE numero = ?)
        """, (fase_num,))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            print(f"   📚 Fase {fase_num}: {result[0]} contenidos, {result[1]} PDAs")
    
    # Estadísticas por campo formativo
    print(f"\n📊 DISTRIBUCIÓN POR CAMPO FORMATIVO:")
    cursor.execute("""
        SELECT 
            cf.nombre,
            SUM(CASE WHEN c.fase_id = (SELECT id FROM fases WHERE numero = 3) THEN 1 ELSE 0 END) as fase3,
            SUM(CASE WHEN c.fase_id = (SELECT id FROM fases WHERE numero = 4) THEN 1 ELSE 0 END) as fase4,
            SUM(CASE WHEN c.fase_id = (SELECT id FROM fases WHERE numero = 5) THEN 1 ELSE 0 END) as fase5
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id
        GROUP BY cf.id, cf.nombre
        ORDER BY cf.id
    """)
    
    for row in cursor.fetchall():
        print(f"   📚 {row[0]}:")
        print(f"      Fase 3: {row[1]} | Fase 4: {row[2]} | Fase 5: {row[3]}")
    
    conn.close()
    print(f"\n✅ Importación de todas las fases completada!")

if __name__ == "__main__":
    main()
