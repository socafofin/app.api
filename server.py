from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging  # Importando o módulo de logging

load_dotenv()

# Configuração de Logging (para registrar erros e informações importantes)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Definir DATABASE_URL antes de usá-la
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("A variável de ambiente DATABASE_URL não está definida.")

app = Flask(__name__)

# Tentativa de conexão para testar o acesso ao banco de dados
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.close()
    logging.info("Conexão com o banco de dados estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Erro ao conectar ao banco de dados: {e}")

# Lista IN-MEMORY para armazenar chaves válidas geradas (SUBSTITUIR POR BANCO DE DADOS EM PRODUÇÃO!)
CHAVES_VALIDAS = []  # <--- INICIALMENTE VAZIA!

# Endpoint para gerar chaves (ADMINISTRATIVO - PROTEJA ESTE ENDPOINT EM PRODUÇÃO!)
@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    """
    Endpoint para gerar chaves de acesso.
    Apenas para uso administrativo (em produção, reforce a segurança deste endpoint!).
    """
    quantidade = request.json.get('quantidade', 1)  # Quantidade padrão é 1 se não for especificado
    duracao_dias = request.json.get('duracao_dias', 30)  # Duração padrão de 30 dias se não for especificado

    # Validação básica dos dados de entrada
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"success": False, "message": "Quantidade inválida. Deve ser um número inteiro positivo."}), 400
    if not isinstance(duracao_dias, int) or duracao_dias <= 0:
        return jsonify({"success": False, "message": "Duração inválida. Deve ser um número inteiro positivo de dias."}), 400

    chaves_geradas = []
    for _ in range(quantidade):
        chave = secrets.token_urlsafe(32)
        # Utilizando datetime aware em UTC
        data_expiracao = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=duracao_dias)
        CHAVES_VALIDAS.append({"chave": chave, "expira_em": data_expiracao})
        chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})
    return jsonify({"success": True, "message": f"{quantidade} chaves geradas com sucesso.", "chaves": chaves_geradas})

@app.route('/register', methods=['POST'])
def register_user():
    """
    Endpoint para registrar um novo usuário.
    Valida a chave de acesso, dados de entrada e armazena no banco de dados.
    """
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')
    usuario = data.get('username')  # Usando 'username' (consistência com o client.py)

    # Validação de dados de entrada
    if not key:
        return jsonify({"success": False, "message": "Chave de acesso (key) não fornecida."}), 400
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400
    if not usuario:
        return jsonify({"success": False, "message": "Nome de usuário (username) não fornecido."}), 400

    # Validação da chave gerada pelo servidor (usando a lista IN-MEMORY)
    chave_valida_encontrada = None
    chave_index = -1  # Inicializando para caso a chave não seja encontrada
    for i, chave_info in enumerate(CHAVES_VALIDAS):
        if chave_info["chave"] == key:
            chave_valida_encontrada = chave_info
            chave_index = i
            break

    if not chave_valida_encontrada:
        return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

    data_expiracao = chave_valida_encontrada["expira_em"]
    if datetime.datetime.now(pytz.utc) > data_expiracao:
        return jsonify({"success": False, "message": "Chave de acesso expirada."}), 401

    # Remover a chave da lista de chaves válidas após o primeiro uso (chave de uso único)
    if chave_valida_encontrada:
        CHAVES_VALIDAS.pop(chave_index)
        logging.info(f"Chave de acesso (uso único) '{key[:8]}... (expira em {data_expiracao})' usada e removida da lista in-memory.")

    try:
        conn = psycopg2.connect(DATABASE_URL)  # RECONECTANDO a cada request (em produção, usar pool de conexões)
        cur = conn.cursor()
        # Registra também a data de expiração e o usuário
        cur.execute(
            "INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)",
            (key, hwid, usuario, datetime.datetime.now(pytz.utc), data_expiracao)
        )
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Usuário '{usuario}' registrado com HWID '{hwid[:10]}...' usando chave válida '{key[:8]}...'.")
        return jsonify({"success": True, "message": "Usuário registrado com sucesso com chave válida!"})
    except Exception as e:
        logging.error(f"Erro ao registrar usuário '{usuario}' no banco de dados: {e}")
        return jsonify({"success": False, "message": f"Erro ao registrar usuário no banco de dados: {e}"}), 500

@app.route('/validate_key', methods=['POST'])
def validate_key():
    """
    Endpoint para validar a chave/usuário para login.
    Valida os dados de entrada e verifica a validade da chave/usuário no banco de dados.
    """
    data = request.get_json()
    key = data.get('key')  # Aqui 'key' representa o username para login
    hwid = data.get('hwid')

    # Validação de dados de entrada
    if not key:
        return jsonify({"success": False, "message": "Nome de usuário (key) não fornecido."}), 400
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Busca o usuário por username e HWID
        cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (key, hwid))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]  # Data de expiração vinda do banco de dados

            # Certifique-se de que data_expiracao_db é um datetime aware
            if data_expiracao_db.tzinfo is None:
                data_expiracao_db = pytz.utc.localize(data_expiracao_db)

            now_utc = datetime.datetime.now(pytz.utc)

            if now_utc <= data_expiracao_db:
                logging.info(f"Usuário '{key}' com HWID '{hwid[:10]}...' validado com sucesso.")
                return jsonify({"success": True, "message": "Chave/Usuário válido e dentro do prazo!"})
            else:
                logging.warning(f"Chave/Usuário '{key}' com HWID '{hwid[:10]}...' expirado.")
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para usuário '{key}' e HWID '{hwid[:10]}...'.")
            return jsonify({"success": False, "message": "Usuário/Chave inválido ou não registrado para este HWID."}), 401

    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário no banco de dados para usuário '{key}' e HWID '{hwid[:10]}...': {e}")
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário no banco de dados: {e}"}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Servidor online!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
