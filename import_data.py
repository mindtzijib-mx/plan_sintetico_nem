#!/usr/bin/env python3
"""
Script para importar los datos de la Fase 3 del Programa Sintético NEM
Extrae datos de los archivos Excel y los inserta en la base de datos SQLite
"""

import sqlite3
import xml.etree.ElementTree as ET
import os

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
        print(f"Error leyendo shared strings: {e}")
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
        print(f"Error procesando worksheet: {e}")
        return []

def import_archivo_excel(base_dir, dir_name, campo_formativo_nombre, conn):
    """Importa un archivo Excel completo a la base de datos"""
    
    cursor = conn.cursor()
    
    # Obtener IDs necesarios
    cursor.execute("SELECT id FROM fases WHERE numero = 3")
    fase_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM campos_formativos WHERE nombre = ?", (campo_formativo_nombre,))
    campo_formativo_id = cursor.fetchone()[0]
    
    print(f"\n📁 Procesando: {campo_formativo_nombre}")
    
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
    
    print(f"📋 Importando contenidos...")
    contenidos_insertados = 0
    
    for row in contenidos_data[1:]:  # Saltar encabezado
        if len(row) >= 2 and row[0].isdigit():
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
    
    print(f"📝 Importando PDAs...")
    pdas_insertados = 0
    
    for row in pdas_data[1:]:  # Saltar encabezado
        if len(row) >= 5 and row[0].isdigit():
            contenido_numero = int(row[0])
            numero_pda = int(row[2])
            grado_nombre = row[3]
            descripcion = row[4]
            
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
    """Función principal para importar todos los datos"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('programa_sintetico_nem.db')
    
    # Mapeo de directorios a campos formativos
    archivos_mapping = [
        ("FASE_3._Saberes_y_pensamiento_científico", "Saberes y Pensamiento Científico"),
        ("FASE_3._Lengiajes", "Lenguajes"),
        ("FASE_3._De_lo_humano_y__lo_comunitario", "De lo Humano y lo Comunitario"),
        ("FASE_3._Ëtica,_Naturaleza_y_Sociedades", "Ética, Naturaleza y Sociedades")
    ]
    
    base_dir = "/home/otilio/Documents/Projects/plan_sintetico_nem/extracted"
    
    print("🚀 Iniciando importación de datos de la Fase 3...")
    
    for dir_name, campo_formativo_nombre in archivos_mapping:
        import_archivo_excel(base_dir, dir_name, campo_formativo_nombre, conn)
    
    # Mostrar estadísticas finales
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM contenidos WHERE fase_id = 1")
    total_contenidos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pdas WHERE contenido_id IN (SELECT id FROM contenidos WHERE fase_id = 1)")
    total_pdas = cursor.fetchone()[0]
    
    print(f"\n📊 RESUMEN DE IMPORTACIÓN:")
    print(f"   📋 Total contenidos Fase 3: {total_contenidos}")
    print(f"   📝 Total PDAs Fase 3: {total_pdas}")
    
    # Mostrar distribución por campo formativo
    cursor.execute("""
        SELECT cf.nombre, COUNT(c.id) as num_contenidos
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id AND c.fase_id = 1
        GROUP BY cf.id, cf.nombre
        ORDER BY cf.id
    """)
    
    print(f"\n📊 CONTENIDOS POR CAMPO FORMATIVO:")
    for row in cursor.fetchall():
        print(f"   📚 {row[0]}: {row[1]} contenidos")
    
    conn.close()
    print(f"\n✅ Importación completada exitosamente!")

if __name__ == "__main__":
    main()
