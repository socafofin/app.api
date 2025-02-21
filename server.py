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

    logging.info(f"Tentativa de login - Username: {username}, HWID: {hwid}")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Primeiro, verifique se o usuário existe
        cur.execute("""
            SELECT id, password, is_admin, hwid 
            FROM users 
            WHERE username = %s
        """, (username,))
        
        result = cur.fetchone()
        
        if not result:
            logging.warning(f"Usuário não encontrado: {username}")
            return jsonify({
                "success": False,
                "message": "Usuário não encontrado"
            }), 401

        user_id, stored_password, is_admin, stored_hwid = result

        # Verifique a senha
        if stored_password != password:
            logging.warning(f"Senha incorreta para usuário: {username}")
            return jsonify({
                "success": False,
                "message": "Senha incorreta"
            }), 401

        # Se o HWID ainda não foi registrado, atualize-o
        if not stored_hwid:
            cur.execute("""
                UPDATE users 
                SET hwid = %s 
                WHERE id = %s
            """, (hwid, user_id))
            conn.commit()
        # Se já existe um HWID, verifique se corresponde
        elif stored_hwid != hwid:
            logging.warning(f"HWID não corresponde - Usuario: {username}, HWID Esperado: {stored_hwid}, HWID Recebido: {hwid}")
            return jsonify({
                "success": False,
                "message": "Dispositivo não autorizado"
            }), 401

        logging.info(f"Login bem sucedido - Usuario: {username}, Admin: {is_admin}")
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
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro não tratado: {str(e)}", exc_info=True)
    logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
    if request.get_json():
        logging.error(f"Dados JSON recebidos: {request.get_json()}")
    return jsonify({"success": False, "message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
