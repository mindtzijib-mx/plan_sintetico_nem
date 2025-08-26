#!/usr/bin/env python3
"""
Single Page Application (SPA) para el Programa Sintético NEM
- Conecta a la base SQLite existente (programa_sintetico_nem.db)
- Sirve la SPA en la ruta principal (/)
- Proporciona API JSON endpoints para la funcionalidad AJAX
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional
from flask import Flask, render_template, request, abort, jsonify


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'programa_sintetico_nem.db')


def create_app() -> Flask:
    app = Flask(__name__)

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

    @app.get('/')
    def index():
        """Single Page Application - Página Principal"""
        return render_template('spa.html')

    @app.get('/spa')
    def spa():
        """Single Page Application - Ruta alternativa"""
        return render_template('spa.html')

    # ------------------------
    # API JSON pública (para la SPA)
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

    @app.get('/api/pdas/filtrados')
    def api_pdas_filtrados():
        """Endpoint para obtener PDAs filtrados por fase, campo y opcionalmente contenido"""
        fase_num = get_fase_num(3)
        campo_id = request.args.get('campo_id', type=int)
        contenido_id = request.args.get('contenido_id', type=int)  # Opcional
        
        if not campo_id:
            return jsonify({'error': 'campo_id requerido'}), 400
            
        conn = get_db()
        try:
            fase_id = get_fase_id(conn, fase_num)
            if not fase_id:
                return jsonify({'error': 'fase no encontrada'}), 404
                
            # Query base
            query = """
                SELECT 
                    p.id as pda_id,
                    p.numero_pda,
                    p.descripcion as pda_descripcion,
                    c.id as contenido_id,
                    c.numero as contenido_numero,
                    c.titulo as contenido_titulo,
                    cf.nombre as campo_nombre,
                    g.nombre as grado,
                    g.numero as grado_numero,
                    f.numero as fase_numero
                FROM pdas p
                JOIN contenidos c ON p.contenido_id = c.id
                JOIN campos_formativos cf ON c.campo_formativo_id = cf.id
                JOIN grados g ON p.grado_id = g.id
                JOIN fases f ON c.fase_id = f.id
                WHERE c.campo_formativo_id = ? AND c.fase_id = ?
            """
            params = [campo_id, fase_id]
            
            # Si se especifica un contenido específico
            if contenido_id:
                query += " AND c.id = ?"
                params.append(contenido_id)
                
            query += " ORDER BY c.numero, g.numero, p.numero_pda"
            
            pdas = conn.execute(query, params).fetchall()
            
            return jsonify([
                {
                    'pda_id': p['pda_id'],
                    'numero_pda': p['numero_pda'],
                    'descripcion': p['pda_descripcion'],
                    'contenido': {
                        'id': p['contenido_id'],
                        'numero': p['contenido_numero'],
                        'titulo': p['contenido_titulo']
                    },
                    'campo': p['campo_nombre'],
                    'grado': p['grado'],
                    'grado_numero': p['grado_numero'],
                    'fase': p['fase_numero']
                }
                for p in pdas
            ])
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
