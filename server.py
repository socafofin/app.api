import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import secrets
from sqlalchemy.exc import OperationalError
import logging
from cryptography.fernet import Fernet
from flask_sqlalchemy import SQLAlchemy  # Importe SQLAlchemy explicitamente
from models import Key, app, db  # Importa Key, app e db de models.py
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

# Configuração do log
logging.basicConfig(filename='server.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Variáveis de ambiente
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("A variável de ambiente ENCRYPTION_KEY não está definida.")

ENCRYPTION_KEY_ENCODED = ENCRYPTION_KEY.encode()
cipher_suite = Fernet(ENCRYPTION_KEY_ENCODED)

# Configuração do banco de dados PostgreSQL (usando variável de ambiente):
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração SSL para PostgreSQL (Render.com requer conexões seguras)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "sslmode": "require"
    }
}

migrate = Migrate(app, db)  # Inicializa o Migrate aqui - APENAS UMA VEZ

# Rotas
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Servidor está funcionando!"}), 200

@app.route('/gerar_chave', methods=['POST'])
def gerar_chave():
    try:
        data = request.json
        expiration_date = data.get('expiration_date')
        duration_days = data.get('duration_days', None)

        if not expiration_date and not duration_days:
            return jsonify({'success': False, 'message': 'Você deve fornecer uma data de expiração ou duração em dias.'}), 400

        new_key = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(12))

        if expiration_date:
            try:
                expiration_time = datetime.fromisoformat(expiration_date)
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido. Use ISO 8601 (ex.: 2023-12-31T23:59:59).'}), 400
        else:
            expiration_time = datetime.now() + timedelta(days=duration_days)

        new_key_record = Key(key=new_key, hwid="", expiration_time=expiration_time)
        db.session.add(new_key_record)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Chave gerada com sucesso!',
            'key': new_key,
            'expiration_time': expiration_time.strftime('%d/%m/%Y %H:%M:%S')
        }), 200
    except Exception as e:
        print(f"Erro interno: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor.'}), 500

@app.route('/ativar', methods=['POST'])
def ativar():
    try:
        data = request.json
        chave = data.get('key')
        hwid = data.get('hwid')

        if not chave or not hwid:
            return jsonify({"success": False, "message": "Chave ou HWID inválido."}), 400

        key_record = Key.query.filter_by(key=chave).first()
        if not key_record:
            return jsonify({"success": False, "message": "Chave não encontrada."}), 404

        if datetime.now() > key_record.expiration_time:
            return jsonify({"success": False, "message": "Chave expirada."}), 400

        if key_record.hwid:
            return jsonify({"success": False, "message": "Chave já ativada."}), 400

        encrypted_hwid = cipher_suite.encrypt(hwid.encode()).decode()
        key_record.hwid = encrypted_hwid
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Chave ativada com sucesso!",
            "expiration_time": key_record.expiration_time.strftime('%d/%m/%Y %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@app.route('/validar', methods=['POST'])
def validar():
    try:
        data = request.json
        chave = data.get('key')
        hwid = data.get('hwid')

        if not chave or not hwid:
            return jsonify({"success": False, "message": "Chave ou HWID inválido."}), 400

        key_record = Key.query.filter_by(key=chave).first()
        if not key_record:
            return jsonify({"success": False, "message": "Chave não encontrada."}), 404

        if datetime.now() > key_record.expiration_time:
            return jsonify({"success": False, "message": "Chave expirada."}), 400

        decrypted_hwid = cipher_suite.decrypt(key_record.hwid.encode()).decode()

        if decrypted_hwid != hwid:
            return jsonify({"success": False, "message": "HWID não corresponde."}), 400

        return jsonify({"success": True, "message": "Chave válida!"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# Função para verificar a conectividade com o banco de dados
def check_database_connection():
    with app.app_context():
        retries = 5
        for attempt in range(retries):
            try:
                db.engine.connect()
                print("Conexão com o banco de dados estabelecida com sucesso.")
                return True
            except OperationalError as e:
                print(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
                if attempt == retries - 1:
                    print("Falha ao conectar ao banco de dados após várias tentativas.")
                    raise e
            except Exception as e:
                print(f"Erro desconhecido ao conectar ao banco de dados: {str(e)}")
                raise e

if __name__ == '__main__':
    try:
        check_database_connection()
    except Exception as e:
        print(f"Erro crítico: {str(e)}")
        exit(1)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)