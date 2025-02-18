import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging
from werkzeug.security import generate_password_hash  # Importe para hashear a senha

from models import db, User, Key  # Importe seus modelos
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

# Configuração do log
logging.basicConfig(filename='server.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
                    format='%(asctime)s - %(levelname)s - %(message)s'

# Variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")  # Recupera o valor

if not DATABASE_URL:  # Verificação *essencial*
    raise ValueError("A variável DATABASE_URL não está definida no .env")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"sslmode": "require"}}

db.init_app(app)  # Inicialize o db com o app
migrate = Migrate(app, db)  # Inicialize o Migrate com o app e o db

# Rotas
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Servidor está funcionando!"}), 200

@app.route('/ping', methods=['GET'])  # <----  Endpoint /ping Adicionado
def ping():
    return jsonify({"status": "ok"}), 200

@app.route('/generate_key', methods=['POST'])
def generate_key():
    try:
        data = request.get_json()
        expiration_days = data.get('expiration_days')

        new_key = Key.generate_key()
        if expiration_days is not None:
            expiration_time = datetime.now() + timedelta(days=expiration_days)
        else:
            expiration_time = datetime.now() + timedelta(days=30)  # Valor padrão: 30 dias

        new_key_record = Key(key=new_key, expiration_time=expiration_time)
        db.session.add(new_key_record)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Chave gerada com sucesso!',
            'key': new_key
        }), 200

    except Exception as e:
        print(f"Erro interno: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro interno do servidor.'}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        key = data.get('key')
        hwid = data.get('hwid')
        username = data.get('username')
        password = data.get('password')

        key_record = Key.query.filter_by(key=key).first()

        if not key_record or key_record.user_id is not None:  # Verifica se a chave já foi usada
            return jsonify({'success': False, 'message': 'Chave inválida ou já utilizada'}), 400

        if key_record.hwid and key_record.hwid != hwid:
            return jsonify({'success': False, 'message': 'Chave já vinculada a outro dispositivo'}), 400

        hashed_password = generate_password_hash(password)  # Hashe a senha AQUI
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.flush()

        key_record.hwid = hwid
        key_record.user_id = new_user.id
        db.session.commit()

        return jsonify({'success': True, 'message': 'Usuário cadastrado com sucesso'}), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao registrar usuário: {e}", exc_info=True)  # Log completo do erro
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

@app.route('/validate_key', methods=['POST']) # <---- Rota /validate_key corrigida
def validate_key():
    try:
        data = request.get_json()
        key = data.get('key')
        hwid = data.get('hwid')

        key_record = Key.query.filter_by(key=key).first()

        if not key_record or not key_record.active:
            return jsonify({'success': False, 'message': 'Chave inválida'}), 400

        if key_record.hwid != hwid:
            return jsonify({'success': False, 'message': 'HWID não corresponde'}), 400

        if key_record.expiration_time and datetime.now() > key_record.expiration_time:
            return jsonify({'success': False, 'message': 'Chave expirada'}), 400

        return jsonify({'success': True, 'message': 'Chave válida'}), 200

    except Exception as e:
        logging.error(f"Erro na validação da chave: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    port = os.environ.get("PORT", 5000)  # Pega a porta da variável de ambiente, usa 5000 como padrão
    app.run(debug=True, host='0.0.0.0', port=port) # Escuta em todas as interfaces e na porta especificada