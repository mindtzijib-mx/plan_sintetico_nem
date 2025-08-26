# 📚 Programa Sintético NEM - Single Page Application

Una aplicación web moderna y elegante para explorar los contenidos y Procesos de Desarrollo de Aprendizaje (PDAs) del Programa Sintético de la Nueva Escuela Mexicana.

## 🚀 Características Principales

- ✨ **Single Page Application** - Navegación fluida sin recarga de páginas
- 🔍 **Filtrado Avanzado de PDAs** - Encuentra PDAs por fase, campo formativo y contenido
- 📱 **Diseño Responsive** - Funciona perfectamente en móviles y escritorio
- 🎯 **Filtrado Rápido** - Acceso directo desde la página principal
- 📊 **Resúmenes Estadísticos** - Vista general de contenidos y PDAs por campo
- 🔎 **Búsqueda Global** - Busca en contenidos y descripciones de PDAs

## 🛠️ Tecnologías

- **Backend**: Flask + SQLite
- **Frontend**: JavaScript vanilla + Pico CSS
- **Base de Datos**: SQLite con datos completos de Fases 3, 4 y 5

## 📁 Estructura del Proyecto

```
plan_sintetico_nem/
├── programa_sintetico_nem.db    # Base de datos SQLite
├── app.py                       # Servidor Flask + API endpoints
├── create_database.py           # Esquema y estructura de la BD (referencia)
├── requirements.txt             # Dependencias Python
├── templates/
│   └── spa.html               # Template único de la SPA
├── static/
│   ├── spa.css               # Estilos de la aplicación
│   └── spa.js                # Lógica JavaScript
└── README.md                   # Este archivo
```

## 🚀 Instalación y Uso

### Prerrequisitos

- Python 3.7+
- pip

### Pasos

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/mindtzijib-mx/plan_sintetico_nem.git
   cd plan_sintetico_nem
   ```

2. **Crear entorno virtual** (recomendado)

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   # o
   .venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**

   ```bash
   python app.py
   ```

5. **Abrir en el navegador**
   ```
   http://127.0.0.1:8000/
   ```

## 🎯 Funcionalidades

### 🏠 Página Principal

- **Filtrado Rápido**: Selecciona fase → campo formativo → contenido (opcional)
- **Tarjetas de Campos**: Exploración visual de todos los campos formativos
- **Vista previa de PDAs**: Primeros 5 resultados con opción de ver más

### 📊 Página de Resumen

- Estadísticas por campo formativo
- Contadores de contenidos y PDAs
- Navegación directa a contenidos

### 🔍 Filtrado Completo

- Filtros avanzados por fase y campo
- Resultados detallados de PDAs
- Navegación a contenidos completos

### 🔎 Búsqueda Global

- Búsqueda en títulos de contenidos
- Búsqueda en descripciones de PDAs
- Resultados categorizados

## 🗂️ Estructura de la Base de Datos

```
Fases (3, 4, 5)
├── Campos Formativos (4)
│   ├── 📖 Lenguajes
│   ├── 🧮 Saberes y pensamiento científico
│   ├── 🌍 Ética, Naturaleza y Sociedades
│   └── 👥 De lo humano y lo comunitario
│       ├── Contenidos (por fase y campo)
│       │   └── PDAs (por contenido y grado)
│       └── Grados (1°-6°, agrupados por fase)
```

## 📊 Datos Disponibles

- ✅ **Fase 3** (1° y 2°): Contenidos y PDAs completos
- ✅ **Fase 4** (3° y 4°): Contenidos y PDAs completos
- ✅ **Fase 5** (5° y 6°): Contenidos y PDAs completos

## 🔧 API Endpoints

La aplicación expone los siguientes endpoints JSON:

- `GET /api/campos` - Lista de campos formativos
- `GET /api/fases` - Lista de fases disponibles
- `GET /api/resumen?fase=3` - Estadísticas por fase
- `GET /api/contenidos?campo_id=1&fase=3` - Contenidos filtrados
- `GET /api/contenidos/{id}` - Detalle de contenido con PDAs
- `GET /api/pdas/filtrados?campo_id=1&fase=3` - PDAs filtrados
- `GET /api/buscar?q=texto&fase=3` - Búsqueda global

## 🎨 Características de Diseño

- **Framework CSS**: Pico CSS para un diseño moderno y minimalista
- **Iconos**: Emojis integrados para mejor UX
- **Animaciones**: Transiciones suaves y efectos hover
- **Responsive**: Grid layouts que se adaptan a cualquier pantalla
- **Accesibilidad**: Cumple estándares de accesibilidad web

## 🔍 Consultas SQL de Referencia

```sql
-- Ver todos los contenidos de un campo formativo
SELECT c.numero, c.titulo
FROM contenidos c
JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
WHERE cf.nombre = 'Lenguajes' AND c.fase_id = 1;

-- Contar PDAs por grado
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

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Nueva Escuela Mexicana por el marco pedagógico
- Comunidad de desarrolladores Python y JavaScript
- Pico CSS por el framework de diseño
