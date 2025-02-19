from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
from datetime import datetime, timedelta, timezone
import logging

load_dotenv()

app = Flask(__name__)

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = os.environ.get("DATABASE_URL")

# Rotas
@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    quantidade = request.json.get('quantidade', 1)
    duracao_dias = request.json.get('duracao_dias', 30)

    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"success": False, "message": "Quantidade inválida."}), 400
    if not isinstance(duracao_dias, int) or duracao_dias <= 0:
        return jsonify({"success": False, "message": "Duração inválida."}), 400

    chaves_geradas = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                for _ in range(quantidade):
                    chave = secrets.token_urlsafe(32)
                    data_geracao = datetime.datetime.now(timezone.utc)
                    data_expiracao = data_geracao + timedelta(days=duracao_dias)
                    cur.execute("INSERT INTO generated_keys (access_key, data_geracao, data_expiracao) VALUES (%s, %s, %s)", (chave, data_geracao, data_expiracao))
                    chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})
                conn.commit()
        logging.info(f"{quantidade} chaves geradas.")
        return jsonify({"success": True, "message": f"{quantidade} chaves geradas.", "chaves": chaves_geradas})
    except psycopg2.Error as e:
        logging.error(f"Erro ao gerar chaves: {e}")
        return jsonify({"success": False, "message": f"Erro: {e}"}), 500
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"success": False, "message": "Erro interno."}), 500

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')
    usuario = data.get('username')

    if not key:
        return jsonify({"success": False, "message": "Chave não fornecida."}), 400
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400
    if not usuario:
        return jsonify({"success": False, "message": "Usuário não fornecido."}), 400

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data_expiracao, usada FROM generated_keys WHERE access_key = %s", (key,))
                result_chave = cur.fetchone()

                if not result_chave:
                    return jsonify({"success": False, "message": "Chave inválida."}), 401

                data_expiracao_chave, chave_usada = result_chave

                if chave_usada:
                    return jsonify({"success": False, "message": "Chave já usada."}), 401

                if datetime.datetime.now(timezone.utc) > data_expiracao_chave:
                    return jsonify({"success": False, "message": "Chave expirada."}), 401

                cur.execute("UPDATE generated_keys SET usada = TRUE WHERE access_key = %s", (key,))

                data_registro = datetime.datetime.now(timezone.utc)
                cur.execute("INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)", (key, hwid, usuario, data_registro, data_expiracao_chave))

                conn.commit()
        logging.info(f"Usuário '{usuario}' registrado.")
        return jsonify({"success": True, "message": "Usuário registrado."})
    except psycopg2.Error as e:
        logging.error(f"Erro no registro: {e}")
        return jsonify({"success": False, "message": f"Erro: {e}"}), 500
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"success": False, "message": "Erro interno."}), 500

@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')

    if not key:
        return jsonify({"success": False, "message": "Usuário não fornecido."}), 400
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (key, hwid))
                result = cur.fetchone()

        if result:
            data_expiracao_db = result[0]
            if datetime.datetime.now(timezone.utc) <= data_expiracao_db:
                logging.info(f"Usuário '{key}' validado.")
                return jsonify({"success": True, "message": "Usuário válido."})
            else:
                logging.warning(f"Usuário '{key}' expirado.")
                return jsonify({"success": False, "message": "Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para '{key}' e '{hwid}'.")
            return jsonify({"success": False, "message": "Usuário/HWID inválidos."}), 401
    except psycopg2.Error as e:
        logging.error(f"Erro na validação: {e}")
        return jsonify({"success": False, "message": f"Erro: {e}"}), 500
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"success": False, "message": "Erro interno."}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Servidor online!"})

if __name__ == '__main__':
    # Verifique se a variável de ambiente FLASK_ENV está definida como 'development'
    if os.environ.get("FLASK_ENV") == "development":