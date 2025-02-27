from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
import secrets
import datetime
import logging
import time
import random
import string
import json

load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],  # Adicionado OPTIONS
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Configuração do PostgreSQL para Render
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CHAVES_VALIDAS = []

port = int(os.environ.get("PORT", 5000))

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

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
    logging.info(f"Headers: {dict(request.headers)}")
    logging.info(f"Body: {request.get_data(as_text=True)}")

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
    logging.debug(f"Iniciando geração de key por: {request.json.get('generatedBy')}")
    try:
        data = request.get_json()
        generated_by = data.get('generatedBy')
        quantidade = data.get('quantidade', 1)
        duracao_dias = data.get('duracao_dias', 30)  # Pegando a duração dos dias

        logging.info(f"Tentativa de gerar key por: {generated_by} com duração de {duracao_dias} dias")

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # Verifica se é admin
            cur.execute("""
                SELECT is_admin FROM users 
                WHERE username = %s
            """, (generated_by,))
            
            result = cur.fetchone()
            if not result or not result[0]:
                return jsonify({
                    "success": False,
                    "message": "Apenas administradores podem gerar keys"
                }), 403

            # Gera nova key
            key = f"MGSP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=16))}"
            
            # Calcula a data de expiração baseada na duração informada
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=duracao_dias)

            # Salva no banco incluindo a duração em dias
            cur.execute("""
                INSERT INTO keys (key_value, expiration_date, generated_by, duration_days)
                VALUES (%s, %s, %s, %s)
                RETURNING key_value, duration_days
            """, (key, expiration_date, generated_by, duracao_dias))
            
            key_data = cur.fetchone()
            conn.commit()

            logging.info(f"Key gerada com sucesso: {key} - Duração: {duracao_dias} dias")

            return jsonify({
                "success": True,
                "key": key,
                "duration_days": duracao_dias,
                "expiration_date": expiration_date.strftime("%d/%m/%Y")
            }), 201

        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao gerar key: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Erro ao gerar key"
            }), 500
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    except Exception as e:
        logging.error(f"Erro no endpoint generate_keys: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        key = data.get('key')
        hwid = data.get('hwid')

        if not all([username, password, key, hwid]):
            return jsonify({
                "success": False,
                "message": "Dados incompletos"
            }), 400

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Verifica se a key é válida e não usada
        cur.execute("""
            SELECT id, duration_days, is_used 
            FROM keys 
            WHERE key_value = %s
        """, (key,))
        
        key_data = cur.fetchone()
        if not key_data:
            return jsonify({"success": False, "message": "Key inválida"}), 400

        key_id, duration_days, is_used = key_data

        if is_used:
            return jsonify({"success": False, "message": "Key já utilizada"}), 400

        # Calcula a data de expiração usando a duração da key
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)

        # Insere o usuário com a data de expiração correta
        cur.execute("""
            INSERT INTO users (username, password, hwid, expiration_date)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (username, password, hwid, expiration_date))
        
        user_id = cur.fetchone()[0]

        # Marca a key como usada
        cur.execute("""
            UPDATE keys 
            SET is_used = TRUE, user_id = %s
            WHERE id = %s
        """, (user_id, key_id))
        
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Usuário registrado com sucesso",
            "expiration_date": expiration_date.strftime("%d/%m/%Y")
        }), 201

    except Exception as e:
        logging.error(f"Erro ao registrar usuário: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "message": "Erro interno do servidor"
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
        logging.debug("Conexão com banco de dados estabelecida")
        cur = conn.cursor()
        cur.execute("SELECT data_expiracao FROM users WHERE key_value = %s AND hwid = %s", (key, hwid))

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
    data = request.get_json()
    logging.info(f"Requisição de login recebida: {data}")
    username = data.get('username')
    password = data.get('password')
    hwid = data.get('hwid')

    if not all([username, password, hwid]):
        logging.error("Dados incompletos")
        return jsonify({"success": False, "message": "Dados incompletos"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password, is_admin FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user[0] == password:
        logging.info(f"Login bem-sucedido para usuário: {username}")
        return jsonify({"success": True, "isAdmin": user[1]})
    else:
        logging.error(f"Falha no login para usuário: {username}")
        return jsonify({"success": False, "message": "Usuário ou senha incorretos"}), 401

@app.route('/check_expiration', methods=['POST'])
def check_expiration():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        hwid = data.get('hwid')

        if not all([username, password, hwid]):
            return jsonify({"valid": False, "message": "Dados incompletos"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Verifica usuário e admin status
        cur.execute("""
            SELECT is_admin, expiration_date 
            FROM users 
            WHERE username = %s AND password = %s AND hwid = %s
        """, (username, password, hwid))
        
        user = cur.fetchone()
        
        if not user:
            return jsonify({"valid": False, "message": "Usuário não encontrado"}), 404

        is_admin, expiration_date = user

        # Se for admin, retorna válido
        if is_admin:
            return jsonify({
                "valid": True,
                "isAdmin": True,
                "message": "Conta administrativa"
            }), 200

        # Se não tiver data de expiração
        if not expiration_date:
            return jsonify({
                "valid": False,
                "message": "Data de expiração não encontrada"
            }), 400

        # Calcula dias restantes
        now = datetime.datetime.now()
        remaining = expiration_date - now
        is_valid = expiration_date > now
        # Calcula dias e horas restantes
        remaining_days = remaining.days
        remaining_hours = remaining.seconds // 3600  # Converte segundos para horas

        return jsonify({
            "valid": is_valid,
            "expirationDate": expiration_date.strftime("%d/%m/%Y"),
            "remainingDays": remaining_days,
            "remainingHours": remaining_hours,
            "message": "Licença válida" if is_valid else "Licença expirada"
        }), 200

    except Exception as e:
        logging.error(f"Erro ao verificar expiração: {str(e)}")
        return jsonify({
            "valid": False,
            "message": f"Erro interno: {str(e)}"
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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

# Variáveis globais para armazenar as informações
current_news = "🔔 Bem-vindo ao MilGrau Spoofer"
current_version = "3.1.0"
current_download_url = "https://github.com/MilGrauSpoofer/releases"

@app.route('/check_updates', methods=['POST'])
def check_updates():
    try:
        data = request.get_json()
        client_version = data.get('version')
        
        needs_update = current_version > client_version
        
        return jsonify({
            'success': True,
            'needs_update': needs_update,
            'download_url': current_download_url if needs_update else None,
            'news': current_news
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar updates: {str(e)}'
        }), 500

# Rota para atualizar as informações
@app.route('/admin/update_info', methods=['POST'])
def update_info():
    try:
        data = request.get_json()
        
        # Atualiza variáveis globais
        global current_news, current_version, current_download_url
        
        if 'news' in data:
            current_news = data['news']
        if 'version' in data:
            current_version = data['version']
        if 'download_url' in data:
            current_download_url = data['download_url']
            
        return jsonify({
            'success': True,
            'message': 'Informações atualizadas com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar informações: {str(e)}'
        }), 500

# Rota para atualizar configurações
@app.route('/update_configs', methods=['POST'])
def update_configs():
    try:
        data = request.json
        
        # Verifica autenticação
        user = authenticate_admin(
            data.get('username'),
            data.get('password'),
            data.get('hwid')
        )
        
        if not user:
            return jsonify({
                "success": False,
                "message": "Acesso negado"
            }), 403

        # Atualiza configurações
        configs = {
            "version": data.get('version'),
            "discord_link": data.get('discord_link'),
            "news_message": data.get('news_message')
        }
        
        db.update_configs(configs, data.get('username'))
        
        return jsonify({
            "success": True,
            "message": "Configurações atualizadas com sucesso"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500

@app.route('/get_configs', methods=['GET'])
def get_configs():
    try:
        configs = db.get_configs()
        return jsonify(configs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

def authenticate_admin(username, password, hwid):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT is_admin FROM users 
            WHERE username = %s AND password = %s AND hwid = %s
        """, (username, password, hwid))
        
        result = cur.fetchone()
        return result and result[0]  # Retorna True se o usuário for admin
        
    except Exception as e:
        logging.error(f"Erro na autenticação de admin: {str(e)}")
        return False

if __name__ == '__main__':
    # Modo de desenvolvimento
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # Modo de produção
        app.run(host='0.0.0.0', port=port)
