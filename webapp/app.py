#!/usr/bin/env python3
"""
Aplicación web mínima (Flask) para explorar el Programa Sintético NEM
- Conecta a la base SQLite existente (programa_sintetico_nem.db)
- Páginas: resumen, contenidos por campo, detalle de contenido (PDAs), búsqueda
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional
from flask import Flask, render_template, request, redirect, url_for, abort, jsonify


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'programa_sintetico_nem.db')


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    def get_db() -> sqlite3.Connection:
        if not os.path.exists(DB_PATH):
            abort(500, description=f"No se encontró la base de datos en {DB_PATH}. Ejecuta create_database.py e importa datos.")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_fase_id(conn: sqlite3.Connection, fase_numero: int = 3) -> Optional[int]:
        cur = conn.execute("SELECT id FROM fases WHERE numero = ?", (fase_numero,))
        row = cur.fetchone()
        return row['id'] if row else None

    def get_fase_num(default: int = 3) -> int:
        try:
            return int(request.args.get('fase', str(default)))
        except Exception:
            return default

    @app.context_processor
    def inject_globals():
        # Fases disponibles + fase seleccionada, disponible en todos los templates
        conn = None
        fases = []
        try:
            conn = get_db()
            fases = conn.execute("SELECT numero, nombre FROM fases ORDER BY numero").fetchall()
        except Exception:
            fases = []
        finally:
            if conn:
                conn.close()
        return {
            'fases_lista': fases,
            'fase_actual': get_fase_num(3)
        }

    @app.get('/')
    def index():
        conn = get_db()
        try:
            campos = conn.execute("SELECT id, nombre FROM campos_formativos ORDER BY id").fetchall()
        finally:
            conn.close()
        return render_template('index.html', campos=campos)

    @app.get('/resumen')
    def resumen():
        fase_num = get_fase_num(3)
        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            if not fase_id:
                abort(404, description=f"Fase {fase_num} no encontrada")
            rows = conn.execute(
                """
                SELECT 
                    cf.id as campo_id,
                    cf.nombre as campo_nombre,
                    COUNT(DISTINCT c.id) as num_contenidos,
                    COUNT(p.id) as num_pdas
                FROM campos_formativos cf
                LEFT JOIN contenidos c 
                    ON cf.id = c.campo_formativo_id AND c.fase_id = ?
                LEFT JOIN pdas p 
                    ON c.id = p.contenido_id
                GROUP BY cf.id, cf.nombre
                ORDER BY cf.id
                """,
                (fase_id,)
            ).fetchall()
        finally:
            conn.close()
        return render_template('resumen.html', fase=fase_num, datos=rows)

    @app.get('/contenidos')
    def contenidos_por_campo():
        fase_num = get_fase_num(3)
        campo_id = request.args.get('campo_id')
        if not campo_id:
            return redirect(url_for('index'))

        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            campo = conn.execute("SELECT id, nombre FROM campos_formativos WHERE id = ?", (campo_id,)).fetchone()
            if not campo:
                abort(404, description="Campo formativo no encontrado")
            contenidos = conn.execute(
                """
                SELECT id, numero, titulo
                FROM contenidos
                WHERE campo_formativo_id = ? AND fase_id = ?
                ORDER BY numero
                """,
                (campo_id, fase_id)
            ).fetchall()
        finally:
            conn.close()
        return render_template('contenidos.html', fase=fase_num, campo=campo, contenidos=contenidos)

    @app.get('/contenido/<int:contenido_id>')
    def detalle_contenido(contenido_id: int):
        conn = get_db()
        try:
            contenido = conn.execute(
                """
                SELECT c.id, c.numero, c.titulo, f.numero as fase_num, cf.nombre as campo_nombre
                FROM contenidos c
                JOIN fases f ON c.fase_id = f.id
                JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                WHERE c.id = ?
                """,
                (contenido_id,)
            ).fetchone()
            if not contenido:
                abort(404, description="Contenido no encontrado")

            pdas = conn.execute(
                """
                SELECT g.nombre as grado, p.numero_pda, p.descripcion
                FROM pdas p
                JOIN grados g ON p.grado_id = g.id
                WHERE p.contenido_id = ?
                ORDER BY g.numero, p.numero_pda
                """,
                (contenido_id,)
            ).fetchall()
        finally:
            conn.close()
        return render_template('contenido_detalle.html', contenido=contenido, pdas=pdas)

    @app.get('/buscar')
    def buscar():
        fase_num = get_fase_num(3)
        q = (request.args.get('q') or '').strip()
        contenidos = []
        pdas = []
        if q:
            conn = get_db()
            try:
                fase_id = get_fase_id(conn, fase_num)
                contenidos = conn.execute(
                    """
                    SELECT c.id, cf.nombre as campo, c.numero, c.titulo
                    FROM contenidos c
                    JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                    WHERE c.titulo LIKE ? AND c.fase_id = ?
                    ORDER BY cf.nombre, c.numero
                    """,
                    (f"%{q}%", fase_id)
                ).fetchall()
                pdas = conn.execute(
                    """
                    SELECT c.id as contenido_id, cf.nombre as campo, c.titulo, g.nombre as grado, p.numero_pda, p.descripcion
                    FROM pdas p
                    JOIN contenidos c ON p.contenido_id = c.id
                    JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                    JOIN grados g ON p.grado_id = g.id
                    WHERE p.descripcion LIKE ? AND c.fase_id = ?
                    ORDER BY cf.nombre, c.numero, g.numero, p.numero_pda
                    """,
                    (f"%{q}%", fase_id)
                ).fetchall()
            finally:
                conn.close()
        return render_template('buscar.html', fase=fase_num, q=q, contenidos=contenidos, pdas=pdas)

    # ------------------------
    # API JSON pública (mínima)
    # ------------------------
    @app.get('/api/fases')
    def api_fases():
        conn = get_db()
        try:
            fases = conn.execute("SELECT numero, nombre, descripcion, grados_incluidos FROM fases ORDER BY numero").fetchall()
            return jsonify([
                {
                    'numero': f['numero'],
                    'nombre': f['nombre'],
                    'descripcion': f['descripcion'],
                    'grados_incluidos': f['grados_incluidos'],
                }
                for f in fases
            ])
        finally:
            conn.close()

    @app.get('/api/campos')
    def api_campos():
        conn = get_db()
        try:
            campos = conn.execute("SELECT id, nombre, descripcion FROM campos_formativos ORDER BY id").fetchall()
            return jsonify([
                {
                    'id': c['id'],
                    'nombre': c['nombre'],
                    'descripcion': c['descripcion'],
                }
                for c in campos
            ])
        finally:
            conn.close()

    @app.get('/api/resumen')
    def api_resumen():
        fase_num = get_fase_num(3)
        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            if not fase_id:
                return jsonify({'error': 'fase no encontrada'}), 404
            rows = conn.execute(
                """
                SELECT 
                    cf.id as campo_id,
                    cf.nombre as campo_nombre,
                    COUNT(DISTINCT c.id) as num_contenidos,
                    COUNT(p.id) as num_pdas
                FROM campos_formativos cf
                LEFT JOIN contenidos c 
                    ON cf.id = c.campo_formativo_id AND c.fase_id = ?
                LEFT JOIN pdas p 
                    ON c.id = p.contenido_id
                GROUP BY cf.id, cf.nombre
                ORDER BY cf.id
                """,
                (fase_id,)
            ).fetchall()
            return jsonify([
                {
                    'campo_id': r['campo_id'],
                    'campo_nombre': r['campo_nombre'],
                    'num_contenidos': r['num_contenidos'],
                    'num_pdas': r['num_pdas'],
                }
                for r in rows
            ])
        finally:
            conn.close()

    @app.get('/api/contenidos')
    def api_contenidos_por_campo():
        fase_num = get_fase_num(3)
        campo_id = request.args.get('campo_id', type=int)
        if not campo_id:
            return jsonify({'error': 'campo_id requerido'}), 400
        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            if not fase_id:
                return jsonify({'error': 'fase no encontrada'}), 404
            contenidos = conn.execute(
                """
                SELECT id, numero, titulo
                FROM contenidos
                WHERE campo_formativo_id = ? AND fase_id = ?
                ORDER BY numero
                """,
                (campo_id, fase_id)
            ).fetchall()
            return jsonify([
                {'id': c['id'], 'numero': c['numero'], 'titulo': c['titulo']}
                for c in contenidos
            ])
        finally:
            conn.close()

    @app.get('/api/contenidos/<int:contenido_id>')
    def api_detalle_contenido(contenido_id: int):
        conn = get_db()
        try:
            contenido = conn.execute(
                """
                SELECT c.id, c.numero, c.titulo, f.numero as fase_num, cf.nombre as campo_nombre
                FROM contenidos c
                JOIN fases f ON c.fase_id = f.id
                JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                WHERE c.id = ?
                """,
                (contenido_id,)
            ).fetchone()
            if not contenido:
                return jsonify({'error': 'contenido no encontrado'}), 404
            pdas = conn.execute(
                """
                SELECT g.nombre as grado, p.numero_pda, p.descripcion
                FROM pdas p
                JOIN grados g ON p.grado_id = g.id
                WHERE p.contenido_id = ?
                ORDER BY g.numero, p.numero_pda
                """,
                (contenido_id,)
            ).fetchall()
            return jsonify({
                'id': contenido['id'],
                'numero': contenido['numero'],
                'titulo': contenido['titulo'],
                'fase': contenido['fase_num'],
                'campo': contenido['campo_nombre'],
                'pdas': [
                    {'grado': p['grado'], 'numero_pda': p['numero_pda'], 'descripcion': p['descripcion']}
                    for p in pdas
                ]
            })
        finally:
            conn.close()

    @app.get('/api/buscar')
    def api_buscar():
        fase_num = get_fase_num(3)
        q = (request.args.get('q') or '').strip()
        if not q:
            return jsonify({'contenidos': [], 'pdas': []})
        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            if not fase_id:
                return jsonify({'error': 'fase no encontrada'}), 404
            contenidos = conn.execute(
                """
                SELECT c.id, cf.nombre as campo, c.numero, c.titulo
                FROM contenidos c
                JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                WHERE c.titulo LIKE ? AND c.fase_id = ?
                ORDER BY cf.nombre, c.numero
                """,
                (f"%{q}%", fase_id)
            ).fetchall()
            pdas = conn.execute(
                """
                SELECT c.id as contenido_id, cf.nombre as campo, c.titulo, g.nombre as grado, p.numero_pda, p.descripcion
                FROM pdas p
                JOIN contenidos c ON p.contenido_id = c.id
                JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                JOIN grados g ON p.grado_id = g.id
                WHERE p.descripcion LIKE ? AND c.fase_id = ?
                ORDER BY cf.nombre, c.numero, g.numero, p.numero_pda
                """,
                (f"%{q}%", fase_id)
            ).fetchall()
            return jsonify({
                'contenidos': [
                    {'id': c['id'], 'campo': c['campo'], 'numero': c['numero'], 'titulo': c['titulo']}
                    for c in contenidos
                ],
                'pdas': [
                    {
                        'contenido_id': p['contenido_id'],
                        'campo': p['campo'],
                        'titulo': p['titulo'],
                        'grado': p['grado'],
                        'numero_pda': p['numero_pda'],
                        'descripcion': p['descripcion']
                    }
                    for p in pdas
                ]
            })
        finally:
            conn.close()

    return app


app = create_app()

if __name__ == '__main__':
    # Modo desarrollo
    app.run(host='127.0.0.1', port=8000, debug=True)
