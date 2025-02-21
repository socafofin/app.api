from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging
import time
# Importe o config do banco
from database.db_config import get_connection

load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

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
    username = data.get('username')
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Verifica se o usuário é admin
        cur.execute("SELECT is_admin FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        
        if not result or not result[0]:
            return jsonify({
                "success": False, 
                "message": "Apenas administradores podem gerar keys"
            }), 403

        # Gera a key
        key = f"MGSP-{secrets.token_hex(8).upper()}"
        expiration = datetime.datetime.now() + datetime.timedelta(days=30)
        
        # Insere a key no banco
        cur.execute("""
            INSERT INTO keys (key, generated_by, expires_at) 
            VALUES (%s, %s, %s)
            RETURNING key
        """, (key, username, expiration))
        
        new_key = cur.fetchone()[0]
        conn.commit()
        
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
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, expira_em, usada FROM keys WHERE chave = %s", (key,))
        chave_info = cur.fetchone()

        if not chave_info:
            return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

        chave_id, expira_em, usada = chave_info

        if usada or datetime.datetime.now() > expira_em:
            return jsonify({"success": False, "message": "Chave de acesso inválida ou expirada."}), 401

        cur.execute("INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)",
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
    chave = data.get('chave')
    usuario = data.get('key')  # Usando 'key' como 'usuario'
    hwid = data.get('hwid')

    if chave == 'invalida':
        return jsonify({'error': 'Chave inválida'}), 400

    if not usuario or not hwid:
        return jsonify({"success": False, "message": "Dados incompletos fornecidos."}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (usuario, hwid))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]
            if datetime.datetime.now() <= data_expiracao_db:
                logging.info(f"Usuário '{usuario}' validado com sucesso.")
                return jsonify({"success": True, "message": "Chave/Usuário válido!"})
            else:
                logging.warning(f"Chave/Usuário '{usuario}' expirado.")
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para usuário '{usuario}'.")
            return jsonify({"success": False, "message": "Usuário/Chave inválido ou não registrado para este HWID."}), 401
    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário: {e}")
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário: {e}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hwid = data.get('hwid')
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT is_admin FROM users WHERE username = %s AND password = %s AND hwid = %s", 
                   (username, password, hwid))
        result = cur.fetchone()
        if result:
            return jsonify({
                "success": True,
                "isAdmin": result[0]
            })
        return jsonify({"success": False, "message": "Credenciais inválidas"}), 401
    finally:
        cur.close()
        conn.close()

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro não tratado: {str(e)}", exc_info=True)
    logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
    if request.get_json():
        logging.error(f"Dados JSON recebidos: {request.get_json()}")
    return jsonify({"success": False, "message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # DESATIVE O DEBUG EM PRODUÇÃO!
