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
CORS(app)

# Configuração do PostgreSQL para Render
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CHAVES_VALIDAS = []

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

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Servidor online!"})

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    logging.debug("Endpoint /generate_keys acessado.")
    quantidade = request.json.get('quantidade', 1)
    duracao_dias = request.json.get('duracao_dias', 30)
    logging.debug(f"Quantidade solicitada: {quantidade}, Duração (dias): {duracao_dias}")

    if not isinstance(quantidade, int) or quantidade <= 0:
        logging.warning("Quantidade inválida fornecida.")
        return jsonify({"success": False, "message": "Quantidade inválida. Deve ser um número inteiro positivo."}), 400
    if not isinstance(duracao_dias, int) or duracao_dias <= 0:
        logging.warning("Duração inválida fornecida.")
        return jsonify({"success": False, "message": "Duração inválida. Deve ser um número inteiro positivo de dias."}), 400

    chaves_geradas = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        for _ in range(quantidade):
            chave = secrets.token_urlsafe(32)
            data_expiracao = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)
            cur.execute("INSERT INTO keys (chave, expira_em) VALUES (%s, %s)", (chave, data_expiracao))
            chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": f"{quantidade} chaves geradas com sucesso.", "chaves": chaves_geradas})
    except Exception as e:
        logging.error(f"Erro ao gerar chaves: {e}")
        return jsonify({"success": False, "message": f"Erro ao gerar chaves: {e}"}), 500

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')
    usuario = data.get('username')

    if not key or not hwid or not usuario:
        return jsonify({"success": False, "message": "Dados incompletos fornecidos."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, expira_em, usada FROM keys WHERE chave = %s", (key,))
        chave_info = cur.fetchone()

        if not chave_info:
            return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

        chave_id, expira_em, usada = chave_info

        if usada or datetime.datetime.now() > expira_em:
            return jsonify({"success": False, "message": "Chave de acesso inválida ou expirada."}), 401

        cur.execute("INSERT INTO users (key, hwid, username, created_at, expires_at) VALUES (%s, %s, %s, %s, %s)",
                    (key, hwid, usuario, datetime.datetime.now(), expira_em))
        cur.execute("UPDATE keys SET hwid = %s, usada = TRUE WHERE id = %s", (hwid, chave_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuário registrado com sucesso!"})
    except Exception as e:
        logging.error(f"Erro ao registrar usuário: {e}")
        return jsonify({"success": False, "message": f"Erro ao registrar usuário: {e}"}), 500

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

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hwid = data.get('hwid')

    if not all([username, password, hwid]):
        logging.warning(f"Tentativa de login com dados incompletos: {data}")
        return jsonify({
            "success": False,
            "message": "Dados incompletos"
        }), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Verifica usuário e senha
        cur.execute("""
            SELECT is_admin, hwid 
            FROM users 
            WHERE username = %s AND password = %s
        """, (username, password))
        
        result = cur.fetchone()
        
        if not result:
            logging.warning(f"Login falhou para usuário: {username}")
            return jsonify({
                "success": False,
                "message": "Usuário ou senha inválidos"
            }), 401

        is_admin, stored_hwid = result

        # Se o HWID ainda não foi registrado, atualize-o
        if not stored_hwid:
            cur.execute("""
                UPDATE users 
                SET hwid = %s 
                WHERE username = %s
            """, (hwid, username))
            conn.commit()
        # Se já existe um HWID, verifique se corresponde
        elif stored_hwid != hwid:
            logging.warning(f"HWID não corresponde para usuário: {username}")
            return jsonify({
                "success": False,
                "message": "Dispositivo não autorizado"
            }), 401

        cur.close()
        conn.close()

        logging.info(f"Login bem sucedido para usuário: {username}")
        return jsonify({
            "success": True,
            "isAdmin": is_admin,
            "username": username
        })

    except Exception as e:
        logging.error(f"Erro no login: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro não tratado: {str(e)}", exc_info=True)
    logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
    if request.get_json():
        logging.error(f"Dados JSON recebidos: {request.get_json()}")
    return jsonify({"success": False, "message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
