# Programa Sintético - Nueva Escuela Mexicana

## Base de Datos SQLite

### 🗂️ Archivos del proyecto:

1. **`create_database.py`** - Crea la estructura de la base de datos
2. **`import_data.py`** - Importa los datos de los archivos Excel
3. **`consultas.py`** - Interface interactiva para consultas
4. **`ejemplos_consultas.py`** - Consultas de ejemplo predefinidas
5. **`programa_sintetico_nem.db`** - Base de datos SQLite
6. **`webapp/`** - Aplicación web (Flask)

### 🚀 Uso básico:

```bash
# 1. Crear la base de datos (solo la primera vez)
python3 create_database.py

# 2. Importar datos de Fase 3 (solo la primera vez)
python3 import_data.py

# 3. Ejecutar consultas interactivas
python3 consultas.py

# 4. Ver ejemplos de consultas
python3 ejemplos_consultas.py

# 5. Iniciar la aplicación web (opcional)
python3 -m pip install -r requirements.txt
python3 webapp/app.py
```

### 🏗️ Estructura de la base de datos:

```
Fases (3, 4, 5)
├── Campos Formativos (4 constantes)
│   ├── Contenidos (por fase y campo)
│   │   └── PDAs (por contenido y grado)
│   └── Grados (1°-6°, agrupados por fase)
```

### 📊 Datos actuales:

- ✅ **Fase 3** (1° y 2° grado): 80 contenidos, 329 PDAs
- ⏳ **Fase 4** (3° y 4° grado): Pendiente
- ⏳ **Fase 5** (5° y 6° grado): Pendiente

### 🔍 Consultas SQL útiles:

```sql
-- Ver todos los contenidos de un campo formativo
SELECT c.numero, c.titulo
FROM contenidos c
JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
WHERE cf.nombre = 'Lenguajes' AND c.fase_id = 1;

-- Comparar PDAs entre grados
SELECT g.nombre, COUNT(p.id) as num_pdas
FROM pdas p
JOIN grados g ON p.grado_id = g.id
JOIN contenidos c ON p.contenido_id = c.id
WHERE c.fase_id = 1
GROUP BY g.id;

-- Buscar por palabra clave
SELECT cf.nombre, c.titulo, p.descripcion
FROM pdas p
JOIN contenidos c ON p.contenido_id = c.id
JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
WHERE p.descripcion LIKE '%palabra%';
```

### 🛠️ Herramientas instaladas en Fedora:

- ✅ Python 3.13.7
- ✅ SQLite 3.47.2
- ✅ LibreOffice (para conversión de Excel)

### 📈 Próximos pasos:

1. Conseguir archivos de Fase 4 y Fase 5
2. Crear interface web (opcional) ✅ (versión mínima incluida en `webapp/`)
3. Agregar funcionalidades de exportación
4. Crear reportes automatizados
