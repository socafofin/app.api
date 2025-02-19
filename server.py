from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging  # Importando o módulo de logging

load_dotenv()

app = Flask(__name__)

# Configuração de Logging (para registrar erros e informações importantes)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = os.environ.get("DATABASE_URL") # <--- **VERIFIQUE SE ESTE É O DATABASE_URL CORRETO NO RENDER.COM!**
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

    # Validação básica dos dados de entrada (boa prática!)
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"success": False, "message": "Quantidade inválida. Deve ser um número inteiro positivo."}), 400
    if not isinstance(duracao_dias, int) or duracao_dias <= 0:
        return jsonify({"success": False, "message": "Duração inválida. Deve ser um número inteiro positivo de dias."}), 400

    chaves_geradas = []
    for _ in range(quantidade):
        chave = secrets.token_urlsafe(32)
        data_expiracao = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)
        CHAVES_VALIDAS.append({"chave": chave, "expira_em": data_expiracao})  # <--- ARMAZENANDO NA LISTA IN-MEMORY
        chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})  # Retornando info de expiração para o cliente (opcional)
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
    usuario = data.get('username')  # Usando 'username' agora (consistência com o client.py corrigido)

    # Validação de dados de entrada (importante para segurança e evitar erros!)
    if not key:
        return jsonify({"success": False, "message": "Chave de acesso (key) não fornecida."}), 400
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400
    if not usuario:
        return jsonify({"success": False, "message": "Nome de usuário (username) não fornecido."}), 400

    # VALIDAÇÃO DA CHAVE GERADA PELO SERVIDOR (usando a lista IN-MEMORY)
    chave_valida_encontrada = None
    chave_index = -1 # Inicializando para caso a chave não seja encontrada
    for i, chave_info in enumerate(CHAVES_VALIDAS):
        if chave_info["chave"] == key:
            chave_valida_encontrada = chave_info
            chave_index = i  # Guarda o índice para poder remover depois
            break

    if not chave_valida_encontrada:
        return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

    data_expiracao = chave_valida_encontrada["expira_em"]
    if datetime.datetime.now() > data_expiracao:
        return jsonify({"success": False, "message": "Chave de acesso expirada."}), 401

    # REMOVER CHAVE DA LISTA DE CHAVES VALIDAS APÓS O PRIMEIRO USO (OPCIONAL - CHAVE DE USO ÚNICO)
    if chave_valida_encontrada:  # Verificação extra antes de remover
        CHAVES_VALIDAS.pop(chave_index)  # REMOVENDO DA LISTA IN-MEMORY (CUIDADO! IN-MEMORY É VOLÁTIL!)
        logging.info(f"Chave de acesso (uso único) '{key[:8]}... (expira em {data_expiracao})' usada e removida da lista in-memory.") # Log informativo

    try:
        conn = psycopg2.connect(DATABASE_URL) # <--- RECONECTANDO A CADA REQUEST (EM PRODUÇÃO, USAR POOL DE CONEXÕES!)
        cur = conn.cursor()
        # Agora guarda TAMBÉM a data de expiração e o usuario
        cur.execute("INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)",  # COLUNA 'key' RENOMEADA PARA 'access_key' NO BD!
                    (key, hwid, usuario, datetime.datetime.now(), data_expiracao))  # GUARDANDO DATA DE EXPIRACAO
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Usuário '{usuario}' registrado com HWID '{hwid[:10]}...' usando chave válida '{key[:8]}...'.") # Log informativo de registro
        return jsonify({"success": True, "message": "Usuário registrado com sucesso com chave válida!"})
    except Exception as e:
        logging.error(f"Erro ao registrar usuário '{usuario}' no banco de dados: {e}") # Log de ERRO!
        return jsonify({"success": False, "message": f"Erro ao registrar usuário no banco de dados: {e}"}), 500

@app.route('/validate_key', methods=['POST'])
def validate_key():
    """
    Endpoint para validar a chave/usuário para login.
    Valida os dados de entrada e verifica a validade da chave/usuário no banco de dados.
    """
    data = request.get_json()
    key = data.get('key')  # Agora 'key' é o 'username' para login
    hwid = data.get('hwid')

    # Validação de dados de entrada (importante para segurança e evitar erros!)
    if not key:
        return jsonify({"success": False, "message": "Nome de usuário (key) não fornecido."}), 400 # Correção para refletir que 'key' é agora username
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL) # <--- RECONECTANDO A CADA REQUEST (EM PRODUÇÃO, USAR POOL DE CONEXÕES!)
        cur = conn.cursor()
        # Busca usuario POR NOME DE USUARIO (key) e HWID
        # QUERY CORRIGIDA: Busca na coluna 'username' e 'hwid' e retorna 'data_expiracao'
        cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (key, hwid))  # BUSCANDO DATA DE EXPIRACAO
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]  # Data de expiração vinda do banco de dados
            if datetime.datetime.now() <= data_expiracao_db:  # VERIFICANDO EXPIRACAO
                logging.info(f"Usuário '{key}' com HWID '{hwid[:10]}...' validado com sucesso.") # Log de validação bem-sucedida
                return jsonify({"success": True, "message": "Chave/Usuário válido e dentro do prazo!"})
            else:
                logging.warning(f"Chave/Usuário '{key}' com HWID '{hwid[:10]}...' expirado.") # Log de chave expirada (WARNING)
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para usuário '{key}' e HWID '{hwid[:10]}...'. Usuário/Chave inválido ou não registrado.") # Log de login inválido (WARNING)
            return jsonify({"success": False, "message": "Usuário/Chave inválido ou não registrado para este HWID."}), 401

    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário no banco de dados para usuário '{key}' e HWID '{hwid[:10]}...': {e}") # Log de ERRO!
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário no banco de dados: {e}"}), 500

@app.route('/ping', methods=['GET'])
def ping():
    """
    Endpoint simples para verificar se o servidor está online.
    Retorna um status 'ok' e uma mensagem.
    """
    return jsonify({"status": "ok", "message": "Servidor online!"})

if __name__ == '__main__':
    # **IMPORTANTE:** Em produção, use um WSGI server como Gunicorn ou uWSGI em vez do servidor de desenvolvimento do Flask!
    # Exemplo para Gunicorn: gunicorn --bind 0.0.0.0:5000 server:app
    app.run(host='0.0.0.0', port=5000, debug=True) # <--- DEBUG MODE ATIVADO (para desenvolvimento). DESATIVE EM PRODUÇÃO (debug=False)!