from flask import Flask, request, jsonify
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
DATABASE_URL = os.environ.get("DATABASE_URL")
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
                logging.info(f"Usuário '{key}' validado com sucesso.")
                return jsonify({"success": True, "message": "Chave/Usuário válido!"})
            else:
                logging.warning(f"Chave/Usuário '{key}' expirado.")
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para usuário '{key}'.")
            return jsonify({"success": False, "message": "Usuário/Chave inválido."}), 401
    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário: {e}")
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário: {e}"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro não tratado: {str(e)}", exc_info=True)
    logging.error(f"Requisição que causou o erro: {request.method} {request.url}")
    if request.get_json():
        logging.error(f"Dados JSON recebidos: {request.get_json()}")
    return jsonify({"success": False, "message": f"Erro interno do servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # DESATIVE O DEBUG EM PRODUÇÃO!
