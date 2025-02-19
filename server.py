from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL") # <--- **VERIFIQUE SE ESTE É O DATABASE_URL CORRETO NO RENDER.COM!**
# Lista IN-MEMORY para armazenar chaves válidas geradas (SUBSTITUIR POR BANCO DE DADOS EM PRODUÇÃO!)
CHAVES_VALIDAS = []  # <---  INICIALMENTE VAZIA!

# Endpoint para gerar chaves (ADMINISTRATIVO - PROTEJA ESTE ENDPOINT EM PRODUÇÃO!)
@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    quantidade = request.json.get('quantidade', 1)  # Quantidade padrão é 1 se não for especificado
    duracao_dias = request.json.get('duracao_dias', 30)  # Duração padrão de 30 dias se não for especificado
    chaves_geradas = []
    for _ in range(quantidade):
        chave = secrets.token_urlsafe(32)
        data_expiracao = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)
        CHAVES_VALIDAS.append({"chave": chave, "expira_em": data_expiracao})  # <--- ARMAZENANDO NA LISTA IN-MEMORY
        chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})  # Retornando info de expiração para o cliente (opcional)
    return jsonify({"success": True, "message": f"{quantidade} chaves geradas com sucesso.", "chaves": chaves_geradas})

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    key = data.get('key')
    hwid = data.get('hwid')
    usuario = data.get('username')  # Usando 'username' agora (consistência com o client.py corrigido)

    if not key or not hwid or not usuario:
        return jsonify({"success": False, "message": "Dados de registro incompletos."}), 400

    # VALIDAÇÃO DA CHAVE GERADA PELO SERVIDOR
    chave_valida_encontrada = None
    for i, chave_info in enumerate(CHAVES_VALIDAS):
        if chave_info["chave"] == key:
            chave_valida_encontrada = chave_info
            chave_index = i  # Para remover a chave depois de usar (se for uso único)
            break

    if not chave_valida_encontrada:
        return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

    data_expiracao = chave_valida_encontrada["expira_em"]
    if datetime.datetime.now() > data_expiracao:
        return jsonify({"success": False, "message": "Chave de acesso expirada."}), 401

    # REMOVER CHAVE DA LISTA DE CHAVES VALIDAS APÓS O PRIMEIRO USO (OPCIONAL - SE QUISER CHAVE DE USO ÚNICO)
    if chave_valida_encontrada:  # <--- Verificação extra antes de remover
        CHAVES_VALIDAS.pop(chave_index)  # <--- REMOVENDO DA LISTA IN-MEMORY (CUIDADO! IN-MEMORY É VOLÁTIL!)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Agora guarda TAMBÉM a data de expiração e o usuario
        cur.execute("INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)",  # <--- COLUNA 'key' RENOMEADA PARA 'access_key' NO BD!
                    (key, hwid, usuario, datetime.datetime.now(), data_expiracao))  # <--- GUARDANDO DATA DE EXPIRACAO
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuário registrado com sucesso com chave válida!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao registrar usuário no banco de dados: {e}"}), 500

@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    key = data.get('key')  # Agora 'key' é o 'username' para login
    hwid = data.get('hwid')

    if not key or not hwid:
        return jsonify({"success": False, "message": "Dados de login incompletos."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Busca usuario POR NOME DE USUARIO (key) e HWID
        # QUERY CORRIGIDA: Busca na coluna 'username' e 'hwid' e retorna 'data_expiracao'
        cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (key, hwid))  # <--- BUSCANDO DATA DE EXPIRACAO
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]  # Data de expiração vinda do banco de dados
            if datetime.datetime.now() <= data_expiracao_db:  # <--- VERIFICANDO EXPIRACAO
                return jsonify({"success": True, "message": "Chave/Usuário válido e dentro do prazo!"})
            else:
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            return jsonify({"success": False, "message": "Usuário/Chave inválido ou não registrado para este HWID."}), 401

    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao validar chave/usuário no banco de dados: {e}"}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Servidor online!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)