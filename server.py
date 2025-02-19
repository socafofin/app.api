from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
from datetime import datetime, timedelta, timezone  # <--- Importação correta de timezone
import logging  # Importando o módulo de logging

load_dotenv()

app = Flask(__name__)

# Configuração de Logging (para registrar erros e informações importantes)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = os.environ.get("DATABASE_URL")  # <--- **VERIFIQUE SE ESTE É O DATABASE_URL CORRETO NO RENDER.COM!**

# Endpoint para gerar chaves (ADMINISTRATIVO - PROTEJA ESTE ENDPOINT EM PRODUÇÃO!)
@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    """
    Endpoint para gerar chaves de acesso.
    Apenas para uso administrativo (em produção, reforce a segurança deste endpoint!).
    Agora salva as chaves DIRETAMENTE no banco de dados 'generated_keys'.
    """
    quantidade = request.json.get('quantidade', 1)  # Quantidade padrão é 1 se não for especificado
    duracao_dias = request.json.get('duracao_dias', 30)  # Duração padrão de 30 dias se não for especificado

    # Validação básica dos dados de entrada (boa prática!)
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"success": False, "message": "Quantidade inválida. Deve ser um número inteiro positivo."}), 400
    if not isinstance(duracao_dias, int) or duracao_dias <= 0:
        return jsonify({"success": False, "message": "Duração inválida. Deve ser um número inteiro positivo de dias."}), 400

    chaves_geradas = []
    try:
        conn = psycopg2.connect(DATABASE_URL)  # <--- RECONECTANDO A CADA REQUEST (EM PRODUÇÃO, USAR POOL DE CONEXÕES!)
        cur = conn.cursor()
        for _ in range(quantidade):
            chave = secrets.token_urlsafe(32)
            # Use datetime.datetime.now(timezone.utc) para fuso horário UTC AQUI
            data_expiracao = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=duracao_dias)
            # INSERINDO CHAVE DIRETAMENTE NA TABELA 'generated_keys'
            cur.execute("INSERT INTO generated_keys (access_key, data_geracao, data_expiracao) VALUES (%s, %s, %s)",
                (chave, datetime.datetime.now(timezone.utc), data_expiracao)) # <--- VERIFIQUE SE TEM `timezone.utc` AQUI!
            chaves_geradas.append({"chave": chave, "expira_em": data_expiracao.isoformat()})  # Retornando info de expiração para o cliente (opcional)
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"{quantidade} chaves geradas e salvas no banco de dados com duração de {duracao_dias} dias.")  # Log informativo
        return jsonify({"success": True, "message": f"{quantidade} chaves geradas e salvas no banco de dados com sucesso.", "chaves": chaves_geradas})
    except Exception as e:
        logging.error(f"Erro ao gerar chaves e salvar no banco de dados: {e}")  # Log de ERRO!
        return jsonify({"success": False, "message": f"Erro ao gerar chaves e salvar no banco de dados: {e}"}), 500

@app.route('/register', methods=['POST'])
def register_user():
    """
    Endpoint para registrar um novo usuário.
    Valida a chave de acesso no banco de dados 'generated_keys',
    registra o usuário no banco de dados 'users' e marca a chave como 'usada'.
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

    try:
        conn = psycopg2.connect(DATABASE_URL)  # <--- RECONECTANDO A CADA REQUEST (EM PRODUÇÃO, USAR POOL DE CONEXÕES!)
        cur = conn.cursor()

        # VALIDANDO CHAVE NO BANCO DE DADOS 'generated_keys'
        cur.execute("SELECT data_expiracao, usada FROM generated_keys WHERE access_key = %s", (key,))
        result_chave = cur.fetchone()

        if not result_chave:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Chave de acesso inválida ou não encontrada."}), 401

        data_expiracao_chave, chave_usada = result_chave  # Obtendo data de expiração e status 'usada'

        if chave_usada:
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Chave de acesso já foi utilizada para registro."}), 401

        # Use datetime.datetime.now(timezone.utc) para comparação com fuso horário UTC AQUI
        if datetime.datetime.now(timezone.utc) > data_expiracao_chave:  # <--- Modificado para usar timezone.utc
            cur.close()
            conn.close()
            return jsonify({"success": False, "message": "Chave de acesso expirada."}), 401

        # MARCANDO CHAVE COMO 'USADA' NA TABELA 'generated_keys'
        cur.execute("UPDATE generated_keys SET usada = TRUE WHERE access_key = %s", (key,))

        # REGISTRANDO USUÁRIO NA TABELA 'users'
        # Use datetime.datetime.now(timezone.utc) para data_registro com fuso horário UTC AQUI (opcional, mas consistente)
        cur.execute("INSERT INTO users (access_key, hwid, username, data_registro, data_expiracao) VALUES (%s, %s, %s, %s, %s)",
                (key, hwid, usuario, datetime.datetime.now(timezone.utc), data_expiracao_chave)) # <--- VERIFIQUE SE TEM `timezone.utc` AQUI!

        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Usuário '{usuario}' registrado com HWID '{hwid[:10]}...' usando chave válida '{key[:8]}...'. Chave marcada como 'usada'.")  # Log informativo
        return jsonify({"success": True, "message": "Usuário registrado com sucesso com chave válida!"})

    except Exception as e:
        logging.error(f"Erro ao registrar usuário '{usuario}' no banco de dados: {e}")  # Log de ERRO!
        return jsonify({"success": False, "message": f"Erro ao registrar usuário no banco de dados: {e}"}), 500

@app.route('/validate_key', methods=['POST'])
def validate_key():
    """
    Endpoint para validar a chave/usuário para login.
    Valida os dados de entrada e verifica a validade da chave/usuário no banco de dados 'users'.
    """
    data = request.get_json()
    key = data.get('key')  # Agora 'key' é o 'username' para login
    hwid = data.get('hwid')

    # Validação de dados de entrada (importante para segurança e evitar erros!)
    if not key:
        return jsonify({"success": False, "message": "Nome de usuário (key) não fornecido."}), 400  # Correção para refletir que 'key' é agora username
    if not hwid:
        return jsonify({"success": False, "message": "HWID não fornecido."}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)  # <--- RECONECTANDO A CADA REQUEST (EM PRODUÇÃO, USAR POOL DE CONEXÕES!)
        cur = conn.cursor()
        # Busca usuario POR NOME DE USUARIO (key) e HWID na tabela 'users'
        cur.execute("SELECT data_expiracao FROM users WHERE username = %s AND hwid = %s", (key, hwid))  # BUSCANDO DATA DE EXPIRACAO
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            data_expiracao_db = result[0]  # Data de expiração vinda do banco de dados 'users'
            # Use datetime.datetime.now(timezone.utc) para comparação com fuso horário UTC AQUI
            if datetime.datetime.now(timezone.utc) <= data_expiracao_db:  # <--- Modificado para usar timezone.utc
                logging.info(f"Usuário '{key}' com HWID '{hwid[:10]}...' validado com sucesso.")  # Log de validação bem-sucedida
                return jsonify({"success": True, "message": "Chave/Usuário válido e dentro do prazo!"})
            else:
                logging.warning(f"Chave/Usuário '{key}' com HWID '{hwid[:10]}...' expirado.")  # Log de chave expirada (WARNING)
                return jsonify({"success": False, "message": "Chave/Usuário expirado."}), 401
        else:
            logging.warning(f"Tentativa de login inválida para usuário '{key}' e HWID '{hwid[:10]}...'. Usuário/Chave inválido ou não registrado.")  # Log de login inválido (WARNING)
            return jsonify({"success": False, "message": "Usuário/Chave inválido ou não registrado para este HWID."}), 401

    except Exception as e:
        logging.error(f"Erro ao validar chave/usuário no banco de dados para usuário '{key}' e HWID '{hwid[:10]}...': {e}")  # Log de ERRO!
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
    app.run(host='0.0.0.0', port=5000, debug=True)  # <--- DEBUG MODE ATIVADO (para desenvolvimento). DESATIVE EM PRODUÇÃO (debug=False)!