#!/usr/bin/env python3
"""
Script debug para entender por qué no se importan los PDAs
"""

import pandas as pd
import sqlite3
import glob
import os

def test_pda_import():
    """Prueba la importación de PDAs"""
    
    # Archivo de prueba
    test_file = "CSV_Output/Fase_3/FASE 3. Saberes y pensamiento científico_PDAs 1°.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🔍 Analizando: {test_file}")
    
    # Leer el archivo
    df = pd.read_csv(test_file)
    
    print(f"📊 Forma del DataFrame: {df.shape}")
    print(f"📋 Columnas: {list(df.columns)}")
    print(f"🔍 Primeras 3 filas:")
    print(df.head(3))
    
    # Ver cuántos registros únicos de cada columna
    for col in df.columns:
        unique_count = df[col].nunique()
        print(f"   {col}: {unique_count} valores únicos")
    
    # Verificar contenido de la columna grado
    if 'Grado' in df.columns:
        print(f"\n🎓 Grados encontrados: {df['Grado'].unique()}")
    
    # Verificar base de datos
    print(f"\n🗄️ Verificando base de datos...")
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    # Ver contenidos de Saberes y Pensamiento Científico en Fase 3
    cursor.execute("""
        SELECT c.numero, c.titulo 
        FROM contenidos c
        JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
        JOIN fases f ON c.fase_id = f.id
        WHERE cf.nombre = 'Saberes y Pensamiento Científico' AND f.numero = 3
        ORDER BY c.numero
        LIMIT 5
    """)
    
    contenidos = cursor.fetchall()
    print(f"📚 Contenidos en BD: {len(contenidos)}")
    for contenido in contenidos[:3]:
        print(f"   {contenido[0]}: {contenido[1][:50]}...")
    
    # Ver grados para Fase 3
    cursor.execute("""
        SELECT g.id, g.nombre, f.id as fase_id, f.numero as fase_numero
        FROM grados g
        JOIN fases f ON g.fase_id = f.id
        WHERE f.numero = 3
    """)
    
    grados = cursor.fetchall()
    print(f"🎓 Grados en BD para Fase 3: {grados}")
    
    conn.close()

def test_field_matching():
    """Prueba el matching de campos formativos"""
    
    files = glob.glob("CSV_Output/Fase_3/*PDAs*.csv")
    
    print(f"🔍 Archivos de PDAs encontrados: {len(files)}")
    
    from import_from_csv import normalize_campo_name
    
    for file in files[:4]:  # Solo los primeros 4
        filename = os.path.basename(file)
        campo = normalize_campo_name(filename)
        print(f"   {filename} -> {campo}")

if __name__ == "__main__":
    test_pda_import()
    print("\n" + "="*50)
    test_field_matching()
