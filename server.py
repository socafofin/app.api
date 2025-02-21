from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging
import time

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
    data = request.get_json()
    generated_by = data.get('generatedBy')
    quantidade = data.get('quantidade', 1)
    duracao_dias = data.get('duracao_dias', 30)

    logging.info(f"Tentativa de gerar key por: {generated_by}")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Verifica se o usuário é admin
        cur.execute("SELECT is_admin FROM users WHERE username = %s", (generated_by,))
        result = cur.fetchone()
        
        if not result or not result[0]:
            logging.warning(f"Usuário não autorizado tentou gerar key: {generated_by}")
            return jsonify({
                "success": False,
                "message": "Apenas administradores podem gerar keys"
            }), 403

        # Gera a key
        key = f"MGSP-{secrets.token_hex(8).upper()}"
        expiration = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)
        
        # Insere a key no banco
        cur.execute("""
            INSERT INTO keys (key, generated_by, expires_at, used) 
            VALUES (%s, %s, %s, FALSE)
            RETURNING key
        """, (key, generated_by, expiration))
        
        new_key = cur.fetchone()[0]
        conn.commit()
        
        logging.info(f"Key gerada com sucesso por {generated_by}: {new_key}")
        
        return jsonify({
            "success": True,
            "message": "Key gerada com sucesso",
            "key": new_key
        }), 201

    except Exception as e:
        logging.error(f"Erro ao gerar key: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao gerar key: {str(e)}"
        }), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')
    usuario = data.get('username')
    password = data.get('password')

    if not all([usuario, password, key, hwid]):
        return jsonify({"success": False, "message": "Dados incompletos fornecidos."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Verifica se a key existe e é válida
        cur.execute("""
            SELECT id, expires_at, used 
            FROM keys 
            WHERE key = %s
        """, (key,))
        
        key_info = cur.fetchone()

        if not key_info:
            return jsonify({"success": False, "message": "Key de ativação inválida."}), 401

        key_id, expires_at, used = key_info

        if used:
            return jsonify({"success": False, "message": "Key já utilizada."}), 401

        if expires_at < datetime.datetime.now():
            return jsonify({"success": False, "message": "Key expirada."}), 401

        # Registra o usuário
        cur.execute("""
            INSERT INTO users (username, password, hwid, created_at) 
            VALUES (%s, %s, %s, %s)
        """, (usuario, password, hwid, datetime.datetime.now()))

        # Marca a key como usada
        cur.execute("""
            UPDATE keys 
            SET used = TRUE, used_by = %s 
            WHERE id = %s
        """, (usuario, key_id))

        conn.commit()
        
        return jsonify({
            "success": True, 
            "message": "Usuário registrado com sucesso!"
        }), 201

    except psycopg2.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Usuário já existe."
        }), 400
    except Exception as e:
        logging.error(f"Erro ao registrar usuário: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao registrar usuário: {str(e)}"
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
        cur = conn.cursor()
        cur.execute("SELECT data_expiracao FROM users WHERE access_key = %s AND hwid = %s", (key, hwid))
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
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        hwid = data.get('hwid')

        if not all([username, password, hwid]):
            return jsonify({
                "success": False,
                "message": "Dados incompletos"
            }), 400

        # Log para debug
        logging.info(f"Tentativa de login - Usuario: {username}, HWID: {hwid}")

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # Verifica usuário
            cur.execute("""
                SELECT id, password, is_admin, hwid 
                FROM users 
                WHERE username = %s
            """, (username,))
            
            result = cur.fetchone()
            
            if not result:
                return jsonify({
                    "success": False,
                    "message": "Usuário não encontrado"
                }), 401

            user_id, stored_password, is_admin, stored_hwid = result

            # Verifica senha
            if stored_password != password:
                return jsonify({
                    "success": False,
                    "message": "Senha incorreta"
                }), 401

            # Verifica/atualiza HWID
            if not stored_hwid:
                cur.execute("""
                    UPDATE users 
                    SET hwid = %s 
                    WHERE id = %s
                """, (hwid, user_id))
                conn.commit()
            elif stored_hwid != hwid:
                return jsonify({
                    "success": False,
                    "message": "Dispositivo não autorizado"
                }), 401

            return jsonify({
                "success": True,
                "isAdmin": is_admin,
                "username": username
            })

        except psycopg2.Error as e:
            logging.error(f"Erro de banco de dados: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Erro interno do servidor"
            }), 500
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    except Exception as e:
        logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
        logging.error(f"Dados JSON recebidos: {data}")
        logging.error(f"Erro no login: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro interno do servidor: {str(e)}"
        }), 500

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
