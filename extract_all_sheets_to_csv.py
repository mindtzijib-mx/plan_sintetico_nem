#!/usr/bin/env python3
"""
Script para extraer todas las hojas de cálculo de los archivos Excel
de las diferentes fases y convertirlas a CSV individual.
"""

import pandas as pd
import os
import glob
from pathlib import Path

def create_output_directories():
    """Crea los directorios de salida para los archivos CSV"""
    output_dirs = [
        'CSV_Output/Fase_3',
        'CSV_Output/Fase_4', 
        'CSV_Output/Fase_5'
    ]
    
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Directorio creado: {dir_path}")

def get_excel_files():
    """Obtiene la lista de todos los archivos Excel organizados por fase"""
    excel_files = {
        'Fase_3': glob.glob('Fase 3 Excel/*.xl*'),
        'Fase_4': glob.glob('Fase 4 Excel/*.xl*'),
        'Fase_5': glob.glob('Fase 5 Excel/*.xl*')
    }
    return excel_files

def sanitize_filename(filename):
    """Limpia el nombre del archivo para que sea válido en el sistema de archivos"""
    # Reemplaza caracteres problemáticos
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Reemplaza espacios múltiples con uno solo
    filename = ' '.join(filename.split())
    
    return filename

def extract_sheets_from_excel(excel_file, output_dir, fase_name):
    """Extrae todas las hojas de un archivo Excel y las guarda como CSV"""
    print(f"\nProcesando: {excel_file}")
    
    try:
        # Lee el archivo Excel
        excel_data = pd.ExcelFile(excel_file)
        sheet_names = excel_data.sheet_names
        
        print(f"  Hojas encontradas: {len(sheet_names)}")
        for sheet_name in sheet_names:
            print(f"    - {sheet_name}")
        
        # Obtiene el nombre base del archivo sin extensión
        base_name = Path(excel_file).stem
        base_name = sanitize_filename(base_name)
        
        # Procesa cada hoja
        for sheet_name in sheet_names:
            try:
                # Lee la hoja específica
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Crea el nombre del archivo CSV
                sheet_name_clean = sanitize_filename(sheet_name)
                csv_filename = f"{base_name}_{sheet_name_clean}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                
                # Guarda como CSV
                df.to_csv(csv_path, index=False, encoding='utf-8')
                print(f"    ✓ {sheet_name} -> {csv_filename}")
                
            except Exception as e:
                print(f"    ✗ Error procesando hoja '{sheet_name}': {e}")
                
    except Exception as e:
        print(f"  ✗ Error abriendo archivo {excel_file}: {e}")

def main():
    """Función principal"""
    print("=== Extractor de hojas de Excel a CSV ===\n")
    
    # Crear directorios de salida
    create_output_directories()
    
    # Obtener archivos Excel
    excel_files = get_excel_files()
    
    # Procesar cada fase
    for fase, files in excel_files.items():
        print(f"\n--- Procesando {fase} ---")
        if not files:
            print(f"No se encontraron archivos Excel en {fase}")
            continue
            
        output_dir = f"CSV_Output/{fase}"
        
        for excel_file in files:
            extract_sheets_from_excel(excel_file, output_dir, fase)
    
    print(f"\n=== Proceso completado ===")
    print("Los archivos CSV se han guardado en la carpeta 'CSV_Output'")
    
    # Mostrar resumen
    total_csv_files = 0
    for fase in ['Fase_3', 'Fase_4', 'Fase_5']:
        csv_dir = f"CSV_Output/{fase}"
        if os.path.exists(csv_dir):
            csv_count = len(glob.glob(f"{csv_dir}/*.csv"))
            total_csv_files += csv_count
            print(f"  {fase}: {csv_count} archivos CSV")
    
    print(f"\nTotal de archivos CSV creados: {total_csv_files}")

if __name__ == "__main__":
    main()
