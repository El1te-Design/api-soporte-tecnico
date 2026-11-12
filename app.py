import os
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "servicio": "API Gestion de Solicitudes de Soporte Tecnico"
    }), 200

# Registrar nueva solicitud (POST)
@app.route('/api/solicitudes', methods=['POST'])
def crear_solicitud():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "El cuerpo de la peticion debe ser JSON valido"}), 400

    campos_requeridos = [
        'folio',
        'nombre_solicitante',
        'correo_solicitante',
        'categoria',
        'prioridad',
        'descripcion'
    ]
    
    faltantes = [c for c in campos_requeridos if not data.get(c)]
    if faltantes:
        return jsonify({"error": f"Faltan campos obligatorios: {', '.join(faltantes)}"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                INSERT INTO solicitudes (
                    folio, nombre_solicitante, correo_solicitante, categoria, prioridad, descripcion
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *;
            """
            cur.execute(query, (
                data['folio'].strip(),
                data['nombre_solicitante'].strip(),
                data['correo_solicitante'].strip(),
                data['categoria'].strip(),
                data['prioridad'].strip(),
                data['descripcion'].strip()
            ))
            nueva_solicitud = cur.fetchone()
        conn.commit()
        return jsonify({
            "mensaje": "Solicitud registrada correctamente",
            "data": nueva_solicitud
        }), 201
    except psycopg.errors.UniqueViolation:
        if conn:
            conn.rollback()
        return jsonify({"error": f"El folio '{data['folio']}' ya existe"}), 409
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Consultar todas las solicitudes (GET)
@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM solicitudes ORDER BY fecha_registro DESC;")
            solicitudes = cur.fetchall()
        return jsonify(solicitudes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Consultar una solicitud especifica por folio (GET)
@app.route('/api/solicitudes/<folio>', methods=['GET'])
def obtener_solicitud_por_folio(folio):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM solicitudes WHERE folio = %s;", (folio,))
            solicitud = cur.fetchone()
        if not solicitud:
            return jsonify({"error": "Folio no encontrado"}), 404
        return jsonify(solicitud), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
