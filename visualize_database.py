#!/usr/bin/env python3
"""
Script para generar un diagrama visual de la estructura de la base de datos
del Programa Sintético NEM
"""

import sqlite3
import os

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

def generate_er_diagram():
    """Genera un diagrama ER de la base de datos"""
    
    if not GRAPHVIZ_AVAILABLE:
        print("⚠️ Graphviz no disponible, saltando diagrama ER")
        return
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    # Crear el diagrama con Graphviz
    dot = graphviz.Digraph(comment='Programa Sintético NEM - Estructura BD')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='filled', fillcolor='lightblue')
    
    # Obtener información de las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    # Para cada tabla, obtener su estructura
    for table in tables:
        table_name = table[0]
        
        # Obtener columnas de la tabla
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Obtener conteo de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # Crear label para la tabla
        label = f"{table_name.upper()}\\n({count} registros)\\l\\l"
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = col[5]
            not_null = col[3]
            
            # Formato de la columna
            col_text = f"{col_name}: {col_type}"
            if is_pk:
                col_text = f"🔑 {col_text}"
            elif not_null:
                col_text = f"• {col_text}"
            else:
                col_text = f"○ {col_text}"
            
            label += f"{col_text}\\l"
        
        # Agregar nodo de la tabla
        fillcolor = 'lightcoral' if table_name == 'pdas' else 'lightblue'
        if table_name == 'contenidos':
            fillcolor = 'lightgreen'
        elif table_name in ['fases', 'campos_formativos', 'grados']:
            fillcolor = 'lightyellow'
            
        dot.node(table_name, label=label, fillcolor=fillcolor)
    
    # Agregar relaciones (foreign keys)
    relationships = [
        ('grados', 'fases', 'fase_id -> id'),
        ('contenidos', 'fases', 'fase_id -> id'),
        ('contenidos', 'campos_formativos', 'campo_formativo_id -> id'),
        ('pdas', 'contenidos', 'contenido_id -> id'),
        ('pdas', 'grados', 'grado_id -> id')
    ]
    
    for from_table, to_table, label in relationships:
        dot.edge(from_table, to_table, label=label, color='blue')
    
    # Guardar el diagrama
    try:
        dot.render('database_structure', format='png', cleanup=True)
        print("✅ Diagrama ER generado: database_structure.png")
    except Exception as e:
        print(f"❌ Error generando diagrama ER: {e}")
        print("💡 Instala graphviz: sudo dnf install graphviz")
        
        # Generar versión en texto
        dot.render('database_structure', format='dot', cleanup=False)
        print("✅ Diagrama DOT generado: database_structure.dot")
    
    conn.close()

def generate_data_summary():
    """Genera un resumen visual de los datos"""
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 RESUMEN VISUAL DE LA BASE DE DATOS")
    print("="*60)
    
    # Resumen por fase
    print("\n🎓 DISTRIBUCIÓN POR FASE:")
    cursor.execute("""
        SELECT 
            f.numero,
            f.nombre,
            COUNT(DISTINCT c.id) as contenidos,
            COUNT(p.id) as pdas,
            GROUP_CONCAT(DISTINCT g.nombre) as grados
        FROM fases f
        LEFT JOIN contenidos c ON f.id = c.fase_id
        LEFT JOIN pdas p ON c.id = p.contenido_id
        LEFT JOIN grados g ON f.id = g.fase_id
        GROUP BY f.id, f.numero, f.nombre
        ORDER BY f.numero
    """)
    
    for row in cursor.fetchall():
        fase_num, fase_nombre, contenidos, pdas, grados = row
        print(f"   Fase {fase_num}: {contenidos:3d} contenidos, {pdas:4d} PDAs")
        print(f"           Grados: {grados}")
        print()
    
    # Resumen por campo formativo
    print("📚 DISTRIBUCIÓN POR CAMPO FORMATIVO:")
    cursor.execute("""
        SELECT 
            cf.nombre,
            COUNT(DISTINCT c.id) as contenidos,
            COUNT(p.id) as pdas,
            COUNT(DISTINCT c.fase_id) as fases_con_datos
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id
        LEFT JOIN pdas p ON c.id = p.contenido_id
        GROUP BY cf.id, cf.nombre
        ORDER BY contenidos DESC
    """)
    
    for row in cursor.fetchall():
        campo, contenidos, pdas, fases = row
        print(f"   📖 {campo}")
        print(f"      {contenidos:3d} contenidos, {pdas:4d} PDAs en {fases} fases")
        print()
    
    # Matriz fase x campo
    print("📋 MATRIZ FASE x CAMPO FORMATIVO (Contenidos):")
    print("     " + "".join(f"{'Fase ' + str(i):>8}" for i in [3,4,5]))
    
    cursor.execute("""
        SELECT 
            cf.nombre,
            SUM(CASE WHEN f.numero = 3 THEN 1 ELSE 0 END) as fase3,
            SUM(CASE WHEN f.numero = 4 THEN 1 ELSE 0 END) as fase4,
            SUM(CASE WHEN f.numero = 5 THEN 1 ELSE 0 END) as fase5
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id
        LEFT JOIN fases f ON c.fase_id = f.id
        GROUP BY cf.id, cf.nombre
        ORDER BY cf.nombre
    """)
    
    for row in cursor.fetchall():
        campo = row[0][:25]  # Truncar nombre si es muy largo
        valores = f"{row[1]:8d}{row[2]:8d}{row[3]:8d}"
        print(f"   {campo:<25} {valores}")
    
    # Estadísticas adicionales
    print(f"\n🔢 ESTADÍSTICAS GENERALES:")
    
    cursor.execute("SELECT COUNT(*) FROM contenidos")
    total_contenidos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pdas")
    total_pdas = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(pda_count) FROM (SELECT COUNT(*) as pda_count FROM pdas GROUP BY contenido_id)")
    avg_pdas_por_contenido = cursor.fetchone()[0] or 0
    
    print(f"   📚 Total contenidos: {total_contenidos}")
    print(f"   📝 Total PDAs: {total_pdas}")
    print(f"   📊 Promedio PDAs por contenido: {avg_pdas_por_contenido:.1f}")
    
    conn.close()

def generate_html_viewer():
    """Genera un visualizador HTML interactivo"""
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Programa Sintético NEM - Base de Datos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #27ae60; margin-top: 30px; }
        .fase { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background: #ecf0f1; }
        .campo { margin: 10px 0; padding: 10px; background: #fff; border-radius: 5px; border: 1px solid #bdc3c7; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #3498db; color: white; padding: 15px; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .table-structure { margin: 20px 0; }
        .table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .table th { background-color: #3498db; color: white; }
        .table tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Programa Sintético - Nueva Escuela Mexicana</h1>
        <h2>Base de Datos Educativa</h2>
        
        <div class="stats">"""
    
    # Obtener estadísticas generales
    cursor.execute("SELECT COUNT(*) FROM contenidos")
    total_contenidos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pdas")
    total_pdas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fases")
    total_fases = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM campos_formativos")
    total_campos = cursor.fetchone()[0]
    
    html_content += f"""
            <div class="stat-card">
                <div class="stat-number">{total_fases}</div>
                <div>Fases</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_campos}</div>
                <div>Campos Formativos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_contenidos}</div>
                <div>Contenidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_pdas}</div>
                <div>PDAs</div>
            </div>
        </div>
        
        <h2>📊 Distribución por Fase</h2>"""
    
    # Obtener datos por fase
    cursor.execute("""
        SELECT 
            f.numero,
            f.nombre,
            f.grados_incluidos,
            COUNT(DISTINCT c.id) as contenidos,
            COUNT(p.id) as pdas
        FROM fases f
        LEFT JOIN contenidos c ON f.id = c.fase_id
        LEFT JOIN pdas p ON c.id = p.contenido_id
        GROUP BY f.id, f.numero, f.nombre, f.grados_incluidos
        ORDER BY f.numero
    """)
    
    for row in cursor.fetchall():
        fase_num, fase_nombre, grados, contenidos, pdas = row
        html_content += f"""
        <div class="fase">
            <h3>🎓 Fase {fase_num} - {grados}</h3>
            <p><strong>{contenidos}</strong> contenidos • <strong>{pdas}</strong> PDAs</p>
        </div>"""
    
    html_content += """
        <h2>📚 Distribución por Campo Formativo</h2>
        <table class="table">
            <tr>
                <th>Campo Formativo</th>
                <th>Contenidos</th>
                <th>PDAs</th>
                <th>Promedio PDAs/Contenido</th>
            </tr>"""
    
    # Datos por campo formativo
    cursor.execute("""
        SELECT 
            cf.nombre,
            COUNT(DISTINCT c.id) as contenidos,
            COUNT(p.id) as pdas
        FROM campos_formativos cf
        LEFT JOIN contenidos c ON cf.id = c.campo_formativo_id
        LEFT JOIN pdas p ON c.id = p.contenido_id
        GROUP BY cf.id, cf.nombre
        ORDER BY contenidos DESC
    """)
    
    for row in cursor.fetchall():
        campo, contenidos, pdas = row
        promedio = round(pdas / contenidos, 1) if contenidos > 0 else 0
        html_content += f"""
            <tr>
                <td>{campo}</td>
                <td>{contenidos}</td>
                <td>{pdas}</td>
                <td>{promedio}</td>
            </tr>"""
    
    html_content += """
        </table>
        
        <h2>🗂️ Estructura de Tablas</h2>
        <div class="table-structure">"""
    
    # Estructura de cada tabla
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        html_content += f"""
            <h3>📋 {table_name.upper()}</h3>
            <table class="table">
                <tr>
                    <th>Columna</th>
                    <th>Tipo</th>
                    <th>PK</th>
                    <th>Not Null</th>
                    <th>Default</th>
                </tr>"""
        
        for col in columns:
            cid, name, col_type, not_null, default_val, pk = col
            pk_icon = "🔑" if pk else ""
            not_null_icon = "✓" if not_null else ""
            default_display = default_val if default_val else ""
            
            html_content += f"""
                <tr>
                    <td>{pk_icon} {name}</td>
                    <td>{col_type}</td>
                    <td>{'✓' if pk else ''}</td>
                    <td>{not_null_icon}</td>
                    <td>{default_display}</td>
                </tr>"""
        
        html_content += "</table>"
    
    html_content += """
        </div>
    </div>
</body>
</html>"""
    
    # Guardar archivo HTML
    with open('database_viewer.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Visualizador HTML generado: database_viewer.html")
    
    conn.close()

def create_simple_schema_view():
    """Crea una vista simple del esquema en texto"""
    
    conn = sqlite3.connect('programa_sintetico_nem.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("🗂️ ESQUEMA DE LA BASE DE DATOS")
    print("="*60)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        
        # Obtener información de la tabla
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f"\n📋 {table_name.upper()} ({count} registros)")
        print("-" * 40)
        
        for col in columns:
            cid, name, col_type, not_null, default_val, pk = col
            
            indicators = []
            if pk:
                indicators.append("🔑 PK")
            if not_null:
                indicators.append("⚠️ NOT NULL")
            if default_val:
                indicators.append(f"DEFAULT: {default_val}")
            
            indicators_str = " | ".join(indicators) if indicators else ""
            print(f"   • {name:<20} {col_type:<15} {indicators_str}")
    
    # Mostrar relaciones
    print(f"\n🔗 RELACIONES:")
    relationships = [
        "grados.fase_id → fases.id",
        "contenidos.fase_id → fases.id", 
        "contenidos.campo_formativo_id → campos_formativos.id",
        "pdas.contenido_id → contenidos.id",
        "pdas.grado_id → grados.id"
    ]
    
    for rel in relationships:
        print(f"   • {rel}")
    
    conn.close()

def main():
    """Función principal"""
    
    print("🎨 GENERADOR DE VISUALIZACIONES DE BD")
    print("Programa Sintético - Nueva Escuela Mexicana")
    print("="*60)
    
    # Verificar que existe la base de datos
    if not os.path.exists('programa_sintetico_nem.db'):
        print("❌ Base de datos no encontrada.")
        return
    
    # Generar todas las visualizaciones
    create_simple_schema_view()
    generate_data_summary()
    generate_html_viewer()
    
    try:
        generate_er_diagram()
    except Exception as e:
        print(f"\n💡 Para generar diagramas ER, instala graphviz:")
        print("   pip install graphviz")
        print("   sudo dnf install graphviz  # En Fedora")
    
    print(f"\n✅ Visualizaciones generadas!")
    print(f"📁 Archivos creados:")
    print(f"   • database_viewer.html - Visualizador web interactivo")
    if os.path.exists('database_structure.png'):
        print(f"   • database_structure.png - Diagrama ER")
    if os.path.exists('database_structure.dot'):
        print(f"   • database_structure.dot - Código Graphviz")

if __name__ == "__main__":
    main()
