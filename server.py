from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging
import time
import random
import string

load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuração do PostgreSQL para Render
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CHAVES_VALIDAS = []

port = int(os.environ.get("PORT", 5000))

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def log_response_time(response):
    duration = time.time() - getattr(request, 'start_time', time.time())
    logging.info(f"Resposta enviada: {response.status} em {duration:.2f} segundos")
    return response

@app.before_request
def log_request_info():
    logging.info(f"Requisição recebida: {request.method} {request.url}")
    logging.info(f"Cabeçalhos: {dict(request.headers)}")
    if request.get_json():
        logging.info(f"Dados JSON: {request.get_json()}")

@app.before_request
def verify_content_type():
    if request.method == "POST":
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Content-Type deve ser application/json"
            }), 415

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Servidor online!"})

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    logging.debug(f"Iniciando geração de key por: {request.json.get('generatedBy')}")
    try:
        data = request.get_json()
        generated_by = data.get('generatedBy')
        quantidade = data.get('quantidade', 1)
        duracao_dias = data.get('duracao_dias', 30)

        logging.info(f"Tentativa de gerar key por: {generated_by}")

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # Verifica se é admin
            cur.execute("""
                SELECT is_admin FROM users 
                WHERE username = %s
            """, (generated_by,))
            
            result = cur.fetchone()
            if not result or not result[0]:
                return jsonify({
                    "success": False,
                    "message": "Apenas administradores podem gerar keys"
                }), 403

            # Gera nova key
            key = f"MGSP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=16))}"
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)

            # Salva no banco (note o uso de key_value ao invés de key)
            cur.execute("""
                INSERT INTO keys (key_value, expiration_date, generated_by)
                VALUES (%s, %s, %s)
                RETURNING key_value
            """, (key, expiration_date, generated_by))
            
            conn.commit()

            return jsonify({
                "success": True,
                "key": key,
                "expiration_date": expiration_date.isoformat()
            }), 201

        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao gerar key: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Erro ao gerar key"
            }), 500
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    except Exception as e:
        logging.error(f"Erro no endpoint generate_keys: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        key = data.get('key')
        hwid = data.get('hwid')

        if not all([username, password, key, hwid]):
            return jsonify({
                "success": False,
                "message": "Dados incompletos"
            }), 400

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Verifica se a key é válida e não usada
        cur.execute("""
            SELECT id, expiration_date, is_used 
            FROM keys 
            WHERE key_value = %s
        """, (key,))
        
        result = cur.fetchone()
        
        if not result:
            return jsonify({
                "success": False,
                "message": "Key inválida"
            }), 400

        key_id, expiration_date, is_used = result

        if is_used:
            return jsonify({
                "success": False,
                "message": "Key já utilizada"
            }), 400

        if datetime.datetime.now() > expiration_date:
            return jsonify({
                "success": False,
                "message": "Key expirada"
            }), 400

        # Insere o novo usuário
        cur.execute("""
            INSERT INTO users (username, password, hwid)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (username, password, hwid))
        
        user_id = cur.fetchone()[0]

        # Marca a key como usada
        cur.execute("""
            UPDATE keys 
            SET is_used = TRUE, user_id = %s
            WHERE id = %s
        """, (user_id, key_id))
        
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Usuário registrado com sucesso"
        }), 201

    except Exception as e:
        logging.error(f"Erro ao registrar usuário: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Erro interno do servidor"
        }), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')

    if not key or not hwid:
        return jsonify({"success": False, "message": "Dados incompletos fornecidos."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        logging.debug("Conexão com banco de dados estabelecida")
        cur = conn.cursor()
        cur.execute("SELECT data_expiracao FROM users WHERE key_value = %s AND hwid = %s", (key, hwid))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]
            if datetime.datetime.now() <= data_expiracao_db:
                return jsonify({"success": True, "message": "Chave/Usuário válido!"})
            else:
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            return jsonify({"success": False, "message": "Usuário/Chave inválido."}), 401
    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário: {e}")
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário: {e}"}), 500

# 1. Modifique a rota de login para corresponder ao client
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hwid = data.get('hwid')

    if not all([username, password, hwid]):
        return jsonify({"success": False, "message": "Dados incompletos"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password, is_admin FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user[0] == password:
        return jsonify({"success": True, "isAdmin": user[1]})
    else:
        return jsonify({"success": False, "message": "Usuário ou senha incorretos"}), 401

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Verifica conexão com banco
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.close()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "message": "Servidor operacional",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0"
        }), 200
    except Exception as e:
        logging.error(f"Erro no health check: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/')
def index():
    return jsonify({
        "name": "MG Spoofer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/login",
            "/api/v1/register",
            "/api/v1/validate_key"
        ]
    })

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro não tratado: {str(e)}", exc_info=True)
    logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
    if request.get_json():
        logging.error(f"Dados JSON recebidos: {request.get_json()}")
    return jsonify({"success": False, "message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    # Modo de desenvolvimento
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # Modo de produção
        app.run(host='0.0.0.0', port=port)
